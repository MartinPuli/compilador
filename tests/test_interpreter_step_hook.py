from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.semantic import SemanticAnalyzer
from morselang.interpreter import Interpreter


def execute(src):
    prog = Parser(Lexer(src).tokenize()).parse()
    SemanticAnalyzer().analyze(prog)
    return prog


def test_on_step_called_once_per_top_level_statement():
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    prog = execute(src)
    calls = []

    def cb(stmt, snapshot):
        calls.append((type(stmt).__name__, dict(snapshot)))

    Interpreter().execute(prog, on_step=cb)
    assert [c[0] for c in calls] == ["Declaracion", "MostrarStmt"]
    assert calls[0][1]["X"]["valor"] == 10


def test_on_step_default_none_keeps_old_behavior():
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    prog = execute(src)
    interp = Interpreter()
    interp.execute(prog)
    assert interp.output == ["10"]
