"""Semantic analyzer for MorseLang.

Walks the AST, enforcing:
- Variables must be declared before being used.
- Variables cannot be redeclared.
- Arithmetic operands must be NUM.
- Comparison operands must be of the same type.
- Conditions of SI / MIENTRAS must be BOOL.
- Division by literal zero is rejected at compile time.
"""

from morselang.ast_nodes import (
    Programa, Declaracion, Asignacion, MostrarStmt, SiStmt, MientrasStmt,
    BinOp, NumeroLit, TextoLit, BoolLit, IdentRef, Expr, Stmt,
)
from morselang.symbol_table import SymbolTable, SymbolError


class SemanticError(Exception):
    pass


_ARITH = {"MAS", "MENOS", "POR", "DIV"}
_COMPARE = {"IGUAL", "DIST", "MEN", "MAY"}


class SemanticAnalyzer:
    def __init__(self) -> None:
        self._table = SymbolTable()

    def analyze(self, program: Programa) -> SymbolTable:
        for stmt in program.statements:
            self._stmt(stmt)
        return self._table

    # --- statements ----------------------------------------------------------

    def _stmt(self, s: Stmt) -> None:
        if isinstance(s, Declaracion):
            self._declaracion(s)
        elif isinstance(s, Asignacion):
            self._asignacion(s)
        elif isinstance(s, MostrarStmt):
            self._expr(s.expr)
        elif isinstance(s, SiStmt):
            self._control(s.condition, s.line)
            for sub in s.then_block:
                self._stmt(sub)
            if s.else_block is not None:
                for sub in s.else_block:
                    self._stmt(sub)
        elif isinstance(s, MientrasStmt):
            self._control(s.condition, s.line)
            for sub in s.body:
                self._stmt(sub)
        else:  # pragma: no cover
            raise SemanticError(f"Sentencia desconocida: {s!r}")

    def _declaracion(self, d: Declaracion) -> None:
        tipo = self._expr(d.value)
        try:
            self._table.declarar(d.name, tipo=tipo, line=d.line)
        except SymbolError as exc:
            raise SemanticError(str(exc)) from exc
        self._table.asignar(d.name, None)

    def _asignacion(self, a: Asignacion) -> None:
        if not self._table.existe(a.name):
            raise SemanticError(f"Línea {a.line}: variable '{a.name}' no declarada")
        expected = self._table.consultar(a.name).tipo
        actual = self._expr(a.value)
        if expected != actual:
            raise SemanticError(
                f"Línea {a.line}: tipo incompatible — esperado {expected}, recibido {actual}"
            )

    def _control(self, condition: Expr, line: int) -> None:
        tipo = self._expr(condition)
        if tipo != "BOOL":
            raise SemanticError(
                f"Línea {line}: la condición debe ser BOOL, vino {tipo}"
            )

    # --- expressions ---------------------------------------------------------

    def _expr(self, e: Expr) -> str:
        if isinstance(e, NumeroLit):
            return "NUM"
        if isinstance(e, TextoLit):
            return "TEXTO"
        if isinstance(e, BoolLit):
            return "BOOL"
        if isinstance(e, IdentRef):
            if not self._table.existe(e.name):
                raise SemanticError(f"Línea {e.line}: variable '{e.name}' no declarada")
            return self._table.consultar(e.name).tipo
        if isinstance(e, BinOp):
            return self._binop(e)
        raise SemanticError(f"Expresión desconocida: {e!r}")

    def _binop(self, e: BinOp) -> str:
        lt = self._expr(e.left)
        rt = self._expr(e.right)
        if e.op in _ARITH:
            if lt != "NUM" or rt != "NUM":
                raise SemanticError(
                    f"Línea {e.line}: tipo incompatible — operador {e.op} requiere NUM, recibió {lt} y {rt}"
                )
            if e.op == "DIV" and isinstance(e.right, NumeroLit) and e.right.value == 0:
                raise SemanticError(f"Línea {e.line}: división por cero")
            return "NUM"
        if e.op in _COMPARE:
            if lt != rt:
                raise SemanticError(
                    f"Línea {e.line}: comparación entre tipos distintos ({lt} vs {rt})"
                )
            return "BOOL"
        raise SemanticError(f"Línea {e.line}: operador desconocido {e.op}")
