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
