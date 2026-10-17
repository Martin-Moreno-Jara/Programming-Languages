import copy
import itertools

import pytest

import main
from main import compute_follow_set

EPS = "ε"
END = "$"

# Every test in this file fails instead of hanging if compute_follow_set never returns (spec §6)
pytestmark = pytest.mark.timeout(2)

# "<test function>::<param id>" -> (reason, expected exception type); filled in by the xfail workflow (tasks.md §9)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}

# (case_id, grammar, first_preset, expected) rows from plan.md §5. The first key of
# each grammar is the start symbol. first_preset is the hand-written FIRST for F rows,
# and None for E rows, which compute FIRST instead. Plain tuples so the property,
# order-independence and idempotence tests can reuse them.
FOLLOW_CASES: list[
    tuple[str, dict[str, list[list[str]]], dict[str, set[str]] | None, dict[str, set[str]]]
] = [
    # F rows: rule-level tests with hand-written FIRST (plan.md §5.1)
    (
        "F1-start-only",
        {"S": [["a"]]},
        {"S": {"a"}},
        {"S": {END}},
    ),
    (
        "F2-terminal-after-nt",
        {"S": [["A", "b"]], "A": [["a"]]},
        {"S": {"a"}, "A": {"a"}},
        {"S": {END}, "A": {"b"}},
    ),
    (
        "F3-nt-at-end",
        {"S": [["a", "A"]], "A": [["b"]]},
        {"S": {"a"}, "A": {"b"}},
        {"S": {END}, "A": {END}},
    ),
    (
        "F4-non-nullable-next",
        {"S": [["A", "B"]], "A": [["a"]], "B": [["b"]]},
        {"S": {"a"}, "A": {"a"}, "B": {"b"}},
        {"S": {END}, "A": {"b"}, "B": {END}},
    ),
    (
        "F5-skip-nullable",
        {"S": [["A", "B", "c"]], "A": [["a"]], "B": [["b"], [EPS]]},
        {"S": {"a"}, "A": {"a"}, "B": {"b", EPS}},
        {"S": {END}, "A": {"b", "c"}, "B": {"c"}},
    ),
    (
        "F6-nullable-tail-inherits",
        {"S": [["A", "B"]], "A": [["a"]], "B": [["b"], [EPS]]},
        {"S": {"a"}, "A": {"a"}, "B": {"b", EPS}},
        {"S": {END}, "A": {"b", END}, "B": {END}},
    ),
    (
        "F7-long-nullable-tail",
        {"S": [["x", "A", "B", "C"]], "A": [["a"]], "B": [["b"], [EPS]], "C": [["c"], [EPS]]},
        {"S": {"x"}, "A": {"a"}, "B": {"b", EPS}, "C": {"c", EPS}},
        {"S": {END}, "A": {"b", "c", END}, "B": {"c", END}, "C": {END}},
    ),
    (
        "F8-same-nt-twice",
        {"S": [["A", "a", "A"]], "A": [["x"]]},
        {"S": {"x"}, "A": {"x"}},
        {"S": {END}, "A": {"a", END}},
    ),
    (
        "F9-used-in-several-rules",
        {"S": [["A", "x"], ["B"]], "B": [["A", "y"]], "A": [["a"]]},
        {"S": {"a"}, "B": {"a"}, "A": {"a"}},
        {"S": {END}, "B": {END}, "A": {"x", "y"}},
    ),
    (
        "F10-multi-level-inherit",
        {"S": [["A", "z"]], "A": [["b", "B"]], "B": [["c", "C"]], "C": [["d"]]},
        {"S": {"b"}, "A": {"b"}, "B": {"c"}, "C": {"d"}},
        {"S": {END}, "A": {"z"}, "B": {"z"}, "C": {"z"}},
    ),
    (
        "F11-nested-nullable-tail",
        {"S": [["A", "z"]], "A": [["B", "C"]], "B": [["b"]], "C": [["c"], [EPS]]},
        {"S": {"b"}, "A": {"b"}, "B": {"b"}, "C": {"c", EPS}},
        {"S": {END}, "A": {"z"}, "B": {"c", "z"}, "C": {"z"}},
    ),
    (
        "F12-follow-cycle",
        {"S": [["A", "t"]], "A": [["a", "B"]], "B": [["b", "A"], [EPS]]},
        {"S": {"a"}, "A": {"a"}, "B": {"b", EPS}},
        {"S": {END}, "A": {"t"}, "B": {"t"}},
    ),
    (
        "F13-start-on-rhs",
        {"S": [["(", "S", ")"], ["x"]]},
        {"S": {"(", "x"}},
        {"S": {END, ")"}},
    ),
    (
        "F14-start-gains-from-deep",
        {"S": [["A"]], "A": [["b", "S", "c"], ["d"]]},
        {"S": {"b", "d"}, "A": {"b", "d"}},
        {"S": {END, "c"}, "A": {END, "c"}},
    ),
    (
        "F15-unreachable-nt",
        {"S": [["a"]], "U": [["u"]]},
        {"S": {"a"}, "U": {"u"}},
        {"S": {END}, "U": set()},
    ),
    (
        "F16-epsilon-only-tail",
        {"S": [["A", "E"]], "A": [["a"]], "E": [[EPS]]},
        {"S": {"a"}, "A": {"a"}, "E": {EPS}},
        {"S": {END}, "A": {END}, "E": {END}},
    ),
    (
        "F17-left-recursion",
        {"E": [["E", "+", "T"], ["T"]], "T": [["id"]]},
        {"E": {"id"}, "T": {"id"}},
        {"E": {END, "+"}, "T": {END, "+"}},
    ),
    (
        "F18-self-at-end",
        {"L": [["x", "L"], [EPS]]},
        {"L": {"x", EPS}},
        {"L": {END}},
    ),
    (
        "F19-nt-followed-by-itself",
        {"S": [["A", "A"]], "A": [["a"], [EPS]]},
        {"S": {"a", EPS}, "A": {"a", EPS}},
        {"S": {END}, "A": {"a", END}},
    ),
    (
        "F20-lua-like",
        {
            "Chunk": [["Block"]],
            "Block": [["Stat", "Block"], [EPS]],
            "Stat": [["if", "Exp", "then", "Block", "end"], ["Name", "=", "Exp"]],
            "Exp": [["Name"], ["Number"]],
        },
        {
            "Chunk": {"if", "Name", EPS},
            "Block": {"if", "Name", EPS},
            "Stat": {"if", "Name"},
            "Exp": {"Name", "Number"},
        },
        {
            "Chunk": {END},
            "Block": {END, "end"},
            "Stat": {"if", "Name", END, "end"},
            "Exp": {"then", "if", "Name", END, "end"},
        },
    ),
    # E rows: full pipeline, FIRST is computed (plan.md §5.2)
    (
        "E1-main-grammar",
        {
            "A": [["B", "C"], ["ant", "A", "all"]],
            "B": [["big", "C"], ["bus", "A", "boss"], [EPS]],
            "C": [["cat"], ["cow"]],
        },
        None,
        {"A": {END, "all", "boss"}, "B": {"cat", "cow"}, "C": {END, "all", "boss", "cat", "cow"}},
    ),
    (
        "E2-expression-grammar",
        {
            "E": [["T", "E'"]],
            "E'": [["+", "T", "E'"], [EPS]],
            "T": [["F", "T'"]],
            "T'": [["*", "F", "T'"], [EPS]],
            "F": [["(", "E", ")"], ["id"]],
        },
        None,
        {
            "E": {END, ")"},
            "E'": {END, ")"},
            "T": {"+", END, ")"},
            "T'": {"+", END, ")"},
            "F": {"*", "+", END, ")"},
        },
    ),
    (
        "E3-indirect-nullable-tail",
        {"S": [["A", "B", "C"]], "A": [["a"]], "B": [["D"]], "D": [["d"], [EPS]], "C": [["c"], [EPS]]},
        None,
        {"S": {END}, "A": {"d", "c", END}, "B": {"c", END}, "C": {END}, "D": {"c", END}},
    ),
]

