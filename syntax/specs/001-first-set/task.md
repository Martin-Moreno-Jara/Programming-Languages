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
- [x] `conftest.py`: define `SYNTAX_ROOT = Path(__file__).resolve().parent.parent`, insert it into `sys.path` if missing, then `from grammar import Grammar`.
- [x] `conftest.py::_new_grammar(grammar)`: returns `Grammar(copy.deepcopy(grammar))`.
- [x] `conftest.py::_reorder(grammar, order)`: returns `{nt: grammar[nt] for nt in order}`.
- [x] `conftest.py::_run_first(grammar)`: builds a Grammar with `_new_grammar`, calls `compute_first_set()`, and returns `g.first`.
- [x] `conftest.py`: add fixtures `new_grammar`, `reorder` and `run_first`, each returning the matching helper.
- [x] `test_first_set.py::EPS = "ε"` and `END = "$"`: used instead of the literal symbols.
- [x] `test_first_set.py`: import `Grammar`, `copy` and `itertools`.
- [x] `test_first_set.py::_grammar_params()`: turns `GRAMMAR_CASES` into `pytest.param(grammar, expected, id=case_id)`.
- [x] Check collection: `pytest tests/test_first_set.py --collect-only -q` lists 109 tests (15 init + 11 unit + 15 end-to-end + 51 order + 15 idempotence + 2 isolation).

## 2.0 Unit tests: `Grammar.__init__` (plan §5.0)
- [x] `test_first_set.py::test_grammar_init`: parametrized with `_grammar_params()`. Assert `grammar`, `non_terminals_set`, empty `first`, `EPS` and `END`.

## 2. Unit tests: `first_of_sequence` (plan §5)
- [x] `test_first_set.py::FIRST_OF_SEQUENCE_CASES`: a list of `pytest.param(sequence, preset, expected, id=...)`. `sequence` is one production.
- [x] `test_first_set.py::test_first_of_sequence`: the test body.
  1. Call `new_grammar({h: [["_"]] for h in preset})` and fill in the preset sets in `g.first`.
  2. Deep-copy `g.first`.
  3. Call `result = g.first_of_sequence(sequence)`.
  4. Assert `result == expected`.
  5. Assert `first` is unchanged.
- [x] Row `U1-single-terminal`: a single terminal.
- [x] Row `U2-terminal-sequence`: only the first terminal of a sequence counts.
- [x] Row `U3-epsilon`: the empty production gives {ε}.
- [x] Row `U4-single-nullable-nt`: a single nullable non-terminal keeps ε.
- [x] Row `U5-leading-terminal-stops`: symbols after a leading terminal are ignored.
- [x] Row `U6-non-nullable-stops`: a non-nullable non-terminal stops the scan, so `y` must not appear.
- [x] Row `U7-nullable-then-terminal`: a nullable non-terminal lets the following terminal in.
- [x] Row `U8-all-nullable`: a fully nullable sequence gives ε.
- [x] Row `U9-nullable-chain-then-nt`: a chain of nullables ending in a non-nullable non-terminal gives no ε.
- [x] Row `U10-stops-before-terminal`: the scan stops at the non-nullable `Y`, so `w` must not appear.
- [x] Row `U11-not-yet-computed-nt`: a non-terminal whose FIRST is still empty contributes nothing and is not nullable.

## 3. End-to-end tests: `compute_first_set` (plan §6)
- [x] `test_first_set.py::GRAMMAR_CASES`: a list of plain tuples `(case_id, grammar, expected)`.
- [x] `test_first_set.py::test_compute_first_set`: parametrized with `_grammar_params()`. Assert `run_first(grammar) == expected`, comparing the whole dict.
- [x] Row `E1-only-terminals`: base case with no non-terminals in the bodies.
- [x] Row `E2-main-grammar`: the grammar currently in `main.py`.
- [x] Row `E3-dependency-chain`: FIRST propagates through several levels.
- [x] Row `E4-nullable-prefix`: nullable prefixes add the following symbols, and there is no ε because of `c`.
- [x] Row `E5-whole-body-nullable`: an all-nullable body adds ε to S.
- [x] Row `E6-indirectly-nullable`: ε reaches S only through other non-terminals.
- [x] Row `E7-epsilon-does-not-leak`: a nullable prefix followed by a terminal gives no ε.
- [x] Row `E8-non-nullable-blocks`: a non-nullable `A` hides `B`.
- [x] Row `E9-left-recursion`: direct left recursion.
- [x] Row `E10-mutual-recursion`: indirect recursion between two non-terminals.
- [x] Row `E11-recursion-with-nullable`: recursion behind a nullable non-terminal.
- [x] Row `E12-right-recursion`: the list pattern `L → x L | ε`.
- [x] Row `E13-expression-grammar`: the classic E/E'/T/T'/F grammar, with primed keys.
- [x] Row `E14-common-prefix`: a non-LL(1) grammar whose FIRST is still well defined.
- [x] Row `E15-multichar-terminals`: multi-character and punctuation terminals (`local`, `==`, `(`) are single symbols.

