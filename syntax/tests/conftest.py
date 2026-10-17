import copy
import sys
from pathlib import Path

import pytest

# The syntax folder (the one holding main.py) must be importable
SYNTAX_ROOT = Path(__file__).resolve().parent.parent
if str(SYNTAX_ROOT) not in sys.path:
    sys.path.insert(0, str(SYNTAX_ROOT))

from main import compute_first_set, compute_follow_set  # noqa: E402


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


def _follow_inputs(
    grammar: dict[str, list[list[str]]],
    first_preset: dict[str, set[str]] | None,
) -> tuple[dict[str, list[list[str]]], dict[str, set[str]], dict[str, set[str]], set[str]]:
    """Build private inputs for compute_follow_set; first is copied from first_preset, or computed if it is None."""
    grammar = copy.deepcopy(grammar)
    follow = {nt: set() for nt in grammar}
    non_terminals_set = set(grammar)
    if first_preset is None:
        first, _ = _fresh(grammar)
        compute_first_set(grammar, first, non_terminals_set)
    else:
        first = copy.deepcopy(first_preset)
    return grammar, first, follow, non_terminals_set


def _run_follow(
    grammar: dict[str, list[list[str]]],
    first_preset: dict[str, set[str]] | None,
) -> dict[str, set[str]]:
    """Compute FOLLOW on private inputs and return the resulting follow dict."""
    grammar, first, follow, non_terminals_set = _follow_inputs(grammar, first_preset)
    compute_follow_set(grammar, first, follow, non_terminals_set)
    return follow


@pytest.fixture
def fresh():
    return _fresh


@pytest.fixture
def reorder():
    return _reorder


@pytest.fixture
def run_first():
    return _run_first


@pytest.fixture
def follow_inputs():
    return _follow_inputs


@pytest.fixture
def run_follow():
    return _run_follow
