# MorseLang Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Python implementation of the MorseLang compiler — a programming language whose source code is written in Morse, with hand-written lexer, parser, semantic analyzer, and tree-walking interpreter, plus an ElevenLabs TTS client that narrates program output.

**Architecture:** Two-stage lexer (Morse codec → tokenizer), recursive descent parser (LL(1)) producing a typed AST, single-scope symbol table, visitor-based semantic check, tree-walking interpreter. CLI in `main.py`. Optional `--tts` flag streams `MOSTRAR` output through ElevenLabs to `output.mp3`.

**Tech Stack:** Python 3.11+, `pytest` for tests, `elevenlabs` SDK for TTS, no parser generators (everything by hand per the TP brief).

**Spec:** [`docs/superpowers/specs/2026-04-29-morselang-design.md`](../specs/2026-04-29-morselang-design.md)

---

## Conventions used in this plan

- Run all commands from the repo root: `c:/Users/marti/Documents/compilador`
- Python: `python` is the project interpreter (use `py -3.11` if needed on Windows)
- Tests: `pytest -q` for fast runs, `pytest -v` to inspect names
- Commit early, commit often. Each task ends with a commit step.
- TDD: write the failing test FIRST, run it to see it fail with a meaningful error, then implement.

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `morselang/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `requirements.txt`**

```
elevenlabs>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.env
*.mp3
output.mp3
.DS_Store
```

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -ra
```

- [ ] **Step 4: Create empty `morselang/__init__.py` and `tests/__init__.py`**

Both files: empty (zero bytes).

- [ ] **Step 5: Create `tests/conftest.py`**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

- [ ] **Step 6: Verify pytest runs (no tests yet, but should not error)**

Run: `pytest -q`
Expected: `no tests ran in <time>` (exit code 5 is fine — it just means no tests collected)

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .gitignore pytest.ini morselang/__init__.py tests/__init__.py tests/conftest.py
git commit -m "chore: scaffold project structure"
```

---

## Task 2: Morse codec — letters and digits

**Files:**
- Create: `morselang/morse.py`
- Create: `tests/test_morse.py`

- [ ] **Step 1: Write failing tests for `decode_letter`**

`tests/test_morse.py`:
```python
import pytest
from morselang.morse import decode_letter, MorseError


def test_decode_letter_basic():
    assert decode_letter(".-") == "A"
    assert decode_letter("-...") == "B"
    assert decode_letter("...") == "S"
    assert decode_letter("---") == "O"


def test_decode_letter_digits():
    assert decode_letter("-----") == "0"
    assert decode_letter(".----") == "1"
    assert decode_letter("....-") == "4"
    assert decode_letter("----.") == "9"


def test_decode_letter_invalid_raises():
    with pytest.raises(MorseError):
        decode_letter("........")  # not a valid Morse symbol
    with pytest.raises(MorseError):
        decode_letter("")  # empty
    with pytest.raises(MorseError):
        decode_letter(".x-")  # bad chars
```

- [ ] **Step 2: Run tests — confirm they fail**

Run: `pytest tests/test_morse.py -v`
Expected: `ImportError` (module `morselang.morse` does not exist).

- [ ] **Step 3: Implement `morselang/morse.py`**

```python
"""Morse codec used by the lexer.

The compiler reads programs whose alphabet is Morse. This module is the
isolated piece that translates between Morse symbols and the underlying
ASCII letters / digits the rest of the toolchain works with.
"""

from typing import Final


class MorseError(Exception):
    """Raised when a Morse symbol cannot be decoded."""


_MORSE_TO_CHAR: Final[dict[str, str]] = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
}

_CHAR_TO_MORSE: Final[dict[str, str]] = {v: k for k, v in _MORSE_TO_CHAR.items()}


def decode_letter(symbol: str) -> str:
    """Decode a single Morse symbol (e.g. '.-') into its ASCII letter/digit."""
    if not symbol or any(c not in ".-" for c in symbol):
        raise MorseError(f"Símbolo Morse inválido: {symbol!r}")
    if symbol not in _MORSE_TO_CHAR:
        raise MorseError(f"Secuencia Morse desconocida: {symbol!r}")
    return _MORSE_TO_CHAR[symbol]


def encode_letter(char: str) -> str:
    """Encode a single ASCII letter/digit into its Morse symbol (used in tests)."""
    upper = char.upper()
    if upper not in _CHAR_TO_MORSE:
        raise MorseError(f"Carácter no codificable en Morse: {char!r}")
    return _CHAR_TO_MORSE[upper]
```

- [ ] **Step 4: Run tests — confirm they pass**

Run: `pytest tests/test_morse.py -v`
Expected: 3 passed.

- [ ] **Step 5: Add tests for `decode_word`**

Append to `tests/test_morse.py`:
```python
from morselang.morse import decode_word


def test_decode_word_basic():
    assert decode_word("...   ---   ...") == "SOS"  # triple spaces also tolerated
    assert decode_word("... --- ...") == "SOS"      # canonical single-space


def test_decode_word_collapses_spaces():
    # multiple spaces between letters should be tolerated
    assert decode_word(".-     -...") == "AB"


def test_decode_word_empty_raises():
    with pytest.raises(MorseError):
        decode_word("")


def test_decode_word_propagates_letter_errors():
    with pytest.raises(MorseError):
        decode_word(".- ........")
```

- [ ] **Step 6: Run — confirm failure**

Run: `pytest tests/test_morse.py -v`
Expected: 4 new failures (`decode_word` not defined).

- [ ] **Step 7: Implement `decode_word` in `morselang/morse.py`**

Append to `morselang/morse.py`:
```python
def decode_word(morse_word: str) -> str:
    """Decode a Morse 'word' (letters separated by single or multiple spaces)."""
    stripped = morse_word.strip()
    if not stripped:
        raise MorseError("Palabra Morse vacía")
    letters = [decode_letter(sym) for sym in stripped.split() if sym]
    return "".join(letters)
