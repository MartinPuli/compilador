"""Tree-walking interpreter for MorseLang.

Walks the AST, evaluates expressions, mutates a SymbolTable for variable
storage. Captures all MOSTRAR output into `self.output` (list of strings)
so it can be replayed by the TTS layer.
"""

from morselang.ast_nodes import (
    Programa, Declaracion, Asignacion, MostrarStmt, SiStmt, MientrasStmt,
    BinOp, NumeroLit, TextoLit, BoolLit, IdentRef, Expr, Stmt,
)
from morselang.symbol_table import SymbolTable


class RuntimeError_(Exception):
    """Renamed to avoid shadowing the builtin."""


_ARITH_OPS = {
    "MAS":   lambda a, b: a + b,
    "MENOS": lambda a, b: a - b,
    "POR":   lambda a, b: a * b,
}


_COMPARE_OPS = {
    "IGUAL": lambda a, b: a == b,
    "DIST":  lambda a, b: a != b,
    "MEN":   lambda a, b: a < b,
    "MAY":   lambda a, b: a > b,
}


class Interpreter:
    def __init__(self) -> None:
        self._env = SymbolTable()
        self.output: list[str] = []

    def execute(self, program: Programa) -> None:
        for stmt in program.statements:
            self._stmt(stmt)

    def _stmt(self, s: Stmt) -> None:
        if isinstance(s, Declaracion):
            value = self._eval(s.value)
            tipo = _runtime_type(value)
            if not self._env.existe(s.name):
                self._env.declarar(s.name, tipo=tipo, line=s.line)
            self._env.asignar(s.name, value)
        elif isinstance(s, Asignacion):
            value = self._eval(s.value)
            self._env.asignar(s.name, value)
        elif isinstance(s, MostrarStmt):
            value = self._eval(s.expr)
            text = _format(value)
            print(text)
            self.output.append(text)
        elif isinstance(s, SiStmt):
            cond = self._eval(s.condition)
            block = s.then_block if cond else (s.else_block or [])
            for sub in block:
                self._stmt(sub)
        elif isinstance(s, MientrasStmt):
            while self._eval(s.condition):
                for sub in s.body:
                    self._stmt(sub)

    def _eval(self, e: Expr):
        if isinstance(e, NumeroLit):
            return e.value
        if isinstance(e, TextoLit):
            return e.value
        if isinstance(e, BoolLit):
            return e.value
        if isinstance(e, IdentRef):
            return self._env.consultar(e.name).valor
        if isinstance(e, BinOp):
            left = self._eval(e.left)
            right = self._eval(e.right)
            if e.op in _ARITH_OPS:
                return _ARITH_OPS[e.op](left, right)
            if e.op == "DIV":
                if right == 0:
                    raise RuntimeError_(f"Línea {e.line}: división por cero en tiempo de ejecución")
                return left // right
            if e.op in _COMPARE_OPS:
                return _COMPARE_OPS[e.op](left, right)
            raise RuntimeError_(f"Línea {e.line}: operador desconocido {e.op}")
        raise RuntimeError_(f"Expresión desconocida: {e!r}")


def _runtime_type(value) -> str:
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, int):
        return "NUM"
    if isinstance(value, str):
        return "TEXTO"
    raise RuntimeError_(f"Valor con tipo no soportado: {value!r}")


def _format(value) -> str:
    if isinstance(value, bool):
        return "VERDADERO" if value else "FALSO"
    return str(value)
