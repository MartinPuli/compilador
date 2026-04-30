"""MorseLang Studio — Streamlit entry point.

Run with:  streamlit run studio/app.py
"""

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="MorseLang Studio",
        page_icon="📡",
        layout="wide",
    )
    st.title("MorseLang Studio")
    st.caption("Editor visual + decoder de audio Morse + inspector del TP")

    page = st.sidebar.radio(
        "Páginas",
        ["Editor", "Audio → Morse", "TP Inspector", "Ayuda"],
        index=0,
    )
    if page == "Editor":
        from studio.pages.editor import render
        render()
    elif page == "Audio → Morse":
        from studio.pages.audio_morse import render
        render()
    elif page == "TP Inspector":
        from studio.pages.tp_inspector import render
        render()
    else:
        from studio.pages.ayuda import render
        render()


if __name__ == "__main__":
    main()
