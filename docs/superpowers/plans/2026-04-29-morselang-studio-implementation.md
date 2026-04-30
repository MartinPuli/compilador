# MorseLang Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Streamlit visual UI, audio Morse decoder, enriched docs, and a Claude SKILL.md on top of the existing MorseLang compiler.

**Architecture:** New top-level `studio/` package with a Streamlit app and four pages (Editor, Audio→Morse, TP Inspector, Ayuda). New `morselang/audio.py` containing pure-DSP Morse-from-audio decoding using numpy/scipy. Non-destructive instrumentation hooks in the existing interpreter and AST. New `.claude/skills/morselang-compiler/SKILL.md` so Claude can be re-taught how to use the compiler in any future session.

**Tech Stack:** Python 3.11+, Streamlit ≥1.30, numpy, scipy, graphviz (Python wrapper), pytest.

**Spec:** [`docs/superpowers/specs/2026-04-29-morselang-studio-design.md`](../specs/2026-04-29-morselang-studio-design.md)

---

## Conventions

- All commands run from `c:/Users/marti/Documents/compilador`
- Branch: `feat/morselang-implementation` (continues here, no new branch)
- Tests via `python -m pytest -q` (Windows + Python 3.12). On this machine the explicit interpreter `C:\Users\marti\AppData\Local\Programs\Python\Python312\python.exe` works if `python` is shadowed.
- Strict TDD: write failing test → see it fail → implement → see it pass → commit.
- Each task ends with a commit. No trailing trash.

---

## Task 1: Update dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Read current `requirements.txt`**

Run: `cat requirements.txt` (or open in editor). Current contents (from prior work):

```
elevenlabs>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Replace with the new dependency set**

Write `requirements.txt`:

```
elevenlabs>=1.0.0
pytest>=8.0.0
streamlit>=1.30,<2.0
numpy>=1.26
scipy>=1.11
graphviz>=0.20
```

- [ ] **Step 3: Install the new deps**

Run: `python -m pip install -r requirements.txt`
Expected: streamlit, numpy, scipy, graphviz installed; no errors.

- [ ] **Step 4: Smoke import**

Run: `python -c "import streamlit, numpy, scipy.signal, graphviz; print('ok')"`
Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "chore: add streamlit, numpy, scipy, graphviz to requirements"
```

---

## Task 2: Audio decoder — letter-level synthesis fixture

**Files:**
- Create: `tests/test_audio.py`
- Create: `morselang/audio.py`

This task lays down the test scaffolding (synthesizer of fake Morse audio) and gets the very first decode working.

- [ ] **Step 1: Write the synth helper and the first failing test**

`tests/test_audio.py`:
```python
import numpy as np
import pytest

from morselang.audio import (
    decode_audio_to_morse,
    AudioDecodeResult,
    AudioDecodeError,
)


# --- synth helper ------------------------------------------------------------

def synth_morse_wav(
    morse: str,
    *,
    wpm: int = 20,
    freq: int = 600,
    sr: int = 16000,
    silence_padding_ms: int = 100,
) -> tuple[np.ndarray, int]:
    """Generate a sine-wave audio array that encodes the given Morse string.

    `morse` may use single-space (intra-letter), triple-space or `/`
    (between words), and `.`/`-` for symbols. PARIS standard timing:
    dot = 1200/wpm milliseconds.
    """
    dot_ms = 1200.0 / wpm
    samples_per_ms = sr / 1000.0
    units = []  # list of (is_on, duration_ms)
    pad = max(silence_padding_ms, 0)

    if pad:
        units.append((False, pad))

    # walk character by character
    i = 0
    while i < len(morse):
        ch = morse[i]
        if ch == ".":
            units.append((True, dot_ms))
            i += 1
            # intra-symbol gap unless next is end of letter
            if i < len(morse) and morse[i] in ".-":
                units.append((False, dot_ms))
        elif ch == "-":
            units.append((True, dot_ms * 3))
            i += 1
            if i < len(morse) and morse[i] in ".-":
                units.append((False, dot_ms))
        elif ch == "/":
            units.append((False, dot_ms * 7))
            i += 1
        elif ch == " ":
            # collapse runs of spaces; classify by length
            run = 0
            while i < len(morse) and morse[i] == " ":
                run += 1
                i += 1
            if run >= 3:
                units.append((False, dot_ms * 7))  # word gap
            else:
                units.append((False, dot_ms * 3))  # letter gap
        else:
            i += 1  # skip anything else

    if pad:
        units.append((False, pad))

    # render
    chunks = []
    for is_on, dur_ms in units:
        n = int(round(dur_ms * samples_per_ms))
        if is_on:
            t = np.arange(n) / sr
            chunks.append(0.5 * np.sin(2 * np.pi * freq * t))
        else:
            chunks.append(np.zeros(n, dtype=np.float64))
    samples = np.concatenate(chunks).astype(np.float32)
    return samples, sr


# --- tests -------------------------------------------------------------------

def test_decode_simple_letter_dot_dash():
    samples, sr = synth_morse_wav(".-", wpm=20)
    result = decode_audio_to_morse(samples, sr)
    assert isinstance(result, AudioDecodeResult)
    assert result.morse == ".-"
    assert 18 <= result.detected_wpm <= 22
```

- [ ] **Step 2: Run — confirm failure**

Run: `python -m pytest tests/test_audio.py -v`
Expected: ImportError on `morselang.audio`.

- [ ] **Step 3: Implement `morselang/audio.py` (minimal — just enough for the first test)**

