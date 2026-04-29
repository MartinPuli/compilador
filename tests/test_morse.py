import pytest
from morselang.morse import decode_letter, decode_word, MorseError


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
