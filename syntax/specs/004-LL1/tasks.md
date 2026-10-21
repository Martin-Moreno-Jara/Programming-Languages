# Tasks 004 — LL(1) condition tests

Each task below becomes one piece of setup, one test function, or one row of a
parametrized test. Tick the box when it is written and behaves as described.

**Legend**
- `conftest.py::name` / `test_ll1_condition.py::name`: the file (in
  `syntax/tests/`) and the function, fixture or constant to write.
- **row**: one `pytest.param` in a data table. Its `id` is shown in backticks.
- Inputs and expected values are **not** repeated here. They live in
  [`plan.md`](plan.md) §5.1 (L rows), §5.2 (N rows) and §5.3 (E rows), which
  are copied from [`spec.md`](spec.md) §4 and §5. If a value changes, edit
  spec.md and plan.md, not this file.
- **xfail**: a test that fails against the current `grammar.py` gets an entry in
  `KNOWN_FAILURES` under `"<test function>::<param id>"`, which becomes
  `xfail(reason=<symptom>, raises=<exception>, strict=True)`. See section 12.

## 1. Setup (plan §2–§4)
_Done on 2026-10-20. The collection check was ticked after section 11: 264 in the file, 803 in total._

- [x] Check that `pytest-timeout` is still installed: `venv/bin/pip show pytest-timeout`, and `timeout` is listed in the pytest header.
- [x] Create `syntax/tests/test_ll1_condition.py`. Don't add an `__init__.py`.
- [x] `conftest.py::_ll1_grammar(predict_preset)`:
  - Build the placeholder grammar `{A: [["_"] for _ in sets] for A, sets in predict_preset.items()}`, with the same keys in the same order.
  - Call `g = _new_grammar(grammar)`.
  - Deep-copy the preset into `g.predict` with `g.predict.update(...)`.
  - Return `g`.
- [x] `conftest.py`: add the fixture `ll1_grammar`, returning the helper.
- [x] Check that the existing helpers and fixtures are unchanged, and that the 539 existing tests (109 FIRST + 204 FOLLOW + 226 prediction) still pass.
- [x] `test_ll1_condition.py`: import `copy`, `itertools` and `pytest`.
- [x] `test_ll1_condition.py::EPS = "ε"` and `END = "$"`.
- [x] `test_ll1_condition.py::pytestmark = pytest.mark.timeout(2)`.
- [x] `test_ll1_condition.py::KNOWN_FAILURES`: a dict mapping `"<test function>::<param id>"` to `(reason, exception type)`. It starts empty.
- [x] Check collection: `pytest tests/test_ll1_condition.py --collect-only -q` lists 264 tests (9 + 10 + 8 + 4×27 + 74 + 54 + 1). `pytest tests --collect-only -q` lists 803.

## 2. Data table (plan §5)
_Done on 2026-10-20. A throwaway script checked the ids, the row shapes, every expected value against the pairwise definition, and that E1–E4 equal the spec 003 grammars._

- [x] `test_ll1_condition.py::LL1_CASES`: a list of plain tuples `(case_id, grammar, predict_preset, expected)`.
  - L and N rows: `grammar = None` and a dict `predict_preset` (a list of sets per non-terminal).
  - E rows: a dict `grammar` and `predict_preset = None`.
- [x] Write the 9 L rows, the 10 N rows and the 8 E rows with the ids of plan §5.1–§5.3.
- [x] Use `END` for `$` and `EPS` for ε everywhere, and `set()` (not `{}`) for empty prediction sets.
- [x] Copy the E grammars into this file. Don't import them from `test_predict_set.py`. The start symbol is always the first key.
- [x] Check that the 27 ids are unique and match plan.md §5 exactly.
- [x] Cross-check every preset, grammar and expected value against spec.md §4/§5, row by row.

## 3. Build and reference helpers (plan §5.4)
_Done on 2026-10-20. A throwaway script confirmed the `_case_params` counts (9/10/8/27), that marks are attached from `KNOWN_FAILURES`, and that `_pairwise_ll1` on each object built by `_build` equals `expected` for all 27 rows._

