import copy
import itertools

import pytest

from grammar import Grammar

EPS = "ε"
END = "$"
# A token that appears in no grammar; added to predict entries by the independence test
PROBE = "<probe>"

# Every test in this file fails instead of hanging if Grammar.compute_predict_set never returns (spec §6)
pytestmark = pytest.mark.timeout(2)

# "<test function>::<param id>" -> (reason, expected exception type); filled in by the xfail workflow (tasks.md §11)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}

# (case_id, grammar, first_preset, follow_preset, expected) rows from plan.md §5. The
# first key of each grammar is the start symbol. P rows have hand-written FIRST and
# FOLLOW; E rows have None for both, which computes them instead. expected maps each
# non-terminal to one set per production, in production order. Plain tuples so the
# property, order-independence and fresh-run tests can reuse them.
PREDICT_CASES: list[
    tuple[
        str,
        dict[str, list[list[str]]],
        dict[str, set[str]] | None,
        dict[str, set[str]] | None,
        dict[str, list[set[str]]],
    ]
] = [
    # P rows: rule-level tests with hand-written FIRST and FOLLOW (plan.md §5.1)
    (
        "P1-single-terminal",
        {"S": [["a"]]},
        {"S": {"a"}},
        {"S": {END}},
        {"S": [{"a"}]},
    ),
    (
        "P2-terminal-led",
        {"S": [["a", "B"], ["b"]], "B": [["c"]]},
        {"S": {"a", "b"}, "B": {"c"}},
        {"S": {END}, "B": {END}},
        {"S": [{"a"}, {"b"}], "B": [{"c"}]},
    ),
    (
        "P3-epsilon-gets-follow",
        {"S": [["A", "b"]], "A": [["a"], [EPS]]},
        {"S": {"a", "b"}, "A": {"a", EPS}},
        {"S": {END}, "A": {"b"}},
        {"S": [{"a", "b"}], "A": [{"a"}, {"b"}]},
    ),
    (
        "P4-start-epsilon-dollar",
        {"S": [["a", "S"], [EPS]]},
        {"S": {"a", EPS}},
        {"S": {END}},
        {"S": [{"a"}, {END}]},
    ),
    (
        "P5-non-nullable-hides-rest",
        {"S": [["A", "b"]], "A": [["a"]]},
        {"S": {"a"}, "A": {"a"}},
        {"S": {END}, "A": {"b"}},
        {"S": [{"a"}], "A": [{"a"}]},
    ),
    (
        "P6-rest-not-follow-of-symbol",
        {"S": [["A", "B"], ["x", "A", "d"]], "A": [["a"], [EPS]], "B": [["b"]]},
        {"S": {"a", "b", "x"}, "A": {"a", EPS}, "B": {"b"}},
        {"S": {END}, "A": {"b", "d"}, "B": {END}},
        {"S": [{"a", "b"}, {"x"}], "A": [{"a"}, {"b", "d"}], "B": [{"b"}]},
    ),
    (
        "P7-long-nullable-prefix",
        {"S": [["A", "B", "c"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]]},
        {"S": {"a", "b", "c"}, "A": {"a", EPS}, "B": {"b", EPS}},
        {"S": {END}, "A": {"b", "c"}, "B": {"c"}},
        {"S": [{"a", "b", "c"}], "A": [{"a"}, {"b", "c"}], "B": [{"b"}, {"c"}]},
    ),
    (
        "P8-all-nullable-adds-follow",
        {"S": [["T", "z"]], "T": [["A", "B"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]]},
        {"S": {"a", "b", "z"}, "T": {"a", "b", EPS}, "A": {"a", EPS}, "B": {"b", EPS}},
        {"S": {END}, "T": {"z"}, "A": {"b", "z"}, "B": {"z"}},
        {"S": [{"a", "b", "z"}], "T": [{"a", "b", "z"}], "A": [{"a"}, {"b", "z"}], "B": [{"b"}, {"z"}]},
    ),
    (
        "P9-indirectly-nullable",
        {"S": [["A", "x"]], "A": [["B"], ["y"]], "B": [["b"], [EPS]]},
        {"S": {"b", "y", "x"}, "A": {"b", "y", EPS}, "B": {"b", EPS}},
        {"S": {END}, "A": {"x"}, "B": {"x"}},
        {"S": [{"b", "y", "x"}], "A": [{"b", "x"}, {"y"}], "B": [{"b"}, {"x"}]},
    ),
    (
        "P10-nullable-start",
        {"S": [["E", "F"]], "E": [[EPS]], "F": [["f"], [EPS]]},
        {"S": {"f", EPS}, "E": {EPS}, "F": {"f", EPS}},
        {"S": {END}, "E": {"f", END}, "F": {END}},
        {"S": [{"f", END}], "E": [{"f", END}], "F": [{"f"}, {END}]},
    ),
    (
        "P11-left-recursion",
        {"E": [["E", "+", "T"], ["T"]], "T": [["id"]]},
        {"E": {"id"}, "T": {"id"}},
        {"E": {END, "+"}, "T": {END, "+"}},
        {"E": [{"id"}, {"id"}], "T": [{"id"}]},
    ),
    (
        "P12-common-prefix",
        {"S": [["a", "b"], ["a", "c"]]},
        {"S": {"a"}},
        {"S": {END}},
        {"S": [{"a"}, {"a"}]},
    ),
    (
        "P13-epsilon-follow-overlap",
        {"S": [["A", "a"]], "A": [["a"], [EPS]]},
        {"S": {"a"}, "A": {"a", EPS}},
        {"S": {END}, "A": {"a"}},
        {"S": [{"a"}], "A": [{"a"}, {"a"}]},
    ),
    (
        "P14-identical-productions",
        {"S": [["a"], ["a"]]},
        {"S": {"a"}},
        {"S": {END}},
        {"S": [{"a"}, {"a"}]},
    ),
    (
        "P15-lua-like",
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
        {
            "Chunk": [{"if", "Name", END}],
            "Block": [{"if", "Name"}, {END, "end"}],
            "Stat": [{"if"}, {"Name"}],
            "Exp": [{"Name"}, {"Number"}],
        },
    ),
    (
        "P16-unreachable-empty-set",
        {"S": [["a"]], "U": [["u"], [EPS]]},
        {"S": {"a"}, "U": {"u", EPS}},
        {"S": {END}, "U": set()},
        {"S": [{"a"}], "U": [{"u"}, set()]},
    ),
    (
        "P17-production-order",
        {"S": [["c"], ["a"], ["b"], [EPS]]},
        {"S": {"a", "b", "c", EPS}},
        {"S": {END}},
        {"S": [{"c"}, {"a"}, {"b"}, {END}]},
    ),
    (
        "P18-terminal-ends-scan",
        {"S": [["a", "A"]], "A": [["b"], [EPS]]},
        {"S": {"a"}, "A": {"b", EPS}},
        {"S": {END}, "A": {END}},
        {"S": [{"a"}], "A": [{"b"}, {END}]},
    ),
    # E rows: full pipeline, FIRST and FOLLOW are computed (plan.md §5.2)
    (
        "E1-main-grammar",
        {
            "A": [["B", "C"], ["ant", "A", "all"]],
            "B": [["big", "C"], ["bus", "A", "boss"], [EPS]],
            "C": [["cat"], ["cow"]],
        },
        None,
        None,
        {"A": [{"big", "bus", "cat", "cow"}, {"ant"}], "B": [{"big"}, {"bus"}, {"cat", "cow"}], "C": [{"cat"}, {"cow"}]},
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
        None,
        {
            "E": [{"(", "id"}],
            "E'": [{"+"}, {END, ")"}],
            "T": [{"(", "id"}],
            "T'": [{"*"}, {"+", END, ")"}],
            "F": [{"("}, {"id"}],
        },
    ),
    (
        "E3-commented-grammar",
        {"S": [["A", "B", "C"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]], "C": [["c"]]},
        None,
        None,
        {"S": [{"a", "b", "c"}], "A": [{"a"}, {"b", "c"}], "B": [{"b"}, {"c"}], "C": [{"c"}]},
    ),
]