```python
"""Audio Morse decoder using DSP primitives only.

Pipeline:
    samples → mono+norm → envelope (RMS) → Otsu threshold → run-length
    encoding → auto-detect dot length → classify pulses → emit Morse string
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import convolve


class AudioDecodeError(Exception):
    pass


@dataclass
class AudioDecodeResult:
    morse: str
    detected_wpm: float
    dot_length_ms: float
    envelope: np.ndarray
    threshold: float
    pulses: list[tuple[bool, float]]


def _to_mono(samples: np.ndarray) -> np.ndarray:
    if samples.ndim == 2:
        samples = samples.mean(axis=1)
    return samples.astype(np.float64)


def _normalize(samples: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(samples)))
    if peak == 0.0:
        raise AudioDecodeError("Audio en silencio: no se detectaron pulsos")
    return samples / peak


def _envelope(samples: np.ndarray, sr: int, window_ms: float = 10.0) -> np.ndarray:
    n = max(1, int(round(window_ms * sr / 1000.0)))
    kernel = np.ones(n) / n
    rms = np.sqrt(convolve(samples ** 2, kernel, mode="same"))
    return rms


def _otsu_threshold(values: np.ndarray) -> float:
    # Otsu's method on 256 bins
    hist, edges = np.histogram(values, bins=256)
    total = hist.sum()
    if total == 0:
        return 0.0
    bin_centers = (edges[:-1] + edges[1:]) / 2
    weight_bg = np.cumsum(hist)
    weight_fg = total - weight_bg
    sum_total = (hist * bin_centers).sum()
    sum_bg = np.cumsum(hist * bin_centers)
    with np.errstate(divide="ignore", invalid="ignore"):
        mean_bg = np.where(weight_bg > 0, sum_bg / weight_bg, 0)
        mean_fg = np.where(weight_fg > 0, (sum_total - sum_bg) / weight_fg, 0)
        between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
    idx = int(np.argmax(between))
    return float(bin_centers[idx])


def _run_length_encode(binary: np.ndarray, sr: int) -> list[tuple[bool, float]]:
    """Return list of (is_on, duration_ms)."""
    if len(binary) == 0:
        return []
    runs: list[tuple[bool, int]] = []
    cur = bool(binary[0])
    count = 1
    for v in binary[1:]:
        b = bool(v)
        if b == cur:
            count += 1
        else:
            runs.append((cur, count))
            cur = b
            count = 1
    runs.append((cur, count))
    return [(on, count * 1000.0 / sr) for on, count in runs]


def _detect_dot_length_ms(pulses: list[tuple[bool, float]]) -> float:
    on_durations = [d for on, d in pulses if on]
    if not on_durations:
        raise AudioDecodeError("No se detectaron pulsos audibles")
    # dot is the shortest cluster; use lower quartile as a robust estimate
    arr = np.array(on_durations)
    return float(np.percentile(arr, 25))


def decode_audio_to_morse(
    samples: np.ndarray,
    sample_rate: int,
    *,
    wpm: float | None = None,
) -> AudioDecodeResult:
    if samples.size == 0:
        raise AudioDecodeError("Audio vacío")
    mono = _to_mono(samples)
    norm = _normalize(mono)
    env = _envelope(norm, sample_rate)
    threshold = _otsu_threshold(env)
    binary = env > threshold
    pulses = _run_length_encode(binary, sample_rate)
    if wpm is not None and wpm > 0:
        dot_ms = 1200.0 / wpm
    else:
        dot_ms = _detect_dot_length_ms(pulses)
    morse = _classify_pulses(pulses, dot_ms)
    detected_wpm = 1200.0 / dot_ms if dot_ms > 0 else 0.0
    return AudioDecodeResult(
        morse=morse,
        detected_wpm=detected_wpm,
        dot_length_ms=dot_ms,
        envelope=env,
        threshold=threshold,
        pulses=pulses,
    )


def _classify_pulses(pulses: list[tuple[bool, float]], dot_ms: float) -> str:
    out_parts: list[str] = []
    # ignore leading/trailing silence
    trimmed = list(pulses)
    while trimmed and not trimmed[0][0]:
        trimmed.pop(0)
    while trimmed and not trimmed[-1][0]:
        trimmed.pop()
    if not trimmed:
        raise AudioDecodeError("No se detectaron pulsos audibles")

    for is_on, dur in trimmed:
        if is_on:
            out_parts.append("." if dur < 1.5 * dot_ms else "-")
        else:
            if dur < 1.5 * dot_ms:
                continue  # intra-letter (no separator)
            elif dur < 5.0 * dot_ms:
                out_parts.append(" ")  # letter gap
            else:
                out_parts.append("   ")  # word gap (triple-space, matches lexer)
    return "".join(out_parts)
```

- [ ] **Step 4: Run — confirm pass**

Run: `python -m pytest tests/test_audio.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add morselang/audio.py tests/test_audio.py
git commit -m "feat(audio): basic envelope-based Morse decoder for single letters"
```

---

## Task 3: Audio decoder — multi-letter words and word gaps

**Files:**
- Modify: `tests/test_audio.py` (append tests)

- [ ] **Step 1: Append more demanding tests**

Append at the bottom of `tests/test_audio.py`:
```python
def test_decode_word_sos():
    samples, sr = synth_morse_wav("... --- ...", wpm=15)
    result = decode_audio_to_morse(samples, sr)
    assert result.morse == "... --- ..."


def test_decode_two_words_with_triple_space():
    samples, sr = synth_morse_wav(".-   -...", wpm=20)  # "AB" as two "words"
    result = decode_audio_to_morse(samples, sr)
    # we expect a triple-space (word gap) between them
    assert ".-" in result.morse and "-..." in result.morse
    assert "   " in result.morse  # three consecutive spaces


def test_decode_handles_explicit_wpm_override():
    samples, sr = synth_morse_wav(".-", wpm=20)
    result = decode_audio_to_morse(samples, sr, wpm=20)
    assert result.morse == ".-"
    assert result.detected_wpm == 20.0


def test_decode_silent_raises():
    silent = np.zeros(16000, dtype=np.float32)  # 1s of silence
    with pytest.raises(AudioDecodeError):
        decode_audio_to_morse(silent, 16000)


def test_decode_empty_raises():
    with pytest.raises(AudioDecodeError):
        decode_audio_to_morse(np.array([], dtype=np.float32), 16000)
```

- [ ] **Step 2: Run — confirm result**

Run: `python -m pytest tests/test_audio.py -v`
Expected: 6 passed (the original `test_decode_simple_letter_dot_dash` plus the 5 new ones). If `test_decode_two_words_with_triple_space` fails because the gap between words is being classified as letter-gap, the threshold `5.0 * dot_ms` in `_classify_pulses` is the knob to tune. Lower it to `4.0 * dot_ms` and re-run.

- [ ] **Step 3: If a test failed, adjust the gap threshold**

If needed, edit `morselang/audio.py` `_classify_pulses` and change:

```python
elif dur < 5.0 * dot_ms:
```

to:

```python
elif dur < 4.0 * dot_ms:
```

Then re-run pytest. Iterate at most twice; if still failing, escalate.

- [ ] **Step 4: Commit**

```bash
git add tests/test_audio.py morselang/audio.py
git commit -m "feat(audio): handle multi-letter words and word-gap classification"
```

---

## Task 4: Audio decoder — robustness against noise

**Files:**
- Modify: `tests/test_audio.py` (append one more test)

- [ ] **Step 1: Append the noise test**

Append at the bottom of `tests/test_audio.py`:
```python
def test_decode_robust_to_moderate_noise():
    rng = np.random.default_rng(seed=42)
    samples, sr = synth_morse_wav("... --- ...", wpm=15)
    noise = rng.normal(0, 0.05, size=samples.shape).astype(np.float32)
    noisy = samples + noise
    result = decode_audio_to_morse(noisy, sr)
    assert result.morse == "... --- ..."
```

- [ ] **Step 2: Run — confirm pass**

Run: `python -m pytest tests/test_audio.py -v`
Expected: 7 passed.

If this test fails because the noise floor is creeping above the Otsu threshold, the envelope window size is too small. Edit `morselang/audio.py` and bump `window_ms` default in `_envelope` from `10.0` to `15.0`. Re-run.

- [ ] **Step 3: Commit**

```bash
git add tests/test_audio.py morselang/audio.py
git commit -m "test(audio): verify decoder robustness against gaussian noise"
```

---

## Task 5: AST serialization for Studio

**Files:**
- Modify: `morselang/ast_nodes.py`
- Create: `tests/test_ast_serialization.py`

The Studio needs the AST as a JSON-friendly dict to render it with graphviz. We add a single `to_dict()` helper module rather than methods on every dataclass — keeps `ast_nodes.py` focused on shape.

- [ ] **Step 1: Write the failing test**

`tests/test_ast_serialization.py`:
```python
from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.ast_nodes import to_dict


def parse(src: str):
    return Parser(Lexer(src).tokenize()).parse()


def test_to_dict_for_simple_declaration():
    # VAR X ASIG 10
    src = "...- .- .-. / -..- / .- ... .. --. / .---- -----"
    prog = parse(src)
    d = to_dict(prog)
    assert d == {
        "node": "Programa",
        "statements": [
            {
                "node": "Declaracion",
                "name": "X",
                "line": 1,
                "value": {"node": "NumeroLit", "value": 10, "line": 1},
            }
        ],
    }


def test_to_dict_for_binary_op():
    # MOSTRAR 1 MAS 2
    src = "-- --- ... - .-. .- .-. / .---- / -- .- ... / ..---"
    prog = parse(src)
    d = to_dict(prog)
    stmt = d["statements"][0]
    assert stmt["node"] == "MostrarStmt"
    expr = stmt["expr"]
    assert expr["node"] == "BinOp"
    assert expr["op"] == "MAS"
    assert expr["left"] == {"node": "NumeroLit", "value": 1, "line": 1}
    assert expr["right"] == {"node": "NumeroLit", "value": 2, "line": 1}


def test_to_dict_for_si_with_else():
    src = (
        "... .. / -..- / -- . -. / .....\n"
        "-- --- ... - .-. .- .-. / -..-\n"
        "... .. -. ---\n"
        "-- --- ... - .-. .- .-. / -----\n"
        "..-. .. -."
    )
    prog = parse(src)
    d = to_dict(prog)
    si = d["statements"][0]
    assert si["node"] == "SiStmt"
    assert isinstance(si["then_block"], list) and len(si["then_block"]) == 1
    assert isinstance(si["else_block"], list) and len(si["else_block"]) == 1
```

