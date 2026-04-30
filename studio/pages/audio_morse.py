"""Audio → Morse page: record/upload audio, decode Morse, send to editor."""

import io

import numpy as np
import streamlit as st
from scipy.io import wavfile

from morselang.audio import decode_audio_to_morse, AudioDecodeError


def _load_wav(buffer: bytes) -> tuple[np.ndarray, int]:
    sr, samples = wavfile.read(io.BytesIO(buffer))
    if samples.dtype.kind in ("i", "u"):
        max_val = float(np.iinfo(samples.dtype).max)
        samples = samples.astype(np.float32) / max_val
    else:
        samples = samples.astype(np.float32)
    return samples, sr


def render() -> None:
    st.header("Audio → Morse")
    st.write(
        "Grabá Morse desde el micrófono o subí un archivo `.wav`. "
        "El decoder usa DSP puro (envolvente RMS + Otsu) para extraer la "
        "secuencia `.` `-` y separadores."
    )

    col_rec, col_up = st.columns(2)
    audio_bytes = None
    with col_rec:
        st.subheader("Grabar")
        if hasattr(st, "audio_input"):
            rec = st.audio_input("Mic")
            if rec is not None:
                audio_bytes = rec.getvalue()
        else:
            st.caption("Tu versión de Streamlit no tiene audio_input. Usá el upload.")
    with col_up:
        st.subheader("Subir .wav")
        up = st.file_uploader("Archivo de audio", type=["wav"])
        if up is not None:
            audio_bytes = up.read()

    wpm_override = st.slider(
        "WPM (0 = autodetectar)", min_value=0, max_value=40, value=0, step=1
    )

    if audio_bytes is None:
        st.caption("Esperando audio...")
        return

    try:
        samples, sr = _load_wav(audio_bytes)
    except Exception as exc:
        st.error(f"No se pudo leer el .wav: {exc}")
        return

    if st.button("Decodificar"):
        try:
            wpm = wpm_override if wpm_override > 0 else None
            result = decode_audio_to_morse(samples, sr, wpm=wpm)
        except AudioDecodeError as exc:
            st.error(f"Decodificación falló: {exc}")
            return

        st.subheader("Morse decodificado")
        st.code(result.morse)

        c1, c2 = st.columns(2)
        c1.metric("WPM detectado", f"{result.detected_wpm:.1f}")
        c2.metric("Dot length (ms)", f"{result.dot_length_ms:.1f}")

        st.subheader("Envolvente y threshold")
        env = result.envelope
        if env.size > 4000:
            step = env.size // 4000
            env = env[::step]
        st.line_chart(env)
        st.caption(f"Threshold: {result.threshold:.4f}")

        if st.button("Mandar al editor"):
            st.session_state["editor_source"] = result.morse
            st.success("Morse cargado en el editor — abrí la pestaña 'Editor'.")
