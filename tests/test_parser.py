import pytest

from morselang.lexer import Lexer
from morselang.parser import Parser, ParseError
from morselang.ast_nodes import (
    Programa, Declaracion, Asignacion, MostrarStmt, SiStmt, MientrasStmt,
    BinOp, NumeroLit, TextoLit, BoolLit, IdentRef,
)


def parse(source: str) -> Programa:
    return Parser(Lexer(source).tokenize()).parse()


def test_parse_var_declaration_with_number():
    src = "...- .- .-. / -..- / .- ... .. --. / .---- -----"
    prog = parse(src)
    assert len(prog.statements) == 1
    s = prog.statements[0]
    assert isinstance(s, Declaracion)
    assert s.name == "X"
    assert isinstance(s.value, NumeroLit)
    assert s.value.value == 10


def test_parse_assignment():
    # X ASIG 5
    src = "-..- / .- ... .. --. / ....."
    prog = parse(src)
    assert isinstance(prog.statements[0], Asignacion)
    assert prog.statements[0].name == "X"
    assert prog.statements[0].value.value == 5


def test_parse_mostrar_string():
    # MOSTRAR "HOLA"
    src = '-- --- ... - .-. .- .-. / ".... --- .-.. .-"'
    prog = parse(src)
    s = prog.statements[0]
    assert isinstance(s, MostrarStmt)
    assert isinstance(s.expr, TextoLit)
    assert s.expr.value == "HOLA"


def test_parse_arithmetic_precedence():
    # VAR R ASIG 1 MAS 2 POR 3       →  R = 1 + (2 * 3)
    src = (
        "...- .- .-. / .-. / .- ... .. --. / "
        ".---- / -- .- ... / ..--- / .--. --- .-. / ...--"
    )
    prog = parse(src)
    decl = prog.statements[0]
    assert isinstance(decl, Declaracion)
    assert isinstance(decl.value, BinOp)
    assert decl.value.op == "MAS"
    assert isinstance(decl.value.left, NumeroLit) and decl.value.left.value == 1
    assert isinstance(decl.value.right, BinOp) and decl.value.right.op == "POR"


def test_parse_comparison():
    # VAR R ASIG X MEN 10
    src = (
        "...- .- .-. / .-. / .- ... .. --. / "
        "-..- / -- . -. / .---- -----"
    )
    prog = parse(src)
    decl = prog.statements[0]
    assert isinstance(decl.value, BinOp)
    assert decl.value.op == "MEN"


def test_parse_si_with_else():
    # SI X MEN 5
    #   MOSTRAR X
    # SINO
    #   MOSTRAR 0
    # FIN
    src = (
        "... .. / -..- / -- . -. / .....\n"
        "-- --- ... - .-. .- .-. / -..-\n"
        "... .. -. ---\n"
        "-- --- ... - .-. .- .-. / -----\n"
        "..-. .. -."
    )
    prog = parse(src)
    s = prog.statements[0]
    assert isinstance(s, SiStmt)
    assert s.else_block is not None
    assert len(s.then_block) == 1 and len(s.else_block) == 1


def test_parse_mientras():
    # MIENTRAS X MEN 5
    #   MOSTRAR X
    # FIN
    src = (
        "-- .. . -. - .-. .- ... / -..- / -- . -. / .....\n"
        "-- --- ... - .-. .- .-. / -..-\n"
        "..-. .. -."
    )
    prog = parse(src)
    s = prog.statements[0]
    assert isinstance(s, MientrasStmt)
    assert len(s.body) == 1


def test_parse_error_unexpected_token():
    # MOSTRAR FIN  (FIN is not a valid expression)
    src = "-- --- ... - .-. .- .-. / ..-. .. -."
    with pytest.raises(ParseError):
        parse(src)
