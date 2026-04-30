"""TP Inspector: pestañas que mapean cada Parte del TP al estado vivo."""

from pathlib import Path

import streamlit as st

from docs.tp_resources import (
    ALFABETO, EBNF, DERIVACION, AFD_ASCII,
    PARSER_JUSTIFICATION, SYMBOL_TABLE_DESC,
)
from morselang.tokens import KEYWORDS
from morselang.morse import encode_letter
from studio.components import compile_and_run, lex_only, parse_only

EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"
DOCS = Path(__file__).resolve().parent.parent.parent / "docs"


def render() -> None:
    st.header("TP Inspector — recorrido por las 7 Partes")
    tabs = st.tabs([
        "1. Definición", "2. Léxico", "3. Sintáctico",
        "4. Tabla de símbolos", "5. Semántico", "6. Síntesis", "7. Uso de IA",
    ])

    with tabs[0]:
        st.subheader("Alfabeto")
        st.code(ALFABETO)
        st.subheader("Tokens")
        rows = [{"Token": k, "Morse": " ".join(encode_letter(c) for c in k)} for k in KEYWORDS]
        st.dataframe(rows, hide_index=True, use_container_width=True)
        st.subheader("Gramática (EBNF)")
        st.code(EBNF, language="ebnf")
        st.subheader("Ejemplo de derivación — VAR X ASIG 10")
        st.code(DERIVACION)

    with tabs[1]:
        st.subheader("AFD del decodificador Morse")
        st.code(AFD_ASCII)
        st.subheader("Trace en vivo — Morse → tokens")
        sample = st.text_input(
            "Tipeá Morse para ver los tokens",
            value="...- .- .-. / -..- / .- ... .. --. / .---- -----",
        )
        result = lex_only(sample)
        if result.error_message:
            st.error(result.error_message)
        elif result.tokens:
            st.dataframe(
                [{"type": t.type.name, "lexeme": t.lexeme, "line": t.line} for t in result.tokens],
                hide_index=True, use_container_width=True,
            )

    with tabs[2]:
        st.subheader("Tipo de parser")
        st.write(PARSER_JUSTIFICATION)
        st.subheader("AST en vivo")
        sample = st.text_input(
            "Programa para parsear",
            value="...- .- .-. / -..- / .- ... .. --. / .---- -----",
            key="ast_sample_input",
        )
        result = parse_only(sample)
        if result.error_message:
            st.error(result.error_message)
        elif result.ast_dict:
            st.json(result.ast_dict)

    with tabs[3]:
        st.subheader("Estructura")
        st.write(SYMBOL_TABLE_DESC)
        st.subheader("Snapshot por sentencia (modo step)")
        default_program = ""
        fact = EXAMPLES / "factorial.morse"
        if fact.exists():
            default_program = fact.read_text(encoding="utf-8")
        sample = st.text_area(
            "Programa",
            value=default_program,
            height=180, key="symtab_program",
        )
        if st.button("Ejecutar y ver tabla paso a paso"):
            result = compile_and_run(sample)
            if result.error_message:
                st.error(f"Error {result.error_phase}: {result.error_message}")
            if result.symbol_table_snapshots:
                idx = st.slider("Sentencia #", 0, len(result.symbol_table_snapshots) - 1, 0)
                stmt_name, snap = result.symbol_table_snapshots[idx]
                st.write(f"Después de **{stmt_name}** (sentencia {idx + 1}):")
                st.json(snap)

    with tabs[4]:
        st.subheader("Programas con error semántico")
        for err_file in sorted(EXAMPLES.glob("error_*.morse")):
            with st.expander(err_file.name):
                src = err_file.read_text(encoding="utf-8")
                st.code(src)
                result = compile_and_run(src)
                if result.error_message:
                    st.error(f"{result.error_phase}: {result.error_message}")
                else:
                    st.warning("Este programa no produjo error — revisar el ejemplo.")

    with tabs[5]:
        st.subheader("Intérprete tree-walking")
        st.write(
            "El intérprete recorre el AST y ejecuta cada sentencia, manteniendo "
            "una tabla de símbolos en runtime. La salida de MOSTRAR se acumula "
            "para enviarse opcionalmente a ElevenLabs y producir un .mp3."
        )
        out_mp3 = Path(__file__).resolve().parent.parent.parent / "output.mp3"
        if out_mp3.exists():
            st.audio(out_mp3.read_bytes(), format="audio/mp3")
            st.caption(f"Último audio generado: {out_mp3.name}")
        else:
            st.info("Aún no se generó audio. Ejecutá un programa con --tts desde el CLI.")

    with tabs[6]:
        st.subheader("Bitácora de uso de IA")
        uso_ia = DOCS / "uso_ia.md"
        if uso_ia.exists():
            st.markdown(uso_ia.read_text(encoding="utf-8"))
        else:
            st.warning(f"Archivo no encontrado: {uso_ia}")