```

- [ ] **Step 8: Run all morse tests**

Run: `pytest tests/test_morse.py -v`
Expected: 7 passed.

- [ ] **Step 9: Commit**

```bash
git add morselang/morse.py tests/test_morse.py
git commit -m "feat(morse): add Morse codec for letters, digits, and words"
```

---

## Task 3: Token model and source-line splitter

**Files:**
- Create: `morselang/tokens.py`
- Create: `tests/test_tokens.py`

- [ ] **Step 1: Write failing test for `Token` and `TokenType`**

`tests/test_tokens.py`:
```python
from morselang.tokens import Token, TokenType


def test_token_has_type_lexeme_line():
    t = Token(type=TokenType.IDENT, lexeme="X", line=1)
    assert t.type == TokenType.IDENT
    assert t.lexeme == "X"
    assert t.line == 1


def test_token_repr_useful_for_errors():
    t = Token(type=TokenType.NUMBER, lexeme="10", line=3)
    assert "NUMBER" in repr(t) and "10" in repr(t) and "3" in repr(t)


def test_tokentype_has_expected_members():
    expected = {
        "VAR", "MOSTRAR", "SI", "SINO", "MIENTRAS", "FIN",
        "VERDADERO", "FALSO",
        "MAS", "MENOS", "POR", "DIV", "IGUAL", "DIST", "MEN", "MAY", "ASIG",
        "IDENT", "NUMBER", "STRING",
        "LPAREN", "RPAREN",
        "NEWLINE", "EOF",
    }
    actual = {m.name for m in TokenType}
    missing = expected - actual
    assert not missing, f"Missing token types: {missing}"
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_tokens.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `morselang/tokens.py`**

```python
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
```

- [ ] **Step 4: Run — confirm pass**

Run: `pytest tests/test_tokens.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add morselang/tokens.py tests/test_tokens.py
git commit -m "feat(tokens): add Token model and TokenType enum"
```

---

## Task 4: Lexer

**Files:**
- Create: `morselang/lexer.py`
- Create: `tests/test_lexer.py`

The lexer's job: take raw Morse source, produce a list of `Token`. It does this in one pass:

1. Walk the source line by line.
2. On each line, split into "groups" using `/` (or 3+ spaces) as group separator.
3. Each group is decoded via `decode_word` to produce ASCII text.
4. Strings (text in `"..."`) are decoded as a unit.
5. The decoded text is classified into a `TokenType`.

- [ ] **Step 1: Write failing tests for simple programs**

`tests/test_lexer.py`:
```python
import pytest
from morselang.lexer import Lexer, LexerError
from morselang.tokens import TokenType


def types(tokens):
    return [t.type for t in tokens]


def lexemes(tokens):
    return [t.lexeme for t in tokens]


def test_lex_var_assign_number():
    # VAR X ASIG 10
    source = "...- .- .-. / -..- / .- ... .. --. / .---- -----"
    tokens = Lexer(source).tokenize()
    assert types(tokens) == [
        TokenType.VAR, TokenType.IDENT, TokenType.ASIG, TokenType.NUMBER,
        TokenType.NEWLINE, TokenType.EOF,
    ]
    assert lexemes(tokens)[:4] == ["VAR", "X", "ASIG", "10"]


def test_lex_mostrar_string():
    # MOSTRAR "HOLA"   →  HOLA in Morse: .... --- .-.. .-
    source = '-- --- ... - .-. .- .-. / ".... --- .-.. .-"'
    tokens = Lexer(source).tokenize()
    assert types(tokens) == [
        TokenType.MOSTRAR, TokenType.STRING, TokenType.NEWLINE, TokenType.EOF,
    ]
    assert tokens[1].lexeme == "HOLA"


def test_lex_two_lines_emit_newlines():
    source = "...- .- .-. / -..- / .- ... .. --. / .---- -----\n-- --- ... - .-. .- .-. / -..-"
    tokens = Lexer(source).tokenize()
    newlines = [t for t in tokens if t.type == TokenType.NEWLINE]
    assert len(newlines) == 2  # one per logical line


def test_lex_unknown_word_is_identifier():
    # CONTADOR  →  -.-. --- -. - .- -.. --- .-.
    source = "-.-. --- -. - .- -.. --- .-."
    tokens = Lexer(source).tokenize()
    assert tokens[0].type == TokenType.IDENT
    assert tokens[0].lexeme == "CONTADOR"


def test_lex_invalid_morse_raises_with_line():
    source = "........"  # not a valid Morse symbol
    with pytest.raises(LexerError) as exc:
        Lexer(source).tokenize()
    assert "línea 1" in str(exc.value).lower() or "linea 1" in str(exc.value).lower()


def test_lex_unterminated_string_raises():
    source = '-- --- ... - .-. .- .-. / ".... --- .-.. .-'
    with pytest.raises(LexerError):
        Lexer(source).tokenize()
```

- [ ] **Step 2: Run — confirm failures**

Run: `pytest tests/test_lexer.py -v`
Expected: ImportError on `morselang.lexer`.

- [ ] **Step 3: Implement `morselang/lexer.py`**

```python
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
```

- [ ] **Step 4: Run lexer tests — confirm pass**

Run: `pytest tests/test_lexer.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run full suite to make sure morse tests still pass**

Run: `pytest -q`
Expected: 13 passed.

- [ ] **Step 6: Commit**

```bash
git add morselang/lexer.py tests/test_lexer.py
git commit -m "feat(lexer): tokenize Morse source into typed tokens"
```

---

## Task 5: AST nodes

**Files:**
- Create: `morselang/ast_nodes.py`
- Create: `tests/test_ast_nodes.py`

- [ ] **Step 1: Write a test that constructs and inspects nodes**

`tests/test_ast_nodes.py`:
```python
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
```

- [ ] **Step 2: Run — confirm import failure**

Run: `pytest tests/test_ast_nodes.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `morselang/ast_nodes.py`**

```python
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
```

- [ ] **Step 4: Run — confirm pass**

Run: `pytest tests/test_ast_nodes.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add morselang/ast_nodes.py tests/test_ast_nodes.py
git commit -m "feat(ast): add AST node dataclasses"
```

---

## Task 6: Parser

**Files:**
- Create: `morselang/parser.py`
- Create: `tests/test_parser.py`

The parser is recursive descent (LL(1)). One method per non-terminal in the EBNF.

- [ ] **Step 1: Write tests for declarations and `MOSTRAR`**

