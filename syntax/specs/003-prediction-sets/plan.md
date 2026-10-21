# Plan 003 — Implementing the prediction set tests

This plan turns the strategy in [`spec.md`](spec.md) into a technical design
for pytest. It describes files, helpers, data tables, test functions and how
failures are handled. It does not contain the test code itself.

## 1. Goal and code under test

Implement the tests described in spec 003 against the `Grammar` class in
`syntax/grammar.py`:

| Member | Signature | Effect |
|---|---|---|
| `__init__` | `(self, grammar: dict[str, list[list[str]]])` | Among other state (tested by specs 001 and 002), sets `self.predict = {nt: [] for nt in grammar}` |
| `compute_predict_set` | `(self) -> None` | Fills `self.predict` in place: `predict[A][i]` is the prediction set of `grammar[A][i]`. Only reads `self.grammar`, `self.first` and `self.follow`. |
| `get_predict_set` | `(self) -> dict[str, list[set[str]]]` | Returns `self.predict` |

`compute_predict_set` uses `first_of_sequence` internally. That method is
already unit-tested by spec 001, so it gets no new tests here.
`check_LL1_condition` is out of scope (§9).

`grammar.py` and `main.py` are not modified by the agent (see `syntax/AGENTS.md`).

## 2. File layout and dependencies

```
syntax/
├── grammar.py
├── main.py
├── specs/003-prediction-sets/{spec.md, plan.md}
└── tests/
    ├── conftest.py           # extended with prediction helpers (existing helpers unchanged)
    ├── test_first_set.py     # unchanged
    ├── test_follow_set.py    # unchanged
    └── test_predict_set.py   # data tables + all tests of this spec
```

- Run with `pytest syntax/tests -v` from the repository root, or `pytest tests -v`
  from `syntax/`. As in 001 §2, run the lexer suite **separately**, because
  both folders contain a `main.py`.
- No new dependency. `pytest-timeout` was already installed for spec 002
  (see 002 plan §2).

## 3. `conftest.py` additions

The existing helpers (`_new_grammar`, `_reorder`, `_run_first`,
`_follow_grammar`, `_run_follow`) and their fixtures stay exactly as they are.
New code follows the same pattern: private helper functions, each exposed
through a fixture that returns the function. No test imports `main` any more,
so `conftest.py` only imports `Grammar`.

| Helper | Signature | Behavior |
|---|---|---|
| `_predict_grammar` | `(grammar, first_preset, follow_preset) -> Grammar` | 1. If both presets are dicts (P case): `g = _follow_grammar(grammar, first_preset)`, then `g.follow.update(copy.deepcopy(follow_preset))`. 2. If both are `None` (E case): `g = _follow_grammar(grammar, None)`, which copies the grammar and computes FIRST, then `g.compute_follow_set()`. Returns `g`, ready for `compute_predict_set`. |
| `_run_predict` | `(grammar, first_preset, follow_preset) -> dict[str, list[set[str]]]` | `g = _predict_grammar(...)`, then `g.compute_predict_set()`, then returns `g.get_predict_set()`. |

The deep copies make sure that if the code under test changes the grammar or
the given sets, the change can't leak into other rows that share the same table
entry. Reusing `_follow_grammar` keeps one single way of computing FIRST for
the pipeline rows. `_run_predict` reads the result through the getter, so every
test that uses it also exercises `get_predict_set`.

Fixtures: `predict_grammar` and `run_predict`, each returning the matching
helper. The order tests reuse the existing `reorder` fixture unchanged, and the
initial-state test reuses `new_grammar`.

## 4. Shared constants in `test_predict_set.py`

```python
EPS = "ε"
END = "$"
PROBE = "<probe>"
pytestmark = pytest.mark.timeout(2)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}
```

- Every grammar, preset and expected set uses `EPS` and `END` instead of the
  literal symbols.