# E4 shares P15's grammar and expected objects, so the two rows can never drift apart
_, _lua_grammar, _, _, _lua_expected = next(case for case in PREDICT_CASES if case[0] == "P15-lua-like")
PREDICT_CASES.append(("E4-lua-like-pipeline", _lua_grammar, None, None, _lua_expected))


def _case_params(test_name: str, kind: str | None = None) -> list:
    """Turn PREDICT_CASES into pytest params of (grammar, first_preset, follow_preset, expected); kind "P" or "E" keeps only those rows."""
    params = []
    for case_id, grammar, first_preset, follow_preset, expected in PREDICT_CASES:
        if kind is not None and not case_id.startswith(kind):
            continue
        marks = []
        key = f"{test_name}::{case_id}"
        if key in KNOWN_FAILURES:
            reason, exception = KNOWN_FAILURES[key]
            marks.append(pytest.mark.xfail(reason=reason, raises=exception, strict=True))
        params.append(pytest.param(grammar, first_preset, follow_preset, expected, id=case_id, marks=marks))
    return params


# ---------------------------------------------------------------------------
# Initial state and getter: Grammar.__init__, Grammar.get_predict_set (plan.md §6.0)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_predict_starts_empty"))
def test_predict_starts_empty(grammar, first_preset, follow_preset, expected, new_grammar):
    # Presets and expected are unused: only the keys of the grammar matter here
    assert new_grammar(grammar).predict == {nt: [] for nt in grammar}


