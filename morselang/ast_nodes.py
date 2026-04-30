"""AST node definitions for MorseLang.

Plain dataclasses — no behavior, just shape. The interpreter and semantic
analyzer dispatch on type via isinstance / match.
"""

from dataclasses import dataclass
from typing import Optional, Union


# --- Expressions -------------------------------------------------------------

@dataclass
class NumeroLit:
    value: int
    line: int


@dataclass
class TextoLit:
    value: str
    line: int


@dataclass
class BoolLit:
    value: bool
    line: int


@dataclass
class IdentRef:
    name: str
    line: int


@dataclass
class BinOp:
    op: str  # one of: MAS, MENOS, POR, DIV, IGUAL, DIST, MEN, MAY
    left: "Expr"
    right: "Expr"
    line: int


Expr = Union[NumeroLit, TextoLit, BoolLit, IdentRef, BinOp]


# --- Statements --------------------------------------------------------------

@dataclass
class Declaracion:
    name: str
    value: Expr
    line: int


@dataclass
class Asignacion:
    name: str
    value: Expr
    line: int


@dataclass
class MostrarStmt:
    expr: Expr
    line: int


@dataclass
class SiStmt:
    condition: Expr
    then_block: list["Stmt"]
    else_block: Optional[list["Stmt"]]
    line: int


@dataclass
class MientrasStmt:
    condition: Expr
    body: list["Stmt"]
    line: int


Stmt = Union[Declaracion, Asignacion, MostrarStmt, SiStmt, MientrasStmt]


@dataclass
class Programa:
    statements: list[Stmt]


def to_dict(node):
    """Serialize an AST node (or list / None) to a JSON-friendly dict.

    Used by the Studio to render the AST as a graph. Pure function — no
    behavior on the dataclasses themselves.
    """
    if node is None:
        return None
    if isinstance(node, list):
        return [to_dict(x) for x in node]

    name = type(node).__name__

    if isinstance(node, NumeroLit):
        return {"node": name, "value": node.value, "line": node.line}
    if isinstance(node, TextoLit):
        return {"node": name, "value": node.value, "line": node.line}
    if isinstance(node, BoolLit):
        return {"node": name, "value": node.value, "line": node.line}
    if isinstance(node, IdentRef):
        return {"node": name, "name": node.name, "line": node.line}
    if isinstance(node, BinOp):
        return {
            "node": name,
            "op": node.op,
            "left": to_dict(node.left),
            "right": to_dict(node.right),
            "line": node.line,
        }
    if isinstance(node, Declaracion):
        return {
            "node": name,
            "name": node.name,
            "value": to_dict(node.value),
            "line": node.line,
        }
    if isinstance(node, Asignacion):
        return {
            "node": name,
            "name": node.name,
            "value": to_dict(node.value),
            "line": node.line,
        }
    if isinstance(node, MostrarStmt):
        return {"node": name, "expr": to_dict(node.expr), "line": node.line}
    if isinstance(node, SiStmt):
        return {
            "node": name,
            "condition": to_dict(node.condition),
            "then_block": to_dict(node.then_block),
            "else_block": to_dict(node.else_block),
            "line": node.line,
        }
    if isinstance(node, MientrasStmt):
        return {
            "node": name,
            "condition": to_dict(node.condition),
            "body": to_dict(node.body),
            "line": node.line,
        }
    if isinstance(node, Programa):
        return {"node": name, "statements": to_dict(node.statements)}
    raise TypeError(f"Nodo AST desconocido: {type(node).__name__}")