`tests/test_parser.py`:
```python
import pytest

from morselang.lexer import Lexer
from morselang.parser import Parser, ParseError
from morselang.ast_nodes import (
    Programa, Declaracion, Asignacion, MostrarStmt, SiStmt, MientrasStmt,
    BinOp, NumeroLit, TextoLit, BoolLit, IdentRef,
)


def parse(source: str) -> Programa:
    return Parser(Lexer(source).tokenize()).parse()


def test_parse_var_declaration_with_number():
    src = "...- .- .-. / -..- / .- ... .. --. / .---- -----"
    prog = parse(src)
    assert len(prog.statements) == 1
    s = prog.statements[0]
    assert isinstance(s, Declaracion)
    assert s.name == "X"
    assert isinstance(s.value, NumeroLit)
    assert s.value.value == 10


def test_parse_assignment():
    # X ASIG 5
    src = "-..- / .- ... .. --. / ....."
    prog = parse(src)
    assert isinstance(prog.statements[0], Asignacion)
    assert prog.statements[0].name == "X"
    assert prog.statements[0].value.value == 5


def test_parse_mostrar_string():
    # MOSTRAR "HOLA"
    src = '-- --- ... - .-. .- .-. / ".... --- .-.. .-"'
    prog = parse(src)
    s = prog.statements[0]
    assert isinstance(s, MostrarStmt)
    assert isinstance(s.expr, TextoLit)
    assert s.expr.value == "HOLA"


def test_parse_arithmetic_precedence():
    # VAR R ASIG 1 MAS 2 POR 3       →  R = 1 + (2 * 3)
    src = (
        "...- .- .-. / .-. / .- ... .. --. / "
        ".---- / -- .- ... / ..--- / .--. --- .-. / ...--"
    )
    prog = parse(src)
    decl = prog.statements[0]
    assert isinstance(decl, Declaracion)
    assert isinstance(decl.value, BinOp)
    assert decl.value.op == "MAS"
    assert isinstance(decl.value.left, NumeroLit) and decl.value.left.value == 1
    assert isinstance(decl.value.right, BinOp) and decl.value.right.op == "POR"


def test_parse_comparison():
    # VAR R ASIG X MEN 10
    src = (
        "...- .- .-. / .-. / .- ... .. --. / "
        "-..- / -- . -. / .---- -----"
    )
    prog = parse(src)
    decl = prog.statements[0]
    assert isinstance(decl.value, BinOp)
    assert decl.value.op == "MEN"


def test_parse_si_with_else():
    # SI X MEN 5
    #   MOSTRAR X
    # SINO
    #   MOSTRAR 0
    # FIN
    src = (
        "... .. / -..- / -- . -. / .....\n"
        "-- --- ... - .-. .- .-. / -..-\n"
        "... .. -. ---\n"
        "-- --- ... - .-. .- .-. / -----\n"
        "..-. .. -."
    )
    prog = parse(src)
    s = prog.statements[0]
    assert isinstance(s, SiStmt)
    assert s.else_block is not None
    assert len(s.then_block) == 1 and len(s.else_block) == 1


def test_parse_mientras():
    # MIENTRAS X MEN 5
    #   MOSTRAR X
    # FIN
    src = (
        "-- .. . -. - .-. .- ... / -..- / -- . -. / .....\n"
        "-- --- ... - .-. .- .-. / -..-\n"
        "..-. .. -."
    )
    prog = parse(src)
    s = prog.statements[0]
    assert isinstance(s, MientrasStmt)
    assert len(s.body) == 1


def test_parse_error_unexpected_token():
    # MOSTRAR FIN  (FIN is not a valid expression)
    src = "-- --- ... - .-. .- .-. / ..-. .. -."
    with pytest.raises(ParseError):
        parse(src)
```

- [ ] **Step 2: Run — confirm import failure**

Run: `pytest tests/test_parser.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `morselang/parser.py`**

```python
"""Recursive-descent parser (LL(1)) for MorseLang.

One method per non-terminal in the EBNF grammar. The parser consumes a
list of tokens produced by the lexer and emits an AST rooted at `Programa`.
"""

from typing import Optional

from morselang.tokens import Token, TokenType
from morselang.ast_nodes import (
    Programa, Declaracion, Asignacion, MostrarStmt, SiStmt, MientrasStmt,
    BinOp, NumeroLit, TextoLit, BoolLit, IdentRef, Expr, Stmt,
)