- `PROBE` is a token that appears in no grammar. The independence test (§7.4)
  adds it to `predict` entries.
- `pytestmark` applies the 2-second limit to every test in the file (spec §6,
  Termination), as in 002.
- `KNOWN_FAILURES` is described in §8.

## 5. Data table — `PREDICT_CASES`

`PREDICT_CASES` is a list of plain tuples
`(case_id, grammar, first_preset, follow_preset, expected)`. It is not a list
of `pytest.param`, because several tests reuse it to build their own
parameters.

- **P rows** have dict presets with the correct FIRST and FOLLOW sets, written
  by hand (spec §4).
- **E rows** have `first_preset = follow_preset = None`. `_predict_grammar` then
  computes both (spec §5).
- `expected` maps each non-terminal to a **list** of sets, one per production,
  in production order.
- In every grammar the start symbol is the **first key**.

### 5.1 P rows (spec §4)

| case_id | grammar | first_preset | follow_preset | expected |
|---|---|---|---|---|
| `P1-single-terminal` | `{"S": [["a"]]}` | `{"S": {"a"}}` | `{"S": {END}}` | `{"S": [{"a"}]}` |
| `P2-terminal-led` | `{"S": [["a","B"],["b"]], "B": [["c"]]}` | `{"S": {"a","b"}, "B": {"c"}}` | `{"S": {END}, "B": {END}}` | `{"S": [{"a"},{"b"}], "B": [{"c"}]}` |
| `P3-epsilon-gets-follow` | `{"S": [["A","b"]], "A": [["a"],[EPS]]}` | `{"S": {"a","b"}, "A": {"a",EPS}}` | `{"S": {END}, "A": {"b"}}` | `{"S": [{"a","b"}], "A": [{"a"},{"b"}]}` |
| `P4-start-epsilon-dollar` | `{"S": [["a","S"],[EPS]]}` | `{"S": {"a",EPS}}` | `{"S": {END}}` | `{"S": [{"a"},{END}]}` |
| `P5-non-nullable-hides-rest` | `{"S": [["A","b"]], "A": [["a"]]}` | `{"S": {"a"}, "A": {"a"}}` | `{"S": {END}, "A": {"b"}}` | `{"S": [{"a"}], "A": [{"a"}]}` |
| `P6-rest-not-follow-of-symbol` | `{"S": [["A","B"],["x","A","d"]], "A": [["a"],[EPS]], "B": [["b"]]}` | `{"S": {"a","b","x"}, "A": {"a",EPS}, "B": {"b"}}` | `{"S": {END}, "A": {"b","d"}, "B": {END}}` | `{"S": [{"a","b"},{"x"}], "A": [{"a"},{"b","d"}], "B": [{"b"}]}` |
| `P7-long-nullable-prefix` | `{"S": [["A","B","c"]], "A": [["a"],[EPS]], "B": [["b"],[EPS]]}` | `{"S": {"a","b","c"}, "A": {"a",EPS}, "B": {"b",EPS}}` | `{"S": {END}, "A": {"b","c"}, "B": {"c"}}` | `{"S": [{"a","b","c"}], "A": [{"a"},{"b","c"}], "B": [{"b"},{"c"}]}` |
| `P8-all-nullable-adds-follow` | `{"S": [["T","z"]], "T": [["A","B"]], "A": [["a"],[EPS]], "B": [["b"],[EPS]]}` | `{"S": {"a","b","z"}, "T": {"a","b",EPS}, "A": {"a",EPS}, "B": {"b",EPS}}` | `{"S": {END}, "T": {"z"}, "A": {"b","z"}, "B": {"z"}}` | `{"S": [{"a","b","z"}], "T": [{"a","b","z"}], "A": [{"a"},{"b","z"}], "B": [{"b"},{"z"}]}` |
| `P9-indirectly-nullable` | `{"S": [["A","x"]], "A": [["B"],["y"]], "B": [["b"],[EPS]]}` | `{"S": {"b","y","x"}, "A": {"b","y",EPS}, "B": {"b",EPS}}` | `{"S": {END}, "A": {"x"}, "B": {"x"}}` | `{"S": [{"b","y","x"}], "A": [{"b","x"},{"y"}], "B": [{"b"},{"x"}]}` |
| `P10-nullable-start` | `{"S": [["E","F"]], "E": [[EPS]], "F": [["f"],[EPS]]}` | `{"S": {"f",EPS}, "E": {EPS}, "F": {"f",EPS}}` | `{"S": {END}, "E": {"f",END}, "F": {END}}` | `{"S": [{"f",END}], "E": [{"f",END}], "F": [{"f"},{END}]}` |
| `P11-left-recursion` | `{"E": [["E","+","T"],["T"]], "T": [["id"]]}` | `{"E": {"id"}, "T": {"id"}}` | `{"E": {END,"+"}, "T": {END,"+"}}` | `{"E": [{"id"},{"id"}], "T": [{"id"}]}` |
| `P12-common-prefix` | `{"S": [["a","b"],["a","c"]]}` | `{"S": {"a"}}` | `{"S": {END}}` | `{"S": [{"a"},{"a"}]}` |
| `P13-epsilon-follow-overlap` | `{"S": [["A","a"]], "A": [["a"],[EPS]]}` | `{"S": {"a"}, "A": {"a",EPS}}` | `{"S": {END}, "A": {"a"}}` | `{"S": [{"a"}], "A": [{"a"},{"a"}]}` |
| `P14-identical-productions` | `{"S": [["a"],["a"]]}` | `{"S": {"a"}}` | `{"S": {END}}` | `{"S": [{"a"},{"a"}]}` |
| `P15-lua-like` | `{"Chunk": [["Block"]], "Block": [["Stat","Block"],[EPS]], "Stat": [["if","Exp","then","Block","end"],["Name","=","Exp"]], "Exp": [["Name"],["Number"]]}` | `{"Chunk": {"if","Name",EPS}, "Block": {"if","Name",EPS}, "Stat": {"if","Name"}, "Exp": {"Name","Number"}}` | `{"Chunk": {END}, "Block": {END,"end"}, "Stat": {"if","Name",END,"end"}, "Exp": {"then","if","Name",END,"end"}}` | `{"Chunk": [{"if","Name",END}], "Block": [{"if","Name"},{END,"end"}], "Stat": [{"if"},{"Name"}], "Exp": [{"Name"},{"Number"}]}` |
| `P16-unreachable-empty-set` | `{"S": [["a"]], "U": [["u"],[EPS]]}` | `{"S": {"a"}, "U": {"u",EPS}}` | `{"S": {END}, "U": set()}` | `{"S": [{"a"}], "U": [{"u"},set()]}` |
| `P17-production-order` | `{"S": [["c"],["a"],["b"],[EPS]]}` | `{"S": {"a","b","c",EPS}}` | `{"S": {END}}` | `{"S": [{"c"},{"a"},{"b"},{END}]}` |
| `P18-terminal-ends-scan` | `{"S": [["a","A"]], "A": [["b"],[EPS]]}` | `{"S": {"a"}, "A": {"b",EPS}}` | `{"S": {END}, "A": {END}}` | `{"S": [{"a"}], "A": [{"b"},{END}]}` |

