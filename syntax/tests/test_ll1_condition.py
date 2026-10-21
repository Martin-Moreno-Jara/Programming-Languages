import copy
import itertools

import pytest

EPS = "ε"
END = "$"

# Every test in this file fails instead of hanging if Grammar.check_LL1_condition never returns (spec §6)
pytestmark = pytest.mark.timeout(2)

# "<test function>::<param id>" -> (reason, expected exception type); filled in by the xfail workflow (tasks.md §12)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}

# (case_id, grammar, predict_preset, expected) rows from plan.md §5. L and N rows give the
# prediction sets by hand (grammar is None, conftest builds a placeholder); E rows give a
# real grammar (predict_preset is None) that runs the full pipeline, start symbol first.
# Plain tuples so the property and order tests can reuse them.
LL1_CASES: list[
    tuple[
        str,
        dict[str, list[list[str]]] | None,
        dict[str, list[set[str]]] | None,
        bool,
    ]
] = [
    # L rows: LL(1), hand-written prediction sets (plan.md §5.1)
    ("L1-single-production", None, {"S": [{"a"}]}, True),
    ("L2-two-disjoint", None, {"S": [{"a"}, {"b"}]}, True),
    ("L3-many-disjoint-with-end", None, {"S": [{"c"}, {"a"}, {"b"}, {END}]}, True),
    ("L4-multi-token-sets", None, {"S": [{"a", "b", "c"}, {"d", "e"}]}, True),
    ("L5-same-token-other-nt", None, {"S": [{"a"}], "A": [{"a"}, {"b"}]}, True),
    ("L6-empty-set", None, {"S": [{"a"}], "U": [{"u"}, set()]}, True),
    ("L7-two-empty-sets", None, {"S": [{"a"}], "U": [set(), set()]}, True),
    ("L8-whole-string-tokens", None, {"S": [{"="}, {"=="}], "T": [{"end"}, {"End"}]}, True),
    (
        "L9-lua-like",
        None,
        {
            "Chunk": [{"if", "Name", END}],
            "Block": [{"if", "Name"}, {END, "end"}],
            "Stat": [{"if"}, {"Name"}],
            "Exp": [{"Name"}, {"Number"}],
        },
        True,
    ),
    # N rows: not LL(1), hand-written prediction sets (plan.md §5.2)
    ("N1-identical", None, {"S": [{"a"}, {"a"}]}, False),
    ("N2-partial-overlap", None, {"S": [{"a", "b"}, {"b", "c"}]}, False),
    ("N3-subset", None, {"S": [{"a"}, {"a", "b"}]}, False),
    ("N4-only-end", None, {"A": [{END}, {"a", END}]}, False),
    ("N5-first-and-third", None, {"S": [{"a"}, {"b"}, {"a"}]}, False),
    ("N6-second-and-third", None, {"S": [{"a"}, {"b"}, {"b", "c"}]}, False),
    ("N7-conflict-in-last-nt", None, {"S": [{"x"}], "A": [{"a"}, {"b"}], "B": [{"c"}, {"c"}]}, False),
    ("N8-conflict-in-first-nt", None, {"S": [{"x"}, {"x"}], "A": [{"a"}, {"b"}]}, False),
    ("N9-several-conflicts", None, {"S": [{"a"}, {"a"}], "A": [{"b"}, {"b"}]}, False),
    ("N10-empty-does-not-hide", None, {"U": [set(), {"a"}, {"a"}]}, False),
    # E rows: full pipeline, copied from the spec 003 tables (plan.md §5.3)
    (
        "E1-expression-grammar",
        {
            "E": [["T", "E'"]],
            "E'": [["+", "T", "E'"], [EPS]],
            "T": [["F", "T'"]],
            "T'": [["*", "F", "T'"], [EPS]],
            "F": [["(", "E", ")"], ["id"]],
        },
        None,
        True,
    ),
    (
        "E2-lua-like-pipeline",
        {
            "Chunk": [["Block"]],
            "Block": [["Stat", "Block"], [EPS]],
            "Stat": [["if", "Exp", "then", "Block", "end"], ["Name", "=", "Exp"]],
            "Exp": [["Name"], ["Number"]],
        },
        None,
        True,
    ),
    (
        "E3-main-grammar",
        {
            "A": [["B", "C"], ["ant", "A", "all"]],
            "B": [["big", "C"], ["bus", "A", "boss"], [EPS]],
            "C": [["cat"], ["cow"]],
        },
        None,
        True,
    ),
    (
        "E4-nullable-no-conflict",
        {"S": [["A", "B", "C"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]], "C": [["c"]]},
        None,
        True,
    ),
    ("E5-left-recursion", {"E": [["E", "+", "T"], ["T"]], "T": [["id"]]}, None, False),
    ("E6-common-prefix", {"S": [["a", "b"], ["a", "c"]]}, None, False),
    ("E7-epsilon-conflict", {"S": [["A", "a"]], "A": [["a"], [EPS]]}, None, False),
    (
        "E8-dangling-else",
        {"S": [["i", "E", "t", "S", "S'"], ["a"]], "S'": [["e", "S"], [EPS]], "E": [["b"]]},
        None,
        False,
    ),
]