_COMPARISON_OPS = {TokenType.IGUAL, TokenType.DIST, TokenType.MEN, TokenType.MAY}
_ADDITIVE_OPS = {TokenType.MAS, TokenType.MENOS}
_MULTIPLICATIVE_OPS = {TokenType.POR, TokenType.DIV}


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # --- public --------------------------------------------------------------

    def parse(self) -> Programa:
        statements: list[Stmt] = []
        self._skip_newlines()
        while not self._check(TokenType.EOF):
            statements.append(self._parse_statement())
            self._skip_newlines()
        return Programa(statements=statements)

    # --- statements ----------------------------------------------------------

    def _parse_statement(self) -> Stmt:
        tok = self._peek()
        if tok.type == TokenType.VAR:
            return self._parse_declaration()
        if tok.type == TokenType.MOSTRAR:
            return self._parse_mostrar()
        if tok.type == TokenType.SI:
            return self._parse_si()
        if tok.type == TokenType.MIENTRAS:
            return self._parse_mientras()
        if tok.type == TokenType.IDENT:
            return self._parse_assignment()
        raise ParseError(
            f"Línea {tok.line}: sentencia inesperada que comienza con {tok.lexeme!r}"
        )

    def _parse_declaration(self) -> Declaracion:
        var_tok = self._consume(TokenType.VAR)
        ident = self._consume(TokenType.IDENT)
        self._consume(TokenType.ASIG)
        value = self._parse_expression()
        self._expect_end_of_statement()
        return Declaracion(name=ident.lexeme, value=value, line=var_tok.line)

    def _parse_assignment(self) -> Asignacion:
        ident = self._consume(TokenType.IDENT)
        self._consume(TokenType.ASIG)
        value = self._parse_expression()
        self._expect_end_of_statement()
        return Asignacion(name=ident.lexeme, value=value, line=ident.line)

    def _parse_mostrar(self) -> MostrarStmt:
        tok = self._consume(TokenType.MOSTRAR)
        expr = self._parse_expression()
        self._expect_end_of_statement()
        return MostrarStmt(expr=expr, line=tok.line)

    def _parse_si(self) -> SiStmt:
        tok = self._consume(TokenType.SI)
        cond = self._parse_expression()
        self._expect_end_of_statement()
        then_block = self._parse_block(stop_tokens={TokenType.SINO, TokenType.FIN})
        else_block: Optional[list[Stmt]] = None
        if self._check(TokenType.SINO):
            self._consume(TokenType.SINO)
            self._expect_end_of_statement()
            else_block = self._parse_block(stop_tokens={TokenType.FIN})
        self._consume(TokenType.FIN)
        self._expect_end_of_statement_optional()
        return SiStmt(condition=cond, then_block=then_block, else_block=else_block, line=tok.line)

    def _parse_mientras(self) -> MientrasStmt:
        tok = self._consume(TokenType.MIENTRAS)
        cond = self._parse_expression()
        self._expect_end_of_statement()
        body = self._parse_block(stop_tokens={TokenType.FIN})
        self._consume(TokenType.FIN)
        self._expect_end_of_statement_optional()
        return MientrasStmt(condition=cond, body=body, line=tok.line)

    def _parse_block(self, stop_tokens: set[TokenType]) -> list[Stmt]:
        stmts: list[Stmt] = []
        self._skip_newlines()
        while not self._check_any(stop_tokens) and not self._check(TokenType.EOF):
            stmts.append(self._parse_statement())
            self._skip_newlines()
        return stmts

    # --- expressions ---------------------------------------------------------

    def _parse_expression(self) -> Expr:
        return self._parse_comparison()

    def _parse_comparison(self) -> Expr:
        left = self._parse_additive()
        if self._peek().type in _COMPARISON_OPS:
            op_tok = self._advance()
            right = self._parse_additive()
            left = BinOp(op=op_tok.type.name, left=left, right=right, line=op_tok.line)
        return left

    def _parse_additive(self) -> Expr:
        left = self._parse_multiplicative()
        while self._peek().type in _ADDITIVE_OPS:
            op_tok = self._advance()
            right = self._parse_multiplicative()
            left = BinOp(op=op_tok.type.name, left=left, right=right, line=op_tok.line)
        return left

    def _parse_multiplicative(self) -> Expr:
        left = self._parse_factor()
        while self._peek().type in _MULTIPLICATIVE_OPS:
            op_tok = self._advance()
            right = self._parse_factor()
            left = BinOp(op=op_tok.type.name, left=left, right=right, line=op_tok.line)
        return left

    def _parse_factor(self) -> Expr:
        tok = self._peek()
        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumeroLit(value=int(tok.lexeme), line=tok.line)
        if tok.type == TokenType.STRING:
            self._advance()
            return TextoLit(value=tok.lexeme, line=tok.line)
        if tok.type == TokenType.VERDADERO:
            self._advance()
            return BoolLit(value=True, line=tok.line)
        if tok.type == TokenType.FALSO:
            self._advance()
            return BoolLit(value=False, line=tok.line)
        if tok.type == TokenType.IDENT:
            self._advance()
            return IdentRef(name=tok.lexeme, line=tok.line)
        if tok.type == TokenType.LPAREN:
            self._advance()
            inner = self._parse_expression()
            self._consume(TokenType.RPAREN)
            return inner
        raise ParseError(
            f"Línea {tok.line}: se esperaba una expresión, vino {tok.lexeme!r}"
        )

    # --- helpers -------------------------------------------------------------

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _check(self, ttype: TokenType) -> bool:
        return self._peek().type == ttype

    def _check_any(self, ttypes: set[TokenType]) -> bool:
        return self._peek().type in ttypes

    def _consume(self, ttype: TokenType) -> Token:
        tok = self._peek()
        if tok.type != ttype:
            raise ParseError(
                f"Línea {tok.line}: se esperaba {ttype.name}, vino {tok.type.name} ({tok.lexeme!r})"
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._check(TokenType.NEWLINE):
            self._advance()

    def _expect_end_of_statement(self) -> None:
        if self._check(TokenType.NEWLINE):
            self._advance()
            return
        if self._check(TokenType.EOF):
            return
        tok = self._peek()
        raise ParseError(
            f"Línea {tok.line}: se esperaba fin de sentencia, vino {tok.lexeme!r}"
        )

    def _expect_end_of_statement_optional(self) -> None:
        if self._check(TokenType.NEWLINE):
            self._advance()
```

- [ ] **Step 4: Run parser tests**

Run: `pytest tests/test_parser.py -v`
Expected: 8 passed.

- [ ] **Step 5: Run full suite**

Run: `pytest -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add morselang/parser.py tests/test_parser.py
git commit -m "feat(parser): recursive-descent parser producing AST"
```

---

## Task 7: Symbol table

**Files:**
- Create: `morselang/symbol_table.py`
- Create: `tests/test_symbol_table.py`

- [ ] **Step 1: Write tests**

`tests/test_symbol_table.py`:
```python
import pytest
from morselang.symbol_table import SymbolTable, SymbolError


def test_declarar_then_consultar():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    info = st.consultar("X")
    assert info.tipo == "NUM"
    assert info.valor is None
    assert info.linea_declaracion == 1


def test_declarar_twice_raises():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    with pytest.raises(SymbolError):
        st.declarar("X", tipo="NUM", line=2)


def test_asignar_updates_value():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    st.asignar("X", 42)
    assert st.consultar("X").valor == 42


def test_asignar_undeclared_raises():
    st = SymbolTable()
    with pytest.raises(SymbolError):
        st.asignar("Y", 5)


def test_consultar_undeclared_raises():
    st = SymbolTable()
    with pytest.raises(SymbolError):
        st.consultar("Y")


def test_existe_returns_bool():
    st = SymbolTable()
    assert not st.existe("X")
    st.declarar("X", tipo="NUM", line=1)
    assert st.existe("X")


def test_snapshot_returns_dict_for_reporting():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    st.asignar("X", 10)
    snap = st.snapshot()
    assert "X" in snap
    assert snap["X"]["valor"] == 10
```

- [ ] **Step 2: Run — confirm import failure**

Run: `pytest tests/test_symbol_table.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

`morselang/symbol_table.py`:
```python
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
```

- [ ] **Step 4: Run tests — confirm pass**

Run: `pytest tests/test_symbol_table.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add morselang/symbol_table.py tests/test_symbol_table.py
git commit -m "feat(symbol-table): hash-based symbol table with declare/assign/lookup"
```

---

## Task 8: Semantic analyzer

**Files:**
- Create: `morselang/semantic.py`
- Create: `tests/test_semantic.py`

The analyzer walks the AST and enforces the rules from the spec (variable declared before use, no redeclaration, type compatibility, division by literal zero).

- [ ] **Step 1: Write tests**

`tests/test_semantic.py`:
```python
import pytest

from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.semantic import SemanticAnalyzer, SemanticError


def analyze(source: str):
    return SemanticAnalyzer().analyze(Parser(Lexer(source).tokenize()).parse())


def test_undeclared_variable_use_raises():
    # MOSTRAR Z
    src = "-- --- ... - .-. .- .-. / --.."
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "Z" in str(exc.value) and "no declarada" in str(exc.value).lower()


def test_redeclaration_raises():
    # VAR X ASIG 1
    # VAR X ASIG 2
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .----\n"
        "...- .- .-. / -..- / .- ... .. --. / ..---"
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "redeclaración" in str(exc.value).lower() or "redeclaracion" in str(exc.value).lower()


def test_type_mismatch_text_plus_num_raises():
    # VAR S ASIG "..."
    # VAR N ASIG S MAS 1
    src = (
        '...- .- .-. / ... / .- ... .. --. / "..."\n'
        "...- .- .-. / -. / .- ... .. --. / "
        "... / -- .- ... / .----"
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "tipo" in str(exc.value).lower()


def test_division_by_literal_zero_raises():
    # VAR X ASIG 1 DIV 0
    src = (
        "...- .- .-. / -..- / .- ... .. --. / "
        ".---- / -.. .. ...- / -----"
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "cero" in str(exc.value).lower()


def test_valid_program_returns_typed_table():
    # VAR X ASIG 10
    # MOSTRAR X
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    table = analyze(src)
    assert table.consultar("X").tipo == "NUM"


def test_condition_must_be_boolean():
    # SI 5
    #   MOSTRAR 1
    # FIN
    src = (
        "... .. / .....\n"
        "-- --- ... - .-. .- .-. / .----\n"
        "..-. .. -."
    )
    with pytest.raises(SemanticError) as exc:
        analyze(src)
    assert "bool" in str(exc.value).lower() or "condición" in str(exc.value).lower()
```

- [ ] **Step 2: Run — confirm import failure**

Run: `pytest tests/test_semantic.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

`morselang/semantic.py`:
```python
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
                    f"Línea {e.line}: operador {e.op} requiere NUM, recibió {lt} y {rt}"
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_semantic.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run full suite**

Run: `pytest -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add morselang/semantic.py tests/test_semantic.py
git commit -m "feat(semantic): type-check AST and validate variable usage"
```

---

## Task 9: Interpreter

**Files:**
- Create: `morselang/interpreter.py`
- Create: `tests/test_interpreter.py`

- [ ] **Step 1: Write tests**

`tests/test_interpreter.py`:
```python
import pytest

from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.semantic import SemanticAnalyzer
from morselang.interpreter import Interpreter, RuntimeError_ as MLRuntimeError


def run(source: str) -> list[str]:
    program = Parser(Lexer(source).tokenize()).parse()
    SemanticAnalyzer().analyze(program)
    interp = Interpreter()
    interp.execute(program)
    return interp.output


def test_run_var_and_mostrar():
    # VAR X ASIG 10
    # MOSTRAR X
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    assert run(src) == ["10"]


def test_run_arithmetic_precedence():
    # MOSTRAR 1 MAS 2 POR 3      → 7
    src = (
        "-- --- ... - .-. .- .-. / "
        ".---- / -- .- ... / ..--- / .--. --- .-. / ...--"
    )
    assert run(src) == ["7"]


def test_run_string_literal():
    # MOSTRAR "HOLA"
    src = '-- --- ... - .-. .- .-. / ".... --- .-.. .-"'
    assert run(src) == ["HOLA"]


def test_run_si_else_taken_when_false():
    # VAR X ASIG 0
    # SI X MAY 5
    #   MOSTRAR 1
    # SINO
    #   MOSTRAR 2
    # FIN
    src = (
        "...- .- .-. / -..- / .- ... .. --. / -----\n"
        "... .. / -..- / -- .- -.-- / .....\n"
        "-- --- ... - .-. .- .-. / .----\n"
        "... .. -. ---\n"
        "-- --- ... - .-. .- .-. / ..---\n"
        "..-. .. -."
    )
    assert run(src) == ["2"]


def test_run_mientras_counts_to_three():
    # VAR I ASIG 0
    # MIENTRAS I MEN 3
    #   MOSTRAR I
    #   I ASIG I MAS 1
    # FIN
    src = (
        "...- .- .-. / .. / .- ... .. --. / -----\n"
        "-- .. . -. - .-. .- ... / .. / -- . -. / ...--\n"
        "-- --- ... - .-. .- .-. / ..\n"
        ".. / .- ... .. --. / .. / -- .- ... / .----\n"
        "..-. .. -."
    )
    assert run(src) == ["0", "1", "2"]


def test_run_runtime_division_by_zero():
    # VAR Z ASIG 0
    # VAR R ASIG 5 DIV Z
    src = (
        "...- .- .-. / --.. / .- ... .. --. / -----\n"
        "...- .- .-. / .-. / .- ... .. --. / "
        "..... / -.. .. ...- / --.."
    )
    program = Parser(Lexer(src).tokenize()).parse()
    SemanticAnalyzer().analyze(program)  # passes — divisor is identifier, not literal
    interp = Interpreter()
    with pytest.raises(MLRuntimeError):
        interp.execute(program)
```

- [ ] **Step 2: Run — confirm import failure**

Run: `pytest tests/test_interpreter.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

`morselang/interpreter.py`:
```python
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
    # DIV handled separately to catch /0
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

    # --- statements ----------------------------------------------------------

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

    # --- expressions ---------------------------------------------------------

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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_interpreter.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run full suite**

Run: `pytest -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add morselang/interpreter.py tests/test_interpreter.py
git commit -m "feat(interpreter): tree-walking evaluator with output capture"
```

---

## Task 10: ElevenLabs TTS client

**Files:**
- Create: `morselang/tts.py`
- Create: `tests/test_tts.py`

We isolate ElevenLabs behind a thin wrapper so the interpreter and CLI never touch the SDK directly. The wrapper is fully testable with a mock.

- [ ] **Step 1: Write tests using a fake client**

`tests/test_tts.py`:
```python
from pathlib import Path
import pytest

from morselang.tts import narrate_to_file, TTSClientProtocol, TTSError


class FakeClient:
    def __init__(self, audio_bytes: bytes = b"FAKE_MP3") -> None:
        self.audio_bytes = audio_bytes
        self.calls: list[dict] = []

    def synthesize(self, text: str, voice_id: str) -> bytes:
        self.calls.append({"text": text, "voice_id": voice_id})
        return self.audio_bytes


def test_narrate_to_file_writes_audio(tmp_path: Path):
    fake = FakeClient(audio_bytes=b"abc123")
    out = tmp_path / "out.mp3"
    narrate_to_file(["HOLA", "10"], voice_id="es-1", out_path=out, client=fake)
    assert out.read_bytes() == b"abc123"
    assert fake.calls == [{"text": "HOLA. 10.", "voice_id": "es-1"}]


def test_narrate_to_file_with_empty_lines_raises(tmp_path: Path):
    with pytest.raises(TTSError):
        narrate_to_file([], voice_id="es-1", out_path=tmp_path / "x.mp3", client=FakeClient())
```

- [ ] **Step 2: Run — confirm import failure**

Run: `pytest tests/test_tts.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `morselang/tts.py`**

```python
"""ElevenLabs text-to-speech client (thin wrapper).

`narrate_to_file` takes the interpreter's output buffer, joins it into a
narration string, calls a TTS client (real or fake), and writes an MP3 to
disk. The real client is constructed lazily so missing API keys don't
break unrelated test runs.
"""

from pathlib import Path
from typing import Protocol


class TTSError(Exception):
    pass


class TTSClientProtocol(Protocol):
    def synthesize(self, text: str, voice_id: str) -> bytes: ...


def narrate_to_file(
    lines: list[str],
    *,
    voice_id: str,
    out_path: Path,
    client: TTSClientProtocol,
) -> None:
    if not lines:
        raise TTSError("No hay salida para narrar — el programa no produjo MOSTRAR.")
    text = ". ".join(lines) + "."
    audio = client.synthesize(text, voice_id=voice_id)
    out_path.write_bytes(audio)


def make_default_client(api_key: str) -> TTSClientProtocol:
    """Construct the real ElevenLabs-backed client. Lazy import keeps the
    SDK out of every test run."""
    from elevenlabs.client import ElevenLabs

    sdk = ElevenLabs(api_key=api_key)

    class _RealClient:
        def synthesize(self, text: str, voice_id: str) -> bytes:
            stream = sdk.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
            )
            return b"".join(stream)

    return _RealClient()
