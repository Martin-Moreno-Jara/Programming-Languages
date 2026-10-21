# Plan 004 — Implementing the LL(1) condition tests

This plan turns the strategy in [`spec.md`](spec.md) into a technical design
for pytest. It describes files, helpers, data tables, test functions and how
failures are handled. It does not contain the test code itself.

## 1. Goal and code under test

Implement the tests described in spec 004 against the `Grammar` class in
`syntax/grammar.py`:

| Member | Signature | Effect |
|---|---|---|
| `check_LL1_condition` | `(self) -> bool` | Returns `True` iff, for every non-terminal A, the sets in `self.predict[A]` are pairwise disjoint. Only reads `self.predict`. |

The pipeline methods that fill `predict` for the E rows (`compute_first_set`,
`compute_follow_set`, `compute_predict_set`) are already tested by specs 001
to 003, so they get no new tests here.

`grammar.py` and `main.py` are not modified by the agent (see `syntax/AGENTS.md`).

## 2. File layout and dependencies

```
syntax/
├── grammar.py
├── main.py
├── specs/004-LL1/{spec.md, plan.md}
└── tests/
    ├── conftest.py             # extended with one LL(1) helper (existing helpers unchanged)
    ├── test_first_set.py       # unchanged
    ├── test_follow_set.py      # unchanged
    ├── test_predict_set.py     # unchanged
    └── test_ll1_condition.py   # data tables + all tests of this spec
```

- Run with `pytest tests -v` from `syntax/`. As in 001 §2, run the lexer suite
  **separately**.
- No new dependency. `pytest-timeout` is already installed (002 plan §2).

## 3. `conftest.py` additions

The existing helpers (`_new_grammar`, `_reorder`, `_run_first`,
`_follow_grammar`, `_run_follow`, `_predict_grammar`, `_run_predict`) and their
fixtures stay exactly as they are. One new helper follows the same pattern.

| Helper | Signature | Behavior |
|---|---|---|
| `_ll1_grammar` | `(predict_preset: dict[str, list[set[str]]]) -> Grammar` | 1. Build a placeholder grammar `{A: [["_"] for _ in sets] for A, sets in predict_preset.items()}`, with the same keys in the same order and one dummy production per set. 2. `g = _new_grammar(grammar)`. 3. `g.predict.update(copy.deepcopy(predict_preset))`. Returns `g`. |

Fixture: `ll1_grammar`, returning the helper. The E rows use the existing
`predict_grammar(grammar, None, None)` fixture, and the order tests use the
existing `reorder` fixture.

The placeholder productions are safe because the check only reads `predict`.
On L/N objects `first` and `follow` stay empty, and that doesn't affect any
test. Because the grammar is built from the preset, its keys and production
counts always match the sets (spec §4).

## 4. Shared constants in `test_ll1_condition.py`

```python
EPS = "ε"
END = "$"
pytestmark = pytest.mark.timeout(2)
KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}
```

- Every grammar, preset and expected value uses `EPS` and `END` instead of the
  literal symbols.
- `pytestmark` applies the 2-second limit to every test in the file (spec §6,
  Termination), as in 002 and 003.
- `KNOWN_FAILURES` is described in §8.

## 5. Data table — `LL1_CASES`

`LL1_CASES` is a list of plain tuples
`(case_id, grammar, predict_preset, expected)`. It is not a list of
`pytest.param`, because several tests reuse it to build their own parameters.

- **L and N rows** have `grammar = None` and a dict `predict_preset`: a list
  of sets per non-terminal, written by hand (spec §4).
- **E rows** have a dict `grammar` and `predict_preset = None`. They run the
  full pipeline (spec §5). In every E grammar the start symbol is the
  **first key**.
- `expected` is `True` or `False`.

### 5.1 L rows — LL(1), expected `True` (spec §4.1)

| case_id | predict_preset |
|---|---|
| `L1-single-production` | `{"S": [{"a"}]}` |
| `L2-two-disjoint` | `{"S": [{"a"}, {"b"}]}` |
| `L3-many-disjoint-with-end` | `{"S": [{"c"}, {"a"}, {"b"}, {END}]}` |
| `L4-multi-token-sets` | `{"S": [{"a","b","c"}, {"d","e"}]}` |
| `L5-same-token-other-nt` | `{"S": [{"a"}], "A": [{"a"}, {"b"}]}` |
| `L6-empty-set` | `{"S": [{"a"}], "U": [{"u"}, set()]}` |
| `L7-two-empty-sets` | `{"S": [{"a"}], "U": [set(), set()]}` |
| `L8-whole-string-tokens` | `{"S": [{"="}, {"=="}], "T": [{"end"}, {"End"}]}` |
| `L9-lua-like` | `{"Chunk": [{"if","Name",END}], "Block": [{"if","Name"}, {END,"end"}], "Stat": [{"if"}, {"Name"}], "Exp": [{"Name"}, {"Number"}]}` |