- [x] `test_ll1_condition.py::_case_params(test_name, kind=None)`: turns `LL1_CASES` into `pytest.param(grammar, predict_preset, expected, id=case_id)`.
  - `kind="L"`, `"N"` or `"E"` filters rows by id prefix. `None` keeps all 27.
  - Attach an xfail mark when `f"{test_name}::{case_id}"` is in `KNOWN_FAILURES`.
- [x] `test_ll1_condition.py::_build(grammar, predict_preset, ll1_grammar, predict_grammar)`:
  - With a dict preset: return `ll1_grammar(predict_preset)`.
  - Otherwise: `g = predict_grammar(grammar, None, None)`, then `g.compute_predict_set()`, then return `g`.
- [x] `test_ll1_condition.py::_pairwise_ll1(predict)`: returns `True` iff every pair from `itertools.combinations(predict[A], 2)` is disjoint, for every A. It must not reuse the cumulative approach of `grammar.py`.
- [x] Sanity check before relying on the reference: `_pairwise_ll1` gives the row's `expected` on every L and N preset, and on every E row's computed `predict`.

## 4. Main tests: LL(1) grammars (plan §6.1)
_Done on 2026-10-20: all 9 rows pass against the current `grammar.py`._

- [x] `test_ll1_condition.py::test_ll1_accepts`: parametrized with `_case_params("test_ll1_accepts", "L")`. Build with `_build`, then assert `g.check_LL1_condition() is True`.
- [x] Row `L1-single-production`: a single production can't conflict.
- [x] Row `L2-two-disjoint`: two disjoint productions.
- [x] Row `L3-many-disjoint-with-end`: many disjoint productions, one of them predicting `$`.
- [x] Row `L4-multi-token-sets`: disjoint sets with several tokens each.
- [x] Row `L5-same-token-other-nt`: the same token in different non-terminals is not a conflict.
- [x] Row `L6-empty-set`: an empty prediction set next to a non-empty one.
- [x] Row `L7-two-empty-sets`: two empty sets never overlap.
- [x] Row `L8-whole-string-tokens`: `=` vs `==` and `end` vs `End` are different tokens.
- [x] Row `L9-lua-like`: four non-terminals, all checked and all disjoint.

## 5. Main tests: non-LL(1) grammars (plan §6.2)
_Done on 2026-10-20: all 10 rows pass against the current `grammar.py`._

- [x] `test_ll1_condition.py::test_ll1_rejects`: parametrized with `_case_params("test_ll1_rejects", "N")`. Build with `_build`, then assert `g.check_LL1_condition() is False`.
- [x] Row `N1-identical`: two identical sets.
- [x] Row `N2-partial-overlap`: overlap on a single token.
- [x] Row `N3-subset`: one set contained in the other.
- [x] Row `N4-only-end`: the only shared token is `$`.
- [x] Row `N5-first-and-third`: conflict between the 1st and 3rd sets, with a clean set in between.
- [x] Row `N6-second-and-third`: conflict only between the 2nd and 3rd sets.
- [x] Row `N7-conflict-in-last-nt`: the conflict is only in the last non-terminal.
- [x] Row `N8-conflict-in-first-nt`: the conflict is only in the first non-terminal.
- [x] Row `N9-several-conflicts`: conflicts in more than one non-terminal.
- [x] Row `N10-empty-does-not-hide`: an empty set doesn't hide the conflict between the other two.

## 6. Main tests: full pipeline (plan §6.3)
_Done on 2026-10-20: all 8 rows pass against the current `grammar.py` (4 True, 4 False)._