```

- [ ] **Step 4: Run tts tests**

Run: `pytest tests/test_tts.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add morselang/tts.py tests/test_tts.py
git commit -m "feat(tts): ElevenLabs wrapper with injectable client"
```

---

## Task 11: CLI

**Files:**
- Create: `main.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write smoke tests**

`tests/test_cli.py`:
```python
import subprocess
import sys
from pathlib import Path


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_cli_runs_simple_program(tmp_path: Path, monkeypatch):
    repo_root = Path(__file__).resolve().parent.parent
    src_file = tmp_path / "hola.morse"
    # MOSTRAR "HI"  →  HI in morse: .... ..
    src_file.write_text('-- --- ... - .-. .- .-. / ".... .."\n', encoding="utf-8")
    result = run_cli([str(src_file)], cwd=repo_root)
    assert result.returncode == 0, result.stderr
    assert "HI" in result.stdout


def test_cli_reports_lex_error_with_exit_code(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent
    src_file = tmp_path / "bad.morse"
    src_file.write_text("........\n", encoding="utf-8")  # invalid morse
    result = run_cli([str(src_file)], cwd=repo_root)
    assert result.returncode != 0
    assert "línea 1" in (result.stdout + result.stderr).lower() \
        or "linea 1" in (result.stdout + result.stderr).lower()


def test_cli_tokens_flag_lists_tokens(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent
    src_file = tmp_path / "x.morse"
    src_file.write_text("-- --- ... - .-. .- .-. / .----\n", encoding="utf-8")
    result = run_cli([str(src_file), "--tokens"], cwd=repo_root)
    assert result.returncode == 0
    assert "MOSTRAR" in result.stdout
    assert "NUMBER" in result.stdout
```

