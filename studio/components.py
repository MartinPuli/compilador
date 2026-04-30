"""Shared helpers used by Studio pages.

These wrap the compiler pipeline so each page can call a single function
to get tokens / AST / output / errors. Pure Python — no Streamlit imports
here so the helpers can be unit-tested independently.
"""

from dataclasses import dataclass, field
from typing import Optional

from morselang.lexer import Lexer, LexerError
from morselang.parser import Parser, ParseError
from morselang.semantic import SemanticAnalyzer, SemanticError
from morselang.interpreter import Interpreter, RuntimeError_
from morselang.ast_nodes import to_dict
from morselang.tokens import Token


@dataclass
class CompileResult:
    tokens: Optional[list[Token]] = None
    ast_dict: Optional[dict] = None
    output: list[str] = field(default_factory=list)
    symbol_table_snapshots: list[tuple[str, dict]] = field(default_factory=list)
    final_symbol_table: Optional[dict] = None
    error_phase: Optional[str] = None
    error_message: Optional[str] = None


def lex_only(source: str) -> CompileResult:
    res = CompileResult()
    try:
        res.tokens = Lexer(source).tokenize()
    except LexerError as exc:
        res.error_phase = "lex"
        res.error_message = str(exc)
    return res


def parse_only(source: str) -> CompileResult:
    res = lex_only(source)
    if res.tokens is None:
        return res
    try:
        program = Parser(res.tokens).parse()
        res.ast_dict = to_dict(program)
    except ParseError as exc:
        res.error_phase = "parse"
        res.error_message = str(exc)
    return res


def compile_and_run(source: str) -> CompileResult:
    res = parse_only(source)
    if res.ast_dict is None:
        return res
    program = Parser(res.tokens).parse()
    try:
        SemanticAnalyzer().analyze(program)
    except SemanticError as exc:
        res.error_phase = "sem"
        res.error_message = str(exc)
        return res
    interp = Interpreter()
    snapshots: list[tuple[str, dict]] = []

    def step_cb(stmt, snap):
        snapshots.append((type(stmt).__name__, snap))

    try:
        interp.execute(program, on_step=step_cb)
    except RuntimeError_ as exc:
        res.error_phase = "runtime"
        res.error_message = str(exc)
        res.output = list(interp.output)
        res.symbol_table_snapshots = snapshots
        return res
    res.output = list(interp.output)
    res.symbol_table_snapshots = snapshots
    res.final_symbol_table = snapshots[-1][1] if snapshots else {}
    return res
