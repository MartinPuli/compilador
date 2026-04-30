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
    assert "HOLAMUNDO" in result.stdout


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