- [ ] **Step 2: Run — confirm CLI missing**

Run: `pytest tests/test_cli.py -v`
Expected: tests fail because `main.py` does not exist (`returncode != 0`, message about missing file).

- [ ] **Step 3: Implement `main.py`**

```python
"""MorseLang CLI.

Usage:
    python main.py file.morse
    python main.py file.morse --tokens
    python main.py file.morse --ast
    python main.py file.morse --tts
"""

import argparse
import os
import sys
from pathlib import Path

from morselang.lexer import Lexer, LexerError
from morselang.parser import Parser, ParseError
from morselang.semantic import SemanticAnalyzer, SemanticError
from morselang.interpreter import Interpreter, RuntimeError_
from morselang.tts import narrate_to_file, make_default_client, TTSError


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MorseLang compiler/interpreter")
    p.add_argument("source", help="Path to a .morse source file")
    p.add_argument("--tokens", action="store_true", help="Print token stream and exit")
    p.add_argument("--ast", action="store_true", help="Print AST and exit")
    p.add_argument("--tts", action="store_true", help="Synthesize output via ElevenLabs")
    p.add_argument("--tts-out", default="output.mp3", help="Where to write the TTS MP3")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    source_path = Path(args.source)
    if not source_path.is_file():
        print(f"error: archivo no encontrado: {source_path}", file=sys.stderr)
        return 2
    source = source_path.read_text(encoding="utf-8")

    try:
        tokens = Lexer(source).tokenize()
    except LexerError as exc:
        print(f"Error léxico: {exc}", file=sys.stderr)
        return 1

    if args.tokens:
        for t in tokens:
            print(t)
        return 0

    try:
        program = Parser(tokens).parse()
    except ParseError as exc:
        print(f"Error sintáctico: {exc}", file=sys.stderr)
        return 1

    if args.ast:
        from pprint import pprint
        pprint(program)
        return 0

    try:
        SemanticAnalyzer().analyze(program)
    except SemanticError as exc:
        print(f"Error semántico: {exc}", file=sys.stderr)
        return 1

    interp = Interpreter()
    try:
        interp.execute(program)
    except RuntimeError_ as exc:
        print(f"Error de ejecución: {exc}", file=sys.stderr)
        return 1

    if args.tts:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        if not api_key:
            print("error: ELEVENLABS_API_KEY no configurada", file=sys.stderr)
            return 1
        try:
            client = make_default_client(api_key)
            narrate_to_file(
                interp.output,
                voice_id=voice_id,
                out_path=Path(args.tts_out),
                client=client,
            )
            print(f"audio escrito en {args.tts_out}")
        except TTSError as exc:
            print(f"error TTS: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests**

Run: `pytest tests/test_cli.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run full suite**

