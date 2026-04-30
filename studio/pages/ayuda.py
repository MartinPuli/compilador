"""Ayuda page: Morse / keywords / operators reference tables."""

import streamlit as st

from morselang.morse import _MORSE_TO_CHAR, encode_letter
from morselang.tokens import KEYWORDS


def render() -> None:
    st.header("Ayuda")

    st.subheader("Tabla Morse — letras y dígitos")
    rows_letters = []
    rows_digits = []
    for morse, ch in _MORSE_TO_CHAR.items():
        if ch.isalpha():
            rows_letters.append({"Letra": ch, "Morse": morse})
        else:
            rows_digits.append({"Dígito": ch, "Morse": morse})
    rows_letters.sort(key=lambda r: r["Letra"])
    rows_digits.sort(key=lambda r: r["Dígito"])
    col1, col2 = st.columns(2)
    col1.dataframe(rows_letters, hide_index=True, use_container_width=True)
    col2.dataframe(rows_digits, hide_index=True, use_container_width=True)

    st.subheader("Keywords y operadores del lenguaje")
    rows = []
    for word in KEYWORDS:
        morse = " ".join(encode_letter(c) for c in word)
        rows.append({"Token": word, "Morse": morse})
    st.dataframe(rows, hide_index=True, use_container_width=True)

    st.subheader("Separadores")
    st.markdown(
        "- **Un espacio** entre letras de la misma palabra.\n"
        "- **Triple espacio** (`   `) o `/` entre palabras / tokens.\n"
        "- **Salto de línea** (`\\n`) entre sentencias.\n"
        "- **Comillas** (`\"...\"`) para literales de texto, contenido también en Morse, "
        "con triple-espacio para preservar espacios reales entre palabras."
    )
