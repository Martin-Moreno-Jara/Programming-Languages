# Tasks 001 — FIRST set tests

Each task below becomes one piece of setup, one test function, or one row of a
parametrized test. Tick the box when it is written and behaves as described.

**Legend**
- `conftest.py::name` / `test_first_set.py::name`: the file (in `syntax/tests/`)
  and the function, fixture or constant to write.
- **row**: one `pytest.param` in a data table. Its `id` is shown in backticks.
- Inputs and expected values are **not** repeated here. They live in
  [`plan.md`](plan.md) §5.1 (U cases) and §6.1 (E cases), which are copied
  from [`spec.md`](spec.md). If a value changes, edit spec.md and plan.md, not
  this file.
- **xfail**: a test that fails against the current `main.py` gets
  `xfail(reason=<symptom>, raises=<exception>, strict=True)`. See section 7.

## 1. Setup (plan §2–§4)
- [x] Create `syntax/tests/` files `conftest.py` and `test_first_set.py`. Don't add an `__init__.py`.
- [x] `conftest.py`: define `SYNTAX_ROOT = Path(__file__).resolve().parent.parent`, insert it into `sys.path` if missing, then `from main import compute_first_set`.
- [x] `conftest.py::_fresh(grammar)`: returns `({nt: set() for nt in grammar}, set(grammar))`.
- [x] `conftest.py::_reorder(grammar, order)`: returns `{nt: grammar[nt] for nt in order}`.
- [x] `conftest.py::_run_first(grammar)`: deep-copies the grammar, calls `_fresh`, calls `compute_first_set`, and returns `first`.
- [x] `conftest.py`: add fixtures `fresh`, `reorder` and `run_first`, each returning the matching helper.
- [x] `test_first_set.py::EPS = "ε"`: used in every table instead of the literal symbol.
- [x] `test_first_set.py`: import `first_of_sequence`, `compute_first_set`, `copy` and `itertools`.
- [x] `test_first_set.py::_grammar_params()`: turns `GRAMMAR_CASES` into `pytest.param(grammar, expected, id=case_id)`.
- [ ] Check collection: `pytest syntax/tests --collect-only -q` lists 93 tests (11 unit + 15 end-to-end + 51 order + 15 idempotence + 1 isolation).

## 2. Unit tests: `first_of_sequence` (plan §5)
- [x] `test_first_set.py::FIRST_OF_SEQUENCE_CASES`: a list of `pytest.param(productions_of_A, preset, expected, id=...)`.
- [x] `test_first_set.py::test_first_of_sequence`: the test body.
  1. Build the grammar as `{"A": …, **{h: [["_"]] for h in preset}}`.
  2. Call `fresh`, then fill in the preset sets.
  3. Deep-copy the helper entries.
  4. Call `first_of_sequence("A", …)`.
  5. Re-read `first["A"]` and compare it with `expected`.
  6. Assert the helper entries are unchanged.
- [x] Row `U1-single-terminal`: a single terminal production.
- [x] Row `U2-several-alternatives`: several alternatives, and only the first symbol of each counts.
- [x] Row `U3-epsilon`: the empty production gives {ε}.
- [x] Row `U4-terminal-or-epsilon`: a terminal alternative and an empty one together.
- [x] Row `U5-leading-terminal-stops`: symbols after a leading terminal are ignored.
- [x] Row `U6-non-nullable-stops`: a non-nullable non-terminal stops the scan, so `y` must not appear.
- [x] Row `U7-nullable-then-terminal`: a nullable non-terminal lets the following terminal in.
- [x] Row `U8-all-nullable`: a fully nullable body adds ε.
- [x] Row `U9-nullable-chain-then-nt`: a chain of nullables ending in a non-nullable non-terminal gives no ε.
- [x] Row `U10-stops-before-terminal`: the scan stops at the non-nullable `Y`, so `w` must not appear.
- [x] `test_first_set.py::test_first_of_sequence_only_adds` (U11): with `first["A"] = {"q"}` and `A → a`, the result is `{"q", "a"}`.

