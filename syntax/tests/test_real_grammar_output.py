import subprocess
import sys
from pathlib import Path

import pytest

from real_grammar_cases import OUTPUT_ROWS
from real_grammar_support import params

# Each case runs main.py in a subprocess (spec §8)
pytestmark = pytest.mark.timeout(30)

# "<test function>::<param id>" -> (reason, expected exception type); filled in by the xfail workflow (tasks.md §10)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}


def run_main(project_copy, source: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "main.py"], cwd=project_copy, input=source, capture_output=True, text=True, timeout=20
    )


# lua_parser is requested only for its skip: main.py prints its own text when the grammar is not LL(1)
@pytest.mark.parametrize("source, expected", params("test_main_output", OUTPUT_ROWS, KNOWN_FAILURES))
def test_main_output(lua_parser, project_copy, source, expected):
    result = run_main(project_copy, source)
    report = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    lines = result.stdout.splitlines()
    assert len(lines) == 1, report
    if callable(expected):
        assert expected(lines[0]), report
    else:
        assert lines[0] == expected, report


# Platform feedback (spec §8.1): NN.in and its NN-output.txt, whose first line is the grader's expected output
PLATFORM_DIR = Path(__file__).resolve().parent.parent / "test_files"


def _platform_rows() -> list[tuple[str, str, str]]:
    rows = []
    for source in sorted(PLATFORM_DIR.glob("*.in")):
        outputs = [PLATFORM_DIR / f"{source.stem}-output.txt", PLATFORM_DIR / f"{source.stem}.output.txt"]
        output = next(path for path in outputs if path.exists())
        expected = output.read_text(encoding="utf-8").splitlines()[0]
        rows.append((f"platform-{source.stem}", source.read_text(encoding="utf-8"), expected))
    return rows


PLATFORM_ROWS = _platform_rows()
assert len(PLATFORM_ROWS) == 10, len(PLATFORM_ROWS)


@pytest.mark.parametrize("source, expected", params("test_platform_output", PLATFORM_ROWS, KNOWN_FAILURES))
def test_platform_output(lua_parser, project_copy, source, expected):
    # The source is passed as downloaded, with no trailing newline, as the platform sends it
    result = run_main(project_copy, source)
    report = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert result.stdout.splitlines() == [expected], report