@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_get_predict_set"))
def test_get_predict_set(grammar, first_preset, follow_preset, expected, predict_grammar):
    # expected is unused: the getter must hand out the object's own predict dict, not a copy
    g = predict_grammar(grammar, first_preset, follow_preset)
    assert g.get_predict_set() is g.predict

    g.compute_predict_set()

    assert g.get_predict_set() is g.predict


# ---------------------------------------------------------------------------
# Main tests: P rows, hand-written FIRST and FOLLOW (plan.md §6.1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_predict_rules", "P"))
def test_predict_rules(grammar, first_preset, follow_preset, expected, run_predict):
    # Whole-dict comparison includes the lists: entry count, order and each set exactly
    assert run_predict(grammar, first_preset, follow_preset) == expected


# ---------------------------------------------------------------------------
# Main tests: E rows, FIRST and FOLLOW computed by Grammar (plan.md §6.2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_predict_pipeline", "E"))
def test_predict_pipeline(grammar, first_preset, follow_preset, expected, run_predict):
    # Same check as test_predict_rules; a failure only here points at how the three methods work together
    assert run_predict(grammar, first_preset, follow_preset) == expected


# ---------------------------------------------------------------------------
# Property tests: shape and contents of predict (plan.md §7.1–§7.2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_predict_shape"))
def test_predict_shape(grammar, first_preset, follow_preset, expected, run_predict):
    predict = run_predict(grammar, first_preset, follow_preset)
    assert set(predict) == set(grammar)
    for A in grammar:
        assert len(predict[A]) == len(grammar[A]), (
            f"predict[{A}] has {len(predict[A])} entries, grammar[{A}] has {len(grammar[A])} productions"
        )
    not_sets = [(A, i, type(entry).__name__) for A, entries in predict.items() for i, entry in enumerate(entries) if not isinstance(entry, set)]
    assert not_sets == [], f"entries that are not sets: {not_sets}"


@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_predict_contents"))
def test_predict_contents(grammar, first_preset, follow_preset, expected, run_predict):
    predict = run_predict(grammar, first_preset, follow_preset)
    # A prediction set holds only terminals and $, never ε or a non-terminal
    offenders = [
        (A, i, sym)
        for A, entries in predict.items()
        for i, entry in enumerate(entries)
        for sym in entry
        if sym == EPS or sym in grammar
    ]
    assert offenders == [], f"ε or non-terminals found as (non-terminal, production index, symbol): {offenders}"


# ---------------------------------------------------------------------------
# Property tests: grammar, FIRST and FOLLOW are read-only (plan.md §7.3)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_inputs_are_read_only"))
def test_inputs_are_read_only(grammar, first_preset, follow_preset, expected, predict_grammar):
    # For E rows the snapshot is taken after FIRST and FOLLOW are computed, so only the prediction call is checked
    g = predict_grammar(grammar, first_preset, follow_preset)
    snapshot = copy.deepcopy((g.grammar, g.first, g.follow))

    g.compute_predict_set()

    assert (g.grammar, g.first, g.follow) == snapshot