### 5.2 E rows (spec §5)

| case_id | grammar | presets | expected |
|---|---|---|---|
| `E1-main-grammar` | `{"A": [["B","C"],["ant","A","all"]], "B": [["big","C"],["bus","A","boss"],[EPS]], "C": [["cat"],["cow"]]}` | `None, None` | `{"A": [{"big","bus","cat","cow"},{"ant"}], "B": [{"big"},{"bus"},{"cat","cow"}], "C": [{"cat"},{"cow"}]}` |
| `E2-expression-grammar` | `{"E": [["T","E'"]], "E'": [["+","T","E'"],[EPS]], "T": [["F","T'"]], "T'": [["*","F","T'"],[EPS]], "F": [["(","E",")"],["id"]]}` | `None, None` | `{"E": [{"(","id"}], "E'": [{"+"},{END,")"}], "T": [{"(","id"}], "T'": [{"*"},{"+",END,")"}], "F": [{"("},{"id"}]}` |
| `E3-commented-grammar` | `{"S": [["A","B","C"]], "A": [["a"],[EPS]], "B": [["b"],[EPS]], "C": [["c"]]}` | `None, None` | `{"S": [{"a","b","c"}], "A": [{"a"},{"b","c"}], "B": [{"b"},{"c"}], "C": [{"c"}]}` |
| `E4-lua-like-pipeline` | same grammar as `P15-lua-like` | `None, None` | same expected as `P15-lua-like` |

