import pytest

from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.semantic import SemanticAnalyzer
from morselang.interpreter import Interpreter, RuntimeError_ as MLRuntimeError


def run(source: str) -> list[str]:
    program = Parser(Lexer(source).tokenize()).parse()
    SemanticAnalyzer().analyze(program)
    interp = Interpreter()
    interp.execute(program)
    return interp.output


def test_run_var_and_mostrar():
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    assert run(src) == ["10"]


def test_run_arithmetic_precedence():
    src = (
        "-- --- ... - .-. .- .-. / "
        ".---- / -- .- ... / ..--- / .--. --- .-. / ...--"
    )
    assert run(src) == ["7"]


def test_run_string_literal():
    src = '-- --- ... - .-. .- .-. / ".... --- .-.. .-"'
    assert run(src) == ["HOLA"]


def test_run_si_else_taken_when_false():
    src = (
        "...- .- .-. / -..- / .- ... .. --. / -----\n"
        "... .. / -..- / -- .- -.-- / .....\n"
        "-- --- ... - .-. .- .-. / .----\n"
        "... .. -. ---\n"
        "-- --- ... - .-. .- .-. / ..---\n"
        "..-. .. -."
    )
    assert run(src) == ["2"]


def test_run_mientras_counts_to_three():
    src = (
        "...- .- .-. / .. / .- ... .. --. / -----\n"
        "-- .. . -. - .-. .- ... / .. / -- . -. / ...--\n"
        "-- --- ... - .-. .- .-. / ..\n"
        ".. / .- ... .. --. / .. / -- .- ... / .----\n"
        "..-. .. -."
    )
    assert run(src) == ["0", "1", "2"]


def test_run_runtime_division_by_zero():
    src = (
        "...- .- .-. / --.. / .- ... .. --. / -----\n"
        "...- .- .-. / .-. / .- ... .. --. / "
        "..... / -.. .. ...- / --.."
    )
    program = Parser(Lexer(src).tokenize()).parse()
    SemanticAnalyzer().analyze(program)
    interp = Interpreter()
    with pytest.raises(MLRuntimeError):
        interp.execute(program)