Run: `pytest -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_cli.py
git commit -m "feat(cli): wire lexer→parser→semantic→interpreter→tts"
```

---

## Task 12: Example programs and end-to-end tests

**Files:**
- Create: `examples/hola.morse`
- Create: `examples/factorial.morse`
- Create: `examples/fizzbuzz.morse`
- Create: `examples/error_no_declarada.morse`
- Create: `examples/error_redeclaracion.morse`
- Create: `examples/error_division_cero.morse`
- Create: `tests/test_examples.py`

Reference (Morse keywords for hand-coding the examples):
- `VAR` = `...- .- .-.`
- `MOSTRAR` = `-- --- ... - .-. .- .-.`
- `SI` = `... ..`
- `SINO` = `... .. -. ---`
- `MIENTRAS` = `-- .. . -. - .-. .- ...`
- `FIN` = `..-. .. -.`
- `ASIG` = `.- ... .. --.`
- `MAS` = `-- .- ...`, `MENOS` = `-- . -. --- ...`, `POR` = `.--. --- .-.`, `DIV` = `-.. .. ...-`
- `IGUAL` = `.. --. ..- .- .-..`, `DIST` = `-.. .. ... -`, `MEN` = `-- . -.`, `MAY` = `-- .- -.--`

- [ ] **Step 1: Create `examples/hola.morse`**

Program: `MOSTRAR "HOLA MUNDO"` (HOLA MUNDO in Morse: `.... --- .-.. .-` + space + `-- ..- -. -.. ---`)

```
-- --- ... - .-. .- .-. / ".... --- .-.. .- -- ..- -. -.. ---"
```

- [ ] **Step 2: Create `examples/factorial.morse`**

Program: factorial of 5.

```
VAR N ASIG 5
VAR R ASIG 1
MIENTRAS N MAY 0
  R ASIG R POR N
  N ASIG N MENOS 1
FIN
MOSTRAR R
```

In Morse:

```
...- .- .-. / -. / .- ... .. --. / .....
...- .- .-. / .-. / .- ... .. --. / .----
-- .. . -. - .-. .- ... / -. / -- .- -.-- / -----
.-. / .- ... .. --. / .-. / .--. --- .-. / -.
-. / .- ... .. --. / -. / -- . -. --- ... / .----
..-. .. -.
-- --- ... - .-. .- .-. / .-.
```

- [ ] **Step 3: Create `examples/fizzbuzz.morse`**