- [x] `test_ll1_condition.py::test_ll1_pipeline`: parametrized with `_case_params("test_ll1_pipeline", "E")`. Build with `_build` (runs FIRST → FOLLOW → predict), then assert `g.check_LL1_condition() is expected`.
- [x] Row `E1-expression-grammar`: textbook LL(1) grammar, `True`.
- [x] Row `E2-lua-like-pipeline`: the L9 grammar computed for real, `True`.
- [x] Row `E3-main-grammar`: the grammar in `main.py`, `True`.
- [x] Row `E4-nullable-no-conflict`: nullable productions whose FOLLOW sets don't collide, `True`.
- [x] Row `E5-left-recursion`: `False`.
- [x] Row `E6-common-prefix`: `False`.
- [x] Row `E7-epsilon-conflict`: the ε production's FOLLOW collides with a sibling, `False`.
- [x] Row `E8-dangling-else`: `S' → ε` predicts {e, $} and collides with `S' → e S`, `False`.

## 7. Result type, read-only and repeatable (plan §7.1–§7.3)
_Done on 2026-10-20: 27 rows each, all 81 pass against the current `grammar.py`._

- [x] `test_ll1_condition.py::test_result_is_bool`: parametrized with `_case_params("test_result_is_bool")`. Assert `type(result) is bool`. The message shows the type returned.
- [x] `test_ll1_condition.py::test_check_is_read_only`: parametrized with `_case_params("test_check_is_read_only")`.
  1. Build with `_build`.
  2. Snapshot `(g.grammar, g.first, g.follow, g.predict)`. For E rows this happens after the pipeline.
  3. Call `g.check_LL1_condition()`.
  4. Assert the four are unchanged.
- [x] `test_ll1_condition.py::test_check_is_repeatable`: parametrized with `_case_params("test_check_is_repeatable")`. Call the check twice on the same object and assert both results are equal.
- [x] Check that each of the three runs once for each of the 27 rows.

## 8. Pairwise reference (plan §7.4)
_Done on 2026-10-20: 27 rows pass._

- [x] `test_ll1_condition.py::test_matches_pairwise_reference`: parametrized with `_case_params("test_matches_pairwise_reference")`.
  1. Assert `_pairwise_ll1(g.predict) is expected`, with a message saying the table value disagrees with the definition.
  2. Assert `g.check_LL1_condition() is _pairwise_ll1(g.predict)`, with a message saying the check disagrees with the reference.
- [x] Check that the two assertions have different messages, so a failure tells a table mistake apart from a bug in the check.
- [x] Check that it runs once for each of the 27 rows.

## 9. Order of non-terminals (plan §7.5)
_Done on 2026-10-20: 74 rows pass. A throwaway script checked every per-case count below, that the two required ids exist, and that no E order moves the start key._

- [x] `test_ll1_condition.py::_order_params()`: generates the order rows.
  - L and N rows: every permutation of **all** keys of `predict_preset`.
  - E rows: keep the start key first. Use every permutation of the rest when the grammar has at most 4 non-terminals. Otherwise use the rest as declared and reversed.
  - Ids look like `f"{case_id}[{','.join(order)}]"`.
  - Attach an xfail mark when `f"test_nonterminal_order_independent::{id}"` is in `KNOWN_FAILURES`.
- [x] `test_ll1_condition.py::test_nonterminal_order_independent`:
  - L/N rows: build with `ll1_grammar(reorder(predict_preset, order))`.
  - E rows: build with `_build(reorder(grammar, order), None, ...)`.
  - Assert the result `is expected`.
- [x] L1, L2, L3, L4 rows: 1 order each.
- [x] L5, L6, L7, L8 rows: 2 orders each.
- [x] L9 rows: 24 orders.
- [x] N1, N2, N3, N4, N5, N6 rows: 1 order each.
- [x] N7 rows: 6 orders. These must include `N7-conflict-in-last-nt[B,A,S]`, where the conflicting non-terminal comes first.
- [x] N8 rows: 2 orders. These must include `N8-conflict-in-first-nt[A,S]`, where the conflicting non-terminal comes last.
- [x] N9 rows: 2 orders.
- [x] N10 rows: 1 order.
- [x] E1 rows: 2 orders, declared and reversed (it has 5 non-terminals).
- [x] E2 rows: 6 orders.
- [x] E3 rows: 2 orders.
- [x] E4 rows: 6 orders.
- [x] E5, E6, E7 rows: 1 order each.
- [x] E8 rows: 2 orders.
- [x] Check that no generated E order moves the start key away from the first position.
- [x] Check that `test_ll1_condition.py` produces 74 order rows (36 L + 17 N + 21 E). `-k order_independent` also matches the other suites, so count only the lines from this file.

