"""Helpers shared by the test_real_grammar_* files (spec 006, tasks §1 and §2)."""
import copy
import importlib.util
import re
import sys

import pytest

import syntax  # noqa: F401  (the generated parser is loaded as a submodule of this package)
from lexer.lexer import Lexer, Token
from syntax.code_generator_script import ASDR_generator
from syntax.grammar import Grammar

EPS = "ε"
END = "$"
PARSER_MODULE = "syntax._real_grammar_parser"


def params(test_name: str, rows: list[tuple], known: dict[str, tuple[str, type[BaseException]]]) -> list:
    """Turn (case_id, *values) rows into pytest.params, adding the xfail mark of known."""
    ids = [row[0] for row in rows]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"{test_name}: duplicated row ids {duplicates}")
    result = []
    for case_id, *values in rows:
        marks = []
        if f"{test_name}::{case_id}" in known:
            reason, exc = known[f"{test_name}::{case_id}"]
            marks.append(pytest.mark.xfail(reason=reason, raises=exc, strict=True))
        result.append(pytest.param(*values, id=case_id, marks=marks))
    return result


# ---------------------------------------------------------------------------
# Grammar and parser (tasks §2.1)
# ---------------------------------------------------------------------------
def lua_grammar() -> dict[str, list[list[str]]]:
    """A private copy of final_grammar from main.py."""
    from main import final_grammar

    return copy.deepcopy(final_grammar)


def lua_pred_exceptions() -> dict[str, dict[int, str]]:
    """A private copy of pred_exceptions from main.py: the tokens removed by hand from prediction sets."""
    from main import pred_exceptions

    return copy.deepcopy(pred_exceptions)


def processed_grammar(with_exceptions: bool = True) -> Grammar:
    """final_grammar processed as main.py does it; with_exceptions=False gives the raw prediction sets."""
    g = Grammar(lua_grammar())
    if with_exceptions:
        g.set_pred_exceptions(lua_pred_exceptions())
    g.process_grammar()
    return g


def generate_parser(folder) -> tuple[Grammar, type] | None:
    """Generate the parser into folder (a syntax/ directory) and load it; None if the grammar is not LL(1)."""
    g = processed_grammar()
    if not g.check_LL1_condition():
        return None
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(folder.parent)
        ASDR_generator(g).generate()
    spec = importlib.util.spec_from_file_location(PARSER_MODULE, folder / "ASDR.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[PARSER_MODULE] = module
    spec.loader.exec_module(module)
    return g, module.ASDR


def traced_parser(ASDR: type, g: Grammar, record: set[tuple[str, int]]) -> type:
    """A subclass of ASDR whose parse_A methods record (A, index of the production chosen) on entry."""
    attrs = {}
    for A in g.grammar:
        original = getattr(ASDR, f"parse_{A}")

        def wrapper(self, A=A, original=original):
            for i, predict in enumerate(g.predict[A]):
                if self.cur_tok.type in predict:
                    record.add((A, i))
                    break
            return original(self)

        attrs[f"parse_{A}"] = wrapper
    return type("TracedASDR", (ASDR,), attrs)


# ---------------------------------------------------------------------------
# Lexing and parsing (tasks §2.2)
# ---------------------------------------------------------------------------
def lex(source: str) -> list[Token]:
    """All tokens of source, ending with $. A lexical error fails the test, since it is a bug in the case."""
    lexer = Lexer(source)
    tokens = []
    try:
        while True:
            tokens.append(lexer.tokenize())
            if tokens[-1].type == END:
                return tokens
    except SystemExit:
        pytest.fail(f"lexical error in test source {source!r}")


def parse(ASDR: type, source: str, lexer=None) -> None:
    """Run the parser on source; SyntacticalError escapes."""
    try:
        ASDR(lexer or Lexer(source)).main()
    except SystemExit:
        pytest.fail(f"lexical error in test source {source!r}")


class CountingLexer(Lexer):
    """A real lexer that counts how many times it returned $."""

    def __init__(self, data: str):
        super().__init__(data)
        self.ends = 0

    def tokenize(self) -> Token:
        token = super().tokenize()
        if token.type == END:
            self.ends += 1
        return token


# ---------------------------------------------------------------------------
# Reading error messages (tasks §2.4)
# ---------------------------------------------------------------------------
# The only place that knows the layout required by the assignment doc
ERROR_RE = re.compile(r'^<(\d+):(\d+)> Error sintactico: se encontro: "(.*)"; se esperaba: (.*)\.$', re.S)
# An item ends at a quote followed by ", " and another quote, or at the end; this keeps "," and ".." whole
_ITEM_RE = re.compile(r'"(.*?)"(?=, "|$)')


def error_parts(message: str) -> tuple[int, int, str, list[str]]:
    """Split an error message into (line, col, lexeme, expected items in order)."""
    m = ERROR_RE.match(message)
    if not m:
        pytest.fail(f"error message doesn't follow the doc layout: {message!r}")
    return int(m.group(1)), int(m.group(2)), m.group(3), _ITEM_RE.findall(m.group(4))


def _build_display() -> dict[str, str]:
    lexer = Lexer("")
    display = {token_type: symbol for symbol, token_type in lexer.operand_symbols_dict.items()}
    display.update({keyword: keyword for keyword in lexer.keywords_set})
    display.update(
        {"id": "id", "tkn_num": "valor_numerico", "tkn_str": "cadena_de_caracteres", END: "final de archivo"}
    )
    return display


# How each token type is shown in the expected list (spec §3.2)
DISPLAY: dict[str, str] = _build_display()
SHOWN_TO_TYPE: dict[str, str] = {shown: token_type for token_type, shown in DISPLAY.items()}
# The grader sorts by token type, except numbers and strings, which sort by their shown name (platform tests 13, 14)
SORT_AS: dict[str, str] = {"tkn_num": "valor_numerico", "tkn_str": "cadena_de_caracteres"}


def is_doc_order(shown: list[str]) -> bool:
    """True when the items, mapped back to token types, are strictly increasing in the grader's order."""
    if any(item not in SHOWN_TO_TYPE for item in shown):
        return False
    keys = [SORT_AS.get(t, t) for t in (SHOWN_TO_TYPE[item] for item in shown)]
    return all(a < b for a, b in zip(keys, keys[1:]))