## 4. Order independence (plan §7.1)
- [x] `test_first_set.py::KNOWN_FAILURES`: a dict mapping each param id to `(reason, exception type)`. It starts empty.
- [x] `test_first_set.py::_order_params()`: generates the order rows.
  - Use every `itertools.permutations` order when the grammar has at most 4 non-terminals. Otherwise use the declared and reversed orders.
  - Ids look like `f"{case_id}[{','.join(order)}]"`.
  - Attach an xfail mark when the id is in `KNOWN_FAILURES`.
- [x] `test_first_set.py::test_first_is_order_independent`: assert `run_first(reorder(grammar, order)) == expected`.
- [x] E1 rows: 1 order.
- [x] E2 rows: 6 orders.
- [x] E3 rows: 6 orders. These must include `E3-dependency-chain[B,A,S]` (bottom-up, required by the spec) and `[S,A,B]` (top-down).
- [x] E4 rows: 6 orders.
- [x] E5 rows: 6 orders.
- [x] E6 rows: 6 orders.
- [x] E7 rows: 2 orders.
- [x] E8 rows: 6 orders.
- [x] E9 rows: 2 orders.
- [x] E10 rows: 2 orders.
- [x] E11 rows: 2 orders.
- [x] E12 rows: 1 order.
- [x] E13 rows: 2 orders, declared and reversed (it has 5 non-terminals).
- [x] E14 rows: 1 order.
- [x] E15 rows: 2 orders.
- [x] Check that `pytest syntax/tests --collect-only -q -k order_independent` lists 51 rows.

## 5. Idempotence (plan §7.2)
- [x] `test_first_set.py::test_compute_first_set_idempotent`: parametrized with `_grammar_params()`.
  1. Build `g = new_grammar(grammar)` and call `g.compute_first_set()`.
  2. Snapshot `g.first`.
  3. Call `g.compute_first_set()` again on the same object.
  4. Assert `first == snapshot`. Don't compare against `expected`.
- [x] Check that it runs once for each of E1–E15 (15 rows).

## 6. Isolation (plan §7.3)
- [x] `test_first_set.py::test_input_grammar_untouched`: `Grammar(grammar).compute_first_set()` on a copy of E4 leaves that dict unchanged.
- [x] `test_first_set.py::test_instances_do_not_share_state`: computing FIRST on an E4 object leaves an E2 object's `first` empty.
- [x] Review that every test builds its own `Grammar` object on a grammar copy.

## 7. First run and xfail workflow (plan §8)
_First run on 2026-10-16: 93 passed, 0 failed. No marks were needed, so the marking steps below were done with nothing to mark._

- [x] Run `pytest syntax/tests -v` with no marks, and save the list of failing ids with their exception types.
- [x] Add `marks=pytest.mark.xfail(reason=…, raises=…, strict=True)` to each failing U and E row.
- [x] Add the `@pytest.mark.xfail(...)` decorator to each failing non-parametrized test (isolation).
- [x] Fill in `KNOWN_FAILURES` for each failing order-independence row.
- [x] Idempotence rows: mark them like the other parametrized rows.
- [x] Check that every `reason` describes only the **symptom** (e.g. "FIRST(S) is missing c"), never the cause or a fix.
- [x] Check that every `raises` is the exception actually seen (`AssertionError`, `KeyError`, …).
- [x] List every marked test in plan.md §10 as `id — symptom — exception`.
- [x] Rerun. Expect only passes and xfails: no failures, no errors, no XPASS.

## 8. Maintenance (recurring)
- [ ] Before editing any test, re-read `grammar.py` and compare it with plan.md (AGENTS.md).
- [ ] When a function in the FIRST computation is added, removed, renamed or changes signature, update spec.md, plan.md, this file and the tests in the same change. A new function gets its own unit-test section, and a removed one has its tests deleted.
- [ ] When a bug is fixed and its test turns XPASS (strict), remove the xfail mark, its `KNOWN_FAILURES` entry and its plan.md §10 line.
- [ ] Don't add tests for the out-of-scope inputs in spec §7 unless the spec is updated first.