- [ ] **Step 2: Run — confirm failure**

Run: `python -m pytest tests/test_ast_serialization.py -v`
Expected: ImportError on `to_dict`.

- [ ] **Step 3: Implement `to_dict` in `morselang/ast_nodes.py`**

Append at the bottom of `morselang/ast_nodes.py`:

```python
def to_dict(node) -> dict | list | None:
    """Serialize an AST node (or list / None) to a JSON-friendly dict.

    Used by the Studio to render the AST as a graph. Pure function, no
    behavior on the dataclasses themselves.
    """
    if node is None:
        return None
    if isinstance(node, list):
        return [to_dict(x) for x in node]

    name = type(node).__name__

    if isinstance(node, NumeroLit):
        return {"node": name, "value": node.value, "line": node.line}
    if isinstance(node, TextoLit):
        return {"node": name, "value": node.value, "line": node.line}
    if isinstance(node, BoolLit):
        return {"node": name, "value": node.value, "line": node.line}
    if isinstance(node, IdentRef):
        return {"node": name, "name": node.name, "line": node.line}
    if isinstance(node, BinOp):
        return {
            "node": name,
            "op": node.op,
            "left": to_dict(node.left),
            "right": to_dict(node.right),
            "line": node.line,
        }
    if isinstance(node, Declaracion):
        return {
            "node": name,
            "name": node.name,
            "value": to_dict(node.value),
            "line": node.line,
        }
    if isinstance(node, Asignacion):
        return {
            "node": name,
            "name": node.name,
            "value": to_dict(node.value),
            "line": node.line,
        }
    if isinstance(node, MostrarStmt):
        return {"node": name, "expr": to_dict(node.expr), "line": node.line}
    if isinstance(node, SiStmt):
        return {
            "node": name,
            "condition": to_dict(node.condition),
            "then_block": to_dict(node.then_block),
            "else_block": to_dict(node.else_block),
            "line": node.line,
        }
    if isinstance(node, MientrasStmt):
        return {
            "node": name,
            "condition": to_dict(node.condition),
            "body": to_dict(node.body),
            "line": node.line,
        }
    if isinstance(node, Programa):
        return {"node": name, "statements": to_dict(node.statements)}
    raise TypeError(f"Nodo AST desconocido: {type(node).__name__}")
```

- [ ] **Step 4: Run — confirm pass**

Run: `python -m pytest tests/test_ast_serialization.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run full suite to make sure nothing broke**

Run: `python -m pytest -q`
Expected: 70 passed (60 prior + 7 audio + 3 AST serialization).

- [ ] **Step 6: Commit**

```bash
git add morselang/ast_nodes.py tests/test_ast_serialization.py
git commit -m "feat(ast): add to_dict serializer for Studio rendering"
```

---

## Task 6: Interpreter step-callback hook

**Files:**
- Modify: `morselang/interpreter.py`
- Create: `tests/test_interpreter_step_hook.py`

The TP Inspector needs to show the symbol table after each statement. Add an optional `on_step` callback to `Interpreter.execute` that receives the statement just finished and a snapshot of the symbol table.

- [ ] **Step 1: Write failing tests**

`tests/test_interpreter_step_hook.py`:
```python
from morselang.lexer import Lexer
from morselang.parser import Parser
from morselang.semantic import SemanticAnalyzer
from morselang.interpreter import Interpreter


def execute(src):
    prog = Parser(Lexer(src).tokenize()).parse()
    SemanticAnalyzer().analyze(prog)
    return prog


def test_on_step_called_once_per_top_level_statement():
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    prog = execute(src)
    calls = []

    def cb(stmt, snapshot):
        calls.append((type(stmt).__name__, dict(snapshot)))

    Interpreter().execute(prog, on_step=cb)
    assert [c[0] for c in calls] == ["Declaracion", "MostrarStmt"]
    # after Declaracion the snapshot has X with value 10
    assert calls[0][1]["X"]["valor"] == 10


def test_on_step_default_none_keeps_old_behavior():
    # No callback → existing behavior; output captured normally.
    src = (
        "...- .- .-. / -..- / .- ... .. --. / .---- -----\n"
        "-- --- ... - .-. .- .-. / -..-"
    )
    prog = execute(src)
    interp = Interpreter()
    interp.execute(prog)
    assert interp.output == ["10"]
```

- [ ] **Step 2: Run — confirm failure**

Run: `python -m pytest tests/test_interpreter_step_hook.py -v`
Expected: TypeError — `execute()` got an unexpected keyword argument `on_step`.

- [ ] **Step 3: Modify `Interpreter.execute` to accept `on_step`**

Open `morselang/interpreter.py` and replace the `execute` method (currently at the top of the class) with:

```python
    def execute(self, program: Programa, on_step=None) -> None:
        for stmt in program.statements:
            self._stmt(stmt)
            if on_step is not None:
                on_step(stmt, self._env.snapshot())
```

`on_step` is optional; if `None`, behavior is identical to before.

- [ ] **Step 4: Run new tests**

Run: `python -m pytest tests/test_interpreter_step_hook.py -v`
Expected: 2 passed.

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: 72 passed (70 prior + 2 hook).

- [ ] **Step 6: Commit**

```bash
git add morselang/interpreter.py tests/test_interpreter_step_hook.py
git commit -m "feat(interpreter): optional on_step callback for live symbol-table inspection"
```

---

## Task 7: Studio package skeleton + Editor page

**Files:**
- Create: `studio/__init__.py`
- Create: `studio/components.py`
- Create: `studio/app.py`
- Create: `studio/pages/editor.py`
- Create: `tests/test_studio_smoke.py`

- [ ] **Step 1: Create empty `studio/__init__.py` and `studio/pages/__init__.py`**

Both files: empty.

- [ ] **Step 2: Write the smoke test (failing)**

`tests/test_studio_smoke.py`:
```python
def test_studio_app_imports_without_error():
    import importlib
    mod = importlib.import_module("studio.app")
    assert hasattr(mod, "main")


def test_studio_components_helpers_importable():
    from studio.components import compile_and_run, lex_only, parse_only
    assert callable(compile_and_run)
    assert callable(lex_only)
    assert callable(parse_only)
```

- [ ] **Step 3: Run — confirm import failure**

Run: `python -m pytest tests/test_studio_smoke.py -v`
Expected: ModuleNotFoundError on `studio.app`.

- [ ] **Step 4: Implement `studio/components.py`**

```python
"""Shared helpers used by Studio pages.

These wrap the compiler pipeline so each page can call a single function
to get tokens / AST / output / errors. Pure Python — no Streamlit imports
here so the helpers can be unit-tested independently.
"""

from dataclasses import dataclass, field
from typing import Optional

from morselang.lexer import Lexer, LexerError
from morselang.parser import Parser, ParseError
from morselang.semantic import SemanticAnalyzer, SemanticError
from morselang.interpreter import Interpreter, RuntimeError_
from morselang.ast_nodes import to_dict
from morselang.tokens import Token


