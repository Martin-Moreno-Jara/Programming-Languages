# Plan 002 — Implementing the FOLLOW set tests

This plan turns the strategy in [`spec.md`](spec.md) into a technical design
for pytest. It describes files, helpers, data tables, test functions and how
failures are handled. It does not contain the test code itself.

## 1. Goal and code under test

Implement the tests described in spec 002 against the `Grammar` class in
`syntax/grammar.py`:

| Member | Signature | Effect |
|---|---|---|
| `__init__` | `(self, grammar: dict[str, list[list[str]]])` | Among other state (tested by spec 001), sets `self.follow = {nt: set() for nt in grammar}` |
| `compute_follow_set` | `(self) -> None` | Fills `self.follow` for every non-terminal, in place. Only reads `self.first`. The first key of `self.grammar` is the start symbol. |

`compute_follow_set` calls `first_of_sequence` internally. That method is
already unit-tested by spec 001, so it gets no new tests here.

`grammar.py` and `main.py` are not modified by the agent (see `syntax/AGENTS.md`).

## 2. File layout and dependencies

```
syntax/
├── grammar.py
├── main.py
├── specs/002-follow-set/{spec.md, plan.md}
└── tests/
    ├── conftest.py          # extended with FOLLOW helpers (FIRST helpers unchanged)
    ├── test_first_set.py    # unchanged
    └── test_follow_set.py   # data tables + all tests of this spec
```

- Run with `pytest syntax/tests -v` from the repository root, or `pytest tests -v`
  from `syntax/`. As in 001 §2, run the lexer suite **separately**, because
  both folders contain a `main.py`.
- **New dev dependency: `pytest-timeout`.** Install it in the project venv with
  `venv/bin/pip install pytest-timeout`, and list it in `syntax/AGENTS.md`
  under Dependencies.
- If the plugin is missing, pytest only warns about an unknown `timeout` mark
  and runs with **no** time limit. A test that never returns would then hang
  the suite. §9 explains how to check the plugin is installed.

## 3. `conftest.py` additions

The existing `_new_grammar`, `_reorder` and `_run_first` helpers (spec 001)
and their fixtures stay exactly as they are, so the FIRST suite is not
affected. New code follows the same pattern: private helper functions, each
exposed through a fixture that returns the function.

| Helper | Signature | Behavior |
|---|---|---|
| `_follow_grammar` | `(grammar, first_preset) -> Grammar` | 1. `g = _new_grammar(grammar)` (deep copy of the grammar). 2. If `first_preset` is a dict (F case): `g.first.update(copy.deepcopy(first_preset))`. If it is `None` (E case): `g.compute_first_set()`. Returns `g`, ready for `compute_follow_set`. |
| `_run_follow` | `(grammar, first_preset) -> dict[str, set[str]]` | `g = _follow_grammar(grammar, first_preset)`, then `g.compute_follow_set()`, then returns `g.follow`. |

The deep copies make sure that if the code under test changes the grammar or
the given FIRST sets, the change can't leak into other rows that share the same
table entry.

Fixtures: `follow_grammar` and `run_follow`, each returning the matching helper.
The order tests reuse the existing `reorder` fixture unchanged, and the
initial-state test reuses `new_grammar`.

## 4. Shared constants in `test_follow_set.py`

```python
EPS = "ε"
END = "$"
pytestmark = pytest.mark.timeout(2)
```

- Every grammar, FIRST preset and expected set uses `EPS` and `END` instead of
  the literal symbols, to avoid copy/paste mistakes.
- `pytestmark` applies a 2-second limit to **every** test in this file
  (spec §6, Termination). Being a module-level mark, it needs no pytest config
  file and doesn't affect the FIRST or lexer suites. A correct run takes
  milliseconds, so 2 seconds only catches calls that never return.

## 5. Data table — `FOLLOW_CASES`

`FOLLOW_CASES` is a list of plain tuples
`(case_id, grammar, first_preset, expected)`. It is not a list of
`pytest.param`, because several tests reuse it to build their own parameters
(see §7).

- **F rows** have a dict `first_preset` with the correct FIRST sets written by
  hand (spec §4).
- **E rows** have `first_preset = None`. `_follow_grammar` then computes FIRST
  with `compute_first_set` (spec §5).
