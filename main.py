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
