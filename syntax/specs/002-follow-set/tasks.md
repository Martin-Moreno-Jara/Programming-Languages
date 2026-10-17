# Tasks 002 — FOLLOW set tests

Each task below becomes one piece of setup, one test function, or one row of a
parametrized test. Tick the box when it is written and behaves as described.

**Legend**
- `conftest.py::name` / `test_follow_set.py::name`: the file (in `syntax/tests/`)
  and the function, fixture or constant to write.
- **row**: one `pytest.param` in a data table. Its `id` is shown in backticks.
- Inputs and expected values are **not** repeated here. They live in
  [`plan.md`](plan.md) §5.1 (F rows) and §5.2 (E rows), which are copied from
  [`spec.md`](spec.md) §4 and §5. If a value changes, edit spec.md and plan.md,
  not this file.
- **xfail**: a test that fails against the current `main.py` gets an entry in
  `KNOWN_FAILURES` under `"<test function>::<param id>"`, which becomes
  `xfail(reason=<symptom>, raises=<exception>, strict=True)`. See section 9.

## 1. Setup and dependency (plan §2–§4)
- [x] Install the plugin: `venv/bin/pip install pytest-timeout`.
- [x] Check that `venv/bin/pip show pytest-timeout` finds it and that the header of `pytest syntax/tests -v` lists `timeout` among the plugins.
- [x] Create `syntax/tests/test_follow_set.py`. Don't add an `__init__.py`.
- [x] `conftest.py`: extend the import to `from main import compute_first_set, compute_follow_set`.
- [x] `conftest.py::_follow_inputs(grammar, first_preset)`: deep-copies the grammar, builds an empty `follow` and `non_terminals_set`, then builds `first`. A dict preset is deep-copied. `None` means FIRST is computed with `_fresh` + `compute_first_set`. Returns `(grammar, first, follow, non_terminals_set)`.
- [x] `conftest.py::_run_follow(grammar, first_preset)`: calls `_follow_inputs`, then `compute_follow_set`, and returns `follow`.
- [x] `conftest.py`: add fixtures `follow_inputs` and `run_follow`, each returning the matching helper.
- [x] Check that `_fresh`, `_reorder`, `_run_first` and their fixtures are unchanged, and that the 93 FIRST tests still pass.
- [x] `test_follow_set.py`: import `copy`, `itertools`, `pytest`, `main` and `compute_follow_set`.
- [x] `test_follow_set.py::EPS = "ε"` and `END = "$"`: used in every table instead of the literal symbols.
- [x] `test_follow_set.py::pytestmark = pytest.mark.timeout(2)`.
- [x] `test_follow_set.py::KNOWN_FAILURES`: a dict mapping `"<test function>::<param id>"` to `(reason, exception type)`. It starts empty.
- [x] `test_follow_set.py::_case_params(test_name, kind=None)`: turns `FOLLOW_CASES` into `pytest.param(grammar, first_preset, expected, id=case_id)`.
  - `kind="F"` or `"E"` filters rows by id prefix. `None` keeps all 24.
  - Attach an xfail mark when `f"{test_name}::{case_id}"` is in `KNOWN_FAILURES`.
- [ ] Check collection: `pytest syntax/tests/test_follow_set.py --collect-only -q` lists 179 tests (20 + 4 + 3×24 + 58 + 24 + 1). `pytest syntax/tests --collect-only -q` lists 272.

## 2. Data table (plan §5)
- [x] `test_follow_set.py::FOLLOW_CASES`: a list of plain tuples `(case_id, grammar, first_preset, expected)`. F rows have a dict `first_preset`. E rows have `None`. The start symbol is always the first key.
- [x] Write `E4-lua-like-pipeline` so it reuses the grammar and expected objects of `F20-lua-like` instead of a copy.
- [x] Check that the 24 ids are unique and match plan.md §5 exactly.
- [x] Cross-check every grammar, FIRST preset and expected set against spec.md §4/§5, row by row.