- In every grammar the start symbol is the **first key**.

### 5.1 F rows (spec §4)

| case_id | grammar | first_preset | expected |
|---|---|---|---|
| `F1-start-only` | `{"S": [["a"]]}` | `{"S": {"a"}}` | `{"S": {END}}` |
| `F2-terminal-after-nt` | `{"S": [["A","b"]], "A": [["a"]]}` | `{"S": {"a"}, "A": {"a"}}` | `{"S": {END}, "A": {"b"}}` |
| `F3-nt-at-end` | `{"S": [["a","A"]], "A": [["b"]]}` | `{"S": {"a"}, "A": {"b"}}` | `{"S": {END}, "A": {END}}` |
| `F4-non-nullable-next` | `{"S": [["A","B"]], "A": [["a"]], "B": [["b"]]}` | `{"S": {"a"}, "A": {"a"}, "B": {"b"}}` | `{"S": {END}, "A": {"b"}, "B": {END}}` |
| `F5-skip-nullable` | `{"S": [["A","B","c"]], "A": [["a"]], "B": [["b"],[EPS]]}` | `{"S": {"a"}, "A": {"a"}, "B": {"b",EPS}}` | `{"S": {END}, "A": {"b","c"}, "B": {"c"}}` |
| `F6-nullable-tail-inherits` | `{"S": [["A","B"]], "A": [["a"]], "B": [["b"],[EPS]]}` | `{"S": {"a"}, "A": {"a"}, "B": {"b",EPS}}` | `{"S": {END}, "A": {"b",END}, "B": {END}}` |
| `F7-long-nullable-tail` | `{"S": [["x","A","B","C"]], "A": [["a"]], "B": [["b"],[EPS]], "C": [["c"],[EPS]]}` | `{"S": {"x"}, "A": {"a"}, "B": {"b",EPS}, "C": {"c",EPS}}` | `{"S": {END}, "A": {"b","c",END}, "B": {"c",END}, "C": {END}}` |
| `F8-same-nt-twice` | `{"S": [["A","a","A"]], "A": [["x"]]}` | `{"S": {"x"}, "A": {"x"}}` | `{"S": {END}, "A": {"a",END}}` |
| `F9-used-in-several-rules` | `{"S": [["A","x"],["B"]], "B": [["A","y"]], "A": [["a"]]}` | `{"S": {"a"}, "B": {"a"}, "A": {"a"}}` | `{"S": {END}, "B": {END}, "A": {"x","y"}}` |
| `F10-multi-level-inherit` | `{"S": [["A","z"]], "A": [["b","B"]], "B": [["c","C"]], "C": [["d"]]}` | `{"S": {"b"}, "A": {"b"}, "B": {"c"}, "C": {"d"}}` | `{"S": {END}, "A": {"z"}, "B": {"z"}, "C": {"z"}}` |
| `F11-nested-nullable-tail` | `{"S": [["A","z"]], "A": [["B","C"]], "B": [["b"]], "C": [["c"],[EPS]]}` | `{"S": {"b"}, "A": {"b"}, "B": {"b"}, "C": {"c",EPS}}` | `{"S": {END}, "A": {"z"}, "B": {"c","z"}, "C": {"z"}}` |
| `F12-follow-cycle` | `{"S": [["A","t"]], "A": [["a","B"]], "B": [["b","A"],[EPS]]}` | `{"S": {"a"}, "A": {"a"}, "B": {"b",EPS}}` | `{"S": {END}, "A": {"t"}, "B": {"t"}}` |
| `F13-start-on-rhs` | `{"S": [["(","S",")"],["x"]]}` | `{"S": {"(","x"}}` | `{"S": {END,")"}}` |
| `F14-start-gains-from-deep` | `{"S": [["A"]], "A": [["b","S","c"],["d"]]}` | `{"S": {"b","d"}, "A": {"b","d"}}` | `{"S": {END,"c"}, "A": {END,"c"}}` |
| `F15-unreachable-nt` | `{"S": [["a"]], "U": [["u"]]}` | `{"S": {"a"}, "U": {"u"}}` | `{"S": {END}, "U": set()}` |
| `F16-epsilon-only-tail` | `{"S": [["A","E"]], "A": [["a"]], "E": [[EPS]]}` | `{"S": {"a"}, "A": {"a"}, "E": {EPS}}` | `{"S": {END}, "A": {END}, "E": {END}}` |
| `F17-left-recursion` | `{"E": [["E","+","T"],["T"]], "T": [["id"]]}` | `{"E": {"id"}, "T": {"id"}}` | `{"E": {END,"+"}, "T": {END,"+"}}` |
| `F18-self-at-end` | `{"L": [["x","L"],[EPS]]}` | `{"L": {"x",EPS}}` | `{"L": {END}}` |
| `F19-nt-followed-by-itself` | `{"S": [["A","A"]], "A": [["a"],[EPS]]}` | `{"S": {"a",EPS}, "A": {"a",EPS}}` | `{"S": {END}, "A": {"a",END}}` |
| `F20-lua-like` | `{"Chunk": [["Block"]], "Block": [["Stat","Block"],[EPS]], "Stat": [["if","Exp","then","Block","end"],["Name","=","Exp"]], "Exp": [["Name"],["Number"]]}` | `{"Chunk": {"if","Name",EPS}, "Block": {"if","Name",EPS}, "Stat": {"if","Name"}, "Exp": {"Name","Number"}}` | `{"Chunk": {END}, "Block": {END,"end"}, "Stat": {"if","Name",END,"end"}, "Exp": {"then","if","Name",END,"end"}}` |

