import ast
import copy
import importlib.util
import itertools
import re
import sys

import pytest

import syntax  # noqa: F401  (the generated parser is loaded as a submodule of this package)
from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer, Token
from syntax.ASDR_base import ASDR_base
from syntax.code_generator_script import ASDR_generator
from syntax.grammar import Grammar

EPS = "ε"
END = "$"
EOF_SHOWN = "final de archivo"

# Every test in this file fails instead of hanging if the generator or the generated parser never returns (spec §7)
pytestmark = pytest.mark.timeout(5)

# "<test function>::<param id>" -> (reason, expected exception type); filled in by the xfail workflow (tasks.md §11)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}


def _params(test_name: str, rows: list[tuple]) -> list:
    """Turn (case_id, *values) rows into pytest.params, adding the xfail mark of KNOWN_FAILURES."""
    params = []
    for case_id, *values in rows:
        marks = []
        if f"{test_name}::{case_id}" in KNOWN_FAILURES:
            reason, exc = KNOWN_FAILURES[f"{test_name}::{case_id}"]
            marks.append(pytest.mark.xfail(reason=reason, raises=exc, strict=True))
        params.append(pytest.param(*values, id=case_id, marks=marks))
    return params


# ---------------------------------------------------------------------------
# Fixtures and helpers (tasks.md §2)
# ---------------------------------------------------------------------------
_module_ids = itertools.count()


@pytest.fixture
def out_dir(tmp_path, monkeypatch):
    """A temporary syntax/ folder, with the working directory moved so ./syntax/ASDR.py lands in it."""
    folder = tmp_path / "syntax"
    folder.mkdir()
    monkeypatch.chdir(tmp_path)
    return folder


@pytest.fixture
def load_parser(monkeypatch):
    """Return a function that imports a generated file and returns its ASDR class."""

    def load(path):
        # A syntax.* name makes `from .ASDR_base import ASDR_base` resolve to the real file,
        # and a unique one never replaces the real syntax.ASDR module
        name = f"syntax._generated_{next(_module_ids)}"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        return module.ASDR

    return load


class FakeLexer:
    """Lexer stand-in: one token per type on line 1, one column apart, then $ forever."""

    def __init__(self, types: list[str]):
        self.tokens = [Token(t, t, 1, i + 1) for i, t in enumerate(types)]
        self.end = Token(END, END, 1, len(types) + 1)
        self.reached_end = False

    def tokenize(self) -> Token:
        if self.tokens:
            return self.tokens.pop(0)
        self.reached_end = True
        return self.end


def _processed(grammar: dict[str, list[list[str]]], exceptions: dict | None = None) -> Grammar:
    """Build a Grammar on a private copy and compute its FIRST, FOLLOW and prediction sets."""
    g = Grammar(copy.deepcopy(grammar))
    if exceptions:
        g.set_pred_exceptions(copy.deepcopy(exceptions))
    g.process_grammar()
    return g


def _generate(
    grammar: dict[str, list[list[str]]], out_dir, exceptions: dict | None = None, hidden: dict | None = None
) -> tuple[Grammar, str]:
    """Generate the parser for grammar into out_dir; return the Grammar and the generated source."""
    g = _processed(grammar, exceptions)
    ASDR_generator(g, hidden).generate()
    return g, (out_dir / "ASDR.py").read_text()


def _run(grammar: dict[str, list[list[str]]], lexer, out_dir, load_parser, hidden: dict | None = None) -> None:
    """Generate, load and run the parser on lexer; SyntacticalError escapes."""
    _generate(grammar, out_dir, hidden=hidden)
    ASDR = load_parser(out_dir / "ASDR.py")
    ASDR(lexer).main()


# The only place that knows the layout of ASDR_base.format_error_message
_ERROR_RE = re.compile(r'^<(\d+):(\d+)> .*se encontro: "(.*)"; se esperaba: (.*)\.$', re.S)


def _error_parts(message: str) -> tuple[int, int, str, set[str]]:
    """Split an error message into (line, col, lexeme, expected tokens)."""
    m = _ERROR_RE.match(message)
    assert m, f"unexpected error message layout: {message!r}"
    return int(m.group(1)), int(m.group(2)), m.group(3), _expected_tokens(m.group(4))


