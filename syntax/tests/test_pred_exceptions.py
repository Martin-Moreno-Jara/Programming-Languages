import copy

import pytest

from grammar import Grammar

pytestmark = pytest.mark.timeout(5)

EPS = "ε"

# The "dangling else" of spec 004 E8: Sp → ε predicts {e, $}, which collides with Sp → e S
DANGLING_ELSE = {
    "S": [["i", "E", "t", "S", "Sp"], ["a"]],
    "Sp": [["e", "S"], [EPS]],
    "E": [["b"]],
}
# Removing e from the ε production resolves it the greedy way, binding else to the nearest if
GREEDY_ELSE = {"Sp": {1: "e"}}


def _processed(grammar, exceptions=None, set_them=True) -> Grammar:
    g = Grammar(copy.deepcopy(grammar))
    if set_them:
        g.set_pred_exceptions(exceptions)
    g.process_grammar()
    return g


def _plain_predict(grammar) -> dict[str, list[set[str]]]:
    """Prediction sets computed step by step, without any exception."""
    g = Grammar(copy.deepcopy(grammar))
    g.compute_first_set()
    g.compute_follow_set()
    g.compute_predict_set()
    return g.predict


# ---------------------------------------------------------------------------
# set_pred_exceptions
# ---------------------------------------------------------------------------
def test_set_pred_exceptions_stores_mapping():
    g = Grammar(copy.deepcopy(DANGLING_ELSE))
    g.set_pred_exceptions(GREEDY_ELSE)
    assert g.pred_exceptions == GREEDY_ELSE


def test_set_pred_exceptions_computes_nothing():
    g = Grammar(copy.deepcopy(DANGLING_ELSE))
    g.set_pred_exceptions(GREEDY_ELSE)
    assert all(sets == [] for sets in g.predict.values())


# ---------------------------------------------------------------------------
# apply_pred_exceptions through process_grammar
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "exceptions, set_them",
    [pytest.param(None, False, id="never-set"), pytest.param(None, True, id="none"), pytest.param({}, True, id="empty")],
)
def test_no_exceptions_gives_plain_predict(exceptions, set_them):
    assert _processed(DANGLING_ELSE, exceptions, set_them).predict == _plain_predict(DANGLING_ELSE)


def test_exception_removes_token_from_its_set():
    g = _processed(DANGLING_ELSE, GREEDY_ELSE)
    assert g.predict["Sp"] == [{"e"}, {"$"}]


def test_exception_resolves_conflict():
    assert _processed(DANGLING_ELSE).check_LL1_condition() is False
    assert _processed(DANGLING_ELSE, GREEDY_ELSE).check_LL1_condition() is True


def test_exception_touches_nothing_else():
    plain = Grammar(copy.deepcopy(DANGLING_ELSE))
    plain.process_grammar()
    g = _processed(DANGLING_ELSE, GREEDY_ELSE)
    assert g.first == plain.first
    assert g.follow == plain.follow
    assert {A: s for A, s in g.predict.items() if A != "Sp"} == {A: s for A, s in plain.predict.items() if A != "Sp"}
    assert g.grammar == DANGLING_ELSE


def test_exceptions_mapping_not_modified():
    exceptions = copy.deepcopy(GREEDY_ELSE)
    _processed(DANGLING_ELSE, exceptions)
    assert exceptions == GREEDY_ELSE


def test_several_non_terminals():
    grammar = {
        "S": [["A", "B"]],
        "A": [["x", "A"], [EPS]],
        "B": [["x"], ["y", "B"], [EPS]],
    }
    # A → ε predicts FOLLOW(A) = {x, y, $}; B → ε predicts {$}
    g = _processed(grammar, {"A": {1: "x"}, "B": {2: "$"}})
    assert g.predict["A"] == [{"x"}, {"y", "$"}]
    assert g.predict["B"] == [{"x"}, {"y"}, set()]


def test_apply_twice_is_idempotent():
    g = _processed(DANGLING_ELSE, GREEDY_ELSE)
    once = copy.deepcopy(g.predict)
    g.apply_pred_exceptions()
    assert g.predict == once


def test_apply_after_compute_predict_set():
    g = Grammar(copy.deepcopy(DANGLING_ELSE))
    g.set_pred_exceptions(GREEDY_ELSE)
    g.compute_first_set()
    g.compute_follow_set()
    g.compute_predict_set()
    g.apply_pred_exceptions()
    assert g.predict == _processed(DANGLING_ELSE, GREEDY_ELSE).predict