@dataclass
class CompileResult:
    tokens: Optional[list[Token]] = None
    ast_dict: Optional[dict] = None
    output: list[str] = field(default_factory=list)
    symbol_table_snapshots: list[tuple[str, dict]] = field(default_factory=list)
    final_symbol_table: Optional[dict] = None
    error_phase: Optional[str] = None  # 'lex' | 'parse' | 'sem' | 'runtime'
    error_message: Optional[str] = None


def lex_only(source: str) -> CompileResult:
    res = CompileResult()
    try:
        res.tokens = Lexer(source).tokenize()
    except LexerError as exc:
        res.error_phase = "lex"
        res.error_message = str(exc)
    return res


def parse_only(source: str) -> CompileResult:
    res = lex_only(source)
    if res.tokens is None:
        return res
    try:
        program = Parser(res.tokens).parse()
        res.ast_dict = to_dict(program)
    except ParseError as exc:
        res.error_phase = "parse"
        res.error_message = str(exc)
    return res


def compile_and_run(source: str) -> CompileResult:
    res = parse_only(source)
    if res.ast_dict is None:
        return res
    program = Parser(res.tokens).parse()  # cheap; tokens already validated
    try:
        SemanticAnalyzer().analyze(program)
    except SemanticError as exc:
        res.error_phase = "sem"
        res.error_message = str(exc)
        return res
    interp = Interpreter()
    snapshots: list[tuple[str, dict]] = []

    def step_cb(stmt, snap):
        snapshots.append((type(stmt).__name__, snap))

    try:
        interp.execute(program, on_step=step_cb)
    except RuntimeError_ as exc:
        res.error_phase = "runtime"
        res.error_message = str(exc)
        res.output = list(interp.output)
        res.symbol_table_snapshots = snapshots
        return res
    res.output = list(interp.output)
    res.symbol_table_snapshots = snapshots
    res.final_symbol_table = snapshots[-1][1] if snapshots else {}
    return res
```

- [ ] **Step 5: Implement `studio/pages/editor.py`**

```python
"""Editor page: write code, run it, see tokens / AST / output / errors."""

from pathlib import Path

import streamlit as st

from studio.components import compile_and_run, lex_only, parse_only

EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"


def render() -> None:
    st.header("📝 Editor")

    cols = st.columns([3, 1])
    with cols[1]:
        examples = sorted(EXAMPLES.glob("*.morse"))
        names = ["—"] + [e.name for e in examples]
        choice = st.selectbox("Cargar ejemplo", names)
        if choice != "—":
            for e in examples:
                if e.name == choice:
                    st.session_state["editor_source"] = e.read_text(encoding="utf-8")
                    break

    source = st.text_area(
        "Código MorseLang",
        value=st.session_state.get("editor_source", ""),
        height=280,
        key="editor_textarea",
    )
    st.session_state["editor_source"] = source

    btn_run, btn_tok, btn_ast = st.columns(3)
    do_run = btn_run.button("▶ Ejecutar", use_container_width=True)
    do_tok = btn_tok.button("🔍 Tokens", use_container_width=True)
    do_ast = btn_ast.button("🌳 AST", use_container_width=True)

    st.divider()

    if do_run:
        result = compile_and_run(source)
        if result.error_message:
            st.error(f"Error {result.error_phase}: {result.error_message}")
        st.subheader("Salida")
        if result.output:
            for line in result.output:
                st.code(line)
        else:
            st.caption("(sin salida)")
        if result.final_symbol_table:
            st.subheader("Tabla de símbolos final")
            st.json(result.final_symbol_table)
    elif do_tok:
        result = lex_only(source)
        if result.error_message:
            st.error(f"Error {result.error_phase}: {result.error_message}")
        if result.tokens:
            st.subheader("Tokens")
            st.json([
                {"type": t.type.name, "lexeme": t.lexeme, "line": t.line}
                for t in result.tokens
            ])
    elif do_ast:
        result = parse_only(source)
        if result.error_message:
            st.error(f"Error {result.error_phase}: {result.error_message}")
        if result.ast_dict:
            st.subheader("AST")
            st.json(result.ast_dict)
```

- [ ] **Step 6: Implement `studio/app.py`**

```python
"""MorseLang Studio — Streamlit entry point.

Run with:  streamlit run studio/app.py
"""

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="MorseLang Studio",
        page_icon="🛰️",
        layout="wide",
    )
    st.title("🛰️ MorseLang Studio")
    st.caption("Editor visual + decoder de audio Morse + inspector del TP")

    page = st.sidebar.radio(
        "Páginas",
        ["📝 Editor", "🎙 Audio → Morse", "📋 TP Inspector", "❓ Ayuda"],
        index=0,
    )
    if page.startswith("📝"):
        from studio.pages.editor import render
        render()
    elif page.startswith("🎙"):
        from studio.pages.audio_morse import render
        render()
    elif page.startswith("📋"):
        from studio.pages.tp_inspector import render
        render()
    else:
        from studio.pages.ayuda import render
        render()


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Stub the other three pages so imports don't fail**

`studio/pages/audio_morse.py`:
```python
import streamlit as st


def render() -> None:
    st.header("🎙 Audio → Morse")
    st.info("Implementado en la siguiente tarea.")
```

`studio/pages/tp_inspector.py`:
```python
import streamlit as st


def render() -> None:
    st.header("📋 TP Inspector")
    st.info("Implementado en una tarea posterior.")
```

`studio/pages/ayuda.py`:
```python
import streamlit as st


def render() -> None:
    st.header("❓ Ayuda")
    st.info("Implementado en una tarea posterior.")
```

- [ ] **Step 8: Run smoke tests**

Run: `python -m pytest tests/test_studio_smoke.py -v`
Expected: 2 passed.

- [ ] **Step 9: Run full suite**

Run: `python -m pytest -q`
Expected: 74 passed (72 prior + 2 smoke).

- [ ] **Step 10: Commit**

```bash
git add studio/ tests/test_studio_smoke.py
git commit -m "feat(studio): scaffold Streamlit app with Editor page"
```

---

## Task 8: Audio → Morse page

**Files:**
- Modify: `studio/pages/audio_morse.py`

- [ ] **Step 1: Replace stub with real implementation**

Open `studio/pages/audio_morse.py` and replace its content with:

```python
"""Audio → Morse page: record/upload audio, decode Morse, send to editor."""

import io

import numpy as np
import streamlit as st
from scipy.io import wavfile

from morselang.audio import decode_audio_to_morse, AudioDecodeError


def _load_wav(buffer: bytes) -> tuple[np.ndarray, int]:
    sr, samples = wavfile.read(io.BytesIO(buffer))
    # scipy returns int16 for typical wavs; normalize to float32
    if samples.dtype.kind in ("i", "u"):
        max_val = float(np.iinfo(samples.dtype).max)
        samples = samples.astype(np.float32) / max_val
    else:
        samples = samples.astype(np.float32)
    return samples, sr


def render() -> None:
    st.header("🎙 Audio → Morse")
    st.write(
        "Grabá Morse desde el micrófono o subí un archivo `.wav`. "
        "El decoder usa DSP puro (envolvente RMS + Otsu) para extraer la "
        "secuencia `.` `-` y separadores."
    )

    col_rec, col_up = st.columns(2)
    audio_bytes: bytes | None = None
    with col_rec:
        st.subheader("Grabar")
        rec = None
        if hasattr(st, "audio_input"):
            rec = st.audio_input("Mic")
        else:
            st.caption("Tu versión de Streamlit no tiene `audio_input`. Usá el upload.")
        if rec is not None:
            audio_bytes = rec.getvalue()
    with col_up:
        st.subheader("Subir .wav")
        up = st.file_uploader("Archivo de audio", type=["wav"])
        if up is not None:
            audio_bytes = up.read()

    wpm_override = st.slider(
        "WPM (0 = autodetectar)", min_value=0, max_value=40, value=0, step=1
    )

    if audio_bytes is None:
        st.caption("Esperando audio...")
        return

    try:
        samples, sr = _load_wav(audio_bytes)
    except Exception as exc:
        st.error(f"No se pudo leer el .wav: {exc}")
        return

    if st.button("🔍 Decodificar"):
        try:
            wpm = wpm_override if wpm_override > 0 else None
            result = decode_audio_to_morse(samples, sr, wpm=wpm)
        except AudioDecodeError as exc:
            st.error(f"Decodificación falló: {exc}")
            return

        st.subheader("Morse decodificado")
        st.code(result.morse)

        c1, c2 = st.columns(2)
        c1.metric("WPM detectado", f"{result.detected_wpm:.1f}")
        c2.metric("Dot length (ms)", f"{result.dot_length_ms:.1f}")

        st.subheader("Envolvente y threshold")
        env = result.envelope
        if env.size > 4000:
            # decimate for plotting
            step = env.size // 4000
            env = env[::step]
        st.line_chart(env)
        st.caption(f"Threshold: {result.threshold:.4f}")

        if st.button("→ Mandar al editor"):
            st.session_state["editor_source"] = result.morse
            st.success("Morse cargado en el editor — abrí la pestaña '📝 Editor'.")
```

