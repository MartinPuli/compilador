from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.ast_nodes import to_dict


def parse(src: str):
    return Parser(Lexer(src).tokenize()).parse()


def test_to_dict_for_simple_declaration():
    src = "...- .- .-. / -..- / .- ... .. --. / .---- -----"
    prog = parse(src)
    d = to_dict(prog)
    assert d == {
        "node": "Programa",
        "statements": [
            {
                "node": "Declaracion",
                "name": "X",
                "line": 1,
                "value": {"node": "NumeroLit", "value": 10, "line": 1},
            }
        ],
    }


def test_to_dict_for_binary_op():
    src = "-- --- ... - .-. .- .-. / .---- / -- .- ... / ..---"
    prog = parse(src)
    d = to_dict(prog)
    stmt = d["statements"][0]
    assert stmt["node"] == "MostrarStmt"
    expr = stmt["expr"]
    assert expr["node"] == "BinOp"
    assert expr["op"] == "MAS"
    assert expr["left"] == {"node": "NumeroLit", "value": 1, "line": 1}
    assert expr["right"] == {"node": "NumeroLit", "value": 2, "line": 1}


def test_to_dict_for_si_with_else():
    src = (
        "... .. / -..- / -- . -. / .....\n"
        "-- --- ... - .-. .- .-. / -..-\n"
        "... .. -. ---\n"
        "-- --- ... - .-. .- .-. / -----\n"
        "..-. .. -."
    )
    prog = parse(src)
    d = to_dict(prog)
    si = d["statements"][0]
    assert si["node"] == "SiStmt"
    assert isinstance(si["then_block"], list) and len(si["then_block"]) == 1
    assert isinstance(si["else_block"], list) and len(si["else_block"]) == 1
