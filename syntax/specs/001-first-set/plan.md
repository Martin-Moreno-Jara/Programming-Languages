# Plan 001 — Implementing the FIRST set tests

This plan turns the strategy in [`spec.md`](spec.md) into a technical design
for pytest. It describes files, helpers, data tables, test functions and how
failures are handled. It does not contain the test code itself.

## 1. Goal and code under test

Implement the tests described in spec 001 against the `Grammar` class in
`syntax/grammar.py`:

| Member | Signature | Effect |
|---|---|---|
| `__init__` | `(self, grammar: dict[str, list[list[str]]])` | Stores `grammar`, sets `non_terminals_set`, an empty `first` set per non-terminal, `EPS` and `END` |
| `first_of_sequence` | `(self, sequence: list[str]) -> set[str]` | Returns FIRST of one production. Only reads `self.first`. |
| `compute_first_set` | `(self) -> None` | Fills `self.first` for every non-terminal, in place |

Unit tests check the constructor's state and the set `first_of_sequence`
returns. End-to-end tests read `g.first` after calling `compute_first_set`.
Arguments are passed by position, so renaming a parameter doesn't break tests.

`grammar.py` and `main.py` are not modified by the agent (see `syntax/AGENTS.md`).

## 2. File layout

```
syntax/
├── grammar.py
├── main.py
├── specs/001-first-set/{spec.md, plan.md}
└── tests/
    ├── conftest.py         # sys.path setup + helpers exposed as fixtures
    └── test_first_set.py   # data tables + all tests of this spec
```

- Run with `pytest syntax/tests -v` from the repository root, or `pytest tests -v` from `syntax/`.
- Run the lexer and syntax suites **separately**. Both `lexer/` and `syntax/`
  contain a `main.py`. In a single pytest run, the first one imported would be
  cached as `main` and the other suite would test the wrong module.
- No `__init__.py` in `tests/`. pytest's default import mode puts `tests/` on
  `sys.path`, as in `lexer/test-strategy/`.

## 3. `conftest.py`

It follows the same pattern as `lexer/test-strategy/conftest.py`: private
helper functions, each exposed through a fixture that returns the function.

```python
SYNTAX_ROOT = Path(__file__).resolve().parent.parent   # folder holding grammar.py
# inserted at sys.path[0] if missing, then:
from grammar import Grammar  # noqa: E402
```

| Helper | Signature | Behavior |
|---|---|---|
| `_new_grammar` | `(grammar) -> Grammar` | Returns `Grammar(copy.deepcopy(grammar))`. |
| `_reorder` | `(grammar, order: tuple[str, ...]) -> dict` | Returns `{nt: grammar[nt] for nt in order}`. Same productions, different key order. |
| `_run_first` | `(grammar) -> dict[str, set[str]]` | `g = _new_grammar(grammar)`, then `g.compute_first_set()`, then returns `g.first`. |

The deep copy in `_new_grammar` makes sure that if the code under test changes
its input grammar, the change can't leak into other rows that share the same
table entry.

Fixtures: `new_grammar`, `reorder`, `run_first`, each returning the matching helper.

Constants and tables live in `test_first_set.py`, not in fixtures, because
`pytest.mark.parametrize` arguments are evaluated at import time and cannot use
fixtures.

## 4. Shared constants in `test_first_set.py`

```python
EPS = "ε"
```

Every grammar and expected set uses `EPS` instead of the literal symbol, to
avoid copy/paste mistakes with look-alike characters.

## 5.0 Unit tests — `Grammar.__init__` (spec §4.1)

`test_grammar_init(grammar, expected, new_grammar)`, parametrized over
`GRAMMAR_CASES` (`expected` unused). With `g = new_grammar(grammar)`, assert
`g.grammar == grammar`, `g.non_terminals_set == set(grammar)`,
`g.first == {nt: set() for nt in grammar}`, `g.EPS == EPS` and `g.END == END`
(`END = "$"` is a module constant next to `EPS`). 15 rows.

## 5. Unit tests — `first_of_sequence` (spec §4.2)

### 5.1 Data table

`FIRST_OF_SEQUENCE_CASES` is a list of
`pytest.param(sequence, preset, expected, id=...)`. `sequence` is one
production. `preset` maps each helper non-terminal to its FIRST set as if it
had already been computed.