- [ ] **Step 2: Verify the file imports**

Run: `python -c "from studio.pages.audio_morse import render; print('ok')"`
Expected: `ok` (no errors).

- [ ] **Step 3: Run full suite to make sure nothing broke**

Run: `python -m pytest -q`
Expected: 74 passed.

- [ ] **Step 4: Commit**

```bash
git add studio/pages/audio_morse.py
git commit -m "feat(studio): wire Audio→Morse page to DSP decoder"
```

---

## Task 9: Ayuda page

**Files:**
- Modify: `studio/pages/ayuda.py`

The Ayuda page renders three reference tables: Morse alphabet, keywords-with-Morse, operators-with-Morse.

- [ ] **Step 1: Replace stub**

Open `studio/pages/ayuda.py` and replace with:

```python
"""Ayuda page: Morse / keywords / operators reference tables."""

import streamlit as st

from morselang.morse import _MORSE_TO_CHAR, encode_letter
from morselang.tokens import KEYWORDS


def render() -> None:
    st.header("❓ Ayuda")

    st.subheader("Tabla Morse — letras y dígitos")
    rows_letters = []
    rows_digits = []
    for morse, ch in _MORSE_TO_CHAR.items():
        if ch.isalpha():
            rows_letters.append({"Letra": ch, "Morse": morse})
        else:
            rows_digits.append({"Dígito": ch, "Morse": morse})
    rows_letters.sort(key=lambda r: r["Letra"])
    rows_digits.sort(key=lambda r: r["Dígito"])
    col1, col2 = st.columns(2)
    col1.dataframe(rows_letters, hide_index=True, use_container_width=True)
    col2.dataframe(rows_digits, hide_index=True, use_container_width=True)

    st.subheader("Keywords y operadores del lenguaje")
    rows = []
    for word in KEYWORDS:
        morse = " ".join(encode_letter(c) for c in word)
        rows.append({"Token": word, "Morse": morse})
    st.dataframe(rows, hide_index=True, use_container_width=True)

    st.subheader("Separadores")
    st.markdown(
        "- **Un espacio** entre letras de la misma palabra.\n"
        "- **Triple espacio** (`   `) o `/` entre palabras / tokens.\n"
        "- **Salto de línea** (`\\n`) entre sentencias.\n"
        "- **Comillas** (`\"...\"`) para literales de texto, contenido también en Morse, "
        "con triple-espacio para preservar espacios reales entre palabras."
    )
```

- [ ] **Step 2: Verify import**

Run: `python -c "from studio.pages.ayuda import render; print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Run full suite**

Run: `python -m pytest -q`
Expected: 74 passed.

- [ ] **Step 4: Commit**

```bash
git add studio/pages/ayuda.py
git commit -m "feat(studio): Ayuda page with Morse and keyword reference tables"
```

---

## Task 10: TP Inspector page

**Files:**
- Modify: `studio/pages/tp_inspector.py`
- Create: `docs/tp_resources.py`

The TP Inspector is the most content-heavy page. It walks Partes 1–7 in tabs.

- [ ] **Step 1: Create `docs/tp_resources.py`**

Static text used by the TP Inspector (kept out of the page file so it can be edited like docs).

`docs/tp_resources.py`:
```python
"""Static reference text consumed by the TP Inspector page.

Keeping the prose here (instead of inline in the Streamlit page file)
makes it easy to edit the documentation without touching UI code.
"""

ALFABETO = (
    "Σ = { '.', '-', ' ', '/', '\\n', '\"' }\n"
    "Letras y dígitos se forman con secuencias de '.' y '-' separadas por\n"
    "un espacio. Las palabras (tokens) se separan con '/' o tres espacios."
)

EBNF = """programa     ::= { sentencia } ;
sentencia    ::= declaracion
              | asignacion
              | mostrar
              | si
              | mientras ;
declaracion  ::= "VAR" identificador "ASIG" expresion "\\n" ;
asignacion   ::= identificador "ASIG" expresion "\\n" ;
mostrar      ::= "MOSTRAR" expresion "\\n" ;
si           ::= "SI" expresion "\\n" { sentencia } [ "SINO" "\\n" { sentencia } ] "FIN" "\\n" ;
mientras     ::= "MIENTRAS" expresion "\\n" { sentencia } "FIN" "\\n" ;

expresion    ::= comparacion ;
comparacion  ::= aritmetica [ ("IGUAL"|"DIST"|"MEN"|"MAY") aritmetica ] ;
aritmetica   ::= termino { ("MAS"|"MENOS") termino } ;
termino      ::= factor { ("POR"|"DIV") factor } ;
factor       ::= numero | texto | "VERDADERO" | "FALSO" | identificador
              | "(" expresion ")" ;
"""

DERIVACION = """sentencia ⇒ declaracion
         ⇒ "VAR" identificador "ASIG" expresion "\\n"
         ⇒ "VAR" "X" "ASIG" expresion "\\n"
         ⇒ "VAR" "X" "ASIG" comparacion "\\n"
         ⇒ "VAR" "X" "ASIG" aritmetica "\\n"
         ⇒ "VAR" "X" "ASIG" termino "\\n"
         ⇒ "VAR" "X" "ASIG" factor "\\n"
         ⇒ "VAR" "X" "ASIG" numero "\\n"
         ⇒ "VAR" "X" "ASIG" "10" "\\n"
"""

AFD_ASCII = """          ┌────────┐
   start ─▶│   S0   │── '.' or '-' ──▶┐
          └────────┘                  ▼
                                   ┌────────┐
                                   │   S1   │── '.' or '-' ──▶ S1
                                   │ accum  │
                                   └────────┘
                                   │  ' '    │  '/' / '\\n' / '\"'
                                   ▼          ▼
                              emit letter   emit separator / start string
"""

PARSER_JUSTIFICATION = (
    "Recursivo descendente, LL(1). La gramática se diseñó para que cada\n"
    "no-terminal se decida con un solo token de lookahead: las sentencias se\n"
    "discriminan por su keyword inicial (VAR/MOSTRAR/SI/MIENTRAS) o por un\n"
    "IDENT en el caso de la asignación. Las expresiones usan precedencia por\n"
    "niveles (comparación → aditivo → multiplicativo → factor) para evitar\n"
    "recursión por izquierda. Es el método más didáctico para un TP y se\n"
    "implementa en pocas líneas por no-terminal — alineado con el requisito\n"
    "de hacer todo a mano."
)

SYMBOL_TABLE_DESC = (
    "Hashmap (`dict` de Python) con clave = nombre de la variable y valor =\n"
    "`SymbolInfo(tipo, valor, linea_declaracion)`. Métodos: declarar, asignar,\n"
    "consultar, existe, snapshot. Un único ámbito global (sin funciones)."
)
```

