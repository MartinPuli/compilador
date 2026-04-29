"""Token model shared by the lexer and parser."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    VAR = auto()
    MOSTRAR = auto()
    SI = auto()
    SINO = auto()
    MIENTRAS = auto()
    FIN = auto()
    VERDADERO = auto()
    FALSO = auto()
    # Operators
    MAS = auto()
    MENOS = auto()
    POR = auto()
    DIV = auto()
    IGUAL = auto()
    DIST = auto()
    MEN = auto()
    MAY = auto()
    ASIG = auto()
    # Literals & identifiers
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    # Structural
    NEWLINE = auto()
    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "VAR": TokenType.VAR,
    "MOSTRAR": TokenType.MOSTRAR,
    "SI": TokenType.SI,
    "SINO": TokenType.SINO,
    "MIENTRAS": TokenType.MIENTRAS,
    "FIN": TokenType.FIN,
    "VERDADERO": TokenType.VERDADERO,
    "FALSO": TokenType.FALSO,
    "MAS": TokenType.MAS,
    "MENOS": TokenType.MENOS,
    "POR": TokenType.POR,
    "DIV": TokenType.DIV,
    "IGUAL": TokenType.IGUAL,
    "DIST": TokenType.DIST,
    "MEN": TokenType.MEN,
    "MAY": TokenType.MAY,
    "ASIG": TokenType.ASIG,
}


@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.lexeme!r}, line={self.line})"
