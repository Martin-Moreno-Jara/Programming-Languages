# Tasks 003 — Prediction set tests

Each task below becomes one piece of setup, one test function, or one row of a
parametrized test. Tick the box when it is written and behaves as described.

**Legend**
- `conftest.py::name` / `test_predict_set.py::name`: the file (in
  `syntax/tests/`) and the function, fixture or constant to write.
- **row**: one `pytest.param` in a data table. Its `id` is shown in backticks.
- Inputs and expected values are **not** repeated here. They live in
  [`plan.md`](plan.md) §5.1 (P rows) and §5.2 (E rows), which are copied from
  [`spec.md`](spec.md) §4 and §5. If a value changes, edit spec.md and plan.md,
  not this file.
- **xfail**: a test that fails against the current `grammar.py` gets an entry in
  `KNOWN_FAILURES` under `"<test function>::<param id>"`, which becomes
  `xfail(reason=<symptom>, raises=<exception>, strict=True)`. See section 11.

## 1. Setup (plan §2–§4)
- [x] Check that `pytest-timeout` is still installed: `venv/bin/pip show pytest-timeout`, and `timeout` is listed in the pytest header.
- [x] Create `syntax/tests/test_predict_set.py`. Don't add an `__init__.py`.
- [x] `conftest.py::_predict_grammar(grammar, first_preset, follow_preset)`:
  - With dict presets: `_follow_grammar(grammar, first_preset)`, then deep-copy the FOLLOW preset into `g.follow`.
  - With `None, None`: `_follow_grammar(grammar, None)`, then `g.compute_follow_set()`.
  - Return the Grammar.
- [x] `conftest.py::_run_predict(grammar, first_preset, follow_preset)`: calls `_predict_grammar`, then `g.compute_predict_set()`, and returns `g.get_predict_set()`.
- [x] `conftest.py`: add fixtures `predict_grammar` and `run_predict`, each returning the matching helper.
- [x] `conftest.py`: remove the functional-API helpers (`_fresh`, `_follow_inputs`, `_predict_inputs`) and the `main` import, now that no suite uses them.
- [x] Check that the FIRST (109) and FOLLOW (204) suites still pass.
- [x] `test_predict_set.py`: import `copy`, `itertools`, `pytest` and `Grammar`.
- [x] `test_predict_set.py::EPS = "ε"`, `END = "$"` and `PROBE = "<probe>"`.
- [x] `test_predict_set.py::pytestmark = pytest.mark.timeout(2)`.
- [x] `test_predict_set.py::KNOWN_FAILURES`: a dict mapping `"<test function>::<param id>"` to `(reason, exception type)`. It starts empty.
- [x] `test_predict_set.py::_case_params(test_name, kind=None)`: turns `PREDICT_CASES` into `pytest.param(grammar, first_preset, follow_preset, expected, id=case_id)`.
  - `kind="P"` or `"E"` filters rows by id prefix. `None` keeps all 22.
  - Attach an xfail mark when `f"{test_name}::{case_id}"` is in `KNOWN_FAILURES`.
- [x] Check collection: `pytest syntax/tests/test_predict_set.py --collect-only -q` lists 226 tests (2×22 + 18 + 4 + 4×22 + 48 + 22 + 2). `pytest syntax/tests --collect-only -q` lists 539.

## 2. Data table (plan §5)
- [x] `test_predict_set.py::PREDICT_CASES`: a list of plain tuples `(case_id, grammar, first_preset, follow_preset, expected)`.
  - P rows have dict presets. E rows have `None, None`.
  - `expected` maps each non-terminal to a list of sets in production order.
  - The start symbol is always the first key.
- [x] Write `E4-lua-like-pipeline` so it reuses the grammar and expected objects of `P15-lua-like` instead of a copy.
- [x] Check that the 22 ids are unique and match plan.md §5 exactly.
- [x] Cross-check every grammar, preset and expected list against spec.md §4/§5, row by row.

