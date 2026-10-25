import itertools

import pytest

from real_grammar_cases import ACCEPT_ROWS, PRODUCTION_ROWS, REJECT_ROWS
from real_grammar_support import (
    DISPLAY,
    EPS,
    lex,
    lua_grammar,
    params,
    parse,
    processed_grammar,
    traced_parser,
)
from exceptions.custom_exceptions import SyntacticalError

pytestmark = pytest.mark.timeout(10)

# "<test function>::<param id>" -> (reason, expected exception type); filled in by the xfail workflow (tasks.md §10)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}


def _symbols(grammar: dict[str, list[list[str]]]) -> list[tuple[str, str]]:
    """(non-terminal, symbol) for every symbol on every right side."""
    return [(A, symbol) for A, productions in grammar.items() for production in productions for symbol in production]


# ---------------------------------------------------------------------------
# Grammar properties (spec §4)
# ---------------------------------------------------------------------------
@pytest.mark.xfail(reason="P1 grammar not LL(1)", raises=AssertionError, strict=True)
def test_P1_grammar_is_ll1():
    g = processed_grammar()
    conflicts = [
        f"{A}: productions {i} and {j} share {sorted(a & b)}"
        for A, sets in g.predict.items()
        for (i, a), (j, b) in itertools.combinations(enumerate(sets), 2)
        if a & b
    ]
    assert g.check_LL1_condition() is True, "\n".join(conflicts)


def test_P2_all_nonterminals_reachable():
    grammar = lua_grammar()
    reached, pending = {"CHUNK"}, ["CHUNK"]
    while pending:
        for production in grammar[pending.pop()]:
            for symbol in production:
                if symbol in grammar and symbol not in reached:
                    reached.add(symbol)
                    pending.append(symbol)
    assert set(grammar) - reached == set(), "unreachable from CHUNK"


def test_P3_no_undefined_or_empty():
    grammar = lua_grammar()
    # Every lexer token type is lowercase, so a symbol with uppercase letters is meant to be a non-terminal
    undefined = sorted({(A, s) for A, s in _symbols(grammar) if s != s.lower() and s not in grammar})
    assert undefined == [], f"non-terminals used but never defined: {undefined}"
    assert [A for A, productions in grammar.items() if not productions] == []
    assert [A for A, productions in grammar.items() if [] in productions] == []


def test_P4_all_nonterminals_productive():
    grammar = lua_grammar()
    productive: set[str] = set()
    changed = True
    while changed:
        changed = False
        for A, productions in grammar.items():
            if A not in productive and any(
                all(s not in grammar or s in productive for s in production) for production in productions
            ):
                productive.add(A)
                changed = True
    assert set(grammar) - productive == set(), "non-terminals that never derive a string of tokens"


def test_P5_terminals_are_lexer_tokens():
    grammar = lua_grammar()
    bad = sorted({(A, s) for A, s in _symbols(grammar) if s not in grammar and s != EPS and s not in DISPLAY})
    assert bad == [], f"terminals the lexer never produces: {bad}"


def test_P6_chunk_is_start_symbol():
    assert next(iter(lua_grammar())) == "CHUNK"
    assert processed_grammar().get_initial_symbol() == "CHUNK"


def test_P7_every_production_is_covered(lua_parser):
    g, ASDR = lua_parser
    used: set[tuple[str, int]] = set()
    Traced = traced_parser(ASDR, g, used)
    for _, source in PRODUCTION_ROWS:
        try:
            parse(Traced, source)
        except SyntacticalError:
            pass  # reported by its own row in test_accepts
    missing = [
        f"{A} → {' '.join(production)}"
        for A, productions in g.grammar.items()
        for i, production in enumerate(productions)
        if (A, i) not in used
    ]
    assert missing == [], "productions no accept case uses:\n" + "\n".join(missing)


# ---------------------------------------------------------------------------
# The cases themselves (tasks §6)
# ---------------------------------------------------------------------------
_SOURCE_ROWS = [(row[0], row[1]) for row in ACCEPT_ROWS + REJECT_ROWS]


@pytest.mark.parametrize("source", params("test_case_sources_lex_cleanly", _SOURCE_ROWS, KNOWN_FAILURES))
def test_case_sources_lex_cleanly(source):
    assert lex(source)[-1].type == "$"


_POSITION_ROWS = [(case_id, source, pos, lexeme) for case_id, source, pos, lexeme, _, _ in REJECT_ROWS if pos]


@pytest.mark.parametrize(
    "source, position, lexeme", params("test_reject_positions_match_lexer", _POSITION_ROWS, KNOWN_FAILURES)
)
def test_reject_positions_match_lexer(source, position, lexeme):
    at = [t for t in lex(source) if (t.line, t.col) == position]
    assert at and at[0].lexeme == lexeme, [(t.type, t.lexeme, t.line, t.col) for t in lex(source)]


@pytest.mark.xfail(reason="print not produced as its own token", raises=AssertionError, strict=True)
def test_display_is_consistent():
    shown = list(DISPLAY.values())
    assert len(shown) == len(set(shown)), "two token types are shown the same way"
    missing = [name for name in ("print", "pcall", "xpcall", "error", "warn") if name not in DISPLAY]
    assert missing == [], f"built-ins the lexer doesn't produce as their own token: {missing}"
