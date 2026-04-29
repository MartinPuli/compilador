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
