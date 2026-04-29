"""Lexer: Morse source → Token stream.

Strategy: iterate the source line by line. Within a line, walk character by
character to handle string literals (`"..."`) atomically. Outside strings,
split on group separators (`/` or 3+ consecutive spaces). Each non-string
group is decoded via the Morse codec; the resulting ASCII text is then
classified into a TokenType (keyword / operator / number / identifier).
"""

import re
from typing import Optional

from morselang.morse import decode_word, MorseError
from morselang.tokens import KEYWORDS, Token, TokenType


class LexerError(Exception):
    """Raised when the source cannot be lexed."""


_GROUP_SEP_RE = re.compile(r"\s*/\s*|\s{3,}")


class Lexer:
    def __init__(self, source: str) -> None:
        self._source = source
        self._tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        lines = self._source.splitlines() or [""]
        for line_no, raw_line in enumerate(lines, start=1):
            self._tokenize_line(raw_line, line_no)
            if raw_line.strip():
                self._tokens.append(Token(TokenType.NEWLINE, "\\n", line_no))
        # always end with EOF, even on empty input
        last_line = max(1, len(lines))
        self._tokens.append(Token(TokenType.EOF, "", last_line))
        return self._tokens

    def _tokenize_line(self, line: str, line_no: int) -> None:
        groups = self._split_into_groups(line, line_no)
        for group in groups:
            if not group.strip():
                continue
            if group.startswith('"'):
                self._emit_string(group, line_no)
            else:
                self._emit_word(group, line_no)

    def _split_into_groups(self, line: str, line_no: int) -> list[str]:
        """Split a line into token groups, treating string literals atomically."""
        groups: list[str] = []
        i = 0
        n = len(line)
        buffer = ""
        while i < n:
            ch = line[i]
            if ch == '"':
                # flush whatever was buffered
                if buffer.strip():
                    groups.extend(_GROUP_SEP_RE.split(buffer.strip()))
                buffer = ""
                # find matching close quote
                j = line.find('"', i + 1)
                if j == -1:
                    raise LexerError(
                        f"Línea {line_no}: literal de texto sin cerrar"
                    )
                groups.append(line[i : j + 1])
                i = j + 1
                # consume any following whitespace / separator
                while i < n and (line[i] == " " or line[i] == "/"):
                    i += 1
            else:
                buffer += ch
                i += 1
        if buffer.strip():
            groups.extend(_GROUP_SEP_RE.split(buffer.strip()))
        return [g for g in groups if g and g.strip()]

    def _emit_word(self, morse_group: str, line_no: int) -> None:
        try:
            text = decode_word(morse_group)
        except MorseError as exc:
            raise LexerError(f"Línea {line_no}: {exc}") from exc
        self._tokens.append(self._classify(text, line_no))

    def _emit_string(self, raw: str, line_no: int) -> None:
        # raw is '"... morse ..."'; decode the inside
        inside = raw[1:-1]
        try:
            text = decode_word(inside) if inside.strip() else ""
        except MorseError as exc:
            raise LexerError(
                f"Línea {line_no}: contenido de texto inválido — {exc}"
            ) from exc
        self._tokens.append(Token(TokenType.STRING, text, line_no))

    def _classify(self, text: str, line_no: int) -> Token:
        if text in KEYWORDS:
            return Token(KEYWORDS[text], text, line_no)
        if text.isdigit():
            return Token(TokenType.NUMBER, text, line_no)
        if text.isalpha():
            return Token(TokenType.IDENT, text, line_no)
        raise LexerError(
            f"Línea {line_no}: token desconocido tras decodificar Morse: {text!r}"
        )
