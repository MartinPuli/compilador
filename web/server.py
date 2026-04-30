"""Flask server for MORSE.LAB — the polished web UI for the MorseLang compiler.

Serves a single-page app and a small JSON API that wraps the compiler:

    GET  /                  → SPA
    POST /api/run           → execute source, return output + symbol table
    POST /api/tokens        → tokenize, return token stream
    POST /api/ast           → parse, return AST as dict
    POST /api/decode-audio  → decode audio bytes to Morse
    GET  /api/examples      → list .morse files in examples/
    GET  /api/example/<n>   → return the contents of an example
    GET  /api/reference     → Morse table + keyword/operator tables (for Ayuda)
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, render_template, request, send_from_directory
from scipy.io import wavfile

from morselang.audio import AudioDecodeError, decode_audio_to_morse
from morselang.morse import _MORSE_TO_CHAR, encode_letter
from morselang.tokens import KEYWORDS
from studio.components import compile_and_run, lex_only, parse_only

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"

app = Flask(
    __name__,
    static_folder=str(Path(__file__).parent / "static"),
    template_folder=str(Path(__file__).parent / "templates"),
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def api_run():
    source = (request.json or {}).get("source", "")
    res = compile_and_run(source)
    return jsonify(_serialize(res))


@app.route("/api/tokens", methods=["POST"])
def api_tokens():
    source = (request.json or {}).get("source", "")
    res = lex_only(source)
    return jsonify(_serialize(res))


@app.route("/api/ast", methods=["POST"])
def api_ast():
    source = (request.json or {}).get("source", "")
    res = parse_only(source)
    return jsonify(_serialize(res))


@app.route("/api/decode-audio", methods=["POST"])
def api_decode_audio():
    if "audio" not in request.files:
        return jsonify({"error": "Falta el archivo 'audio'"}), 400
    f = request.files["audio"]
    raw = f.read()
    try:
        sr, samples = wavfile.read(io.BytesIO(raw))
    except Exception as exc:
        return jsonify({"error": f"No se pudo leer el .wav: {exc}"}), 400
    if samples.dtype.kind in ("i", "u"):
        max_val = float(np.iinfo(samples.dtype).max)
        samples = samples.astype(np.float32) / max_val
    else:
        samples = samples.astype(np.float32)
    wpm = request.form.get("wpm")
    wpm_val = float(wpm) if wpm and float(wpm) > 0 else None
    try:
        result = decode_audio_to_morse(samples, sr, wpm=wpm_val)
    except AudioDecodeError as exc:
        return jsonify({"error": str(exc)}), 400
    env = result.envelope
    if env.size > 1024:
        step = env.size // 1024
        env = env[::step]
    return jsonify(
        {
            "morse": result.morse,
            "detected_wpm": round(result.detected_wpm, 1),
            "dot_length_ms": round(result.dot_length_ms, 1),
            "threshold": float(result.threshold),
            "envelope": env.tolist(),
        }
    )


@app.route("/api/examples")
def api_examples():
    return jsonify(
        sorted(p.name for p in EXAMPLES_DIR.glob("*.morse")) if EXAMPLES_DIR.exists() else []
    )


@app.route("/api/example/<name>")
def api_example(name: str):
    target = (EXAMPLES_DIR / name).resolve()
    if not str(target).startswith(str(EXAMPLES_DIR.resolve())):
        return jsonify({"error": "ruta inválida"}), 400
    if not target.is_file():
        return jsonify({"error": "no encontrado"}), 404
    return jsonify({"name": name, "source": target.read_text(encoding="utf-8")})


@app.route("/api/reference")
def api_reference():
    letters = []
    digits = []
    for morse, ch in _MORSE_TO_CHAR.items():
        entry = {"char": ch, "morse": morse}
        (letters if ch.isalpha() else digits).append(entry)
    letters.sort(key=lambda r: r["char"])
    digits.sort(key=lambda r: r["char"])
    keywords = [
        {"text": kw, "morse": " ".join(encode_letter(c) for c in kw)}
        for kw in KEYWORDS
    ]
    return jsonify({"letters": letters, "digits": digits, "keywords": keywords})


def _serialize(res) -> dict:
    return {
        "tokens": (
            [{"type": t.type.name, "lexeme": t.lexeme, "line": t.line} for t in res.tokens]
            if res.tokens else None
        ),
        "ast": res.ast_dict,
        "output": list(res.output),
        "symbol_table_snapshots": [
            {"stmt": name, "table": table}
            for name, table in res.symbol_table_snapshots
        ],
        "final_symbol_table": res.final_symbol_table,
        "error": (
            {"phase": res.error_phase, "message": res.error_message}
            if res.error_message else None
        ),
    }


def main() -> None:  # pragma: no cover
    app.run(host="127.0.0.1", port=5173, debug=True)


if __name__ == "__main__":  # pragma: no cover
    main()