- [ ] **Step 2: Replace `studio/pages/tp_inspector.py`**

```python
"""TP Inspector: pestañas que mapean cada Parte del TP al estado vivo."""

from pathlib import Path

import streamlit as st

from docs.tp_resources import (
    ALFABETO, EBNF, DERIVACION, AFD_ASCII,
    PARSER_JUSTIFICATION, SYMBOL_TABLE_DESC,
)
from morselang.tokens import KEYWORDS
from morselang.morse import encode_letter
from studio.components import compile_and_run, lex_only

EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"
DOCS = Path(__file__).resolve().parent.parent.parent / "docs"


def render() -> None:
    st.header("📋 TP Inspector — recorrido por las 7 Partes")
    tabs = st.tabs([
        "1. Definición", "2. Léxico", "3. Sintáctico",
        "4. Tabla de símbolos", "5. Semántico", "6. Síntesis", "7. Uso de IA",
    ])

    with tabs[0]:
        st.subheader("Alfabeto")
        st.code(ALFABETO)
        st.subheader("Tokens")
        rows = [{"Token": k, "Morse": " ".join(encode_letter(c) for c in k)} for k in KEYWORDS]
        st.dataframe(rows, hide_index=True, use_container_width=True)
        st.subheader("Gramática (EBNF)")
        st.code(EBNF, language="ebnf")
        st.subheader("Ejemplo de derivación — `VAR X ASIG 10`")
        st.code(DERIVACION)

    with tabs[1]:
        st.subheader("AFD del decodificador Morse")
        st.code(AFD_ASCII)
        st.subheader("Trace en vivo — Morse → tokens")
        sample = st.text_input(
            "Tipeá Morse para ver los tokens",
            value="...- .- .-. / -..- / .- ... .. --. / .---- -----",
        )
        result = lex_only(sample)
        if result.error_message:
            st.error(result.error_message)
        elif result.tokens:
            st.dataframe(
                [{"type": t.type.name, "lexeme": t.lexeme, "line": t.line} for t in result.tokens],
                hide_index=True, use_container_width=True,
            )

    with tabs[2]:
        st.subheader("Tipo de parser")
        st.write(PARSER_JUSTIFICATION)
        st.subheader("AST en vivo")
        sample = st.text_input(
            "Programa para parsear",
            value="...- .- .-. / -..- / .- ... .. --. / .---- -----",
            key="ast_sample_input",
        )
        from studio.components import parse_only
        result = parse_only(sample)
        if result.error_message:
            st.error(result.error_message)
        elif result.ast_dict:
            st.json(result.ast_dict)

    with tabs[3]:
        st.subheader("Estructura")
        st.write(SYMBOL_TABLE_DESC)
        st.subheader("Snapshot por sentencia (modo step)")
        sample = st.text_area(
            "Programa",
            value=(EXAMPLES / "factorial.morse").read_text(encoding="utf-8")
            if (EXAMPLES / "factorial.morse").exists() else "",
            height=180, key="symtab_program",
        )
        if st.button("Ejecutar y ver tabla paso a paso"):
            result = compile_and_run(sample)
            if result.error_message:
                st.error(f"Error {result.error_phase}: {result.error_message}")
            if result.symbol_table_snapshots:
                idx = st.slider("Sentencia #", 0, len(result.symbol_table_snapshots) - 1, 0)
                stmt_name, snap = result.symbol_table_snapshots[idx]
                st.write(f"Después de **{stmt_name}** (línea {idx + 1}):")
                st.json(snap)

    with tabs[4]:
        st.subheader("Programas con error semántico")
        for err_file in sorted(EXAMPLES.glob("error_*.morse")):
            with st.expander(err_file.name):
                src = err_file.read_text(encoding="utf-8")
                st.code(src)
                result = compile_and_run(src)
                if result.error_message:
                    st.error(f"{result.error_phase}: {result.error_message}")
                else:
                    st.warning("Este programa no produjo error — revisar el ejemplo.")

    with tabs[5]:
        st.subheader("Intérprete tree-walking")
        st.write(
            "El intérprete recorre el AST y ejecuta cada sentencia, manteniendo "
            "una tabla de símbolos en runtime. La salida de `MOSTRAR` se acumula "
            "para enviarse opcionalmente a ElevenLabs y producir un `.mp3`."
        )
        out_mp3 = Path(__file__).resolve().parent.parent.parent / "output.mp3"
        if out_mp3.exists():
            st.audio(out_mp3.read_bytes(), format="audio/mp3")
            st.caption(f"Último audio generado: `{out_mp3.name}`")
        else:
            st.info("Aún no se generó audio. Ejecutá un programa con `--tts` desde el CLI.")

    with tabs[6]:
        st.subheader("Bitácora de uso de IA")
        uso_ia = DOCS / "uso_ia.md"
        if uso_ia.exists():
            st.markdown(uso_ia.read_text(encoding="utf-8"))
        else:
            st.warning(f"Archivo no encontrado: {uso_ia}")
```

- [ ] **Step 3: Verify imports**

Run: `python -c "from studio.pages.tp_inspector import render; print('ok')"`
Expected: `ok`.

- [ ] **Step 4: Run full suite**

Run: `python -m pytest -q`
Expected: 74 passed.

- [ ] **Step 5: Commit**

```bash
git add studio/pages/tp_inspector.py docs/tp_resources.py
git commit -m "feat(studio): TP Inspector with tabs for Partes 1-7"
```

---

## Task 11: Enrich `docs/informe.md`

**Files:**
- Modify: `docs/informe.md`

The current informe is a skeleton. Replace with a proper draft that mirrors the spec, includes the AFD ASCII art, and references the live Studio panels.

- [ ] **Step 1: Replace `docs/informe.md` with the full draft**

Write `docs/informe.md`:

```markdown
# TP Integrador — Compilador MorseLang

**Lenguaje:** MorseLang — lenguaje imperativo cuyo código fuente se escribe en código Morse.
**Implementación:** Python 3.12, todo a mano (sin parser generators), 74 tests automatizados.

> Para una vista interactiva de cada Parte, abrir el Studio y usar la pestaña **TP Inspector**:
> `streamlit run studio/app.py`.

## 1. Definición del lenguaje

### Descripción informal
MorseLang es un lenguaje imperativo de propósito general (nivel intermedio). Soporta variables tipadas (NUM, TEXTO, BOOL), aritmética entera, comparaciones, `SI/SINO`, `MIENTRAS` y `MOSTRAR`. Su rasgo distintivo es que el código fuente se escribe en código Morse: cada keyword, identificador, número y string es una secuencia de `.` y `-`.

### Alfabeto

```
Σ = { '.', '-', ' ', '/', '\n', '"' }
```

### Tokens

| Categoría | Ejemplos |
|---|---|
| Keyword | VAR, MOSTRAR, SI, SINO, MIENTRAS, FIN, VERDADERO, FALSO |
| Operador (palabra Morse) | MAS, MENOS, POR, DIV, IGUAL, DIST, MEN, MAY, ASIG |
| Identificador | A–Z, ≥1 letra |
| Número | secuencia de dígitos Morse |
| Texto | `"..."` con contenido Morse |
| Estructural | NEWLINE, EOF |

### Gramática (EBNF)

Ver `morselang/parser.py` para la implementación; transcripción en `docs/tp_resources.py:EBNF`.

### Ejemplo de derivación

Para `VAR X ASIG 10`:

```
sentencia ⇒ declaracion
         ⇒ "VAR" identificador "ASIG" expresion
         ⇒ "VAR" "X" "ASIG" numero
         ⇒ "VAR" "X" "ASIG" "10"
