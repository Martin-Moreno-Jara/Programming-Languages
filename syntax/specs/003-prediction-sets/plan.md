# Plan 003 — Implementing the prediction set tests

This plan turns the strategy in [`spec.md`](spec.md) into a technical design
for pytest. It describes files, helpers, data tables, test functions and how
failures are handled. It does not contain the test code itself.

## 1. Goal and code under test

Implement the tests described in spec 003 against `syntax/main.py`:

| Function | Signature | Effect |
|---|---|---|
| `compute_predict_set` | `(grammar: dict[str, list[list[str]]], predict: dict[str, list[set[str]]], first: dict[str, set[str]], follow: dict[str, set[str]], non_terminals_set: set[str]) -> None` | Fills `predict` in place: `predict[A][i]` is the prediction set of `grammar[A][i]`. Only reads `grammar`, `first` and `follow`. |

`compute_predict_set` may use `first_of_sequence` internally. That function is
already unit-tested by spec 001, so it gets no new tests here. Arguments are
passed by position, so renaming a parameter in `main.py` doesn't break tests.

`main.py` is not modified by the agent (see `syntax/AGENTS.md`).

## 2. File layout and dependencies

```
syntax/
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

The existing helpers (`_fresh`, `_reorder`, `_run_first`, `_follow_inputs`,
`_run_follow`) and their fixtures stay exactly as they are. New code follows
the same pattern: private helper functions, each exposed through a fixture that
returns the function.

```python
from main import compute_first_set, compute_follow_set, compute_predict_set  # noqa: E402
```

| Helper | Signature | Behavior |
|---|---|---|
| `_predict_inputs` | `(grammar, first_preset, follow_preset) -> tuple[grammar, first, follow, predict, non_terminals_set]` | 1. If both presets are dicts (P case): `g = copy.deepcopy(grammar)`, `first = copy.deepcopy(first_preset)`, `follow = copy.deepcopy(follow_preset)`, `non_terminals_set = set(g)`. 2. If both are `None` (E case): `g, first, follow, non_terminals_set = _follow_inputs(grammar, None)`, which copies the grammar and computes FIRST, then `compute_follow_set(g, first, follow, non_terminals_set)`. 3. In both cases `predict = {nt: [] for nt in g}`. Returns all five, ready for a call. |
| `_run_predict` | `(grammar, first_preset, follow_preset) -> dict[str, list[set[str]]]` | `g, first, follow, predict, nts = _predict_inputs(...)`, then `compute_predict_set(g, predict, first, follow, nts)`, then returns `predict`. |

The deep copies make sure that if the code under test changes the grammar or
the given sets, the change can't leak into other rows that share the same table
entry. Reusing `_follow_inputs` keeps one single way of computing FIRST for
the pipeline rows.

Fixtures: `predict_inputs` and `run_predict`, each returning the matching
helper. The order tests reuse the existing `reorder` fixture unchanged.

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
- **E rows** have `first_preset = follow_preset = None`. `_predict_inputs` then
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
A failure only in `test_predict_pipeline` points at how the three functions
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

### 7.3 `test_inputs_are_read_only(grammar, first_preset, follow_preset, expected, predict_inputs)`

1. `g, first, follow, predict, nts = predict_inputs(grammar, first_preset, follow_preset)`.
2. `snapshot = copy.deepcopy((g, first, follow))`.
3. `compute_predict_set(g, predict, first, follow, nts)`.
4. Assert `(g, first, follow) == snapshot`.

For E rows the snapshot is taken **after** FIRST and FOLLOW are computed, so
only the prediction call is checked.

### 7.4 `test_predict_independent_of_inputs(grammar, first_preset, follow_preset, expected, predict_inputs)`

Checks the spec §6 property "Output independent of inputs".

1. `g, first, follow, predict, nts = predict_inputs(...)`.
2. `compute_predict_set(g, predict, first, follow, nts)`.
3. `snapshot = copy.deepcopy((first, follow))`.
4. For every entry of every `predict[A]`: `entry.add(PROBE)`.
5. Assert `(first, follow) == snapshot`. When it fails, the message names the
   non-terminals whose FIRST or FOLLOW gained `PROBE`.

This test checks behavior, not object identity. It doesn't care how the
function builds its sets, only that changing them can't reach the inputs. If
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

### 7.6 Same result on fresh runs — `test_predict_same_on_fresh_runs(grammar, first_preset, follow_preset, expected, predict_inputs)`

1. `g, first, follow, predict_1, nts = predict_inputs(...)`.
2. `predict_2 = {nt: [] for nt in g}`.
3. `compute_predict_set(g, predict_1, first, follow, nts)`, then
   `compute_predict_set(g, predict_2, first, follow, nts)`. Both use the
   **same** input objects.
4. Assert `predict_1 == predict_2`.

Calling it a second time on an already-filled `predict` is out of scope
(spec §7), so it is not tested.

### 7.7 Isolation — `test_module_globals_untouched(run_predict)`

1. Run `import main` and save deep copies of `main.grammar`, `main.first`,
   `main.follow`, `main.predict` and `main.non_terminals_set`.
2. Call `run_predict` on the `E1-main-grammar` row, which runs the full
   pipeline.
3. Assert the five globals are equal to their saved copies.

As in 001 and 002, isolation also comes from how the tests are built. Every
test gets its own copies through `predict_inputs` and `run_predict`, and no
test writes to module-level state.

### 7.8 Expected collection count

| Test | Rows |
|---|---|
| `test_predict_rules` | 18 |
| `test_predict_pipeline` | 4 |
| `test_predict_shape` | 22 |
| `test_predict_contents` | 22 |
| `test_inputs_are_read_only` | 22 |
| `test_predict_independent_of_inputs` | 22 |
| `test_predict_is_order_independent` | 48 |
| `test_predict_same_on_fresh_runs` | 22 |
| `test_module_globals_untouched` | 1 |
| **Total in `test_predict_set.py`** | **181** |

Together with the 93 FIRST tests and the 179 FOLLOW tests,
`pytest syntax/tests --collect-only -q` lists 453 tests.

## 8. Handling failing tests (xfail)

The approach is the same as in 002 §8:

1. Write all tests without marks and run `pytest syntax/tests -v`.
2. For each failing parametrized test, add an entry to `KNOWN_FAILURES`,
   keyed `"<test function>::<param id>"`, for example
   `"test_predict_rules::P6-rest-not-follow-of-symbol"`. `_case_params` and
   `_order_params` attach
   `pytest.mark.xfail(reason=..., raises=..., strict=True)` from it. The
   isolation test uses the `@pytest.mark.xfail(...)` decorator instead.
3. `raises` is the exception actually seen: usually `AssertionError`,
   sometimes `KeyError`, `IndexError` or `AttributeError`. A timeout raises
   `pytest.fail.Exception`; 002 §8 confirmed that this works with xfail.
4. `strict=True` turns an unexpected pass into a failure (XPASS strict).
5. The `reason` describes only the **symptom**, never the cause or a fix. For
   example "prediction set of S → A B contains d" or "changing predict
   changes FOLLOW(A)".
6. List every marked test in §10 below and keep the list up to date.

## 9. Keeping the plan in sync

- Before changing any test, re-read `main.py` and compare it with this plan
  (`syntax/AGENTS.md`).
- If `compute_predict_set` is renamed or its signature changes, update
  spec.md, this plan and the tests together. The same applies if the output
  format changes from a list of sets, or a helper is extracted from it, which
  would get its own unit-test section.
- The E rows depend on `first_of_sequence`, `compute_first_set` and
  `compute_follow_set`. When any of them changes, re-run all three suites.
- An LL(1) conflict check or parse-table function is out of scope here. If
  one is added, it gets its own spec.
- When a known failure is fixed, remove its `KNOWN_FAILURES` entry or
  decorator and its line in §10.
- Out of scope: the inputs listed in spec §7. No tests are written for them.

## 10. Known failures

Format: test id — symptom — expected exception.

_Not run yet._ This section is filled in after the first full run (see §8).
