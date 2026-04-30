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


def test_cli_runs_simple_program(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent
    src_file = tmp_path / "hola.morse"
    src_file.write_text('-- --- ... - .-. .- .-. / ".... .."\n', encoding="utf-8")
    result = run_cli([str(src_file)], cwd=repo_root)
    assert result.returncode == 0, result.stderr
    assert "HI" in result.stdout


def test_cli_reports_lex_error_with_exit_code(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent
    src_file = tmp_path / "bad.morse"
    src_file.write_text("........\n", encoding="utf-8")
    result = run_cli([str(src_file)], cwd=repo_root)
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "línea 1" in combined or "linea 1" in combined


def test_cli_tokens_flag_lists_tokens(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent
    src_file = tmp_path / "x.morse"
    src_file.write_text("-- --- ... - .-. .- .-. / .----\n", encoding="utf-8")
    result = run_cli([str(src_file), "--tokens"], cwd=repo_root)
    assert result.returncode == 0
    assert "MOSTRAR" in result.stdout
    assert "NUMBER" in result.stdout