## 10. Order of productions (plan §7.6)
_Done on 2026-10-20: 54 rows pass. The variants live in a `PRODUCTION_ORDERS` dict (name → list function), which the test applies._

- [x] `test_ll1_condition.py::_production_order_params()`: two variants per row, `reversed` (`list(reversed(x))`) and `rotated` (`x[1:] + x[:1]`).
  - L and N rows: apply the variant to every `predict_preset[A]`.
  - E rows: apply the variant to every production list `grammar[A]`. Keep the order of the keys.
  - Ids look like `f"{case_id}[{variant}]"`.
  - Attach an xfail mark when `f"test_production_order_independent::{id}"` is in `KNOWN_FAILURES`.
- [x] `test_ll1_condition.py::test_production_order_independent`: L/N rows build with `ll1_grammar`, and E rows with `_build`, which runs the pipeline again. Assert the result `is expected`.
- [x] Check that `N5-first-and-third[rotated]` gives `[{b}, {a}, {a}]` and `N6-second-and-third[rotated]` gives `[{b}, {b,c}, {a}]`, so the conflicting pair moves.
- [x] Check that it produces 54 rows (27 × 2).

## 11. Isolation (plan §7.7)
_Done on 2026-10-20: passes. Rows are looked up with a small `_preset(case_id)` helper._

- [x] `test_ll1_condition.py::test_instances_do_not_share_state`:
  1. Build `g_n1` from `N1-identical` and `g_l2` from `L2-two-disjoint`, and snapshot `g_l2.predict`.
  2. Call `g_n1.check_LL1_condition()`.
  3. Assert `g_l2.check_LL1_condition() is True` and that `g_l2.predict` is unchanged.
- [x] Review that every test builds its own `Grammar` object on deep copies, through `ll1_grammar`, `predict_grammar` or `_build`.

## 12. First run and xfail workflow (plan §8)
- [ ] Run `pytest tests -v` with no marks, and save the list of failing ids with their exception types.
- [ ] For every failing test that times out, confirm the exception is `pytest.fail.Exception` before using it as `raises`.
- [ ] Add a `KNOWN_FAILURES` entry for each failing parametrized row: main, property, non-terminal order and production order tests.
- [ ] Add the `@pytest.mark.xfail(...)` decorator if the isolation test fails.
- [ ] Check that every `reason` describes only the **symptom** (e.g. "N5-first-and-third reported as LL(1)", "returns int instead of bool"), never the cause or a fix.
- [ ] Check that every `raises` is the exception actually seen (`AssertionError`, `pytest.fail.Exception`, …) and that every mark has `strict=True`.
- [ ] List every marked test in plan.md §10 as `id — symptom — exception`, and record the run date and result.
- [ ] Rerun. Expect only passes and xfails: no failures, no errors, no XPASS.
- [ ] Check that the FIRST (109), FOLLOW (204) and prediction (226) suites still all pass.

## 13. Maintenance (recurring)
- [ ] Before editing any test, re-read `grammar.py` and compare it with plan.md (AGENTS.md).
- [ ] When `check_LL1_condition` is renamed, changes signature or starts reporting conflicts, update spec.md, plan.md, this file and the tests in the same change.
- [ ] When `compute_first_set`, `compute_follow_set` or `compute_predict_set` changes, re-run all four suites.
- [ ] Keep the copied E grammars in `LL1_CASES` equal to spec.md §5 and plan.md §5.3.
- [ ] When a bug is fixed and its test turns XPASS (strict), remove its `KNOWN_FAILURES` entry or decorator and its plan.md §10 line.
- [ ] Don't add tests for the out-of-scope inputs in spec §7 unless the spec is updated first.
- [ ] After setting up a new environment, check again that `pytest-timeout` is installed. Without it there is no time limit.
