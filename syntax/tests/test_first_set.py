import copy
import itertools

import pytest

import main
from main import compute_first_set, first_of_sequence

EPS = "ε"

# (case_id, grammar, expected) rows from plan.md §6.1. Plain tuples so the
# order-independence and idempotence tests can reuse them.
GRAMMAR_CASES: list[tuple[str, dict[str, list[list[str]]], dict[str, set[str]]]] = [
    (
        "E1-only-terminals",
        {"S": [["a", "b"], ["c"]]},
        {"S": {"a", "c"}},
    ),
    (
        "E2-main-grammar",
        {
            "A": [["B", "C"], ["ant", "A", "all"]],
            "B": [["big", "C"], ["bus", "A", "boss"], [EPS]],
            "C": [["cat"], ["cow"]],
        },
        {"A": {"ant", "big", "bus", "cat", "cow"}, "B": {"big", "bus", EPS}, "C": {"cat", "cow"}},
    ),
    (
        "E3-dependency-chain",
        {"S": [["A"]], "A": [["B"]], "B": [["b"]]},
        {"S": {"b"}, "A": {"b"}, "B": {"b"}},
    ),
    (
        "E4-nullable-prefix",
        {"S": [["A", "B", "c"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]]},
        {"S": {"a", "b", "c"}, "A": {"a", EPS}, "B": {"b", EPS}},
    ),
    (
        "E5-whole-body-nullable",
        {"S": [["A", "B"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]]},
        {"S": {"a", "b", EPS}, "A": {"a", EPS}, "B": {"b", EPS}},
    ),
    (
        "E6-indirectly-nullable",
        {"S": [["A"]], "A": [["B"]], "B": [[EPS]]},
        {"S": {EPS}, "A": {EPS}, "B": {EPS}},
    ),
    (
        "E7-epsilon-does-not-leak",
        {"S": [["A", "b"]], "A": [[EPS]]},
        {"S": {"b"}, "A": {EPS}},
    ),
    (
        "E8-non-nullable-blocks",
        {"S": [["A", "B"]], "A": [["a"]], "B": [["b"]]},
        {"S": {"a"}, "A": {"a"}, "B": {"b"}},
    ),
    (
        "E9-left-recursion",
        {"E": [["E", "+", "T"], ["T"]], "T": [["id"], ["(", "E", ")"]]},
        {"E": {"id", "("}, "T": {"id", "("}},
    ),
    (
        "E10-mutual-recursion",
        {"A": [["B", "a"], ["x"]], "B": [["A", "b"], ["y"]]},
        {"A": {"x", "y"}, "B": {"x", "y"}},
    ),
    (
        "E11-recursion-with-nullable",
        {"A": [["B", "A"], ["a"]], "B": [["b"], [EPS]]},
        {"A": {"a", "b"}, "B": {"b", EPS}},
    ),
    (
        "E12-right-recursion",
        {"L": [["x", "L"], [EPS]]},
        {"L": {"x", EPS}},
    ),
    (
        "E13-expression-grammar",
        {
            "E": [["T", "E'"]],
            "E'": [["+", "T", "E'"], [EPS]],
            "T": [["F", "T'"]],
            "T'": [["*", "F", "T'"], [EPS]],
            "F": [["(", "E", ")"], ["id"]],
        },
        {"E": {"(", "id"}, "E'": {"+", EPS}, "T": {"(", "id"}, "T'": {"*", EPS}, "F": {"(", "id"}},
    ),
    (
        "E14-common-prefix",
        {"S": [["a", "b"], ["a", "c"]]},
        {"S": {"a"}},
    ),
    (
        "E15-multichar-terminals",
        {
            "Stat": [["local", "Name", "=", "Exp"], ["Exp"]],
            "Exp": [["(", "Exp", ")"], ["Exp", "==", "Exp"], ["Name"]],
        },
        {"Stat": {"local", "(", "Name"}, "Exp": {"(", "Name"}},
    ),
]


def _grammar_params() -> list:
    """Turn GRAMMAR_CASES into pytest params of (grammar, expected), with the case id as test id."""
    return [pytest.param(grammar, expected, id=case_id) for case_id, grammar, expected in GRAMMAR_CASES]


# ---------------------------------------------------------------------------
# Unit tests: first_of_sequence (plan.md §5)
# ---------------------------------------------------------------------------

