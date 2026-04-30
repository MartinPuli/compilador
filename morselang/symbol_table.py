"""Single-scope symbol table.

Maps identifier names to (tipo, valor, línea de declaración). Used by the
semantic analyzer (declaration / type checks) and by the interpreter
(runtime variable storage).
"""

from dataclasses import dataclass
from typing import Any, Optional


class SymbolError(Exception):
    """Raised on undeclared / redeclared symbol operations."""


@dataclass
class SymbolInfo:
    tipo: str  # "NUM" | "TEXTO" | "BOOL"
    valor: Optional[Any]
    linea_declaracion: int


class SymbolTable:
    def __init__(self) -> None:
        self._table: dict[str, SymbolInfo] = {}

    def declarar(self, name: str, *, tipo: str, line: int) -> None:
        if name in self._table:
            existing = self._table[name]
            raise SymbolError(
                f"Línea {line}: redeclaración de '{name}' "
                f"(declarada originalmente en línea {existing.linea_declaracion})"
            )
        self._table[name] = SymbolInfo(tipo=tipo, valor=None, linea_declaracion=line)

    def asignar(self, name: str, valor: Any) -> None:
        if name not in self._table:
            raise SymbolError(f"variable '{name}' no declarada")
        self._table[name].valor = valor

    def consultar(self, name: str) -> SymbolInfo:
        if name not in self._table:
            raise SymbolError(f"variable '{name}' no declarada")
        return self._table[name]

    def existe(self, name: str) -> bool:
        return name in self._table

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "tipo": info.tipo,
                "valor": info.valor,
                "linea_declaracion": info.linea_declaracion,
            }
            for name, info in self._table.items()
        }