def _expected_tokens(text: str) -> set[str]:
    """Read the expected-tokens text back: `"a", "b"` or a bare `a`."""
    tokens = set()
    for item in text.split(", "):
        if len(item) >= 2 and item.startswith('"') and item.endswith('"'):
            item = item[1:-1]
        tokens.add(item)
    return tokens


# Lexer symbol table, reversed: token type -> the symbol a Lua programmer sees
_SYMBOLS = {token_type: symbol for symbol, token_type in Lexer("").operand_symbols_dict.items()}


def _class_def(source: str) -> ast.ClassDef:
    return next(
        node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == "ASDR"
    )


def _methods(class_def: ast.ClassDef) -> dict[str, ast.FunctionDef]:
    return {node.name: node for node in class_def.body if isinstance(node, ast.FunctionDef)}


def _describe(stmt: ast.stmt) -> tuple:
    """Describe a branch statement: ("call", X), ("match", t), ("pass",), or ("other", code)."""
    if isinstance(stmt, ast.Pass):
        return ("pass",)
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        func = stmt.value.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "self":
            if func.attr == "match" and len(stmt.value.args) == 1:
                return ("match", stmt.value.args[0].value)
            if func.attr.startswith("parse_") and not stmt.value.args:
                return ("call", func.attr.removeprefix("parse_"))
    return ("other", ast.unparse(stmt))


def _branches(func: ast.FunctionDef) -> tuple[list[tuple[list[str], list[tuple]]], list[ast.stmt]]:
    """Walk the if/elif chain of a parse_A method; return ([(tokens, body)], else_body)."""
    branches = []
    node = func.body[0]
    while True:
        assert isinstance(node, ast.If), f"{func.name}: expected an if/elif, got {ast.unparse(node)}"
        compare = node.test
        assert ast.unparse(compare.left) == "self.cur_tok.type" and isinstance(compare.ops[0], ast.In)
        tokens = [elt.value for elt in compare.comparators[0].elts]
        branches.append((tokens, [_describe(stmt) for stmt in node.body]))
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            node = node.orelse[0]
        else:
            return branches, node.orelse


def _expected_body(production: list[str], non_terminals: set[str]) -> list[tuple]:
    return [
        ("pass",) if s == EPS else ("call", s) if s in non_terminals else ("match", s)
        for s in production
    ]


def _single_nullable(g: Grammar, productions: list[list[str]]) -> bool:
    """True when A has one production and it derives ε: parse_A then calls its symbols with no if."""
    return len(productions) == 1 and EPS in g.first_of_sequence(productions[0])


def _is_nullable(g: Grammar, productions: list[list[str]]) -> bool:
    return any(EPS in g.first_of_sequence(p) for p in productions)


def _emitted(productions: list[list[str]]) -> list[tuple[int, list[str]]]:
    """(index, production) of every production that gets a branch: all but a lone ε."""
    return [(i, p) for i, p in enumerate(productions) if p != [EPS]]


def _pending_tokens(g: Grammar, A: str) -> list[str]:
    """The tokens parse_A's else adds to pending: what starts each branch, without FOLLOW or excepted tokens."""
    tokens = set()
    for i, p in _emitted(g.grammar[A]):
        tokens |= (g.first_of_sequence(p) - {EPS}) & g.predict[A][i]
    return sorted(tokens)


def _pending_literal(stmt: ast.stmt) -> list[str]:
    """Read `self.pending |= set([...])` back as its list of tokens."""
    assert isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.BitOr), ast.unparse(stmt)
    assert ast.unparse(stmt.target) == "self.pending"
    assert isinstance(stmt.value, ast.Call) and ast.unparse(stmt.value.func) == "set", ast.unparse(stmt)
    return ast.literal_eval(stmt.value.args[0])


def _assert_raises_pending(stmt: ast.stmt) -> None:
    """stmt is `raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))`."""
    assert isinstance(stmt, ast.Raise), ast.unparse(stmt)
    assert ast.unparse(stmt.exc) == "SyntacticalError(self.format_error_message(self.report_expected_symbols()))"


