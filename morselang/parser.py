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