## 3. Main tests: F rows (plan §6.1)
- [x] `test_follow_set.py::test_follow_rules`: parametrized with `_case_params("test_follow_rules", "F")`. Assert `run_follow(grammar, first_preset) == expected`, comparing the whole dict.
- [x] Row `F1-start-only`: the start symbol gets only $.
- [x] Row `F2-terminal-after-nt`: a terminal after a non-terminal. $ goes to the start symbol only.
- [x] Row `F3-nt-at-end`: a non-terminal at the end gets FOLLOW of the left side.
- [x] Row `F4-non-nullable-next`: followed by a non-nullable non-terminal, it gets FIRST of it and no inheritance.
- [x] Row `F5-skip-nullable`: the scan skips a nullable non-terminal to reach `c`. ε is dropped.
- [x] Row `F6-nullable-tail-inherits`: a nullable tail makes `A` also get FOLLOW(S).
- [x] Row `F7-long-nullable-tail`: a long nullable tail.
- [x] Row `F8-same-nt-twice`: both occurrences of `A` in one production count.
- [x] Row `F9-used-in-several-rules`: `A` collects from productions of different non-terminals.
- [x] Row `F10-multi-level-inherit`: inheritance travels through several levels.
- [x] Row `F11-nested-nullable-tail`: inheritance through a nullable tail one level down.
- [x] Row `F12-follow-cycle`: FOLLOW(A) and FOLLOW(B) feed each other, and the computation finishes.
- [x] Row `F13-start-on-rhs`: the start symbol keeps $ and gains `)`.
- [x] Row `F14-start-gains-from-deep`: the start symbol gains `c` from a deeper rule, and it flows back to `A`.
- [x] Row `F15-unreachable-nt`: an unused non-terminal keeps an empty set and its key.
- [x] Row `F16-epsilon-only-tail`: a tail that only derives ε adds no ε, so `A` only inherits.
- [x] Row `F17-left-recursion`: direct left recursion.
- [x] Row `F18-self-at-end`: a non-terminal at the end of its own production, and the computation finishes.
- [x] Row `F19-nt-followed-by-itself`: a nullable non-terminal followed by itself.
- [x] Row `F20-lua-like`: a Lua-like grammar where multi-character terminals are single symbols.

## 4. Main tests: E rows (plan §6.2)
- [ ] `test_follow_set.py::test_follow_pipeline`: parametrized with `_case_params("test_follow_pipeline", "E")`. Same body as `test_follow_rules`. FIRST is computed for real.
- [ ] Row `E1-main-grammar`: the grammar currently in `main.py`.
- [ ] Row `E2-expression-grammar`: the classic E/E'/T/T'/F grammar, with primed keys.
- [ ] Row `E3-indirect-nullable-tail`: a tail that is nullable only through another non-terminal.
- [ ] Row `E4-lua-like-pipeline`: the F20 grammar with FIRST computed instead of written by hand.

## 5. Property tests (plan §7.1–§7.3)
- [ ] `test_follow_set.py::test_follow_has_no_epsilon`: parametrized with `_case_params("test_follow_has_no_epsilon")`. Collect the non-terminals whose FOLLOW contains `EPS` and assert the list is empty. The message names them. `expected` is unused.
- [ ] Check that it runs once for each of the 24 rows.
- [ ] `test_follow_set.py::test_follow_keys_are_non_terminals`: parametrized with `_case_params("test_follow_keys_are_non_terminals")`. Assert `set(follow) == set(grammar)`.
- [ ] Check that it runs once for each of the 24 rows.
- [ ] `test_follow_set.py::test_first_is_read_only`: parametrized with `_case_params("test_first_is_read_only")`.
  1. Call `follow_inputs`.
  2. Snapshot `first`. For E rows this happens after FIRST is computed.
  3. Call `compute_follow_set`.
  4. Assert `first` is unchanged.
- [ ] Check that it runs once for each of the 24 rows.

## 6. Order independence (plan §7.4)
- [ ] `test_follow_set.py::_order_params()`: generates the order rows.
  - Keep the start key first.
  - Use every permutation of the other keys when the grammar has at most 4 non-terminals. Otherwise use them as declared and reversed.
  - Ids look like `f"{case_id}[{','.join(order)}]"`.
  - Attach an xfail mark when `f"test_follow_is_order_independent::{id}"` is in `KNOWN_FAILURES`.