# ---------------------------------------------------------------------------
# Grammar table (spec §4, tasks.md §3)
# ---------------------------------------------------------------------------
GRAMMARS: dict[str, dict[str, list[list[str]]]] = {
    "G1": {"S": [["a"]]},
    "G2": {"S": [["a"], ["b"], ["c"]]},
    "G3": {"S": [["A", "b"]], "A": [["a"], [EPS]]},
    "G4": {"S": [["a", "b", "c"]]},
    "G5": {"S": [["A", "B"]], "A": [["a"]], "B": [["b"]]},
    "G6": {"S": [["a", "A", "b", "B"]], "A": [["x"]], "B": [["y"]]},
    "G7": {"S": [["a", "a"]]},
    "G8": {"S": [["A"]], "A": [["a"], [EPS]]},
    "G9": {"S": [["a"]], "U": [["u"], [EPS]]},
    "G10": {"S": [["'"], ['"'], ["\\"]]},
    "G11": {"S": [["if", "E", "then", "S", "end"], ["x"]], "E": [["x", "==", "x"], ["y", "..", "y"]]},
    "G12": {"B": [["b"]], "A": [["B"]]},
    # grammar1 and grammar2 in main.py
    "G13-grammar1": {
        "A": [["B", "C"], ["ant", "A", "all"]],
        "B": [["big", "C"], ["bus", "A", "boss"], [EPS]],
        "C": [["cat"], ["cow"]],
    },
    "G13-grammar2": {"S": [["A", "B", "C"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]], "C": [["c"]]},
    # spec 004 E1, with E' and T' renamed (spec §8)
    "G13-expression": {
        "E": [["T", "Ep"]],
        "Ep": [["+", "T", "Ep"], [EPS]],
        "T": [["F", "Tp"]],
        "Tp": [["*", "F", "Tp"], [EPS]],
        "F": [["(", "E", ")"], ["id"]],
    },
    # spec 004 E2
    "G13-lua": {
        "Chunk": [["Block"]],
        "Block": [["Stat", "Block"], [EPS]],
        "Stat": [["if", "Exp", "then", "Block", "end"], ["Name", "=", "Exp"]],
        "Exp": [["Name"], ["Number"]],
    },
    # A rule whose only production is ε
    "G14": {"S": [["A", "b"]], "A": [[EPS]]},
    # A start symbol with a single nullable production of two non-terminals
    "G15": {"S": [["A", "B"]], "A": [["a"], [EPS]], "B": [["b"], [EPS]]},
    # A nullable production that isn't ε: its branch tests FOLLOW(A) too, its pending doesn't
    "G16": {"S": [["A", "x"]], "A": [["y"], ["B"]], "B": [["b"], [EPS]]},
}

G_ROWS = [(name, grammar) for name, grammar in GRAMMARS.items()]


@pytest.mark.parametrize("grammar", _params("test_grammars_are_ll1", G_ROWS))
def test_grammars_are_ll1(grammar):
    # Non-LL(1) grammars are out of scope (spec §8), so every grammar of the table must be LL(1)
    assert _processed(grammar).check_LL1_condition() is True


# ---------------------------------------------------------------------------
# Structural tests (spec §3.1, tasks.md §4)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("grammar", _params("test_generated_file_is_valid_python", G_ROWS))
def test_generated_file_is_valid_python(grammar, out_dir):
    _, source = _generate(grammar, out_dir)
    try:
        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"generated file is not valid Python ({e}):\n{source}")


@pytest.mark.parametrize("grammar", _params("test_generated_class_extends_base", G_ROWS))
def test_generated_class_extends_base(grammar, out_dir):
    _, source = _generate(grammar, out_dir)
    assert [ast.unparse(base) for base in _class_def(source).bases] == ["ASDR_base"]