E4 reuses P15's grammar and expected objects (looked up by id after the list
is built), so the two can never drift apart.

All grammars, presets and expected sets must match `spec.md` §4 and §5
exactly. If one of them changes, update both files. They were cross-checked
against an independent reference computation when the spec was written.

### 5.3 Parameter helpers

- `_case_params(test_name, kind=None) -> list`: turns `PREDICT_CASES` into
  `pytest.param(grammar, first_preset, follow_preset, expected, id=case_id, marks=...)`.
  - `kind="P"` keeps only rows whose id starts with `P`, `kind="E"` only those
    starting with `E`, and `None` keeps all 22.
  - The marks come from `KNOWN_FAILURES` (see §8), looked up with the key
    `f"{test_name}::{case_id}"`.
- `_order_params() -> list`: see §7.5.

## 6. Main tests — exact prediction sets (spec §4, §5)

### 6.0 Initial state and getter (spec §6)

Both are parametrized over all 22 rows; presets and `expected` are unused.

- `test_predict_starts_empty(grammar, first_preset, follow_preset, expected, new_grammar)`:
  assert `new_grammar(grammar).predict == {nt: [] for nt in grammar}`.
- `test_get_predict_set(grammar, first_preset, follow_preset, expected, predict_grammar)`:
  with `g = predict_grammar(...)`, assert `g.get_predict_set() is g.predict`,
  call `g.compute_predict_set()`, and assert it again. `is` checks that the
  getter hands out the object itself, not a copy.

### 6.1 `test_predict_rules(grammar, first_preset, follow_preset, expected, run_predict)`

Parametrized with `_case_params("test_predict_rules", "P")`, which gives 18 rows.

- Assert `run_predict(grammar, first_preset, follow_preset) == expected`.
- Comparing whole dicts compares the **lists** too, so it checks the number of
  entries, their order and each set exactly. When it fails, pytest's diff
  points at the wrong entry.

### 6.2 `test_predict_pipeline(grammar, first_preset, follow_preset, expected, run_predict)`

Parametrized with `_case_params("test_predict_pipeline", "E")`, which gives 4
rows. The body is the same as 6.1. FIRST and FOLLOW are computed for real.

There are two functions so that the spec's split stays visible in pytest output.
A failure only in `test_predict_pipeline` points at how the three methods
work together.

## 7. Property tests (spec §3, §6)

Each test is parametrized over all 22 rows with `_case_params("<test name>")`,
unless stated otherwise. `expected` is unused in all of them: exact sets are
the main tests' job.

### 7.1 `test_predict_shape(grammar, first_preset, follow_preset, expected, run_predict)`

1. `predict = run_predict(grammar, first_preset, follow_preset)`.
2. Assert `set(predict) == set(grammar)`.
3. For each non-terminal, assert `len(predict[A]) == len(grammar[A])`. The
   message names A and both lengths.
4. Assert every entry is a `set`. The message lists `(A, i, type name)` for
   the entries that are not.