```

## 2. Análisis léxico

### Estrategia

Dos pasos: (1) decodificación Morse → texto, (2) clasificación del texto en tokens. La separación mantiene el AFD de la primera fase pequeño y testeable.

### Expresiones regulares (sobre el texto decodificado)

| Token | Regex |
|---|---|
| KEYWORD/OPERATOR | `VAR|MOSTRAR|SI|...|ASIG` |
| IDENT | `[A-Z]+` |
| NUMBER | `[0-9]+` |
| STRING | `"[^"]*"` |
| NEWLINE | `\n` |

### AFD del decodificador Morse

```
          ┌────────┐
   start ─▶│   S0   │── '.' or '-' ──▶┐
          └────────┘                  ▼
                                   ┌────────┐
                                   │   S1   │── '.' or '-' ──▶ S1
                                   │ accum  │
                                   └────────┘
                                   │  ' '    │  '/' / '\n' / '"'
                                   ▼          ▼
                              emit letter   emit separator / start string
```

Implementación: `morselang/lexer.py`. Visualización en vivo: TP Inspector → pestaña 2.

## 3. Análisis sintáctico

### Tipo

Recursivo descendente, **LL(1)**.

### Justificación

Cada no-terminal se decide con un único token de lookahead. Las sentencias se discriminan por keyword inicial (VAR/MOSTRAR/SI/MIENTRAS) o IDENT (asignación). Las expresiones usan precedencia por niveles (`comparacion` → `aritmetica` → `termino` → `factor`) para evitar recursión por izquierda. Es el método más didáctico para un TP y se implementa en pocas líneas por no-terminal — alineado con el requisito de hacer todo a mano.

### Implementación

`morselang/parser.py`. Construye un AST de dataclasses definidas en `morselang/ast_nodes.py`.

### Ejemplo

Para `VAR X ASIG 10 MAS 5`:

```
Programa
└── Declaracion(name='X')
    └── BinOp('MAS')
        ├── NumeroLit(10)
        └── NumeroLit(5)
```

Visualización en vivo: TP Inspector → pestaña 3.

## 4. Tabla de símbolos

### Estructura

`dict` con clave = nombre de la variable y valor = `SymbolInfo(tipo, valor, linea_declaracion)`. Métodos: `declarar`, `asignar`, `consultar`, `existe`, `snapshot`. Un único ámbito global.

### Estrategia

- `declarar(name, tipo, line)` — falla si ya existe.
- `asignar(name, valor)` — falla si no fue declarada.
- `consultar(name)` — falla si no existe.

### Ejemplo de uso (factorial.morse)

| Línea | Tabla |
|---|---|
| 1 (VAR N=5)  | `{N: NUM=5}` |
| 2 (VAR R=1)  | `{N: NUM=5, R: NUM=1}` |
| iter 1       | `{N: NUM=4, R: NUM=5}` |
| iter 2       | `{N: NUM=3, R: NUM=20}` |
| iter 3       | `{N: NUM=2, R: NUM=60}` |
| iter 4       | `{N: NUM=1, R: NUM=120}` |
| iter 5       | `{N: NUM=0, R: NUM=120}` |
| 7 (MOSTRAR R)| `{N: NUM=0, R: NUM=120}` → imprime 120 |

Visualización en vivo: TP Inspector → pestaña 4.

## 5. Análisis semántico

### Reglas

1. Variable declarada antes de usarse.
2. No redeclaración.
3. Aritmética requiere ambos operandos NUM.
4. Comparación requiere operandos del mismo tipo.
5. Condición de SI / MIENTRAS debe ser BOOL.
6. División por literal `0` rechazada en compilación.
7. División por variable `0` se detecta en runtime (`RuntimeError_`).

### Errores

| Programa | Mensaje |
|---|---|
| `error_no_declarada.morse` | `Línea 1: variable 'Z' no declarada` |
| `error_redeclaracion.morse` | `Línea 2: redeclaración de 'X' (declarada originalmente en línea 1)` |
| `error_division_cero.morse` | `Línea 1: división por cero` |

Visualización en vivo: TP Inspector → pestaña 5.

## 6. Síntesis — intérprete + ElevenLabs

Se eligió **intérprete tree-walking** como fase de síntesis (Parte 6 del TP — opción "Intérprete del lenguaje"). El intérprete recorre el AST, mantiene una tabla de símbolos en runtime y captura cada `MOSTRAR` en `interp.output`.

Como cierre vistoso, la salida acumulada se envía a la **API de ElevenLabs** para producir un `output.mp3` que narra el resultado con voz humana en español.

```
archivo.morse → Lexer → Parser → AST → Semántico → Intérprete → output.mp3
```

CLI:

```bash
python main.py examples/factorial.morse        # solo ejecuta
python main.py examples/factorial.morse --tts  # + narración ElevenLabs
```

Studio:

```bash
streamlit run studio/app.py
```

## 7. Uso de IA

Ver `docs/uso_ia.md`.
```

- [ ] **Step 2: Run full suite** (no tests touch the informe directly, but smoke-checking)

Run: `python -m pytest -q`
Expected: 74 passed.

- [ ] **Step 3: Commit**

```bash
git add docs/informe.md
git commit -m "docs: enrich informe with AFD diagram, derivations, examples"
```

---

## Task 12: Claude SKILL.md

**Files:**
- Create: `.claude/skills/morselang-compiler/SKILL.md`

- [ ] **Step 1: Create the skill directory and write the file**

`.claude/skills/morselang-compiler/SKILL.md`:

````markdown
---
name: morselang-compiler
description: Use when working with the MorseLang compiler — writing or running .morse programs, decoding Morse from audio, opening the Studio UI, or asking how to use the CLI. Triggers on requests like "run this morse program", "open morselang studio", "how do I write X in morselang", or any mention of MorseLang / .morse files.
---

# MorseLang — Skill

MorseLang es un lenguaje de programación imperativo cuyo código fuente se escribe en código Morse. Este skill enseña a Claude cómo usar el compilador y el Studio que están en este repo.

## Sintaxis del lenguaje

Cada keyword, identificador, número y string se escribe en Morse. Letras de una palabra se separan con un espacio; palabras (tokens) se separan con `/` o tres espacios; sentencias con salto de línea.

### Keywords

| Texto | Morse |
|---|---|
| VAR | `...- .- .-.` |
| MOSTRAR | `-- --- ... - .-. .- .-.` |
| SI | `... ..` |
| SINO | `... .. -. ---` |
| MIENTRAS | `-- .. . -. - .-. .- ...` |
| FIN | `..-. .. -.` |
| VERDADERO | `...- . .-. -.. .- -.. . .-. ---` |
| FALSO | `..-. .- .-.. ... ---` |

### Operadores (palabras Morse, no símbolos)

| Texto | Morse | Significado |
|---|---|---|
| MAS | `-- .- ...` | + |
| MENOS | `-- . -. --- ...` | − |
| POR | `.--. --- .-.` | × |
| DIV | `-.. .. ...-` | ÷ (entera) |
| IGUAL | `.. --. ..- .- .-..` | == |
| DIST | `-.. .. ... -` | != |
| MEN | `-- . -.` | < |
| MAY | `-- .- -.--` | > |
| ASIG | `.- ... .. --.` | = (asignación) |

### Tabla Morse de referencia

```
A=.-     B=-...   C=-.-.   D=-..    E=.      F=..-.
G=--.    H=....   I=..     J=.---   K=-.-    L=.-..
M=--     N=-.     O=---    P=.--.   Q=--.-   R=.-.
S=...    T=-      U=..-    V=...-   W=.--    X=-..-
Y=-.--   Z=--..

