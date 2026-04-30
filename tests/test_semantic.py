import pytest

from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.semantic import SemanticAnalyzer, SemanticError


def analyze(source: str):
    return SemanticAnalyzer().analyze(Parser(Lexer(source).tokenize()).parse())


def test_undeclared_variable_use_raises():
    # MOSTRAR Z
    src = "-- --- ... - .-. .- .-. / --.."
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "Z" in str(exc.value) and "no declarada" in str(exc.value).lower()


def test_redeclaration_raises():
    # VAR X ASIG 1
    # VAR X ASIG 2
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .----\n"
        "...- .- .-. / -..- / .- ... .. --. / ..---"
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "redeclaración" in str(exc.value).lower() or "redeclaracion" in str(exc.value).lower()


def test_type_mismatch_text_plus_num_raises():
    # VAR S ASIG "..."
    # VAR N ASIG S MAS 1
    src = (
        '...- .- .-. / ... / .- ... .. --. / "..."\n'
        "...- .- .-. / -. / .- ... .. --. / "
        "... / -- .- ... / .----"
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "tipo" in str(exc.value).lower()


def test_division_by_literal_zero_raises():
    # VAR X ASIG 1 DIV 0
    src = (
        "...- .- .-. / -..- / .- ... .. --. / "
        ".---- / -.. .. ...- / -----"
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "cero" in str(exc.value).lower()


def test_valid_program_returns_typed_table():
    # VAR X ASIG 10
    # MOSTRAR X
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    table = analyze(src)
    assert table.consultar("X").tipo == "NUM"


def test_condition_must_be_boolean():
    # SI 5
    #   MOSTRAR 1
    # FIN
    src = (
        "... .. / .....\n"
        "-- --- ... - .-. .- .-. / .----\n"
        "..-. .. -."
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "bool" in str(exc.value).lower() or "condición" in str(exc.value).lower()
