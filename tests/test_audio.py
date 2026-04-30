import numpy as np
import pytest

from morselang.audio import (
    decode_audio_to_morse,
    AudioDecodeResult,
    AudioDecodeError,
)


def synth_morse_wav(
    morse: str,
    *,
    wpm: int = 20,
    freq: int = 600,
    sr: int = 16000,
    silence_padding_ms: int = 100,
) -> tuple[np.ndarray, int]:
    """Generate a sine-wave audio array that encodes the given Morse string."""
    dot_ms = 1200.0 / wpm
    samples_per_ms = sr / 1000.0
    units = []
    pad = max(silence_padding_ms, 0)

    if pad:
        units.append((False, pad))

    i = 0
    while i < len(morse):
        ch = morse[i]
        if ch == ".":
            units.append((True, dot_ms))
            i += 1
            if i < len(morse) and morse[i] in ".-":
                units.append((False, dot_ms))
        elif ch == "-":
            units.append((True, dot_ms * 3))
            i += 1
            if i < len(morse) and morse[i] in ".-":
                units.append((False, dot_ms))
        elif ch == "/":
            units.append((False, dot_ms * 7))
            i += 1
        elif ch == " ":
            run = 0
            while i < len(morse) and morse[i] == " ":
                run += 1
                i += 1
            if run >= 3:
                units.append((False, dot_ms * 7))
            else:
                units.append((False, dot_ms * 3))
        else:
            i += 1

    if pad:
        units.append((False, pad))

    chunks = []
    for is_on, dur_ms in units:
        n = int(round(dur_ms * samples_per_ms))
        if is_on:
            t = np.arange(n) / sr
            chunks.append(0.5 * np.sin(2 * np.pi * freq * t))
        else:
            chunks.append(np.zeros(n, dtype=np.float64))
    samples = np.concatenate(chunks).astype(np.float32)
    return samples, sr


def test_decode_simple_letter_dot_dash():
    samples, sr = synth_morse_wav(".-", wpm=20)
    result = decode_audio_to_morse(samples, sr)
    assert isinstance(result, AudioDecodeResult)
    assert result.morse == ".-"
    # WPM detection is approximate; what matters is the `.`/`-` classification
    assert 12 <= result.detected_wpm <= 28


def test_decode_word_sos():
    samples, sr = synth_morse_wav("... --- ...", wpm=15)
    result = decode_audio_to_morse(samples, sr)
    assert result.morse == "... --- ..."


def test_decode_two_words_with_triple_space():
    samples, sr = synth_morse_wav(".-   -...", wpm=20)
    result = decode_audio_to_morse(samples, sr)
    assert ".-" in result.morse and "-..." in result.morse
    assert "   " in result.morse


def test_decode_handles_explicit_wpm_override():
    samples, sr = synth_morse_wav(".-", wpm=20)
    result = decode_audio_to_morse(samples, sr, wpm=20)
    assert result.morse == ".-"
    assert result.detected_wpm == 20.0


def test_decode_silent_raises():
    silent = np.zeros(16000, dtype=np.float32)
    with pytest.raises(AudioDecodeError):
        decode_audio_to_morse(silent, 16000)


def test_decode_empty_raises():
    with pytest.raises(AudioDecodeError):
        decode_audio_to_morse(np.array([], dtype=np.float32), 16000)


def test_decode_robust_to_moderate_noise():
    rng = np.random.default_rng(seed=42)
    samples, sr = synth_morse_wav("... --- ...", wpm=15)
    noise = rng.normal(0, 0.05, size=samples.shape).astype(np.float32)
    noisy = samples + noise
    result = decode_audio_to_morse(noisy, sr)
    assert result.morse == "... --- ..."


def test_load_audio_bytes_handles_wav(tmp_path):
    """`load_audio_bytes` should round-trip a synthesized WAV."""
    from io import BytesIO

    from scipy.io import wavfile

    from morselang.audio import load_audio_bytes

    samples, sr = synth_morse_wav(".-", wpm=20)
    samples_i16 = (samples * 32767).astype(np.int16)
    buf = BytesIO()
    wavfile.write(buf, sr, samples_i16)
    raw = buf.getvalue()

    out_samples, out_sr = load_audio_bytes(raw, filename="sample.wav")
    assert out_sr == sr
    assert out_samples.shape == samples.shape
    # decoded WAV bytes should still decode to ".-"
    result = decode_audio_to_morse(out_samples, out_sr)
    assert result.morse == ".-"


def test_load_audio_bytes_handles_mp3(tmp_path):
    """`load_audio_bytes` should also handle MP3 via pydub + imageio-ffmpeg.

    Skipped if pydub or imageio-ffmpeg aren't installed in the environment.
    """
    pydub = pytest.importorskip("pydub")
    pytest.importorskip("imageio_ffmpeg")
    from io import BytesIO

    from morselang.audio import load_audio_bytes

    samples, sr = synth_morse_wav("... --- ...", wpm=15)
    samples_i16 = (samples * 32767).astype(np.int16)
    seg = pydub.AudioSegment(
        samples_i16.tobytes(),
        frame_rate=sr,
        sample_width=2,
        channels=1,
    )
    import imageio_ffmpeg

    pydub.AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    mp3_buf = BytesIO()
    seg.export(mp3_buf, format="mp3", bitrate="64k")
    raw = mp3_buf.getvalue()

    out_samples, out_sr = load_audio_bytes(raw, filename="sample.mp3")
    assert out_sr == sr
    # mp3 is lossy, exact length / amplitudes vary slightly — just decode it
    result = decode_audio_to_morse(out_samples, out_sr)
    assert result.morse == "... --- ..."


def test_load_audio_bytes_empty_raises():
    from morselang.audio import AudioDecodeError, load_audio_bytes

    with pytest.raises(AudioDecodeError):
        load_audio_bytes(b"")
