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