@pytest.mark.parametrize("grammar", _params("test_one_method_per_nonterminal", G_ROWS))
def test_one_method_per_nonterminal(grammar, out_dir):
    _, source = _generate(grammar, out_dir)
    methods = _methods(_class_def(source))
    assert {name for name in methods if name.startswith("parse_")} == {f"parse_{A}" for A in grammar}
    assert "main" in methods


@pytest.mark.parametrize("grammar", _params("test_branches_match_predict_sets", G_ROWS))
def test_branches_match_predict_sets(grammar, out_dir):
    g, source = _generate(grammar, out_dir)
    methods = _methods(_class_def(source))
    for A, productions in grammar.items():
        if _single_nullable(g, productions):
            continue
        branches, _ = _branches(methods[f"parse_{A}"])
        emitted = _emitted(productions)
        assert len(branches) == len(emitted), f"parse_{A}: one branch per production that isn't ε"
        for (tokens, _), (i, _) in zip(branches, emitted):
            assert len(tokens) == len(set(tokens)), f"parse_{A} branch {i}: repeated token"
            assert set(tokens) == g.predict[A][i], f"parse_{A} branch {i}: tokens differ from predict"


@pytest.mark.parametrize("grammar", _params("test_branch_bodies_follow_productions", G_ROWS))
def test_branch_bodies_follow_productions(grammar, out_dir):
    g, source = _generate(grammar, out_dir)
    methods = _methods(_class_def(source))
    for A, productions in grammar.items():
        if _single_nullable(g, productions):
            continue
        branches, _ = _branches(methods[f"parse_{A}"])
        for (_, body), (i, production) in zip(branches, _emitted(productions)):
            assert body == _expected_body(production, set(grammar)), f"parse_{A} branch {i}"


@pytest.mark.parametrize("grammar", _params("test_single_nullable_production_has_no_if", G_ROWS))
def test_single_nullable_production_has_no_if(grammar, out_dir):
    g, source = _generate(grammar, out_dir)
    methods = _methods(_class_def(source))
    for A, productions in grammar.items():
        if not _single_nullable(g, productions):
            continue
        # A lone ε gives pass, anything else calls its non-terminals in order
        symbols = [s for s in productions[0] if s != EPS] or [EPS]
        body = [_describe(stmt) for stmt in methods[f"parse_{A}"].body]
        assert body == _expected_body(symbols, set(grammar)), f"parse_{A}"


@pytest.mark.parametrize("grammar", _params("test_else_adds_pending_tokens", G_ROWS))
def test_else_adds_pending_tokens(grammar, out_dir):
    g, source = _generate(grammar, out_dir)
    methods = _methods(_class_def(source))
    for A, productions in grammar.items():
        if _single_nullable(g, productions):
            continue
        _, else_body = _branches(methods[f"parse_{A}"])
        # The raw token types, sorted so the file is the same on every run; ASDR_base sorts them for the grader
        assert _pending_literal(else_body[0]) == _pending_tokens(g, A), f"parse_{A}"
        if _is_nullable(g, productions):
            assert len(else_body) == 1, f"parse_{A}: a nullable rule must not raise"
        else:
            assert len(else_body) == 2, f"parse_{A}: a rule that isn't nullable must raise"
            _assert_raises_pending(else_body[1])


def test_pending_leaves_out_follow(out_dir):
    # A → y | B with B nullable: the B branch tests FOLLOW(A) = {x}, but x isn't something A can start with
    g, source = _generate(GRAMMARS["G16"], out_dir)
    branches, else_body = _branches(_methods(_class_def(source))["parse_A"])
    assert set(branches[1][0]) == {"b", "x"}
    assert _pending_literal(else_body[0]) == ["b", "y"]


def test_pending_leaves_out_excepted_tokens(out_dir):
    # An exception removes b from the second branch, so the else doesn't name it either
    grammar = {"S": [["a"], ["b"]]}
    _, source = _generate(grammar, out_dir, exceptions={"S": {1: "b"}})
    branches, else_body = _branches(_methods(_class_def(source))["parse_S"])
    assert [tokens for tokens, _ in branches] == [["a"], []]
    assert _pending_literal(else_body[0]) == ["a"]


