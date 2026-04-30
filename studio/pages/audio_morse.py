"""Audio → Morse page: record/upload audio, decode Morse, send to editor."""

import streamlit as st

from morselang.audio import decode_audio_to_morse, load_audio_bytes, AudioDecodeError


def render() -> None:
    st.header("Audio → Morse")
    st.write(
        "Grabá Morse desde el micrófono o subí un archivo de audio "
        "(`.wav`, `.mp3`, `.ogg`, `.m4a`, `.flac`). El decoder usa DSP "
        "puro (envolvente RMS + Otsu) para extraer la secuencia `.` `-` "
        "y separadores."
    )

    col_rec, col_up = st.columns(2)
    audio_bytes = None
    audio_filename = None
    with col_rec:
        st.subheader("Grabar")
        if hasattr(st, "audio_input"):
            rec = st.audio_input("Mic")
            if rec is not None:
                audio_bytes = rec.getvalue()
                audio_filename = "mic.wav"
        else:
            st.caption("Tu versión de Streamlit no tiene audio_input. Usá el upload.")
    with col_up:
        st.subheader("Subir audio")
        up = st.file_uploader(
            "Archivo de audio",
            type=["wav", "mp3", "ogg", "m4a", "flac"],
        )
        if up is not None:
            audio_bytes = up.read()
            audio_filename = up.name

    wpm_override = st.slider(
        "WPM (0 = autodetectar)", min_value=0, max_value=40, value=0, step=1
    )

    if audio_bytes is None:
        st.caption("Esperando audio...")
        return

    try:
        samples, sr = load_audio_bytes(audio_bytes, filename=audio_filename)
    except AudioDecodeError as exc:
        st.error(str(exc))
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
