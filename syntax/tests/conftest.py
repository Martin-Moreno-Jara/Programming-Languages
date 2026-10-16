import copy
import sys
from pathlib import Path

import pytest

# The syntax folder (the one holding main.py) must be importable
SYNTAX_ROOT = Path(__file__).resolve().parent.parent
if str(SYNTAX_ROOT) not in sys.path:
    sys.path.insert(0, str(SYNTAX_ROOT))

from main import compute_first_set  # noqa: E402


def _fresh(grammar: dict[str, list[list[str]]]) -> tuple[dict[str, set[str]], set[str]]:
    """Build the inputs the caller must prepare: an empty FIRST set per non-terminal, and the non-terminal set."""
    return {nt: set() for nt in grammar}, set(grammar)


def _reorder(grammar: dict[str, list[list[str]]], order: tuple[str, ...]) -> dict[str, list[list[str]]]:
    """Return the same grammar with its non-terminals declared in the given order."""
    return {nt: grammar[nt] for nt in order}


def _run_first(grammar: dict[str, list[list[str]]]) -> dict[str, set[str]]:
    """Compute FIRST on a private copy of grammar and return the resulting first dict."""
    grammar = copy.deepcopy(grammar)
    first, non_terminals_set = _fresh(grammar)
    compute_first_set(grammar, first, non_terminals_set)
    return first


@pytest.fixture
def fresh():
    return _fresh


@pytest.fixture
def reorder():
    return _reorder


@pytest.fixture
def run_first():
    return _run_first