### 5.2 E rows (spec §5)

| case_id | grammar | first_preset | expected |
|---|---|---|---|
| `E1-main-grammar` | `{"A": [["B","C"],["ant","A","all"]], "B": [["big","C"],["bus","A","boss"],[EPS]], "C": [["cat"],["cow"]]}` | `None` | `{"A": {END,"all","boss"}, "B": {"cat","cow"}, "C": {END,"all","boss","cat","cow"}}` |
| `E2-expression-grammar` | `{"E": [["T","E'"]], "E'": [["+","T","E'"],[EPS]], "T": [["F","T'"]], "T'": [["*","F","T'"],[EPS]], "F": [["(","E",")"],["id"]]}` | `None` | `{"E": {END,")"}, "E'": {END,")"}, "T": {"+",END,")"}, "T'": {"+",END,")"}, "F": {"*","+",END,")"}}` |
| `E3-indirect-nullable-tail` | `{"S": [["A","B","C"]], "A": [["a"]], "B": [["D"]], "D": [["d"],[EPS]], "C": [["c"],[EPS]]}` | `None` | `{"S": {END}, "A": {"d","c",END}, "B": {"c",END}, "C": {END}, "D": {"c",END}}` |
| `E4-lua-like-pipeline` | same grammar as `F20-lua-like` | `None` | same expected as `F20-lua-like` |

E4 should reuse F20's grammar and expected objects (look them up by id),
so the two can never drift apart.

All grammars and expected sets must match `spec.md` §4 and §5 exactly. If one
of them changes, update both files.

### 5.3 Parameter helpers

- `_case_params(test_name, kind=None) -> list`: turns `FOLLOW_CASES` into
  `pytest.param(grammar, first_preset, expected, id=case_id, marks=...)`.
  - `kind="F"` keeps only rows whose id starts with `F`, `kind="E"` only those
    starting with `E`, and `None` keeps all 24.
  - The marks come from `KNOWN_FAILURES` (see §8), looked up with the key
    `f"{test_name}::{case_id}"`.
- `_order_params() -> list`: see §7.4.

## 6. Main tests — exact FOLLOW sets (spec §4, §5)

### 6.0 `test_follow_starts_empty(grammar, first_preset, expected, new_grammar)`

Parametrized over all 24 rows with `_case_params("test_follow_starts_empty")`.
Assert `new_grammar(grammar).follow == {nt: set() for nt in grammar}`.
`first_preset` and `expected` are unused (spec §6, Initial state).

### 6.1 `test_follow_rules(grammar, first_preset, expected, run_follow)`

Parametrized with `_case_params("test_follow_rules", "F")`, which gives 20 rows.

- Assert `run_follow(grammar, first_preset) == expected`.
- Comparing whole dicts checks exact sets for every non-terminal. When it
  fails, pytest's diff points at the wrong entry.