# ---------------------------------------------------------------------------
# Hidden expected tokens: still parsed, never named in an error
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("grammar", _params("test_visible_first_without_hidden_is_first", G_ROWS))
def test_visible_first_without_hidden_is_first(grammar):
    g = _processed(grammar)
    visible = ASDR_generator(g).compute_visible_first()
    assert visible == {A: g.first[A] - {EPS} for A in grammar}


def test_visible_first_of_sequence():
    g = _processed(GRAMMARS["G13-grammar2"])
    gen = ASDR_generator(g)
    visible = gen.compute_visible_first()
    assert gen.visible_first_of_sequence(["A", "B", "C"], visible) == {"a", "b", "c"}
    assert gen.visible_first_of_sequence(["A"], visible) == {"a"}
    assert gen.visible_first_of_sequence(["c", "A"], visible) == {"c"}
    assert gen.visible_first_of_sequence([EPS], visible) == set()


def test_init_has_no_hidden_tokens():
    assert ASDR_generator(_processed(GRAMMARS["G1"])).hidden_expected == {}


def test_hidden_token_is_still_parsed(out_dir, load_parser):
    grammar, hidden = {"S": [["a"], ["b"]]}, {"S": {1: {"b"}}}
    _, source = _generate(grammar, out_dir, hidden=hidden)
    branches, else_body = _branches(_methods(_class_def(source))["parse_S"])
    assert [tokens for tokens, _ in branches] == [["a"], ["b"]]
    assert _pending_literal(else_body[0]) == ["a"]
    lexer = FakeLexer(["b"])
    _run(grammar, lexer, out_dir, load_parser, hidden)
    assert lexer.reached_end
    with pytest.raises(SyntacticalError) as err:
        _run(grammar, FakeLexer(["c"]), out_dir, load_parser, hidden)
    assert _error_parts(err.value.message) == (1, 1, "c", {"a"})


def test_hidden_token_stays_hidden_in_outer_rules(out_dir, load_parser):
    # Hidden in N, so E, which starts with N, doesn't name it either
    grammar = {"S": [["E"]], "E": [["id"], ["N"]], "N": [["nil"], ["function"]]}
    hidden = {"N": {1: {"function"}}}
    with pytest.raises(SyntacticalError) as err:
        _run(grammar, FakeLexer(["for"]), out_dir, load_parser, hidden)
    assert _error_parts(err.value.message) == (1, 1, "for", {"id", "nil"})
    lexer = FakeLexer(["function"])
    _run(grammar, lexer, out_dir, load_parser, hidden)
    assert lexer.reached_end


def test_hidden_token_only_in_its_production(out_dir, load_parser):
    # f is hidden where A starts with it, but B starts with f too and still names it
    grammar = {"S": [["A"], ["k", "B"]], "A": [["f", "x"]], "B": [["f", "y"]]}
    hidden = {"A": {0: {"f"}}}
    with pytest.raises(SyntacticalError) as err:
        _run(grammar, FakeLexer(["z"]), out_dir, load_parser, hidden)
    assert _error_parts(err.value.message) == (1, 1, "z", {"k"})
    with pytest.raises(SyntacticalError) as err:
        _run(grammar, FakeLexer(["k", "z"]), out_dir, load_parser, hidden)
    assert _error_parts(err.value.message) == (1, 2, "z", {"f"})


@pytest.mark.parametrize("grammar", _params("test_main_parses_start_symbol", G_ROWS))
def test_main_parses_start_symbol(grammar, out_dir):
    _, source = _generate(grammar, out_dir)
    body = _methods(_class_def(source))["main"].body
    start = next(iter(grammar))
    assert ast.unparse(body[0]) == "self.cur_tok = self.lexer.tokenize()"
    assert ast.unparse(body[1]) == f"self.parse_{start}()"
    end_check = body[2]
    assert isinstance(end_check, ast.If)
    assert ast.unparse(end_check.test) == f"self.cur_tok.type != {END!r}"
    assert ast.unparse(end_check.body[0]) == f"self.pending |= {{{END!r}}}"
    _assert_raises_pending(end_check.body[1])