# ---------------------------------------------------------------------------
# Property tests: changing predict never reaches FIRST or FOLLOW (plan.md §7.4)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_predict_independent_of_inputs"))
def test_predict_independent_of_inputs(grammar, first_preset, follow_preset, expected, predict_grammar):
    g = predict_grammar(grammar, first_preset, follow_preset)
    g.compute_predict_set()
    snapshot = copy.deepcopy((g.first, g.follow))

    # Checks behavior, not identity: a predict entry sharing an object with an input shows up here
    for entries in g.predict.values():
        for entry in entries:
            entry.add(PROBE)

    leaked_first = sorted(A for A, s in g.first.items() if PROBE in s)
    leaked_follow = sorted(A for A, s in g.follow.items() if PROBE in s)
    assert (g.first, g.follow) == snapshot, f"PROBE reached FIRST of {leaked_first} and FOLLOW of {leaked_follow}"


# ---------------------------------------------------------------------------
# Order independence (plan.md §7.5)
# ---------------------------------------------------------------------------

def _order_params() -> list:
    """One param per declaration order of each PREDICT_CASES grammar, start key always first: all permutations of the rest up to 4 non-terminals, else declared and reversed."""
    params = []
    for case_id, grammar, first_preset, follow_preset, expected in PREDICT_CASES:
        start, *rest = tuple(grammar)
        if len(grammar) <= 4:
            rest_orders = list(itertools.permutations(rest))
        else:
            rest_orders = [tuple(rest), tuple(reversed(rest))]
        for rest_order in rest_orders:
            order = (start, *rest_order)
            param_id = f"{case_id}[{','.join(order)}]"
            marks = []
            key = f"test_predict_is_order_independent::{param_id}"
            if key in KNOWN_FAILURES:
                reason, exception = KNOWN_FAILURES[key]
                marks.append(pytest.mark.xfail(reason=reason, raises=exception, strict=True))
            params.append(pytest.param(grammar, first_preset, follow_preset, order, expected, id=param_id, marks=marks))
    return params


@pytest.mark.parametrize("grammar, first_preset, follow_preset, order, expected", _order_params())
def test_predict_is_order_independent(grammar, first_preset, follow_preset, order, expected, reorder, run_predict):
    # Only the keys move; each non-terminal keeps its productions in order, so expected stays valid
    assert run_predict(reorder(grammar, order), first_preset, follow_preset) == expected


# ---------------------------------------------------------------------------
# Same result on fresh runs (plan.md §7.6)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, first_preset, follow_preset, expected", _case_params("test_predict_same_on_fresh_runs"))
def test_predict_same_on_fresh_runs(grammar, first_preset, follow_preset, expected, predict_grammar):
    # Two objects built from the same inputs; a second call on one object is out of scope (spec §7)
    g_1 = predict_grammar(grammar, first_preset, follow_preset)
    g_2 = predict_grammar(grammar, first_preset, follow_preset)

    g_1.compute_predict_set()
    g_2.compute_predict_set()

    assert g_1.predict == g_2.predict


# ---------------------------------------------------------------------------
# Isolation (plan.md §7.7)
# ---------------------------------------------------------------------------

def _case(case_id: str) -> dict[str, list[list[str]]]:
    """Return the grammar of the PREDICT_CASES row with the given id."""
    return next(grammar for cid, grammar, _, _, _ in PREDICT_CASES if cid == case_id)


def test_input_grammar_untouched():
    # No deep copy here on purpose: the object passed to Grammar is the one checked
    grammar = copy.deepcopy(_case("E1-main-grammar"))
    grammar_before = copy.deepcopy(grammar)

    g = Grammar(grammar)
    g.compute_first_set()
    g.compute_follow_set()
    g.compute_predict_set()

    assert grammar == grammar_before


def test_instances_do_not_share_state(predict_grammar):
    g_e1 = predict_grammar(_case("E1-main-grammar"), None, None)
    g_e2 = predict_grammar(_case("E2-expression-grammar"), None, None)

    g_e1.compute_predict_set()

    assert g_e2.predict == {nt: [] for nt in _case("E2-expression-grammar")}