def _case_params(test_name: str, kind: str | None = None) -> list:
    """Turn LL1_CASES into pytest params of (grammar, predict_preset, expected); kind "L", "N" or "E" keeps only those rows."""
    params = []
    for case_id, grammar, predict_preset, expected in LL1_CASES:
        if kind is not None and not case_id.startswith(kind):
            continue
        marks = []
        key = f"{test_name}::{case_id}"
        if key in KNOWN_FAILURES:
            reason, exception = KNOWN_FAILURES[key]
            marks.append(pytest.mark.xfail(reason=reason, raises=exception, strict=True))
        params.append(pytest.param(grammar, predict_preset, expected, id=case_id, marks=marks))
    return params


def _build(grammar, predict_preset, ll1_grammar, predict_grammar):
    """Build the Grammar for one row: hand-written sets for L/N rows, the full pipeline for E rows."""
    if predict_preset is not None:
        return ll1_grammar(predict_preset)
    g = predict_grammar(grammar, None, None)
    g.compute_predict_set()
    return g


def _pairwise_ll1(predict: dict[str, list[set[str]]]) -> bool:
    """Reference LL(1) check (spec §3): compares every pair of sets of each non-terminal directly."""
    return all(a.isdisjoint(b) for sets in predict.values() for a, b in itertools.combinations(sets, 2))


# ---------------------------------------------------------------------------
# Main tests: L rows, LL(1) grammars (plan.md §6.1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, predict_preset, expected", _case_params("test_ll1_accepts", "L"))
def test_ll1_accepts(grammar, predict_preset, expected, ll1_grammar, predict_grammar):
    # `is True` instead of `== True`: a truthy non-bool result fails here too
    g = _build(grammar, predict_preset, ll1_grammar, predict_grammar)
    assert g.check_LL1_condition() is True


# ---------------------------------------------------------------------------
# Main tests: N rows, non-LL(1) grammars (plan.md §6.2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, predict_preset, expected", _case_params("test_ll1_rejects", "N"))
def test_ll1_rejects(grammar, predict_preset, expected, ll1_grammar, predict_grammar):
    # `is False` instead of `== False`: a falsy non-bool result (None, 0, set()) fails here too
    g = _build(grammar, predict_preset, ll1_grammar, predict_grammar)
    assert g.check_LL1_condition() is False


# ---------------------------------------------------------------------------
# Main tests: E rows, full pipeline (plan.md §6.3)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, predict_preset, expected", _case_params("test_ll1_pipeline", "E"))
def test_ll1_pipeline(grammar, predict_preset, expected, ll1_grammar, predict_grammar):
    # _build runs FIRST, FOLLOW and predict; a failure only here points at how the steps connect
    g = _build(grammar, predict_preset, ll1_grammar, predict_grammar)
    assert g.check_LL1_condition() is expected


# ---------------------------------------------------------------------------
# Property tests: real bool, read-only, repeatable (plan.md §7.1–§7.3)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, predict_preset, expected", _case_params("test_result_is_bool"))
def test_result_is_bool(grammar, predict_preset, expected, ll1_grammar, predict_grammar):
    # expected is unused: the answer itself is checked by the main tests
    result = _build(grammar, predict_preset, ll1_grammar, predict_grammar).check_LL1_condition()
    assert type(result) is bool, f"returned {type(result).__name__}: {result!r}"


@pytest.mark.parametrize("grammar, predict_preset, expected", _case_params("test_check_is_read_only"))
def test_check_is_read_only(grammar, predict_preset, expected, ll1_grammar, predict_grammar):
    # For E rows the snapshot is taken after the pipeline, so only the check is tested
    g = _build(grammar, predict_preset, ll1_grammar, predict_grammar)
    snapshot = copy.deepcopy((g.grammar, g.first, g.follow, g.predict))

    g.check_LL1_condition()

    assert (g.grammar, g.first, g.follow, g.predict) == snapshot


@pytest.mark.parametrize("grammar, predict_preset, expected", _case_params("test_check_is_repeatable"))
def test_check_is_repeatable(grammar, predict_preset, expected, ll1_grammar, predict_grammar):
    g = _build(grammar, predict_preset, ll1_grammar, predict_grammar)
    assert g.check_LL1_condition() == g.check_LL1_condition()


