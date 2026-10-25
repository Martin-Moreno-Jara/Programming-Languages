import pytest

from exceptions.custom_exceptions import SyntacticalError
from real_grammar_cases import ACCEPT_ROWS, FIRST_ERROR_ROWS, LAYOUT_ROWS, REJECT_ROWS, STRUCTURE_ROWS
from real_grammar_support import CountingLexer, error_parts, is_doc_order, params, parse

pytestmark = pytest.mark.timeout(10)

# "<test function>::<param id>" -> (reason, expected exception type); filled in by the xfail workflow (tasks.md §10)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}


# ---------------------------------------------------------------------------
# Accept (spec §5, §6)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("source", params("test_accepts", ACCEPT_ROWS, KNOWN_FAILURES))
def test_accepts(lua_parser, source):
    _, ASDR = lua_parser
    try:
        parse(ASDR, source)
    except SyntacticalError as e:
        pytest.fail(f"rejected {source!r}: {e.message}")


@pytest.mark.parametrize("source", params("test_parser_reads_to_end", STRUCTURE_ROWS + LAYOUT_ROWS, KNOWN_FAILURES))
def test_parser_reads_to_end(lua_parser, source):
    _, ASDR = lua_parser
    lexer = CountingLexer(source)
    parse(ASDR, source, lexer)
    assert lexer.ends >= 1, "the parser returned before reading $"


# ---------------------------------------------------------------------------
# Reject (spec §7)
# ---------------------------------------------------------------------------
def _reject(ASDR, source: str) -> tuple[int, int, str, list[str]]:
    with pytest.raises(SyntacticalError) as err:
        parse(ASDR, source)
    return error_parts(err.value.message)


@pytest.mark.parametrize(
    "source, position, lexeme, contains, exact", params("test_rejects", REJECT_ROWS, KNOWN_FAILURES)
)
def test_rejects(lua_parser, source, position, lexeme, contains, exact):
    _, ASDR = lua_parser
    line, col, found, shown = _reject(ASDR, source)
    assert found == lexeme
    if position is not None:
        assert (line, col) == position
    assert contains <= set(shown), f"missing {sorted(contains - set(shown))} in {shown}"
    if exact is not None:
        assert shown == exact


_ORDER_ROWS = [(case_id, source) for case_id, source, *_ in REJECT_ROWS]


@pytest.mark.parametrize("source", params("test_reject_expected_list_order", _ORDER_ROWS, KNOWN_FAILURES))
def test_reject_expected_list_order(lua_parser, source):
    _, ASDR = lua_parser
    *_, shown = _reject(ASDR, source)
    assert shown and is_doc_order(shown), shown


@pytest.mark.parametrize("source, position", params("test_reports_only_first_error", FIRST_ERROR_ROWS, KNOWN_FAILURES))
def test_reports_only_first_error(lua_parser, source, position):
    _, ASDR = lua_parser
    with pytest.raises(SyntacticalError) as err:
        parse(ASDR, source)
    assert err.value.message.startswith(f"<{position[0]}:{position[1]}>"), err.value.message