### 5.2 N rows — not LL(1), expected `False` (spec §4.2)

| case_id | predict_preset |
|---|---|
| `N1-identical` | `{"S": [{"a"}, {"a"}]}` |
| `N2-partial-overlap` | `{"S": [{"a","b"}, {"b","c"}]}` |
| `N3-subset` | `{"S": [{"a"}, {"a","b"}]}` |
| `N4-only-end` | `{"A": [{END}, {"a",END}]}` |
| `N5-first-and-third` | `{"S": [{"a"}, {"b"}, {"a"}]}` |
| `N6-second-and-third` | `{"S": [{"a"}, {"b"}, {"b","c"}]}` |
| `N7-conflict-in-last-nt` | `{"S": [{"x"}], "A": [{"a"}, {"b"}], "B": [{"c"}, {"c"}]}` |
| `N8-conflict-in-first-nt` | `{"S": [{"x"}, {"x"}], "A": [{"a"}, {"b"}]}` |
| `N9-several-conflicts` | `{"S": [{"a"}, {"a"}], "A": [{"b"}, {"b"}]}` |
| `N10-empty-does-not-hide` | `{"U": [set(), {"a"}, {"a"}]}` |

### 5.3 E rows — full pipeline (spec §5)

| case_id | grammar | expected |
|---|---|---|
| `E1-expression-grammar` | `{"E": [["T","E'"]], "E'": [["+","T","E'"],[EPS]], "T": [["F","T'"]], "T'": [["*","F","T'"],[EPS]], "F": [["(","E",")"],["id"]]}` | `True` |
| `E2-lua-like-pipeline` | `{"Chunk": [["Block"]], "Block": [["Stat","Block"],[EPS]], "Stat": [["if","Exp","then","Block","end"],["Name","=","Exp"]], "Exp": [["Name"],["Number"]]}` | `True` |
| `E3-main-grammar` | `{"A": [["B","C"],["ant","A","all"]], "B": [["big","C"],["bus","A","boss"],[EPS]], "C": [["cat"],["cow"]]}` | `True` |
| `E4-nullable-no-conflict` | `{"S": [["A","B","C"]], "A": [["a"],[EPS]], "B": [["b"],[EPS]], "C": [["c"]]}` | `True` |
| `E5-left-recursion` | `{"E": [["E","+","T"],["T"]], "T": [["id"]]}` | `False` |
| `E6-common-prefix` | `{"S": [["a","b"],["a","c"]]}` | `False` |
| `E7-epsilon-conflict` | `{"S": [["A","a"]], "A": [["a"],[EPS]]}` | `False` |
| `E8-dangling-else` | `{"S": [["i","E","t","S","S'"],["a"]], "S'": [["e","S"],[EPS]], "E": [["b"]]}` | `False` |

The E grammars are **copied** from the spec 003 tables, not imported from
`test_predict_set.py`, so each suite stands alone. All values must match
`spec.md` §4 and §5 exactly. If one of them changes, update both files.

### 5.4 Parameter and build helpers

- `_case_params(test_name, kind=None) -> list`: turns `LL1_CASES` into
  `pytest.param(grammar, predict_preset, expected, id=case_id, marks=...)`.
  - `kind="L"`, `"N"` or `"E"` keeps only rows whose id starts with that
    letter, and `None` keeps all 27.
  - The marks come from `KNOWN_FAILURES` (see §8), looked up with the key
    `f"{test_name}::{case_id}"`.
- `_build(grammar, predict_preset, ll1_grammar, predict_grammar) -> Grammar`:
  - if `predict_preset` is a dict: `return ll1_grammar(predict_preset)`;
  - otherwise: `g = predict_grammar(grammar, None, None)`, then
    `g.compute_predict_set()`, then return `g`.

  It is a module-level function that receives the two fixtures as arguments,
  so every test builds its object the same way.
- `_pairwise_ll1(predict) -> bool`: the reference from spec §6, "Matches the
  definition".
  `all(a.isdisjoint(b) for sets in predict.values() for a, b in itertools.combinations(sets, 2))`.
  It compares every pair directly, unlike the cumulative `check_set` in
  `grammar.py`.
