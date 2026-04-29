from morselang.ast_nodes import (
    Programa, Declaracion, Asignacion, MostrarStmt, SiStmt, MientrasStmt,
    BinOp, NumeroLit, TextoLit, BoolLit, IdentRef,
)


def test_numero_lit_holds_int():
    n = NumeroLit(value=10, line=1)
    assert n.value == 10 and n.line == 1


def test_binop_holds_op_and_children():
    a = NumeroLit(value=1, line=1)
    b = NumeroLit(value=2, line=1)
    op = BinOp(op="MAS", left=a, right=b, line=1)
    assert op.op == "MAS" and op.left is a and op.right is b


def test_programa_is_list_of_statements():
    decl = Declaracion(name="X", value=NumeroLit(value=10, line=1), line=1)
    show = MostrarStmt(expr=IdentRef(name="X", line=2), line=2)
    p = Programa(statements=[decl, show])
    assert len(p.statements) == 2


def test_si_with_else_branch_optional():
    cond = BoolLit(value=True, line=1)
    si = SiStmt(condition=cond, then_block=[], else_block=None, line=1)
    assert si.else_block is None
    si2 = SiStmt(condition=cond, then_block=[], else_block=[], line=1)
    assert si2.else_block == []


def test_mientras_holds_body_list():
    cond = BoolLit(value=True, line=1)
    w = MientrasStmt(condition=cond, body=[], line=1)
    assert w.body == []