### 7.2 `test_predict_contents(grammar, first_preset, follow_preset, expected, run_predict)`

1. `predict = run_predict(...)`.
2. `offenders = [(A, i, sym) for A, entries in predict.items() for i, entry in enumerate(entries) for sym in entry if sym == EPS or sym in grammar]`.
3. Assert `offenders == []`. The message lists them: the non-terminal, the
   production index and the bad symbol.

### 7.3 `test_inputs_are_read_only(grammar, first_preset, follow_preset, expected, predict_grammar)`

1. `g = predict_grammar(grammar, first_preset, follow_preset)`.
2. `snapshot = copy.deepcopy((g.grammar, g.first, g.follow))`.
3. `g.compute_predict_set()`.
4. Assert `(g.grammar, g.first, g.follow) == snapshot`.

For E rows the snapshot is taken **after** FIRST and FOLLOW are computed, so
only the prediction call is checked.

### 7.4 `test_predict_independent_of_inputs(grammar, first_preset, follow_preset, expected, predict_grammar)`

Checks the spec §6 property "Output independent of inputs".

1. `g = predict_grammar(...)`.
2. `g.compute_predict_set()`.
3. `snapshot = copy.deepcopy((g.first, g.follow))`.
4. For every entry of every `g.predict[A]`: `entry.add(PROBE)`.
5. Assert `(g.first, g.follow) == snapshot`. When it fails, the message names
   the non-terminals whose FIRST or FOLLOW gained `PROBE`.

This test checks behavior, not object identity. It doesn't care how the
method builds its sets, only that changing them can't reach the inputs. If
an entry is not a set, `add` raises. `test_predict_shape` then shows the real
symptom.

### 7.5 Order independence — `test_predict_is_order_independent(grammar, first_preset, follow_preset, order, expected, reorder, run_predict)`

Parameters are generated at import time by `_order_params()`, using the same
rule as 002 §7.4:

- `start, *rest = tuple(grammar)`. The start key **always stays first**.
- If the grammar has at most 4 non-terminals: use `(start, *p)` for every `p`
  in `itertools.permutations(rest)`. Otherwise (E2, which has 5): use `rest`
  as declared and reversed.
- `reorder` only changes the order of the **keys**. Each non-terminal keeps
  its list of productions as is, so `expected` stays valid.
- Each order becomes
  `pytest.param(grammar, first_preset, follow_preset, order, expected, id=f"{case_id}[{','.join(order)}]")`,
  with marks from `KNOWN_FAILURES` under
  `f"test_predict_is_order_independent::{id}"`.

Rows per case (they come from (n − 1)! for up to 4 non-terminals, otherwise 2):

| Rows | Cases |
|---|---|
| 1 | P1, P2, P3, P4, P5, P11, P12, P13, P14, P16, P17, P18 |
| 2 | P6, P7, P9, P10, E1, E2 |
| 6 | P8, P15, E3, E4 |

Total: 12 + 12 + 24 = **48 rows**.

Test body: assert `run_predict(reorder(grammar, order), first_preset, follow_preset) == expected`.

### 7.6 Same result on fresh runs — `test_predict_same_on_fresh_runs(grammar, first_preset, follow_preset, expected, predict_grammar)`

1. `g_1 = predict_grammar(...)` and `g_2 = predict_grammar(...)`, from the
   same row.
2. `g_1.compute_predict_set()`, then `g_2.compute_predict_set()`.
3. Assert `g_1.predict == g_2.predict`.

Calling it a second time on the same object, whose `predict` is already
filled, is out of scope (spec §7), so it is not tested.

### 7.7 Isolation

A helper `_case(case_id)` returns the grammar of a `PREDICT_CASES` row.

`test_input_grammar_untouched()`:
1. Deep-copy the `E1-main-grammar` grammar into `grammar` and save
   `grammar_before`.