# (sequence, preset FIRST of helper non-terminals, expected FIRST(sequence))
FIRST_OF_SEQUENCE_CASES = [
    pytest.param(["a"], {}, {"a"}, id="U1-single-terminal"),
    pytest.param(["b", "c"], {}, {"b"}, id="U2-terminal-sequence"),
    pytest.param([EPS], {}, {EPS}, id="U3-epsilon"),
    pytest.param(["X"], {"X": {"x", EPS}}, {"x", EPS}, id="U4-single-nullable-nt"),
    pytest.param(["a", "X"], {"X": {"x"}}, {"a"}, id="U5-leading-terminal-stops"),
    pytest.param(["X", "y"], {"X": {"x"}}, {"x"}, id="U6-non-nullable-stops"),
    pytest.param(["X", "y"], {"X": {"x", EPS}}, {"x", "y"}, id="U7-nullable-then-terminal"),
    pytest.param(
        ["X", "Y"],
        {"X": {"x", EPS}, "Y": {"y", EPS}},
        {"x", "y", EPS},
        id="U8-all-nullable",
    ),
    pytest.param(
        ["X", "Y", "Z"],
        {"X": {"x", EPS}, "Y": {"y", EPS}, "Z": {"z"}},
        {"x", "y", "z"},
        id="U9-nullable-chain-then-nt",
    ),
    pytest.param(
        ["X", "Y", "w"],
        {"X": {"x", EPS}, "Y": {"y"}},
        {"x", "y"},
        id="U10-stops-before-terminal",
    ),
    pytest.param(["X", "y"], {"X": set()}, set(), id="U11-not-yet-computed-nt"),
]


@pytest.mark.parametrize("sequence, preset, expected", FIRST_OF_SEQUENCE_CASES)
def test_first_of_sequence(sequence, preset, expected, fresh):
    # Helpers get dummy productions: they only need to be keys to count as non-terminals
    first, non_terminals_set = fresh({h: [["_"]] for h in preset})
    for h, s in preset.items():
        first[h] = set(s)
    first_before = copy.deepcopy(first)

    result = first_of_sequence(sequence, first, non_terminals_set)

    assert result == expected
    assert first == first_before  # the function only reads first


# ---------------------------------------------------------------------------
# End-to-end tests: compute_first_set (plan.md §6)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, expected", _grammar_params())
def test_compute_first_set(grammar, expected, run_first):
    # Whole-dict comparison: exact set per non-terminal and no keys added or missing
    assert run_first(grammar) == expected


# ---------------------------------------------------------------------------
# Order independence (plan.md §7.1)
# ---------------------------------------------------------------------------

# param id -> (reason, expected exception type); filled in by the xfail workflow (task.md §7)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}


def _order_params() -> list:
    """One param per declaration order of each GRAMMAR_CASES grammar: all permutations up to 4 non-terminals, else declared and reversed."""
    params = []
    for case_id, grammar, expected in GRAMMAR_CASES:
        declared = tuple(grammar)
        if len(declared) <= 4:
            orders = list(itertools.permutations(declared))
        else:
            orders = [declared, tuple(reversed(declared))]
        for order in orders:
            param_id = f"{case_id}[{','.join(order)}]"
            marks = []
            if param_id in KNOWN_FAILURES:
                reason, exception = KNOWN_FAILURES[param_id]
                marks.append(pytest.mark.xfail(reason=reason, raises=exception, strict=True))
            params.append(pytest.param(grammar, order, expected, id=param_id, marks=marks))
    return params


@pytest.mark.parametrize("grammar, order, expected", _order_params())
def test_first_is_order_independent(grammar, order, expected, reorder, run_first):
    assert run_first(reorder(grammar, order)) == expected


# ---------------------------------------------------------------------------
# Idempotence (plan.md §7.2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, expected", _grammar_params())
def test_compute_first_set_idempotent(grammar, expected, fresh):
    # expected is unused: correctness is checked by test_compute_first_set,
    # here a second call only has to leave first unchanged
    grammar = copy.deepcopy(grammar)
    first, non_terminals_set = fresh(grammar)
    compute_first_set(grammar, first, non_terminals_set)
    snapshot = copy.deepcopy(first)

    compute_first_set(grammar, first, non_terminals_set)

    assert first == snapshot


# ---------------------------------------------------------------------------
# Isolation (plan.md §7.3)
# ---------------------------------------------------------------------------

def test_module_globals_untouched(run_first):
    globals_before = copy.deepcopy((main.grammar, main.first, main.non_terminals_set))
    e4_grammar = next(grammar for case_id, grammar, _ in GRAMMAR_CASES if case_id == "E4-nullable-prefix")

    run_first(e4_grammar)

    assert (main.grammar, main.first, main.non_terminals_set) == globals_before