## 3. Main tests: P rows (plan §6.1)
- [x] `test_predict_set.py::test_predict_rules`: parametrized with `_case_params("test_predict_rules", "P")`. Assert `run_predict(grammar, first_preset, follow_preset) == expected`, comparing the whole dict, lists included.
- [x] Row `P1-single-terminal`: a single terminal production.
- [x] Row `P2-terminal-led`: productions that start with a terminal predict only that terminal.
- [x] Row `P3-epsilon-gets-follow`: an ε production predicts FOLLOW of its left side.
- [x] Row `P4-start-epsilon-dollar`: the start symbol's ε production predicts $.
- [x] Row `P5-non-nullable-hides-rest`: a non-nullable leading non-terminal hides the rest, so `b` must not appear.
- [x] Row `P6-rest-not-follow-of-symbol`: after a nullable first symbol, the scan uses the rest of the production, not FOLLOW of that symbol, so `d` must not appear.
- [x] Row `P7-long-nullable-prefix`: a long nullable prefix ending in a terminal, so FOLLOW(S) is not added.
- [x] Row `P8-all-nullable-adds-follow`: a production of only nullable non-terminals adds FOLLOW of its left side.
- [x] Row `P9-indirectly-nullable`: a production that is nullable only through another non-terminal.
- [x] Row `P10-nullable-start`: $ appears in the set of a production that is not `["ε"]`.
- [x] Row `P11-left-recursion`: not LL(1). The overlapping sets are still computed.
- [x] Row `P12-common-prefix`: not LL(1), a common prefix.
- [x] Row `P13-epsilon-follow-overlap`: not LL(1). An ε production's FOLLOW overlaps a sibling's FIRST.
- [x] Row `P14-identical-productions`: two identical productions get one entry each.
- [x] Row `P15-lua-like`: a Lua-like grammar where multi-character terminals are single symbols.
- [x] Row `P16-unreachable-empty-set`: an unused non-terminal's ε production predicts an empty set, and the entry is still there.
- [x] Row `P17-production-order`: entries follow production order.
- [x] Row `P18-terminal-ends-scan`: a leading terminal ends the scan even when the rest is nullable, so `$` must not appear.

## 4. Main tests: E rows (plan §6.2)
- [x] `test_predict_set.py::test_predict_pipeline`: parametrized with `_case_params("test_predict_pipeline", "E")`. Same body as `test_predict_rules`. FIRST and FOLLOW are computed for real.
- [x] Row `E1-main-grammar`: the grammar currently in `main.py` (data only, `main` is not imported).
- [x] Row `E2-expression-grammar`: the classic E/E'/T/T'/F grammar, with primed keys.
- [x] Row `E3-commented-grammar`: the grammar commented out in `main.py`.
- [x] Row `E4-lua-like-pipeline`: the P15 grammar with FIRST and FOLLOW computed instead of written by hand.

## 5. Shape and contents (plan §7.1–§7.2)
- [x] `test_predict_set.py::test_predict_shape`: parametrized with `_case_params("test_predict_shape")`.
  1. Assert the keys equal the grammar's non-terminals.
  2. Assert each `predict[A]` has one entry per production. The message names A and both lengths.
  3. Assert every entry is a `set`. The message lists `(A, i, type name)`.
- [x] Check that it runs once for each of the 22 rows.
- [x] `test_predict_set.py::test_predict_contents`: parametrized with `_case_params("test_predict_contents")`. Collect `(A, i, symbol)` for every symbol that is `EPS` or a non-terminal, and assert the list is empty. The message lists them.
- [x] Check that it runs once for each of the 22 rows.

## 6. Inputs unchanged (plan §7.3)
- [x] `test_predict_set.py::test_inputs_are_read_only`: parametrized with `_case_params("test_inputs_are_read_only")`.
  1. Call `predict_grammar`.
  2. Snapshot `(g.grammar, g.first, g.follow)`. For E rows this happens after FIRST and FOLLOW are computed.
  3. Call `g.compute_predict_set()`.
  4. Assert the three are unchanged.
- [x] Check that it runs once for each of the 22 rows.

## 7. Output independent of inputs (plan §7.4)
- [x] `test_predict_set.py::test_predict_independent_of_inputs`: parametrized with `_case_params("test_predict_independent_of_inputs")`.
  1. Call `predict_grammar` and `g.compute_predict_set()`.
  2. Snapshot `(g.first, g.follow)`.
  3. Add `PROBE` to every entry of every `g.predict[A]`.
  4. Assert `(g.first, g.follow)` are unchanged. The message names the non-terminals whose FIRST or FOLLOW gained `PROBE`.
- [x] Check that it runs once for each of the 22 rows.