| id | `sequence` | `preset` | `expected` |
|---|---|---|---|
| `U1-single-terminal` | `["a"]` | `{}` | `{"a"}` |
| `U2-terminal-sequence` | `["b", "c"]` | `{}` | `{"b"}` |
| `U3-epsilon` | `[EPS]` | `{}` | `{EPS}` |
| `U4-single-nullable-nt` | `["X"]` | `{"X": {"x", EPS}}` | `{"x", EPS}` |
| `U5-leading-terminal-stops` | `["a", "X"]` | `{"X": {"x"}}` | `{"a"}` |
| `U6-non-nullable-stops` | `["X", "y"]` | `{"X": {"x"}}` | `{"x"}` |
| `U7-nullable-then-terminal` | `["X", "y"]` | `{"X": {"x", EPS}}` | `{"x", "y"}` |
| `U8-all-nullable` | `["X", "Y"]` | `{"X": {"x", EPS}, "Y": {"y", EPS}}` | `{"x", "y", EPS}` |
| `U9-nullable-chain-then-nt` | `["X", "Y", "Z"]` | `{"X": {"x", EPS}, "Y": {"y", EPS}, "Z": {"z"}}` | `{"x", "y", "z"}` |
| `U10-stops-before-terminal` | `["X", "Y", "w"]` | `{"X": {"x", EPS}, "Y": {"y"}}` | `{"x", "y"}` |
| `U11-not-yet-computed-nt` | `["X", "y"]` | `{"X": set()}` | `set()` |

### 5.2 `test_first_of_sequence(sequence, preset, expected, new_grammar)`

1. Call `g = new_grammar({h: [["_"]] for h in preset})`. The helpers'
   productions are dummies. They only need to be keys so that X/Y/Z count as
   non-terminals.
2. Fill the helpers with `g.first[h] = set(s)` for each entry of `preset`.
3. Save `first_before = copy.deepcopy(g.first)`.
4. Call `result = g.first_of_sequence(sequence)`.
5. Assert `result == expected`.
6. Assert `g.first == first_before`. The method must only read `first`.

Combining several alternatives of one non-terminal is not tested here. It
belongs to `compute_first_set` and is covered by §6.

## 6. End-to-end tests — `compute_first_set` (spec §5)

### 6.1 Data table

`GRAMMAR_CASES` is a list of plain tuples `(case_id, grammar, expected)`. It is
not a list of `pytest.param`, because §7 reuses it to generate other
parametrizations. Each test turns it into params with a small helper:
`[pytest.param(g, e, id=i) for i, g, e in GRAMMAR_CASES]`.

| case_id | grammar | expected |
|---|---|---|
| `E1-only-terminals` | `{"S": [["a","b"],["c"]]}` | `{"S": {"a","c"}}` |
| `E2-main-grammar` | `{"A": [["B","C"],["ant","A","all"]], "B": [["big","C"],["bus","A","boss"],[EPS]], "C": [["cat"],["cow"]]}` | `{"A": {"ant","big","bus","cat","cow"}, "B": {"big","bus",EPS}, "C": {"cat","cow"}}` |
| `E3-dependency-chain` | `{"S": [["A"]], "A": [["B"]], "B": [["b"]]}` | all three `{"b"}` |
| `E4-nullable-prefix` | `{"S": [["A","B","c"]], "A": [["a"],[EPS]], "B": [["b"],[EPS]]}` | `{"S": {"a","b","c"}, "A": {"a",EPS}, "B": {"b",EPS}}` |
| `E5-whole-body-nullable` | `{"S": [["A","B"]], "A": [["a"],[EPS]], "B": [["b"],[EPS]]}` | `{"S": {"a","b",EPS}, "A": {"a",EPS}, "B": {"b",EPS}}` |
| `E6-indirectly-nullable` | `{"S": [["A"]], "A": [["B"]], "B": [[EPS]]}` | all three `{EPS}` |
| `E7-epsilon-does-not-leak` | `{"S": [["A","b"]], "A": [[EPS]]}` | `{"S": {"b"}, "A": {EPS}}` |
| `E8-non-nullable-blocks` | `{"S": [["A","B"]], "A": [["a"]], "B": [["b"]]}` | `{"S": {"a"}, "A": {"a"}, "B": {"b"}}` |
| `E9-left-recursion` | `{"E": [["E","+","T"],["T"]], "T": [["id"],["(","E",")"]]}` | `{"E": {"id","("}, "T": {"id","("}}` |
| `E10-mutual-recursion` | `{"A": [["B","a"],["x"]], "B": [["A","b"],["y"]]}` | `{"A": {"x","y"}, "B": {"x","y"}}` |
| `E11-recursion-with-nullable` | `{"A": [["B","A"],["a"]], "B": [["b"],[EPS]]}` | `{"A": {"a","b"}, "B": {"b",EPS}}` |
| `E12-right-recursion` | `{"L": [["x","L"],[EPS]]}` | `{"L": {"x",EPS}}` |
| `E13-expression-grammar` | `{"E": [["T","E'"]], "E'": [["+","T","E'"],[EPS]], "T": [["F","T'"]], "T'": [["*","F","T'"],[EPS]], "F": [["(","E",")"],["id"]]}` | `{"E": {"(","id"}, "E'": {"+",EPS}, "T": {"(","id"}, "T'": {"*",EPS}, "F": {"(","id"}}` |
| `E14-common-prefix` | `{"S": [["a","b"],["a","c"]]}` | `{"S": {"a"}}` |
| `E15-multichar-terminals` | `{"Stat": [["local","Name","=","Exp"],["Exp"]], "Exp": [["(","Exp",")"],["Exp","==","Exp"],["Name"]]}` | `{"Stat": {"local","(","Name"}, "Exp": {"(","Name"}}` |

