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


def decode_word(morse_word: str) -> str:
    """Decode a Morse 'word' (letters separated by single or multiple spaces)."""
    stripped = morse_word.strip()
    if not stripped:
        raise MorseError("Palabra Morse vacía")
    letters = [decode_letter(sym) for sym in stripped.split() if sym]
    return "".join(letters)
