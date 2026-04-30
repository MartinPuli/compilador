"""Audio Morse decoder using DSP primitives only.

Pipeline:
    samples -> mono+norm -> envelope (RMS) -> Otsu threshold -> run-length
    encoding -> auto-detect dot length -> classify pulses -> emit Morse string
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import convolve


class AudioDecodeError(Exception):
    pass


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
