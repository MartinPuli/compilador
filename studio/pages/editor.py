"""Editor page: write code, run it, see tokens / AST / output / errors."""

from pathlib import Path

import streamlit as st

from studio.components import compile_and_run, lex_only, parse_only

EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"


def render() -> None:
    st.header("Editor")

    cols = st.columns([3, 1])
    with cols[1]:
        examples = sorted(EXAMPLES.glob("*.morse"))
        names = ["—"] + [e.name for e in examples]
        choice = st.selectbox("Cargar ejemplo", names)
        if choice != "—":
            for e in examples:
                if e.name == choice:
                    st.session_state["editor_source"] = e.read_text(encoding="utf-8")
                    break

    source = st.text_area(
        "Código MorseLang",
        value=st.session_state.get("editor_source", ""),
        height=280,
        key="editor_textarea",
    )
    st.session_state["editor_source"] = source

    btn_run, btn_tok, btn_ast = st.columns(3)
    do_run = btn_run.button("Ejecutar", use_container_width=True)
    do_tok = btn_tok.button("Tokens", use_container_width=True)
    do_ast = btn_ast.button("AST", use_container_width=True)

    st.divider()

    if do_run:
        result = compile_and_run(source)
        if result.error_message:
            st.error(f"Error {result.error_phase}: {result.error_message}")
        st.subheader("Salida")
        if result.output:
            for line in result.output:
                st.code(line)
        else:
            st.caption("(sin salida)")
        if result.final_symbol_table:
            st.subheader("Tabla de símbolos final")
            st.json(result.final_symbol_table)
    elif do_tok:
        result = lex_only(source)
        if result.error_message:
            st.error(f"Error {result.error_phase}: {result.error_message}")
        if result.tokens:
            st.subheader("Tokens")
            st.json([
                {"type": t.type.name, "lexeme": t.lexeme, "line": t.line}
                for t in result.tokens
            ])
    elif do_ast:
        result = parse_only(source)
        if result.error_message:
            st.error(f"Error {result.error_phase}: {result.error_message}")
        if result.ast_dict:
            st.subheader("AST")
            st.json(result.ast_dict)