- [ ] `test_follow_set.py::test_follow_is_order_independent`: assert `run_follow(reorder(grammar, order), first_preset) == expected`.
- [ ] F1 rows: 1 order.
- [ ] F2 rows: 1 order.
- [ ] F3 rows: 1 order.
- [ ] F4 rows: 2 orders.
- [ ] F5 rows: 2 orders.
- [ ] F6 rows: 2 orders.
- [ ] F7 rows: 6 orders.
- [ ] F8 rows: 1 order.
- [ ] F9 rows: 2 orders.
- [ ] F10 rows: 6 orders. These must include `F10-multi-level-inherit[S,A,B,C]` (top-down) and `[S,C,B,A]` (bottom-up), as the spec requires.
- [ ] F11 rows: 6 orders.
- [ ] F12 rows: 2 orders.
- [ ] F13 rows: 1 order.
- [ ] F14 rows: 1 order.
- [ ] F15 rows: 1 order.
- [ ] F16 rows: 2 orders.
- [ ] F17 rows: 1 order.
- [ ] F18 rows: 1 order.
- [ ] F19 rows: 1 order.
- [ ] F20 rows: 6 orders.
- [ ] E1 rows: 2 orders.
- [ ] E2 rows: 2 orders, declared and reversed (it has 5 non-terminals).
- [ ] E3 rows: 2 orders, declared and reversed (it has 5 non-terminals).
- [ ] E4 rows: 6 orders.
- [ ] Check that no generated order moves the start key away from the first position.
- [ ] Check that `pytest syntax/tests --collect-only -q -k order_independent` lists 58 rows from this file. The 51 FIRST order rows are also matched by `-k`, so filter by file or count only the `test_follow_set.py` lines.

## 7. Idempotence (plan §7.5)
- [ ] `test_follow_set.py::test_compute_follow_set_idempotent`: parametrized with `_case_params("test_compute_follow_set_idempotent")`.
  1. Call `follow_inputs` and `compute_follow_set`.
  2. Snapshot `follow`.
  3. Call `compute_follow_set` again on the same objects.
  4. Assert `follow == snapshot`. Don't compare against `expected`.
- [ ] Check that it runs once for each of the 24 rows.

## 8. Isolation (plan §7.6)
- [ ] `test_follow_set.py::test_module_globals_untouched`:
  1. Deep-copy `main.grammar`, `main.first`, `main.follow` and `main.non_terminals_set`.
  2. Run `run_follow` on the `E1-main-grammar` row.
  3. Assert the four globals are unchanged.
- [ ] Review that no test or helper writes to `main`'s module-level variables, and that every test builds its own inputs.

## 9. First run and xfail workflow (plan §8)
- [ ] Run `pytest syntax/tests -v` with no marks, and save the list of failing ids with their exception types.
- [ ] For every failing test that times out, confirm the exception pytest-timeout raises is `pytest.fail.Exception` before using it as `raises`.
- [ ] Add a `KNOWN_FAILURES` entry for each failing parametrized row: main, property, order and idempotence tests.
- [ ] Add the `@pytest.mark.xfail(...)` decorator if the isolation test fails.
- [ ] Check that every `reason` describes only the **symptom** (e.g. "FOLLOW(A) is missing $", "FOLLOW(B) contains ε", "compute_follow_set does not return"), never the cause or a fix.
- [ ] Check that every `raises` is the exception actually seen (`AssertionError`, `KeyError`, `pytest.fail.Exception`, …) and that every mark has `strict=True`.
- [ ] List every marked test in plan.md §10 as `id — symptom — exception`.
- [ ] Rerun. Expect only passes and xfails: no failures, no errors, no XPASS.
- [ ] Check that the FIRST suite still reports 93 passed.

## 10. Maintenance (recurring)
- [ ] Before editing any test, re-read `main.py` and compare it with plan.md (AGENTS.md).
- [ ] When `compute_follow_set` is renamed, changes signature or gets a helper extracted from it, update spec.md, plan.md, this file and the tests in the same change. A new function gets its own unit-test section, and a removed one has its tests deleted.
- [ ] When `first_of_sequence` changes, re-run both the FIRST and FOLLOW suites.
- [ ] When a bug is fixed and its test turns XPASS (strict), remove its `KNOWN_FAILURES` entry or decorator and its plan.md §10 line.
- [ ] Don't add tests for the out-of-scope inputs in spec §7 unless the spec is updated first.
- [ ] After setting up a new environment, check again that `pytest-timeout` is installed. Without it there is no time limit.
