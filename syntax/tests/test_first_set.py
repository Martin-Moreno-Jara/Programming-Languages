import copy
import itertools

import pytest

from main import compute_first_set, first_of_sequence

EPS = "ε"

# (case_id, grammar, expected) rows from plan.md §6.1, filled in by task.md section 3
GRAMMAR_CASES: list[tuple[str, dict[str, list[list[str]]], dict[str, set[str]]]] = []


def _grammar_params() -> list:
    """Turn GRAMMAR_CASES into pytest params of (grammar, expected), with the case id as test id."""
    return [pytest.param(grammar, expected, id=case_id) for case_id, grammar, expected in GRAMMAR_CASES]


# ---------------------------------------------------------------------------
# Unit tests: first_of_sequence (plan.md §5)
# ---------------------------------------------------------------------------

# (productions_of_A, preset FIRST of helper non-terminals, expected FIRST(A))
FIRST_OF_SEQUENCE_CASES = [
    pytest.param([["a"]], {}, {"a"}, id="U1-single-terminal"),
    pytest.param([["a"], ["b", "c"]], {}, {"a", "b"}, id="U2-several-alternatives"),
    pytest.param([[EPS]], {}, {EPS}, id="U3-epsilon"),
    pytest.param([["a"], [EPS]], {}, {"a", EPS}, id="U4-terminal-or-epsilon"),
    pytest.param([["a", "X"]], {"X": {"x"}}, {"a"}, id="U5-leading-terminal-stops"),
    pytest.param([["X", "y"]], {"X": {"x"}}, {"x"}, id="U6-non-nullable-stops"),
    pytest.param([["X", "y"]], {"X": {"x", EPS}}, {"x", "y"}, id="U7-nullable-then-terminal"),
    pytest.param(
        [["X", "Y"]],
        {"X": {"x", EPS}, "Y": {"y", EPS}},
        {"x", "y", EPS},
        id="U8-all-nullable",
    ),
    pytest.param(
        [["X", "Y", "Z"]],
        {"X": {"x", EPS}, "Y": {"y", EPS}, "Z": {"z"}},
        {"x", "y", "z"},
        id="U9-nullable-chain-then-nt",
    ),
    pytest.param(
        [["X", "Y", "w"]],
        {"X": {"x", EPS}, "Y": {"y"}},
        {"x", "y"},
        id="U10-stops-before-terminal",
    ),
]


@pytest.mark.parametrize("productions_of_A, preset, expected", FIRST_OF_SEQUENCE_CASES)
def test_first_of_sequence(productions_of_A, preset, expected, fresh):
    # Helpers get dummy productions: they only need to be keys to count as non-terminals
    grammar = {"A": productions_of_A, **{h: [["_"]] for h in preset}}
    first, non_terminals_set = fresh(grammar)
    for h, s in preset.items():
        first[h] = set(s)
    helpers_before = copy.deepcopy({h: first[h] for h in preset})

    first_of_sequence("A", grammar["A"], first, non_terminals_set)

    # Re-read first["A"]: the implementation may replace the set object
    assert first["A"] == expected
    assert {h: first[h] for h in preset} == helpers_before


def test_first_of_sequence_only_adds(fresh):
    grammar = {"A": [["a"]]}
    first, non_terminals_set = fresh(grammar)
    first["A"] = {"q"}

    first_of_sequence("A", grammar["A"], first, non_terminals_set)

    assert first["A"] == {"q", "a"}