- `_order_params()`: see §7.5. `_production_order_params()`: see §7.6.

## 6. Main tests — the expected answer (spec §4, §5)

### 6.1 `test_ll1_accepts(grammar, predict_preset, expected, ll1_grammar, predict_grammar)`

Parametrized with `_case_params("test_ll1_accepts", "L")`, which gives 9 rows.
`g = _build(...)`, then assert `g.check_LL1_condition() is True`.

### 6.2 `test_ll1_rejects(grammar, predict_preset, expected, ll1_grammar, predict_grammar)`

Parametrized with `_case_params("test_ll1_rejects", "N")`, which gives 10
rows. Same body, but assert `... is False`.

### 6.3 `test_ll1_pipeline(grammar, predict_preset, expected, ll1_grammar, predict_grammar)`

Parametrized with `_case_params("test_ll1_pipeline", "E")`, which gives 8 rows.
Assert `g.check_LL1_condition() is expected`.

There are three functions so that the pytest output shows what kind of failure
it is. A failure in `test_ll1_accepts` means a conflict was reported that
doesn't exist. A failure in `test_ll1_rejects` means a real conflict was
missed. A failure only in `test_ll1_pipeline` points at how the pipeline and
the check work together. `is` instead of `==` also catches results like `1` or
`0`, which §7.1 reports more clearly.

## 7. Property tests (spec §6)

Each test is parametrized over all 27 rows with `_case_params("<test name>")`,
unless stated otherwise. Each one builds its object with `_build`.

### 7.1 `test_result_is_bool`

Assert `type(g.check_LL1_condition()) is bool`. The message shows the type
actually returned.

### 7.2 `test_check_is_read_only`

1. `snapshot = copy.deepcopy((g.grammar, g.first, g.follow, g.predict))`.
2. `g.check_LL1_condition()`.
3. Assert `(g.grammar, g.first, g.follow, g.predict) == snapshot`.

For E rows the snapshot is taken after the pipeline, so only the check is
tested.

### 7.3 `test_check_is_repeatable`

Call `g.check_LL1_condition()` twice on the same object and assert the two
results are equal.

### 7.4 `test_matches_pairwise_reference`

1. Assert `_pairwise_ll1(g.predict) is expected`, with the message "table value
   disagrees with the definition". This guards the hand-written `expected`
   values and, for E rows, the computed `predict`.
2. Assert `g.check_LL1_condition() is _pairwise_ll1(g.predict)`.

If only the first assertion fails, the mistake is in the table. If only the
second fails, it's in the check.

### 7.5 Order of non-terminals — `test_nonterminal_order_independent(grammar, predict_preset, order, expected, reorder, ll1_grammar, predict_grammar)`

Parameters are generated at import time by `_order_params()`:

- **L and N rows:** every permutation of **all** keys of `predict_preset`
  (all of them have at most 4 non-terminals). These rows have no start
  symbol, so the first key can move too. That is what lets N7 and N8 put the
  conflicting non-terminal first or last. The body builds the object with
  `ll1_grammar(reorder(predict_preset, order))`.
- **E rows:** same rule as 002 §7.4 and 003 §7.5. The start key always stays
  first. Use every permutation of the rest when there are at most 4
  non-terminals, otherwise the rest as declared and reversed. The body builds
  the object with `_build(reorder(grammar, order), None, ...)`, so the
  pipeline runs again on the reordered grammar.
- Each order becomes
  `pytest.param(grammar, predict_preset, order, expected, id=f"{case_id}[{','.join(order)}]")`,
  with marks from `KNOWN_FAILURES` under
  `f"test_nonterminal_order_independent::{id}"`.
- Assert `g.check_LL1_condition() is expected`.

Rows per case:

| Rows | Cases |
|---|---|
| 1 | L1, L2, L3, L4, N1–N6, N10, E5, E6, E7 |
| 2 | L5, L6, L7, L8, N8, N9, E1, E3, E8 |
| 6 | N7, E2, E4 |
| 24 | L9 |

Total: L 36 + N 17 + E 21 = **74 rows**. The E counts were confirmed against
the current code on 2026-10-20.

### 7.6 Order of productions — `test_production_order_independent(grammar, predict_preset, variant, expected, ll1_grammar, predict_grammar)`

Parameters are generated at import time by `_production_order_params()`. Each
row gets two variants, named by `variant`:

| variant | Applied to each list `x` |
|---|---|
| `reversed` | `list(reversed(x))` |
| `rotated` | `x[1:] + x[:1]` |