Program (simplified — only fizz/buzz/normal, no fizzbuzz combo, since we don't have modulo):

We'll fake modulo with a counter pattern. To stay within scope, this example just shows the SI/SINO + MIENTRAS interaction:

```
VAR I ASIG 1
MIENTRAS I MEN 16
  SI I IGUAL 3
    MOSTRAR "FIZZ"
  SINO
    MOSTRAR I
  FIN
  I ASIG I MAS 1
FIN
```

Translated:

```
...- .- .-. / .. / .- ... .. --. / .----
-- .. . -. - .-. .- ... / .. / -- . -. / .---- -....
... .. / .. / .. --. ..- .- .-.. / ...--
-- --- ... - .-. .- .-. / "..-. .. --.. --.."
... .. -. ---
-- --- ... - .-. .- .-. / ..
..-. .. -.
.. / .- ... .. --. / .. / -- .- ... / .----
..-. .. -.
```

- [ ] **Step 4: Create error examples**

`examples/error_no_declarada.morse`:

```
-- --- ... - .-. .- .-. / --..
```

(MOSTRAR Z — Z is not declared)

`examples/error_redeclaracion.morse`:

```
...- .- .-. / -..- / .- ... .. --. / .----
...- .- .-. / -..- / .- ... .. --. / ..---
```

`examples/error_division_cero.morse`:

```
...- .- .-. / -..- / .- ... .. --. / ..... / -.. .. ...- / -----
```

(VAR X ASIG 5 DIV 0 — division by literal 0)

- [ ] **Step 5: Write end-to-end tests**

`tests/test_examples.py`:
```python
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def run(example: str, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "main.py", str(EXAMPLES / example), *extra_args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


def test_hola_runs_and_prints():
    result = run("hola.morse")
    assert result.returncode == 0, result.stderr
    assert "HOLA MUNDO" in result.stdout


def test_factorial_outputs_120():
    result = run("factorial.morse")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "120"


def test_fizzbuzz_runs_without_error():
    result = run("fizzbuzz.morse")
    assert result.returncode == 0, result.stderr
    assert "FIZZ" in result.stdout
    assert "1" in result.stdout


@pytest.mark.parametrize("path,fragment", [
    ("error_no_declarada.morse", "no declarada"),
    ("error_redeclaracion.morse", "redeclaraci"),
    ("error_division_cero.morse", "cero"),
])
def test_error_examples_fail_with_clear_message(path: str, fragment: str):
    result = run(path)
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert fragment in combined
```

- [ ] **Step 6: Run end-to-end tests**

Run: `pytest tests/test_examples.py -v`
Expected: 6 passed.

If `factorial` doesn't print 120, double-check the Morse for the loop body — common mistake is mis-counting spaces between letters of `MIENTRAS`.

- [ ] **Step 7: Run full suite**

Run: `pytest -q`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git add examples/ tests/test_examples.py
git commit -m "test: add example programs and end-to-end tests"
```

---

## Task 13: Documentation scaffolding (informe + uso_ia + README)

**Files:**
- Create: `README.md`
- Create: `docs/informe.md`
- Create: `docs/uso_ia.md`
- Create: `.env.example`

These files are required by the TP brief. We don't write the *full* informe here — we scaffold it with section headings that mirror the spec, so completing the report is a straight fill-in-the-blanks exercise after the implementation works end to end.

- [ ] **Step 1: Create `README.md`**

```markdown
# MorseLang

Lenguaje de programación cuyo código fuente se escribe en código Morse.
TP integrador de Lenguajes Formales y Compiladores.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

## Uso

```bash
python main.py examples/hola.morse              # ejecuta
python main.py examples/factorial.morse --tts   # ejecuta + narra con ElevenLabs
python main.py archivo.morse --tokens           # solo tokens
python main.py archivo.morse --ast              # solo AST
```

## Tests

```bash
pytest -q
```

## Variables de entorno

Para `--tts`:

- `ELEVENLABS_API_KEY` — clave de API
- `ELEVENLABS_VOICE_ID` — id de la voz (default: voz multilingüe estándar)

Ver `.env.example`.
```

- [ ] **Step 2: Create `.env.example`**

```
ELEVENLABS_API_KEY=tu_api_key_aca
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

- [ ] **Step 3: Create `docs/informe.md` skeleton**

```markdown
# TP Integrador — Compilador MorseLang

## 1. Definición del lenguaje
- Descripción informal: …
- Alfabeto: …
- Tokens: …
- Gramática (EBNF): ver spec
- Ejemplo de derivación: …

## 2. Análisis léxico
- Lista de tokens y regex: …
- Autómata (AFD): diagrama …
- Implementación: ver `morselang/lexer.py`
- Ejemplo de ejecución: ver `python main.py examples/hola.morse --tokens`

## 3. Análisis sintáctico
- Tipo: recursivo descendente (LL(1))
- Justificación: …
- Implementación: ver `morselang/parser.py`
- Ejemplo de árbol: ver `python main.py examples/hola.morse --ast`

## 4. Tabla de símbolos
- Información almacenada: tipo, valor, línea de declaración
- Estructura: hashmap (`dict` de Python)
- Ejemplo de uso: …

## 5. Análisis semántico
- Reglas: …
- Errores detectados: variable no declarada, redeclaración, tipos incompatibles, división por cero
- Ejemplos: ver `examples/error_*.morse`

## 6. Síntesis — intérprete + ElevenLabs
- Intérprete tree-walking (`morselang/interpreter.py`)
- TTS con ElevenLabs (`morselang/tts.py`)
- Ejemplo: `python main.py examples/factorial.morse --tts` genera `output.mp3`

## 7. Uso de IA
- Ver `docs/uso_ia.md`
```

- [ ] **Step 4: Create `docs/uso_ia.md` skeleton**

```markdown
# Uso de IA en el desarrollo del compilador

## Herramientas usadas
- Claude Code (Anthropic) — modelo Opus 4.7

## Prompts relevantes
- Diseño del lenguaje (entrada inicial sobre Morse + ElevenLabs)
- Diseño de la gramática EBNF
- Generación de la estructura del lexer en dos pasos
- Implementación del parser recursivo descendente
- (completar a medida que se desarrolla)

## Componentes generados con asistencia
- `morselang/morse.py` — generado, validado con tests
- `morselang/lexer.py` — generado y ajustado a mano (separadores)
- `morselang/parser.py` — generado, ajustada precedencia de operadores
- `morselang/semantic.py` — generado
- `morselang/interpreter.py` — generado
- (completar)

## Errores detectados en respuestas de IA
- (anotar a medida que aparecen — ej: "el parser inicial confundía MAS con MENOS por orden de checks")

## Correcciones manuales
- (idem — registrar diff o descripción)
```

- [ ] **Step 5: Verify the scaffolding files exist**

Run: `ls README.md .env.example docs/informe.md docs/uso_ia.md`
Expected: 4 files listed.

- [ ] **Step 6: Commit**

```bash
git add README.md .env.example docs/informe.md docs/uso_ia.md
git commit -m "docs: scaffold informe, uso_ia, README, env example"
```

---

## Self-Review Checklist

After implementing all tasks, verify:

- [ ] Spec coverage: every section of the design spec maps to at least one task. Walked the spec and confirmed: language definition (Task 5/6 — AST + parser), lexical analysis (Tasks 2-4), syntactic analysis (Task 6), symbol table (Task 7), semantic analysis (Task 8), synthesis with ElevenLabs (Tasks 9-10-11), examples and AI usage (Tasks 12-13).
- [ ] No placeholders: every step has concrete code or commands.
- [ ] Type / name consistency: `Token`, `TokenType`, `Programa`, `Declaracion`, `BinOp.op` (string `"MAS"` etc.), `SymbolTable.declarar/asignar/consultar/existe`, `Interpreter.execute`, `Interpreter.output`, `narrate_to_file` — all referenced consistently across tasks.
- [ ] Each task ends with a commit step.
- [ ] Each task has a verification step (run tests / check output) before commit.

---

## Execution Handoff

Plan complete and saved to [`docs/superpowers/plans/2026-04-29-morselang-implementation.md`](2026-04-29-morselang-implementation.md). Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

Which approach?