0=-----  1=.----  2=..---  3=...--  4=....-
5=.....  6=-....  7=--...  8=---..  9=----.
```

### Strings

Entre `"..."`. El contenido es Morse. Para preservar espacios entre palabras dentro del string, usar **triple espacio o `/`** entre las palabras y espacio simple entre las letras de cada palabra:

```
"-- --- ... - .-. .- .-." / ".... --- .-.. .-   -- ..- -. -.. ---"
       MOSTRAR             "HOLA   MUNDO"  → imprime "HOLA MUNDO"
```

## Cómo correr un programa

```bash
python main.py archivo.morse                # solo ejecuta
python main.py archivo.morse --tokens       # imprime el token stream
python main.py archivo.morse --ast          # imprime el AST
python main.py archivo.morse --tts          # ejecuta + narra con ElevenLabs (necesita ELEVENLABS_API_KEY)
```

Códigos de salida:
- `0` — éxito
- `1` — error en alguna fase del compilador (léxico/sintáctico/semántico/runtime)
- `2` — archivo no encontrado

## Studio (UI visual)

```bash
streamlit run studio/app.py
```

Tiene 4 páginas:
- **Editor** — escribir / pegar código, ejecutar, ver tokens y AST.
- **Audio → Morse** — grabar o subir un `.wav` con beeps, decodificarlo, mandarlo al editor.
- **TP Inspector** — pestañas con cada Parte del TP (1 a 7) en vivo.
- **Ayuda** — tablas de Morse, keywords y operadores.

## Plantillas de programas

### Hola mundo

```
-- --- ... - .-. .- .-. / ".... --- .-.. .-   -- ..- -. -.. ---"
```

### Variable + aritmética

```
...- .- .-. / -..- / .- ... .. --. / .---- -----
...- .- .-. / -.-- / .- ... .. --. / -..- / -- .- ... / .....
-- --- ... - .-. .- .-. / -.--
```

### `MIENTRAS` con condición

```
...- .- .-. / .. / .- ... .. --. / -----
-- .. . -. - .-. .- ... / .. / -- . -. / ...--
-- --- ... - .-. .- .-. / ..
.. / .- ... .. --. / .. / -- .- ... / .----
..-. .. -.
```

## Errores comunes

| Síntoma | Causa frecuente |
|---|---|
| `Símbolo Morse inválido: '........'` | Secuencia de 8 puntos no es ninguna letra. |
| `token desconocido tras decodificar Morse: 'XYZ'` | Secuencia decodificada no es keyword/ident/número válido. |
| `literal de texto sin cerrar` | Falta el `"` de cierre. |
| `redeclaración de 'X'` | Hay dos `VAR X ASIG ...` en el mismo programa. |
| `la condición debe ser BOOL` | Pasaste un número o texto a `SI`/`MIENTRAS`. |

## Workflow para defender el TP

1. Abrir Studio (`streamlit run studio/app.py`).
2. **TP Inspector** → recorrer las 7 pestañas mostrando lo que hace cada una.
3. Volver al **Editor** → cargar `factorial.morse` desde el dropdown → `▶ Ejecutar` → mostrar la salida `120`.
4. Click `🔊 TTS` → reproducir el audio narrado.
5. **Audio → Morse** → grabar/subir un `.wav` → `🔍 Decodificar` → `→ Mandar al editor` → ejecutar.
6. Mostrar el repo: `morselang/` (compilador), `tests/` (74 tests verdes), `docs/informe.md`.
````

- [ ] **Step 2: Verify the file is well-formed**

Run: `python -c "from pathlib import Path; t = Path('.claude/skills/morselang-compiler/SKILL.md').read_text(encoding='utf-8'); assert t.startswith('---'); print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Run full suite**

Run: `python -m pytest -q`
Expected: 74 passed.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/morselang-compiler/SKILL.md
git commit -m "docs: add Claude SKILL.md for the MorseLang compiler"
```

---

## Task 13: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace `README.md`**

```markdown
# MorseLang

Lenguaje de programación cuyo código fuente se escribe en código Morse.
TP integrador de Lenguajes Formales y Compiladores.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uso — CLI

```bash
python main.py examples/hola.morse              # ejecuta
python main.py examples/factorial.morse --tts   # + narra con ElevenLabs
python main.py archivo.morse --tokens           # solo tokens
python main.py archivo.morse --ast              # solo AST
```

## Uso — Studio (UI visual)

```bash
streamlit run studio/app.py
```

Cuatro páginas: Editor, Audio→Morse (decodifica .wav o grabación de mic), TP Inspector (Partes 1-7 en vivo), Ayuda.

## Tests

```bash
pytest -q
```

74 tests cubriendo lexer, parser, semántico, intérprete, TTS, decoder de audio, AST y CLI.

## Variables de entorno

Para `--tts`:

- `ELEVENLABS_API_KEY` — clave de API.
- `ELEVENLABS_VOICE_ID` — id de la voz (default: voz multilingüe estándar).

Ver `.env.example`.

## Estructura

```
morselang/        # paquete del compilador
  morse.py        # codec Morse <-> texto
  tokens.py       # modelo de tokens
  lexer.py        # tokenizador
  ast_nodes.py    # nodos del AST + to_dict
  parser.py       # parser recursivo descendente (LL(1))
  symbol_table.py # tabla de símbolos
  semantic.py     # análisis semántico
  interpreter.py  # intérprete tree-walking
  tts.py          # cliente ElevenLabs
  audio.py        # decoder Morse desde audio (DSP)
studio/           # UI Streamlit
  app.py          # entry point
  components.py   # helpers compilador → estado
  pages/          # una página por archivo
examples/         # programas de ejemplo (.morse)
tests/            # pytest
docs/             # informe + bitácora de IA + tp_resources
.claude/skills/morselang-compiler/SKILL.md   # skill para Claude
main.py           # CLI
```

## Defensa del TP

Ver `docs/informe.md` y abrir el Studio para una vista interactiva de las 7 Partes del TP.
```

- [ ] **Step 2: Run full suite**

Run: `python -m pytest -q`
Expected: 74 passed.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README with Studio and audio decoder"
```

---

## Self-Review Checklist

After implementing all tasks, verify:

- [ ] **Spec coverage:**
  - Studio + 4 páginas → Tasks 7-10 ✅
  - Audio decoder → Tasks 2-4 ✅
  - AST serialization → Task 5 ✅
  - Interpreter step hook → Task 6 ✅
  - Enriched informe → Task 11 ✅
  - SKILL.md → Task 12 ✅
  - README → Task 13 ✅
  - Dependencies → Task 1 ✅
- [ ] **Type / name consistency:**
  - `decode_audio_to_morse` and `AudioDecodeResult` consistent across Tasks 2/3/4/8.
  - `compile_and_run`, `lex_only`, `parse_only` consistent across Tasks 7/10.
  - `to_dict` consistent in Tasks 5/7/10.
  - `on_step` callback signature consistent in Tasks 6/7.
- [ ] **No placeholders:** every step has actual code or commands. Reviewed.
- [ ] **Each task ends with a commit step.** Reviewed.

---

## Execution Handoff

Plan complete and saved to [`docs/superpowers/plans/2026-04-29-morselang-studio-implementation.md`](2026-04-29-morselang-studio-implementation.md). Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks.
2. **Inline Execution** — execute tasks in this session with checkpoints.

Which approach?