2. Build `Grammar(grammar)` directly (no `new_grammar`, so the checked object
   is the one the class received), then run `compute_first_set()`,
   `compute_follow_set()` and `compute_predict_set()`.
3. Assert `grammar == grammar_before`.

`test_instances_do_not_share_state(predict_grammar)`:
1. Build `g_e1` from E1 and `g_e2` from E2, both with FIRST and FOLLOW
   computed.
2. Call `g_e1.compute_predict_set()`.
3. Assert `g_e2.predict` is still one empty list per E2 non-terminal.

As in 001 and 002, isolation also comes from how the tests are built. Every
test gets its own `Grammar` object on a grammar copy through `predict_grammar`
and `run_predict`.

### 7.8 Expected collection count

| Test | Rows |
|---|---|
| `test_predict_starts_empty` | 22 |
| `test_get_predict_set` | 22 |
| `test_predict_rules` | 18 |
| `test_predict_pipeline` | 4 |
| `test_predict_shape` | 22 |
| `test_predict_contents` | 22 |
| `test_inputs_are_read_only` | 22 |
| `test_predict_independent_of_inputs` | 22 |
| `test_predict_is_order_independent` | 48 |
| `test_predict_same_on_fresh_runs` | 22 |
| `test_input_grammar_untouched` | 1 |
| `test_instances_do_not_share_state` | 1 |
| **Total in `test_predict_set.py`** | **226** |

Together with the 109 FIRST tests and the 204 FOLLOW tests,
`pytest syntax/tests --collect-only -q` lists 539 tests.

## 8. Handling failing tests (xfail)

The approach is the same as in 002 §8:

1. Write all tests without marks and run `pytest syntax/tests -v`.
2. For each failing parametrized test, add an entry to `KNOWN_FAILURES`,
   keyed `"<test function>::<param id>"`, for example
   `"test_predict_rules::P6-rest-not-follow-of-symbol"`. `_case_params` and
   `_order_params` attach
   `pytest.mark.xfail(reason=..., raises=..., strict=True)` from it. The
   isolation tests use the `@pytest.mark.xfail(...)` decorator instead.
3. `raises` is the exception actually seen: usually `AssertionError`,
   sometimes `KeyError`, `IndexError` or `AttributeError`. A timeout raises
   `pytest.fail.Exception`; 002 §8 confirmed that this works with xfail.
4. `strict=True` turns an unexpected pass into a failure (XPASS strict).
5. The `reason` describes only the **symptom**, never the cause or a fix. For
   example "prediction set of S → A B contains d" or "changing predict
   changes FOLLOW(A)".
6. List every marked test in §10 below and keep the list up to date.

## 9. Keeping the plan in sync

- Before changing any test, re-read `grammar.py` and compare it with this plan
  (`syntax/AGENTS.md`).
- If `compute_predict_set` is renamed or its signature changes, update
  spec.md, this plan and the tests together. The same applies if the output
  format changes from a list of sets, or a helper is extracted from it, which
  would get its own unit-test section.
- The E rows depend on `first_of_sequence`, `compute_first_set` and
  `compute_follow_set`. When any of them changes, re-run all three suites.
- An LL(1) conflict check or parse-table function is out of scope here. If
  one is added, it gets its own spec. `Grammar.check_LL1_condition` now
  exists and has no spec or tests yet.
- When a known failure is fixed, remove its `KNOWN_FAILURES` entry or
  decorator and its line in §10.
- Out of scope: the inputs listed in spec §7. No tests are written for them.

## 10. Known failures

Format: test id — symptom — expected exception.

None. On the first full run (2026-10-19), all 181 prediction tests passed
against the current `compute_predict_set`, which builds each entry from
`first_of_sequence`. After the move to the `Grammar` class, run on
2026-10-20: 226 prediction tests passed (539 in the whole suite).
`KNOWN_FAILURES` is empty and the isolation tests have no xfail decorator.