### 6.2 `test_follow_pipeline(grammar, first_preset, expected, run_follow)`

Parametrized with `_case_params("test_follow_pipeline", "E")`, which gives 4
rows. The body is the same as 6.1. `first_preset` is always `None` here, so
FIRST is computed for real.

There are two functions instead of one so that the spec's split stays visible
in pytest output. A failure in `test_follow_rules` is a FOLLOW problem. A
failure only in `test_follow_pipeline` points at how FIRST and FOLLOW work
together.

## 7. Property tests (spec §3, §6)

Each property is its own test, parametrized over all 24 rows with
`_case_params("<test name>")`, unless stated otherwise. A failure then names
exactly one symptom.

### 7.1 `test_follow_has_no_epsilon(grammar, first_preset, expected, run_follow)`

1. `follow = run_follow(grammar, first_preset)`.
2. `offenders = sorted(nt for nt, s in follow.items() if EPS in s)`.
3. Assert `offenders == []`. The assertion message lists the offending
   non-terminals.

`expected` is unused.

### 7.2 `test_follow_keys_are_non_terminals(grammar, first_preset, expected, run_follow)`

Assert `set(run_follow(grammar, first_preset)) == set(grammar)`. No terminal
was added as a key, and no non-terminal key is missing (F15 has a key whose set
is empty).

### 7.3 `test_first_is_read_only(grammar, first_preset, expected, follow_grammar)`

1. `g = follow_grammar(grammar, first_preset)`.
2. `snapshot = copy.deepcopy(g.first)`.
3. `g.compute_follow_set()`.
4. Assert `g.first == snapshot`.

For E rows the snapshot is taken **after** `compute_first_set`, so only the
FOLLOW call is checked.

### 7.4 Order independence — `test_follow_is_order_independent(grammar, first_preset, order, expected, reorder, run_follow)`

Parameters are generated at import time by `_order_params()`:

- For each `(case_id, grammar, first_preset, expected)` in `FOLLOW_CASES`:
  - `start, *rest = tuple(grammar)`. The start key **always stays first**.
  - If the grammar has at most 4 non-terminals: use `(start, *p)` for every `p`
    in `itertools.permutations(rest)`.
  - Otherwise (E2 and E3, which have 5 each): use `rest` as declared and
    reversed.
- Each order becomes
  `pytest.param(grammar, first_preset, order, expected, id=f"{case_id}[{','.join(order)}]")`,
  with marks from `KNOWN_FAILURES` under
  `f"test_follow_is_order_independent::{id}"`.
- `F10-multi-level-inherit[S,A,B,C]` (top-down) and
  `F10-multi-level-inherit[S,C,B,A]` (bottom-up) are the orders the spec
  explicitly requires. Both come out of the permutations.

Rows per case (they come from (n − 1)! for up to 4 non-terminals, otherwise 2):

| Rows | Cases |
|---|---|
| 1 | F1, F2, F3, F8, F13, F14, F15, F17, F18, F19 |
| 2 | F4, F5, F6, F9, F12, F16, E1, E2, E3 |
| 6 | F7, F10, F11, F20, E4 |

Total: 10 + 18 + 30 = **58 rows**.

`first_preset` is a dict, so its key order doesn't matter. Only the grammar is
reordered.

Test body: assert `run_follow(reorder(grammar, order), first_preset) == expected`.

### 7.5 Idempotence — `test_compute_follow_set_idempotent(grammar, first_preset, expected, follow_grammar)`

1. `g = follow_grammar(grammar, first_preset)`.
2. `g.compute_follow_set()`.
3. `snapshot = copy.deepcopy(g.follow)`.
4. Call `g.compute_follow_set()` again on the same object.
5. Assert `g.follow == snapshot`.

This test does not compare against `expected`, so an error in the first call
is not reported twice.

### 7.6 Isolation

A helper `_case(case_id)` returns the grammar of a `FOLLOW_CASES` row.

`test_input_grammar_untouched()`:
1. Deep-copy the `E1-main-grammar` grammar into `grammar` and save
   `grammar_before`.
2. Build `Grammar(grammar)` directly (no `new_grammar`, so the checked object
   is the one the class received), then call `compute_first_set()` and
   `compute_follow_set()`.