# ---------------------------------------------------------------------------
# ASDR_base: how the error message shows tokens (spec §3.2)
# ---------------------------------------------------------------------------
def _base_at(token_type: str, lexeme: str, line: int = 2, col: int = 7) -> ASDR_base:
    """An ASDR_base whose current token is the given one; no lexer is needed to format messages."""
    base = ASDR_base(None)
    base.cur_tok = Token(token_type, lexeme, line, col)
    return base


_SHOWN_ROWS = [
    ("tkn_num", "tkn_num", "valor_numerico"),
    ("tkn_str", "tkn_str", "cadena_de_caracteres"),
    ("end-of-input", END, EOF_SHOWN),
    ("keyword", "end", "end"),
    ("builtin", "print", "print"),
    ("id", "id", "id"),
    ("plain-token", "a", "a"),
] + [(token_type, token_type, symbol) for token_type, symbol in sorted(_SYMBOLS.items())]


@pytest.mark.parametrize("token, shown", _params("test_format_expected_symbol", _SHOWN_ROWS))
def test_format_expected_symbol(token, shown):
    assert ASDR_base(None).format_expected_symbol(token) == f'"{shown}"'


_MESSAGE_ROWS = [
    ("one-token", ["tkn_closing_par"], '")"'),
    ("several", ["end", "id", "tkn_num"], '"end", "id", "valor_numerico"'),
    ("order-kept", ["tkn_plus", "and"], '"+", "and"'),
    ("comma-token", ["tkn_assign", "tkn_comma", "tkn_concat"], '"=", ",", ".."'),
    ("end-of-input", [END], f'"{EOF_SHOWN}"'),
]


@pytest.mark.parametrize("expected, shown", _params("test_format_error_message", _MESSAGE_ROWS))
def test_format_error_message(expected, shown):
    message = _base_at("tkn_num", "45").format_error_message(expected)
    assert message == f'<2:7> Error sintactico: se encontro: "45"; se esperaba: {shown}.'


def test_format_error_message_at_end_of_input():
    message = _base_at(END, END).format_error_message(["end"])
    assert message == f'<2:7> Error sintactico: se encontro: "{EOF_SHOWN}"; se esperaba: "end".'


def test_match_names_the_one_expected_token():
    with pytest.raises(SyntacticalError) as err:
        _base_at("id", "x").match("tkn_closing_par")
    assert err.value.message.endswith('se esperaba: ")".')


def test_match_adds_its_token_to_pending():
    base = _base_at("id", "x")
    base.pending = {"tkn_plus", "end"}
    with pytest.raises(SyntacticalError) as err:
        base.match("tkn_closing_par")
    assert err.value.message.endswith('se esperaba: "end", ")", "+".')


def test_match_clears_pending():
    base = ASDR_base(FakeLexer(["b"]))
    base.cur_tok = Token("a", "a", 1, 1)
    base.pending = {"x"}
    base.match("a")
    assert base.pending == set()
    assert base.cur_tok.type == "b"


def test_init_starts_with_empty_pending():
    assert ASDR_base(None).pending == set()


def test_report_expected_symbols_sort_order():
    # Token types sort by name, except tkn_num and tkn_str, which sort as their shown names
    base = ASDR_base(None)
    base.pending = {"tkn_num", "tkn_str", "tkn_plus", "id", "true", "tkn_varargs", "and"}
    assert base.report_expected_symbols() == ["and", "tkn_str", "id", "tkn_plus", "tkn_varargs", "true", "tkn_num"]


def test_report_expected_symbols_keeps_pending():
    base = ASDR_base(None)
    base.pending = {"a", "b"}
    base.report_expected_symbols()
    assert base.pending == {"a", "b"}


# ---------------------------------------------------------------------------
# Unit tests for each method (spec §1, tasks.md §5)
# ---------------------------------------------------------------------------


def test_init_sets_header(out_dir):
    gen = ASDR_generator(_processed(GRAMMARS["G1"]))
    assert [line.strip() for line in gen.lines] == [
        "from exceptions.custom_exceptions import SyntacticalError",
        "from lexer.lexer import Lexer",
        "from .ASDR_base import ASDR_base",
        "",
        "class ASDR(ASDR_base):",
    ]
    assert gen.eps == EPS
    assert list(out_dir.iterdir()) == []


