"""Audio Morse decoder using DSP primitives only.

Pipeline:
    samples -> mono+norm -> envelope (RMS) -> Otsu threshold -> run-length
    encoding -> auto-detect dot length -> classify pulses -> emit Morse string

Also exposes `load_audio_bytes` which decodes any common audio format
(wav, mp3, ogg, m4a, flac, ...) into a numpy array. Pure-Python wav is
done via scipy; everything else delegates to pydub + a bundled ffmpeg
binary (imageio-ffmpeg) so users don't have to install ffmpeg manually.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from scipy.signal import convolve


class AudioDecodeError(Exception):
    pass


def load_audio_bytes(raw: bytes, *, filename: str | None = None) -> tuple[np.ndarray, int]:
    """Decode raw audio bytes to (mono float32 samples in [-1, 1], sample_rate).

    Tries fast path with scipy for WAV first; on failure (e.g. MP3) falls
    back to pydub. Pydub needs an ffmpeg binary; we point it at the one
    bundled by `imageio-ffmpeg` so no system install is required.
    """
    if not raw:
        raise AudioDecodeError("Audio vacio")

    # Fast path: scipy handles standard PCM WAV without spawning ffmpeg.
    try:
        from scipy.io import wavfile

        sr, samples = wavfile.read(io.BytesIO(raw))
        return _normalize_samples(samples), int(sr)
    except Exception:
        pass

    # General path via pydub + bundled ffmpeg.
    try:
        from pydub import AudioSegment

        try:
            import imageio_ffmpeg

            AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass  # rely on a system-installed ffmpeg, if any

        fmt = None
        if filename and "." in filename:
            fmt = filename.rsplit(".", 1)[-1].lower()
        seg = AudioSegment.from_file(io.BytesIO(raw), format=fmt)
        if seg.channels == 2:
            seg = seg.set_channels(1)
        samples = np.array(seg.get_array_of_samples())
        return _normalize_samples(samples), int(seg.frame_rate)
    except AudioDecodeError:
        raise
    except Exception as exc:  # pragma: no cover (depends on pydub install)
        raise AudioDecodeError(
            f"No se pudo decodificar el audio: {exc}. "
            "Formatos soportados: wav, mp3, ogg, m4a, flac (mp3 y derivados "
            "requieren `pydub` + `imageio-ffmpeg` instalados)."
        ) from exc


def _normalize_samples(samples: np.ndarray) -> np.ndarray:
    """Convert any int/float sample buffer to mono float32 in [-1, 1]."""
    arr = np.asarray(samples)
    if arr.ndim == 2:
        arr = arr.mean(axis=1)
    if arr.dtype.kind in ("i", "u"):
        max_val = float(np.iinfo(arr.dtype).max)
        return (arr.astype(np.float32) / max_val) if max_val else arr.astype(np.float32)
    return arr.astype(np.float32)


@dataclass
class AudioDecodeResult:
    morse: str
    detected_wpm: float
    dot_length_ms: float
    envelope: np.ndarray
    threshold: float
    pulses: list[tuple[bool, float]]


def _to_mono(samples: np.ndarray) -> np.ndarray:
    if samples.ndim == 2:
        samples = samples.mean(axis=1)
    return samples.astype(np.float64)


def _normalize(samples: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(samples)))
    if peak == 0.0:
        raise AudioDecodeError("Audio en silencio: no se detectaron pulsos")
    return samples / peak


def _envelope(samples: np.ndarray, sr: int, window_ms: float = 3.0) -> np.ndarray:
    n = max(1, int(round(window_ms * sr / 1000.0)))
    kernel = np.ones(n) / n
    rms = np.sqrt(convolve(samples ** 2, kernel, mode="same"))
    return rms


def _otsu_threshold(values: np.ndarray) -> float:
    hist, edges = np.histogram(values, bins=256)
    total = hist.sum()
    if total == 0:
        return 0.0
    bin_centers = (edges[:-1] + edges[1:]) / 2
    weight_bg = np.cumsum(hist)
    weight_fg = total - weight_bg
    sum_total = (hist * bin_centers).sum()
    sum_bg = np.cumsum(hist * bin_centers)
    with np.errstate(divide="ignore", invalid="ignore"):
        mean_bg = np.where(weight_bg > 0, sum_bg / weight_bg, 0)
        mean_fg = np.where(weight_fg > 0, (sum_total - sum_bg) / weight_fg, 0)
        between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
    idx = int(np.argmax(between))
    return float(bin_centers[idx])


def _run_length_encode(binary: np.ndarray, sr: int) -> list[tuple[bool, float]]:
    if len(binary) == 0:
        return []
    runs: list[tuple[bool, int]] = []
    cur = bool(binary[0])
    count = 1
    for v in binary[1:]:
        b = bool(v)
        if b == cur:
            count += 1
        else:
            runs.append((cur, count))
            cur = b
            count = 1
    runs.append((cur, count))
    return [(on, count * 1000.0 / sr) for on, count in runs]


def _detect_dot_length_ms(pulses: list[tuple[bool, float]]) -> float:
    on_durations = [d for on, d in pulses if on]
    if not on_durations:
        raise AudioDecodeError("No se detectaron pulsos audibles")
    arr = np.array(on_durations)
    return float(np.percentile(arr, 25))


def _classify_pulses(pulses: list[tuple[bool, float]], dot_ms: float) -> str:
    out_parts: list[str] = []
    trimmed = list(pulses)
    while trimmed and not trimmed[0][0]:
        trimmed.pop(0)
    while trimmed and not trimmed[-1][0]:
        trimmed.pop()
    if not trimmed:
        raise AudioDecodeError("No se detectaron pulsos audibles")

    for is_on, dur in trimmed:
        if is_on:
            out_parts.append("." if dur < 1.5 * dot_ms else "-")
        else:
            if dur < 1.5 * dot_ms:
                continue
            elif dur < 5.0 * dot_ms:
                out_parts.append(" ")
            else:
                out_parts.append("   ")
    return "".join(out_parts)


def decode_audio_to_morse(
    samples: np.ndarray,
    sample_rate: int,
    *,
    wpm: float | None = None,
) -> AudioDecodeResult:
    if samples.size == 0:
        raise AudioDecodeError("Audio vacio")
    mono = _to_mono(samples)
    norm = _normalize(mono)
    env = _envelope(norm, sample_rate)
    threshold = _otsu_threshold(env)
    binary = env > threshold
    pulses = _run_length_encode(binary, sample_rate)
    if wpm is not None and wpm > 0:
        dot_ms = 1200.0 / wpm
    else:
        dot_ms = _detect_dot_length_ms(pulses)
    morse = _classify_pulses(pulses, dot_ms)
    detected_wpm = 1200.0 / dot_ms if dot_ms > 0 else 0.0
    return AudioDecodeResult(
        morse=morse,
        detected_wpm=detected_wpm,
        dot_length_ms=dot_ms,
        envelope=env,
        threshold=threshold,
        pulses=pulses,
    )