3. Assert `grammar == grammar_before`.

`test_instances_do_not_share_state(follow_grammar)`:
1. Build `g_e1` from E1 and `g_e2` from E2, both with FIRST computed.
2. Call `g_e1.compute_follow_set()`.
3. Assert `g_e2.follow` is still one empty set per E2 non-terminal.

As in 001, isolation also comes from how the tests are built. Every test gets
its own `Grammar` object on a grammar copy through `follow_grammar` and
`run_follow`.

### 7.7 Expected collection count

| Test | Rows |
|---|---|
| `test_follow_starts_empty` | 24 |
| `test_follow_rules` | 20 |
| `test_follow_pipeline` | 4 |
| `test_follow_has_no_epsilon` | 24 |
| `test_follow_keys_are_non_terminals` | 24 |
| `test_first_is_read_only` | 24 |
| `test_follow_is_order_independent` | 58 |
| `test_compute_follow_set_idempotent` | 24 |
| `test_input_grammar_untouched` | 1 |
| `test_instances_do_not_share_state` | 1 |
| **Total in `test_follow_set.py`** | **204** |

## 8. Handling failing tests (xfail)

The approach is the same as in 001 §8:

1. Write all tests without marks and run `pytest syntax/tests -v`.
2. For each failing test, add an entry to the module-level
   `KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]]`. It maps
   `"<test function>::<param id>"` to `(reason, exception type)`, for example
   `"test_follow_rules::F6-nullable-tail-inherits"`.
   - `_case_params` and `_order_params` look the key up and attach
     `pytest.mark.xfail(reason=..., raises=..., strict=True)`. Every
     parametrized test then uses one shared mechanism.
   - The non-parametrized isolation tests use the `@pytest.mark.xfail(...)`
     decorator instead.
3. `raises` is the exception actually seen. It is usually `AssertionError` or
   `KeyError`. A test stopped by the time limit fails through `pytest.fail`,
   so its exception type is `pytest.fail.Exception`. Confirmed on 2026-10-17
   with a throwaway probe test: a timed-out test marked
   `xfail(raises=pytest.fail.Exception, strict=True)` is reported as XFAIL,
   and the same test with `raises=AssertionError` is reported as FAILED.
4. `strict=True` turns an unexpected pass into a failure (XPASS strict), so
   the suite reminds you to remove the mark once the code is fixed.
5. The `reason` describes only the **symptom**, never the cause or a fix. For
   example "FOLLOW(A) is missing $", "FOLLOW(B) contains ε" or
   "compute_follow_set does not return".
6. List every marked test in §10 below and keep the list up to date.

## 9. Keeping the plan in sync

- Before changing any test, re-read `grammar.py` and compare it with this plan
  (`syntax/AGENTS.md`).
- If `compute_follow_set` is renamed or its signature changes, update spec.md,
  this plan and the tests together. The same applies if a helper is extracted
  from it, which would get its own unit-test section. A removed function's
  tests are deleted.
- `first_of_sequence` is shared with spec 001. If it changes, re-run both
  suites.
- Check that the time limit is active: `venv/bin/pip show pytest-timeout`
  must find the package, and the header of a `pytest -v` run must list
  `timeout` among the plugins.
- When a known failure is fixed, remove its `KNOWN_FAILURES` entry or
  decorator and its line in §10.
- Out of scope: the inputs listed in spec §7. No tests are written for them.

## 10. Known failures

Format: test id — symptom — expected exception.

_None._ First full run on 2026-10-17: 272 passed (179 FOLLOW + 93 FIRST),
0 failed, no timeouts. After the move to the `Grammar` class, run on
2026-10-20: 204 FOLLOW tests passed, 0 failed, no timeouts. No test carries an
xfail mark and `KNOWN_FAILURES` is empty. If a later change to `grammar.py`
makes a test fail, add it here and mark it as described in §8.

While the suite was being written, an earlier version of `compute_follow_set`
failed 6 F rows: F6, F7, F11, F16, F19 and F20. Their symptoms were missing
`$`/`end`/`z` and an extra ε in some FOLLOW sets. That version was replaced
before the first full run, so no marks were added for it.