def test_populate_lines_does_not_write(out_dir):
    gen = ASDR_generator(_processed(GRAMMARS["G1"]))
    header = len(gen.lines)
    gen.populate_lines()
    assert len(gen.lines) > header
    assert list(out_dir.iterdir()) == []


def test_write_program_writes_lines(out_dir):
    gen = ASDR_generator(_processed(GRAMMARS["G1"]))
    gen.lines = ["x", "y"]
    gen.write_program()
    assert (out_dir / "ASDR.py").read_text() == "x\ny\n"


def test_generate_is_populate_then_write(out_dir):
    _, generated = _generate(GRAMMARS["G3"], out_dir)
    gen = ASDR_generator(_processed(GRAMMARS["G3"]))
    gen.populate_lines()
    gen.write_program()
    assert (out_dir / "ASDR.py").read_text() == generated


# ---------------------------------------------------------------------------
# Accept tests (spec §5.1, tasks.md §6)
# ---------------------------------------------------------------------------
ACCEPT_ROWS = [
    ("A1-shortest", "G1", ["a"]),
    ("A2-alt-a", "G2", ["a"]),
    ("A2-alt-b", "G2", ["b"]),
    ("A2-alt-c", "G2", ["c"]),
    ("A3-epsilon", "G3", ["b"]),
    ("A3-non-epsilon", "G3", ["a", "b"]),
    ("A4-empty-nullable", "G8", []),
    ("A5-c", "G13-grammar2", ["c"]),
    ("A5-ac", "G13-grammar2", ["a", "c"]),
    ("A5-bc", "G13-grammar2", ["b", "c"]),
    ("A5-abc", "G13-grammar2", ["a", "b", "c"]),
    ("A6-expression", "G13-expression", "id + id * ( id )".split()),
    ("A7-deep-nesting", "G13-expression", ["("] * 50 + ["id"] + [")"] * 50),
    ("A8-lua-nested-if", "G13-lua", "if Name then if Name then Name = Number end end".split()),
    ("A9-only-epsilon", "G14", ["b"]),
    ("A10-empty", "G15", []),
    ("A10-a", "G15", ["a"]),
    ("A10-b", "G15", ["b"]),
    ("A10-ab", "G15", ["a", "b"]),
    ("A11-x", "G16", ["x"]),
    ("A11-yx", "G16", ["y", "x"]),
    ("A11-bx", "G16", ["b", "x"]),
]


@pytest.mark.parametrize("grammar_name, types", _params("test_parser_accepts", ACCEPT_ROWS))
def test_parser_accepts(grammar_name, types, out_dir, load_parser):
    lexer = FakeLexer(types)
    _run(GRAMMARS[grammar_name], lexer, out_dir, load_parser)
    assert lexer.reached_end, "parser stopped before reading the whole input"


# ---------------------------------------------------------------------------
# Reject tests (spec §5.2, tasks.md §7)
# ---------------------------------------------------------------------------
REJECT_ROWS = [
    ("R1-wrong-first-token", "G1", ["b"], (1, 1, "b", {"a"})),
    ("R2-wrong-mid-production", "G4", ["a", "x", "c"], (1, 2, "x", {"b"})),
    ("R3-ends-early", "G4", ["a", "b"], (1, 3, EOF_SHOWN, {"c"})),
    ("R4-extra-tokens", "G1", ["a", "a"], (1, 2, "a", {EOF_SHOWN})),
    ("R5-empty-not-nullable", "G1", [], (1, 1, EOF_SHOWN, {"a"})),
    ("R6-union-named", "G3", ["c"], (1, 1, "c", {"a", "b"})),
    ("R7-inside-recursion", "G13-expression", ["id", "+"], (1, 3, EOF_SHOWN, {"(", "id"})),
    # Tp and Ep took ε at $, so * and + are pending too
    ("R8-missing-close-paren", "G13-expression", ["(", "id"], (1, 3, EOF_SHOWN, {"*", "+", ")"})),
    ("R9-pending-chain", "G13-grammar2", ["d"], (1, 1, "d", {"a", "b", "c"})),
    ("R10-match-clears-pending", "G13-grammar2", ["a", "d"], (1, 2, "d", {"b", "c"})),
    ("R11-nullable-production", "G16", ["z"], (1, 1, "z", {"b", "x", "y"})),
    ("R12-after-nullable-production", "G16", ["b", "b"], (1, 2, "b", {"x"})),
    ("R13-extra-after-nullable-start", "G15", ["a", "a"], (1, 2, "a", {"b", EOF_SHOWN})),
]