## 8. Order independence (plan §7.5)
- [x] `test_predict_set.py::_order_params()`: generates the order rows.
  - Keep the start key first.
  - Use every permutation of the other keys when the grammar has at most 4 non-terminals. Otherwise use them as declared and reversed.
  - Never reorder the productions inside a non-terminal.
  - Ids look like `f"{case_id}[{','.join(order)}]"`.
  - Attach an xfail mark when `f"test_predict_is_order_independent::{id}"` is in `KNOWN_FAILURES`.
- [x] `test_predict_set.py::test_predict_is_order_independent`: assert `run_predict(reorder(grammar, order), first_preset, follow_preset) == expected`.
- [x] P1 rows: 1 order.
- [x] P2 rows: 1 order.
- [x] P3 rows: 1 order.
- [x] P4 rows: 1 order.
- [x] P5 rows: 1 order.
- [x] P6 rows: 2 orders.
- [x] P7 rows: 2 orders.
- [x] P8 rows: 6 orders.
- [x] P9 rows: 2 orders.
- [x] P10 rows: 2 orders.
- [x] P11 rows: 1 order.
- [x] P12 rows: 1 order.
- [x] P13 rows: 1 order.
- [x] P14 rows: 1 order.
- [x] P15 rows: 6 orders.
- [x] P16 rows: 1 order.
- [x] P17 rows: 1 order.
- [x] P18 rows: 1 order.
- [x] E1 rows: 2 orders.
- [x] E2 rows: 2 orders, declared and reversed (it has 5 non-terminals).
- [x] E3 rows: 6 orders.
- [x] E4 rows: 6 orders.
- [x] Check that no generated order moves the start key away from the first position.
- [x] Check that `test_predict_set.py` produces 48 order rows. `-k order_independent` also matches the FIRST and FOLLOW order tests, so count only the lines from this file.

## 9. Same result on fresh runs (plan §7.6)
- [x] `test_predict_set.py::test_predict_same_on_fresh_runs`: parametrized with `_case_params("test_predict_same_on_fresh_runs")`.
  1. Call `predict_grammar` twice on the same row.
  2. Call `compute_predict_set()` on each object.
  3. Assert the two `predict` dicts are equal.
- [x] Check that it runs once for each of the 22 rows.

## 10. Isolation (plan §7.7)
- [x] `test_predict_set.py::test_input_grammar_untouched`: the full pipeline with `Grammar(grammar)` on a copy of E1 leaves that dict unchanged.
- [x] `test_predict_set.py::test_instances_do_not_share_state`: computing the prediction sets on an E1 object leaves an E2 object's `predict` empty.
- [x] Review that every test builds its own `Grammar` object on a grammar copy.

## 11. First run and xfail workflow (plan §8)
- [x] Run `pytest syntax/tests -v` with no marks, and save the list of failing ids with their exception types.
- [x] Add a `KNOWN_FAILURES` entry for each failing parametrized row: main, shape, contents, inputs, independence, order and fresh-run tests.
- [x] Add the `@pytest.mark.xfail(...)` decorator if an isolation test fails.
- [x] Check that every `reason` describes only the **symptom** (e.g. "prediction set of S → A B contains d", "changing predict changes FOLLOW(A)"), never the cause or a fix.
- [x] Check that every `raises` is the exception actually seen (`AssertionError`, `KeyError`, `IndexError`, `AttributeError`, `pytest.fail.Exception`, …) and that every mark has `strict=True`.
- [x] List every marked test in plan.md §10 as `id — symptom — exception`.
- [x] Rerun. Expect only passes and xfails: no failures, no errors, no XPASS.
- [x] Check that the FIRST (109) and FOLLOW (204) suites still all pass.

## 12. Maintenance (recurring)
- [ ] Before editing any test, re-read `grammar.py` and compare it with plan.md (AGENTS.md).
- [ ] When `compute_predict_set` is renamed, changes signature, changes its output format or gets a helper extracted from it, update spec.md, plan.md, this file and the tests in the same change. A new function gets its own unit-test section, and a removed one has its tests deleted.
- [ ] When `first_of_sequence`, `compute_first_set` or `compute_follow_set` change, re-run all three suites.
- [ ] When a bug is fixed and its test turns XPASS (strict), remove its `KNOWN_FAILURES` entry or decorator and its plan.md §10 line.
- [ ] Don't add tests for the out-of-scope inputs in spec §7, including LL(1) disjointness checks, unless the spec is updated first.