# E4 shares F20's grammar and expected objects, so the two rows can never drift apart
_, _lua_grammar, _, _lua_expected = next(case for case in FOLLOW_CASES if case[0] == "F20-lua-like")
FOLLOW_CASES.append(("E4-lua-like-pipeline", _lua_grammar, None, _lua_expected))


def _case_params(test_name: str, kind: str | None = None) -> list:
    """Turn FOLLOW_CASES into pytest params of (grammar, first_preset, expected); kind "F" or "E" keeps only those rows."""
    params = []
    for case_id, grammar, first_preset, expected in FOLLOW_CASES:
        if kind is not None and not case_id.startswith(kind):
            continue
        marks = []
        key = f"{test_name}::{case_id}"
        if key in KNOWN_FAILURES:
            reason, exception = KNOWN_FAILURES[key]
            marks.append(pytest.mark.xfail(reason=reason, raises=exception, strict=True))
        params.append(pytest.param(grammar, first_preset, expected, id=case_id, marks=marks))
    return params


# ---------------------------------------------------------------------------
# Main tests: F rows, hand-written FIRST (plan.md §6.1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, expected", _case_params("test_follow_rules", "F"))
def test_follow_rules(grammar, first_preset, expected, run_follow):
    # Whole-dict comparison: exact set per non-terminal and no keys added or missing
    assert run_follow(grammar, first_preset) == expected