The variants are kept in a module-level dict `PRODUCTION_ORDERS` (name →
function). The params carry only the name, and the test applies the function.

- **L and N rows:** apply the variant to every `predict_preset[A]`, then
  build with `ll1_grammar`.
- **E rows:** apply the variant to every production list `grammar[A]`, then
  build with `_build`, which runs the pipeline again. The order of the keys
  doesn't change, so the start symbol stays first.
- Ids look like `f"{case_id}[{variant}]"`, with marks under
  `f"test_production_order_independent::{id}"`.
- Assert `g.check_LL1_condition() is expected`.

On `N5-first-and-third`, `rotated` gives `[{b}, {a}, {a}]`, so the
conflicting pair becomes adjacent. On `N6-second-and-third`, it gives
`[{b}, {b,c}, {a}]`, so the pair moves to the front. With a single production,
both variants return the same list, and the row is still valid. All 16 E
variants were confirmed to keep their expected answer on 2026-10-20.

Total: 27 × 2 = **54 rows**.

### 7.7 Isolation — `test_instances_do_not_share_state(ll1_grammar)`

1. Build `g_n1` from `N1-identical` and `g_l2` from `L2-two-disjoint` (looked
   up with a small `_preset(case_id)` helper), and save
   `l2_before = copy.deepcopy(g_l2.predict)`.
2. Call `g_n1.check_LL1_condition()`.
3. Assert `g_l2.check_LL1_condition() is True` and `g_l2.predict == l2_before`.

Isolation also comes from how the tests are built. Every test gets its own
`Grammar` object on deep copies through `ll1_grammar` and `predict_grammar`.

### 7.8 Expected collection count

| Test | Rows |
|---|---|
| `test_ll1_accepts` | 9 |
| `test_ll1_rejects` | 10 |
| `test_ll1_pipeline` | 8 |
| `test_result_is_bool` | 27 |
| `test_check_is_read_only` | 27 |
| `test_check_is_repeatable` | 27 |
| `test_matches_pairwise_reference` | 27 |
| `test_nonterminal_order_independent` | 74 |
| `test_production_order_independent` | 54 |
| `test_instances_do_not_share_state` | 1 |
| **Total in `test_ll1_condition.py`** | **264** |

Together with the 109 FIRST, 204 FOLLOW and 226 prediction tests,
`pytest tests --collect-only -q` lists 803 tests.

## 8. Handling failing tests (xfail)

The approach is the same as in 003 §8:

1. Write all tests without marks and run `pytest tests -v`.
2. For each failing parametrized test, add an entry to `KNOWN_FAILURES`,
   keyed `"<test function>::<param id>"`, for example
   `"test_ll1_rejects::N5-first-and-third"`. `_case_params`, `_order_params`
   and `_production_order_params` attach
   `pytest.mark.xfail(reason=..., raises=..., strict=True)` from it. The
   isolation test uses the `@pytest.mark.xfail(...)` decorator instead.
3. `raises` is the exception actually seen: usually `AssertionError`. A
   timeout raises `pytest.fail.Exception`, which 002 §8 confirmed works with
   xfail.
4. `strict=True` turns an unexpected pass into a failure (XPASS strict).
5. The `reason` describes only the **symptom**, never the cause or a fix. For
   example "N5-first-and-third reported as LL(1)" or "returns int instead of
   bool".
6. List every marked test in §10 below and keep the list up to date.

## 9. Keeping the plan in sync

- Before changing any test, re-read `grammar.py` and compare it with this plan
  (`syntax/AGENTS.md`).
- If `check_LL1_condition` is renamed, changes signature, or starts reporting
  which non-terminal or tokens conflict, update spec.md, this plan and the
  tests together.
- The E rows depend on `compute_first_set`, `compute_follow_set` and
  `compute_predict_set`. When any of them changes, re-run all four suites.
- The E grammars are copies of spec 003 data. If a shared grammar changes
  there, decide whether to update it here too, and keep `spec.md` §5 equal to
  §5.3 of this plan.
- When a known failure is fixed, remove its `KNOWN_FAILURES` entry or
  decorator and its line in §10.
- Out of scope: the inputs listed in spec §7. No tests are written for them.

## 10. Known failures

Format: test id — symptom — expected exception.

None so far. The tests are not written yet, so there has been no full run.
On 2026-10-20 the eight E grammars, plus their reversed and rotated
production variants, were run through the current `Grammar` class with a
throwaway script. Every one gave the expected answer from §5.3.