# ---------------------------------------------------------------------------
# Property tests: matches the pairwise definition (plan.md §7.4)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grammar, predict_preset, expected", _case_params("test_matches_pairwise_reference"))
def test_matches_pairwise_reference(grammar, predict_preset, expected, ll1_grammar, predict_grammar):
    g = _build(grammar, predict_preset, ll1_grammar, predict_grammar)
    reference = _pairwise_ll1(g.predict)
    # Two messages so a mistake in the table is told apart from a bug in the check
    assert reference is expected, f"table value {expected} disagrees with the definition ({reference})"
    assert g.check_LL1_condition() is reference, f"check disagrees with the pairwise reference ({reference})"


# ---------------------------------------------------------------------------
# Order of non-terminals (plan.md §7.5)
# ---------------------------------------------------------------------------

def _order_params() -> list:
    """One param per key order of each LL1_CASES row: L/N rows permute all keys; E rows keep the start key first and permute the rest up to 4 non-terminals, else declared and reversed."""
    params = []
    for case_id, grammar, predict_preset, expected in LL1_CASES:
        if predict_preset is not None:
            # No start symbol on hand-written rows, so the first key can move too
            orders = list(itertools.permutations(predict_preset))
        else:
            start, *rest = tuple(grammar)
            if len(grammar) <= 4:
                rest_orders = list(itertools.permutations(rest))
            else:
                rest_orders = [tuple(rest), tuple(reversed(rest))]
            orders = [(start, *rest_order) for rest_order in rest_orders]
        for order in orders:
            param_id = f"{case_id}[{','.join(order)}]"
            marks = []
            key = f"test_nonterminal_order_independent::{param_id}"
            if key in KNOWN_FAILURES:
                reason, exception = KNOWN_FAILURES[key]
                marks.append(pytest.mark.xfail(reason=reason, raises=exception, strict=True))
            params.append(pytest.param(grammar, predict_preset, order, expected, id=param_id, marks=marks))
    return params


@pytest.mark.parametrize("grammar, predict_preset, order, expected", _order_params())
def test_nonterminal_order_independent(grammar, predict_preset, order, expected, reorder, ll1_grammar, predict_grammar):
    if predict_preset is not None:
        g = ll1_grammar(reorder(predict_preset, order))
    else:
        g = _build(reorder(grammar, order), None, ll1_grammar, predict_grammar)
    assert g.check_LL1_condition() is expected


# ---------------------------------------------------------------------------
# Order of productions (plan.md §7.6)
# ---------------------------------------------------------------------------

# variant name -> how it reorders one list of prediction sets (L/N) or productions (E)
PRODUCTION_ORDERS = {
    "reversed": lambda x: list(reversed(x)),
    "rotated": lambda x: x[1:] + x[:1],
}


def _production_order_params() -> list:
    """Two params per LL1_CASES row, one per PRODUCTION_ORDERS variant."""
    params = []
    for case_id, grammar, predict_preset, expected in LL1_CASES:
        for variant in PRODUCTION_ORDERS:
            param_id = f"{case_id}[{variant}]"
            marks = []
            key = f"test_production_order_independent::{param_id}"
            if key in KNOWN_FAILURES:
                reason, exception = KNOWN_FAILURES[key]
                marks.append(pytest.mark.xfail(reason=reason, raises=exception, strict=True))
            params.append(pytest.param(grammar, predict_preset, variant, expected, id=param_id, marks=marks))
    return params


@pytest.mark.parametrize("grammar, predict_preset, variant, expected", _production_order_params())
def test_production_order_independent(grammar, predict_preset, variant, expected, ll1_grammar, predict_grammar):
    # Only the lists inside each non-terminal move; the key order (and so the start symbol) stays
    reorder_list = PRODUCTION_ORDERS[variant]
    if predict_preset is not None:
        g = ll1_grammar({A: reorder_list(sets) for A, sets in predict_preset.items()})
    else:
        g = _build({A: reorder_list(prods) for A, prods in grammar.items()}, None, ll1_grammar, predict_grammar)
    assert g.check_LL1_condition() is expected


# ---------------------------------------------------------------------------
# Isolation (plan.md §7.7)
# ---------------------------------------------------------------------------

def _preset(case_id: str) -> dict[str, list[set[str]]]:
    """Return the predict_preset of the LL1_CASES row with the given id."""
    return next(preset for cid, _, preset, _ in LL1_CASES if cid == case_id)


def test_instances_do_not_share_state(ll1_grammar):
    g_n1 = ll1_grammar(_preset("N1-identical"))
    g_l2 = ll1_grammar(_preset("L2-two-disjoint"))
    l2_before = copy.deepcopy(g_l2.predict)

    g_n1.check_LL1_condition()

    assert g_l2.check_LL1_condition() is True
    assert g_l2.predict == l2_before
