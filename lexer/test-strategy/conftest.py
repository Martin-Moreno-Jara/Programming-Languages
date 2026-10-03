import contextlib
import io
import subprocess
import sys
from pathlib import Path

import pytest

# Project root (the folder holding lexer.py and main.py) must be importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lexer import Lexer  # noqa: E402


def _lex_all(src: str) -> list:
    """Tokenize src until EOF or a lexical error; return tokens plus any printed lines."""
    lexer = Lexer(src)
    tokens = []
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            while True:
                tokens.append(lexer.tokenize())
    except (EOFError, SystemExit):
        pass
    return tokens + buffer.getvalue().splitlines()


def _run_main_process(stdin: str) -> subprocess.CompletedProcess:
    """Run main.py as a separate process with stdin as input; return the full result."""
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py")],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=PROJECT_ROOT,
        timeout=10,
    )


def _run_main(stdin: str) -> str:
    """Run main.py as a separate process with stdin as input; return its stdout."""
    return _run_main_process(stdin).stdout


@pytest.fixture
def lex_all():
    return _lex_all


@pytest.fixture
def run_main():
    return _run_main


@pytest.fixture
def run_main_process():
    return _run_main_process