All grammars and expected sets must match `spec.md` §5 exactly. If one of them
changes, update both files.

### 6.2 `test_compute_first_set(grammar, expected, run_first)`

- Assert `run_first(grammar) == expected`.
- Comparing whole dictionaries checks exact sets for every non-terminal. It
  also checks that the keys are exactly the grammar's non-terminals (spec §3).
  When it fails, pytest's diff points at the wrong entry.

## 7. Cross-cutting tests (spec §6)

### 7.1 Order independence — `test_first_is_order_independent(grammar, order, expected, reorder, run_first)`

Parameters are generated at import time by `_order_params()`:

- For each `(case_id, grammar, expected)` in `GRAMMAR_CASES`:
  - If the grammar has at most 4 non-terminals: use every order from
    `itertools.permutations(grammar)`.
  - Otherwise (only E13): use the declared order and the reversed order.
- Each order becomes `pytest.param(grammar, order, expected, id=f"{case_id}[{','.join(order)}]")`.
  For example `E3-dependency-chain[B,A,S]` is the bottom-up order the spec
  explicitly requires.
- That gives 51 rows. Single-non-terminal grammars give one row each.

Test body: assert `run_first(reorder(grammar, order)) == expected`.

### 7.2 Idempotence — `test_compute_first_set_idempotent(grammar, expected, new_grammar)`

Parametrized over `GRAMMAR_CASES`.

1. Run `g = new_grammar(grammar)`, then `g.compute_first_set()`.
2. Save `snapshot = copy.deepcopy(g.first)`.
3. Call `g.compute_first_set()` again on the same object.
4. Assert `g.first == snapshot`.

This test does not compare against `expected`. That is §6.2's job. Here it
only checks that a second call changes nothing, so an error in the first call
is not reported twice.

### 7.3 Isolation

A helper `_case(case_id)` returns the grammar of a `GRAMMAR_CASES` row.

`test_input_grammar_untouched()`:
1. Deep-copy the E4 grammar into `grammar` and save `grammar_before`.
2. Call `Grammar(grammar).compute_first_set()` directly (no `new_grammar`, so
   the checked object is the one the class received).
3. Assert `grammar == grammar_before`.

`test_instances_do_not_share_state(new_grammar)`:
1. Build `g_e4` from E4 and `g_e2` from E2.
2. Call `g_e4.compute_first_set()`.
3. Assert `g_e2.first` is still one empty set per E2 non-terminal.

Isolation also comes from how the tests are built. Every test gets its own
`Grammar` object on a grammar copy through `new_grammar` and `run_first`.

## 8. Handling failing tests (xfail)

Same approach as the lexer suite:

1. Write all tests without marks and run `pytest syntax/tests -v`.
2. For each failing test, add an xfail mark:
   - Parametrized rows: `pytest.param(..., marks=pytest.mark.xfail(reason=..., raises=<Exc>, strict=True))`.
   - Plain tests: the `@pytest.mark.xfail(...)` decorator.
   - Generated order rows (§7.1): `_order_params()` looks the generated id up in
     a module-level `KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]]`
     (id → (reason, exception type)) and attaches the mark when the id is found.
3. `raises` is the exception actually seen, usually `AssertionError` or
   `KeyError`. Then an unrelated new error is still reported as a failure.
4. `strict=True` turns an unexpected pass into a failure (XPASS strict). When
   the code is fixed, the suite reminds you to remove the mark.
5. The `reason` text describes only the **symptom**, never the cause or a
   fix. For example "FIRST(S) is missing c" or "KeyError on terminal y". This
   keeps the strategy neutral, as agreed for the spec.
6. List every marked test in §10 below and keep the list up to date.

## 9. Keeping the plan in sync

- Before changing any test, re-read `grammar.py` and compare it with this plan
  (`syntax/AGENTS.md`).
- If a function is added, removed, renamed, or its signature changes, update
  spec.md, this plan and the tests together. For example, `is_non_terminal`
  might gain a `non_terminals_set` parameter, or a new helper might be
  extracted from `first_of_sequence`. A new function gets its own unit-test
  section. A removed function's tests are deleted.
- When a known failure is fixed, remove its xfail mark and its line in §10.
- Out of scope: the inputs listed in spec §7. No tests are written for them.

## 10. Known failures

Format: test id — symptom — expected exception.

_None._ First full run on 2026-10-16: 93 passed, 0 failed. After the move to the
`Grammar` class, run on 2026-10-20: 109 passed, 0 failed. No test carries an
xfail mark and `KNOWN_FAILURES` is empty. If a later change to `grammar.py` makes
a test fail, add it here and mark it as described in §8.