## 3. End-to-end tests: `compute_first_set` (plan §6)
- [ ] `test_first_set.py::GRAMMAR_CASES`: a list of plain tuples `(case_id, grammar, expected)`.
- [ ] `test_first_set.py::test_compute_first_set`: parametrized with `_grammar_params()`. Assert `run_first(grammar) == expected`, comparing the whole dict.
- [ ] Row `E1-only-terminals`: base case with no non-terminals in the bodies.
- [ ] Row `E2-main-grammar`: the grammar currently in `main.py`.
- [ ] Row `E3-dependency-chain`: FIRST propagates through several levels.
- [ ] Row `E4-nullable-prefix`: nullable prefixes add the following symbols, and there is no ε because of `c`.
- [ ] Row `E5-whole-body-nullable`: an all-nullable body adds ε to S.
- [ ] Row `E6-indirectly-nullable`: ε reaches S only through other non-terminals.
- [ ] Row `E7-epsilon-does-not-leak`: a nullable prefix followed by a terminal gives no ε.
- [ ] Row `E8-non-nullable-blocks`: a non-nullable `A` hides `B`.
- [ ] Row `E9-left-recursion`: direct left recursion.
- [ ] Row `E10-mutual-recursion`: indirect recursion between two non-terminals.
- [ ] Row `E11-recursion-with-nullable`: recursion behind a nullable non-terminal.
- [ ] Row `E12-right-recursion`: the list pattern `L → x L | ε`.
- [ ] Row `E13-expression-grammar`: the classic E/E'/T/T'/F grammar, with primed keys.
- [ ] Row `E14-common-prefix`: a non-LL(1) grammar whose FIRST is still well defined.
- [ ] Row `E15-multichar-terminals`: multi-character and punctuation terminals (`local`, `==`, `(`) are single symbols.

## 4. Order independence (plan §7.1)
- [ ] `test_first_set.py::KNOWN_FAILURES`: a dict mapping each param id to `(reason, exception type)`. It starts empty.
- [ ] `test_first_set.py::_order_params()`: generates the order rows.
  - Use every `itertools.permutations` order when the grammar has at most 4 non-terminals. Otherwise use the declared and reversed orders.
  - Ids look like `f"{case_id}[{','.join(order)}]"`.
  - Attach an xfail mark when the id is in `KNOWN_FAILURES`.
- [ ] `test_first_set.py::test_first_is_order_independent`: assert `run_first(reorder(grammar, order)) == expected`.
- [ ] E1 rows: 1 order.
- [ ] E2 rows: 6 orders.
- [ ] E3 rows: 6 orders. These must include `E3-dependency-chain[B,A,S]` (bottom-up, required by the spec) and `[S,A,B]` (top-down).
- [ ] E4 rows: 6 orders.
- [ ] E5 rows: 6 orders.
- [ ] E6 rows: 6 orders.
- [ ] E7 rows: 2 orders.
- [ ] E8 rows: 6 orders.
- [ ] E9 rows: 2 orders.
- [ ] E10 rows: 2 orders.
- [ ] E11 rows: 2 orders.
- [ ] E12 rows: 1 order.
- [ ] E13 rows: 2 orders, declared and reversed (it has 5 non-terminals).
- [ ] E14 rows: 1 order.
- [ ] E15 rows: 2 orders.
- [ ] Check that `pytest syntax/tests --collect-only -q -k order_independent` lists 51 rows.

## 5. Idempotence (plan §7.2)
- [ ] `test_first_set.py::test_compute_first_set_idempotent`: parametrized with `_grammar_params()`.
  1. Deep-copy the grammar, then call `fresh` and `compute_first_set`.
  2. Snapshot `first`.
  3. Call `compute_first_set` again on the same objects.
  4. Assert `first == snapshot`. Don't compare against `expected`.
- [ ] Check that it runs once for each of E1–E15 (15 rows).

## 6. Isolation (plan §7.3)
- [ ] `test_first_set.py::test_module_globals_untouched`:
  1. Deep-copy `main.grammar`, `main.first` and `main.non_terminals_set`.
  2. Run `run_first` on the E4 grammar.
  3. Assert the three globals are unchanged.
- [ ] Review that no test or helper writes to `main`'s module-level variables, and that every test builds its own inputs.

## 7. First run and xfail workflow (plan §8)
- [ ] Run `pytest syntax/tests -v` with no marks, and save the list of failing ids with their exception types.
- [ ] Add `marks=pytest.mark.xfail(reason=…, raises=…, strict=True)` to each failing U and E row.
- [ ] Add the `@pytest.mark.xfail(...)` decorator to each failing non-parametrized test (U11 and isolation).
- [ ] Fill in `KNOWN_FAILURES` for each failing order-independence row.
- [ ] Idempotence rows: mark them like the other parametrized rows.
- [ ] Check that every `reason` describes only the **symptom** (e.g. "FIRST(S) is missing c"), never the cause or a fix.
- [ ] Check that every `raises` is the exception actually seen (`AssertionError`, `KeyError`, …).
- [ ] List every marked test in plan.md §10 as `id — symptom — exception`.
- [ ] Rerun. Expect only passes and xfails: no failures, no errors, no XPASS.

## 8. Maintenance (recurring)
- [ ] Before editing any test, re-read `main.py` and compare it with plan.md (AGENTS.md).
- [ ] When a function in the FIRST computation is added, removed, renamed or changes signature, update spec.md, plan.md, this file and the tests in the same change. A new function gets its own unit-test section, and a removed one has its tests deleted.
- [ ] When a bug is fixed and its test turns XPASS (strict), remove the xfail mark, its `KNOWN_FAILURES` entry and its plan.md §10 line.
- [ ] Don't add tests for the out-of-scope inputs in spec §7 unless the spec is updated first.