@pytest.mark.parametrize("grammar_name, types, expected", _params("test_parser_rejects", REJECT_ROWS))
def test_parser_rejects(grammar_name, types, expected, out_dir, load_parser):
    with pytest.raises(SyntacticalError) as err:
        _run(GRAMMARS[grammar_name], FakeLexer(types), out_dir, load_parser)
    assert _error_parts(err.value.message) == expected


# ---------------------------------------------------------------------------
# End-to-end tests with the real lexer (spec §6, tasks.md §8)
# ---------------------------------------------------------------------------
# Terminals are the token types the lexer produces
LEXER_GRAMMAR: dict[str, list[list[str]]] = {
    "Chunk": [["Block"]],
    "Block": [["Stat", "Block"], [EPS]],
    "Stat": [["if", "Exp", "then", "Block", "end"], ["id", "tkn_assign", "Exp"]],
    "Exp": [["id"], ["tkn_num"]],
}

E2E_ROWS = [
    ("E1-assignment", "x = 1", None),
    ("E2-if-block", "if x then y = 2 end", None),
    # Block took ε at $, so a new statement could start there too
    ("E3-missing-end", "if x then y = 2", (1, 16, EOF_SHOWN, {"end", "id", "if"})),
    ("E4-double-assign", "x = = 1", (1, 5, "=", {"id", "valor_numerico"})),
    ("E5-error-on-line-3", "x = 1\ny = 2\nz = then\n", (3, 5, "then", {"id", "valor_numerico"})),
]


@pytest.mark.parametrize("source, expected", _params("test_end_to_end", E2E_ROWS))
def test_end_to_end(source, expected, out_dir, load_parser):
    if expected is None:
        _run(LEXER_GRAMMAR, Lexer(source), out_dir, load_parser)
        return
    with pytest.raises(SyntacticalError) as err:
        _run(LEXER_GRAMMAR, Lexer(source), out_dir, load_parser)
    assert _error_parts(err.value.message) == expected


# ---------------------------------------------------------------------------
# Properties (spec §7, tasks.md §9)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("grammar", _params("test_generation_is_deterministic", G_ROWS))
def test_generation_is_deterministic(grammar, out_dir):
    _, first = _generate(grammar, out_dir)
    _, second = _generate(grammar, out_dir)
    assert first == second


@pytest.mark.parametrize("grammar", _params("test_grammar_is_not_modified", G_ROWS))
def test_grammar_is_not_modified(grammar, out_dir):
    g = _processed(grammar)
    before = copy.deepcopy((g.grammar, g.first, g.follow, g.predict))
    ASDR_generator(g).generate()
    assert (g.grammar, g.first, g.follow, g.predict) == before


def test_generate_overwrites_existing_file(out_dir):
    (out_dir / "ASDR.py").write_text("STALE")
    _, generated = _generate(GRAMMARS["G1"], out_dir)
    assert "STALE" not in generated
    _, clean = _generate(GRAMMARS["G1"], out_dir)
    assert generated == clean


def test_generators_do_not_share_lines(out_dir):
    gen1 = ASDR_generator(_processed(GRAMMARS["G1"]))
    gen2 = ASDR_generator(_processed(GRAMMARS["G2"]))
    gen1.generate()
    first = (out_dir / "ASDR.py").read_text()
    gen2.generate()
    ASDR_generator(_processed(GRAMMARS["G1"])).generate()
    assert (out_dir / "ASDR.py").read_text() == first
