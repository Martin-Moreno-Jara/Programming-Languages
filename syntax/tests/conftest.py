import copy
import sys
from pathlib import Path

import pytest

# The syntax folder (the one holding grammar.py) must be importable
SYNTAX_ROOT = Path(__file__).resolve().parent.parent
if str(SYNTAX_ROOT) not in sys.path:
    sys.path.insert(0, str(SYNTAX_ROOT))

# The project root must be importable too: the code generator and the parser it writes import syntax.*, lexer.* and exceptions.*
PROJECT_ROOT = SYNTAX_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from grammar import Grammar  # noqa: E402


def _reorder(grammar: dict[str, list[list[str]]], order: tuple[str, ...]) -> dict[str, list[list[str]]]:
    """Return the same grammar with its non-terminals declared in the given order."""
    return {nt: grammar[nt] for nt in order}


def _new_grammar(grammar: dict[str, list[list[str]]]) -> Grammar:
    """Build a Grammar object on a private copy of grammar."""
    return Grammar(copy.deepcopy(grammar))


def _run_first(grammar: dict[str, list[list[str]]]) -> dict[str, set[str]]:
    """Compute FIRST with a fresh Grammar object and return its first dict."""
    g = _new_grammar(grammar)
    g.compute_first_set()
    return g.first


def _follow_grammar(
    grammar: dict[str, list[list[str]]],
    first_preset: dict[str, set[str]] | None,
) -> Grammar:
    """Build a Grammar ready for compute_follow_set; first is copied from first_preset, or computed if it is None."""
    g = _new_grammar(grammar)
    if first_preset is None:
        g.compute_first_set()
    else:
        g.first.update(copy.deepcopy(first_preset))
    return g


def _run_follow(
    grammar: dict[str, list[list[str]]],
    first_preset: dict[str, set[str]] | None,
) -> dict[str, set[str]]:
    """Compute FOLLOW with a fresh Grammar object and return its follow dict."""
    g = _follow_grammar(grammar, first_preset)
    g.compute_follow_set()
    return g.follow


def _predict_grammar(
    grammar: dict[str, list[list[str]]],
    first_preset: dict[str, set[str]] | None,
    follow_preset: dict[str, set[str]] | None,
) -> Grammar:
    """Build a Grammar ready for compute_predict_set; first/follow are copied from the presets, or computed if they are None."""
    if first_preset is None:
        g = _follow_grammar(grammar, None)
        g.compute_follow_set()
    else:
        g = _follow_grammar(grammar, first_preset)
        g.follow.update(copy.deepcopy(follow_preset))
    return g


def _run_predict(
    grammar: dict[str, list[list[str]]],
    first_preset: dict[str, set[str]] | None,
    follow_preset: dict[str, set[str]] | None,
) -> dict[str, list[set[str]]]:
    """Compute the prediction sets with a fresh Grammar object and return them through get_predict_set."""
    g = _predict_grammar(grammar, first_preset, follow_preset)
    g.compute_predict_set()
    return g.get_predict_set()


def _ll1_grammar(predict_preset: dict[str, list[set[str]]]) -> Grammar:
    """Build a Grammar whose predict is a private copy of predict_preset; its productions are placeholders, one per set."""
    g = _new_grammar({A: [["_"] for _ in sets] for A, sets in predict_preset.items()})
    g.predict.update(copy.deepcopy(predict_preset))
    return g


@pytest.fixture
def new_grammar():
    return _new_grammar


@pytest.fixture
def reorder():
    return _reorder


@pytest.fixture
def run_first():
    return _run_first


@pytest.fixture
def follow_grammar():
    return _follow_grammar


@pytest.fixture
def run_follow():
    return _run_follow


@pytest.fixture
def predict_grammar():
    return _predict_grammar


@pytest.fixture
def run_predict():
    return _run_predict


@pytest.fixture
def ll1_grammar():
    return _ll1_grammar


# ---------------------------------------------------------------------------
# Real Lua grammar (spec 006, tasks §2.3)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def lua_parser(tmp_path_factory):
    """(Grammar, ASDR) for final_grammar, generated once into a temporary folder; skips if it is not LL(1)."""
    from real_grammar_support import generate_parser

    folder = tmp_path_factory.mktemp("real") / "syntax"
    folder.mkdir()
    result = generate_parser(folder)
    if result is None:
        pytest.skip("final_grammar is not LL(1)")
    return result


@pytest.fixture(scope="session")
def project_copy(tmp_path_factory):
    """A copy of the files main.py needs, so running it never rewrites the real syntax/ASDR.py."""
    import shutil

    root = tmp_path_factory.mktemp("project")
    ignore = shutil.ignore_patterns("__pycache__", "tests", "specs", "docs")
    shutil.copy(PROJECT_ROOT / "main.py", root / "main.py")
    for folder in ("syntax", "lexer", "exceptions"):
        shutil.copytree(PROJECT_ROOT / folder, root / folder, ignore=ignore)
    return root
