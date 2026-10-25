import subprocess
import sys

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
