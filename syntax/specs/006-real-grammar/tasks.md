# Tasks 006 — Real Lua grammar tests

Each task below becomes one piece of setup, one test function, or one row of a
parametrized test. Tick the box when it is written and behaves as described.

**Legend**
- `file.py::name`: the file (in `syntax/tests/`) and the function, fixture or
  constant to write.
- **row**: one `pytest.param` in a data table. Its `id` is the spec ID in
  backticks (`S12`, `R27`, ...). A spec row that lists several programs
  becomes several rows with a suffix (`E1-nil`, `E1-false`, `E1-true`).
- Sources are Python strings. Every `↵` in the spec is `"\n"`.
- **xfail**: a row that fails against the current code gets an entry in its
  file's `KNOWN_FAILURES` under `"<test function>::<param id>"`, which becomes
  `xfail(reason=<symptom>, raises=<exception>, strict=True)`. See section 10.

**Files**

| File | Contents |
|------|----------|
| `real_grammar_support.py` | Helpers shared by the three test files: loading the grammar, generating the parser, lexing, parsing, reading the error message (section 2) |
| `real_grammar_cases.py` | Data only: every accept, reject and output row of spec §5 to §8 (sections 3 to 5) |
| `conftest.py` | Two new fixtures (section 2.3) |
| `test_real_grammar_properties.py` | Spec §4 (P cases) and a check of the case sources themselves (section 6) |
| `test_real_grammar_parse.py` | Spec §5 to §7 (section 7) |
| `test_real_grammar_output.py` | Spec §8 (section 8) |

The two support modules don't start with `test_`, so pytest doesn't collect
them. The test files import them by name, which works because pytest puts
`syntax/tests/` on `sys.path` (no `__init__.py`, as in the other suites).

Until `pred_exceptions` was added to `main.py` (2026-10-25), `final_grammar` was **not** LL(1). P1
fails, and every parsing and output test is skipped by the fixture in 2.3
until it is.

## 1. Setup (spec §2, §11)

- [x] Before writing anything, re-read `main.py`, `syntax/ASDR_base.py`,
  `syntax/code_generator_script.py` and `lexer/lexer.py`, and note any
  difference from spec §3.4 (AGENTS.md).
- [x] Create the five files above. Don't add an `__init__.py`.
- [x] Every test file sets `pytestmark = pytest.mark.timeout(10)`. Output
  tests run a subprocess, so use `timeout(30)` there.
- [x] Every test file has
  `KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}`.
- [x] `real_grammar_support.py::params(test_name, rows, known)`: the same as
  `_params` in `test_code_generator.py`, but it takes the file's
  `KNOWN_FAILURES` as `known`. It turns `(case_id, *values)` into
  `pytest.param(*values, id=case_id)` plus the xfail mark. Every
  parametrized test uses it.
- [x] `params` raises if two rows share an id, so a copy-paste mistake in the
  tables can't hide a case.

## 2. Helpers and fixtures (spec §2, §3.2)

### 2.1 Grammar and parser (`real_grammar_support.py`)

- [x] `lua_grammar()`: `from main import final_grammar` and return a deep copy.
  Import inside the function, so the import cost only applies to tests that
  need it.
- [x] `lua_pred_exceptions()`: a deep copy of `pred_exceptions` from `main.py`.
- [x] `lua_hidden_expected()`: a deep copy of `hidden_expected` from `main.py` (2026-10-25). `generate_parser` passes it to `ASDR_generator`.
- [x] `processed_grammar(with_exceptions=True)`: `Grammar(lua_grammar())`, then
  `set_pred_exceptions(lua_pred_exceptions())` unless `with_exceptions` is
  `False` (P8 needs the raw sets), then `process_grammar()`,
  return it.
- [x] `generate_parser(folder)`: inside `pytest.MonkeyPatch.context()`,
  `chdir(folder.parent)` (where `folder` is a `syntax/` directory), run
  `ASDR_generator(g).generate()`, and load `folder / "ASDR.py"` with
  `importlib` under the module name `syntax._real_grammar_parser`.
  - The `syntax.` prefix makes `from .ASDR_base import ASDR_base` resolve to the
    real file. The name is not `syntax.ASDR`, so the real module is never
    replaced.
  - Register the module in `sys.modules` before `exec_module`. Return
    `(g, ASDR)`.
  - If `g.check_LL1_condition()` is `False`, don't generate. Return `None`, and
    the fixture skips.

### 2.2 Lexing and parsing (`real_grammar_support.py`)

- [x] `lex(source)`: calls `Lexer(source).tokenize()` until a `$` token and
  returns the list, including `$`.
  - The lexer calls `exit()` on a lexical error. Catch `SystemExit` and call
    `pytest.fail` with the source. A bad test source then reads as a test bug,
    not a parser bug.
- [x] `parse(ASDR, source)`: `ASDR(Lexer(source)).main()`. It lets
  `SyntacticalError` escape, and turns `SystemExit` into `pytest.fail` as in
  `lex`.

### 2.3 Fixtures (`conftest.py`)

- [x] `lua_parser` (scope `"session"`): makes
  `tmp_path_factory.mktemp("real") / "syntax"` and calls `generate_parser`. If
  it returns `None`, call `pytest.skip("final_grammar is not LL(1)")`.
  Otherwise return `(g, ASDR)`. Session scope means the grammar is processed
  and generated **once** for all three files.
- [x] `project_copy` (scope `"session"`): copies `main.py`, `syntax/`, `lexer/`
  and `exceptions/` from the project root into
  `tmp_path_factory.mktemp("project")`, ignoring `__pycache__` and
  `syntax/tests`, and returns that folder. The output tests run `main.py`
  there, so the real `syntax/ASDR.py` is never rewritten.

### 2.4 Reading error messages (`real_grammar_support.py`)

- [x] `ERROR_RE`: the doc layout,
  `^<(\d+):(\d+)> Error sintactico: se encontro: "(.*)"; se esperaba: (.*)\.$`.
  This is the only place that knows it.
- [x] `error_parts(message)`: matches `ERROR_RE` and returns
  `(line, col, lexeme, shown)`. `shown` is the **ordered list** of expected
  items without their quotes. If the message doesn't match, fail with the
  message.
- [x] Split the expected text with `re.findall(r'"(.*?)"(?=, "|$)', text)`,
  **not** by splitting on `", "`. The `","` token contains a comma, and
  splitting on `", "` would cut it. Check by hand that `"=", ":", ",", "["`
  gives `["=", ":", ",", "["]` and that `".."` survives.
- [x] `DISPLAY`: a dict from token type to how it is shown (spec §3.2). Build it
  from the lexer, don't type it by hand:
  - every value of `Lexer("").operand_symbols_dict` maps to its key
    (`tkn_plus → "+"`);
  - every keyword in `Lexer("").keywords_set` maps to itself;
  - `id → "id"`, `tkn_num → "valor_numerico"`,
    `tkn_str → "cadena_de_caracteres"`, `$ → "final de archivo"`.
  - Assert that no two token types share a shown value, so the reverse lookup
    in the next task is safe.
- [x] `SHOWN_TO_TYPE`: the reverse of `DISPLAY`.
- [x] `is_doc_order(shown)`: maps each item back with `SHOWN_TO_TYPE` and
  returns whether the types are strictly increasing (sorted with no
  repeats). The sort key is the type, except `SORT_AS` (`tkn_num` as
  `valor_numerico`, `tkn_str` as `cadena_de_caracteres`; spec §3.2). An
  unknown item returns `False`.

## 3. Accept rows (`real_grammar_cases.py`, spec §5 and §6)

Each table is a list of `(case_id, source)`. Copy the programs from the spec
verbatim. The total is collected at the end in `ACCEPT_ROWS`.

- [x] `STRUCTURE_ROWS`: `B1` to `B7`. `B1` is `""`. 7 rows.
- [x] `STATEMENT_ROWS`: `S1` to `S34`. 34 rows.
- [x] `ATTRIB_ROWS`: `AT1` to `AT5`. 5 rows.
- [x] `RETURN_ROWS`: `RT1` to `RT10`. 10 rows.
- [x] `FUNCTION_ROWS`: `F1` to `F11`. 11 rows.
- [x] `TABLE_ROWS`: `T1` to `T13`. 13 rows.
- [x] `EXPRESSION_ROWS`: 28 rows.
  - `E1-nil`, `E1-false`, `E1-true`;
  - `E2-int` (`x = 42`), `E2-float` (`x = 3.14`), `E2-hex` (`x = 0xFF`);
  - `E3-double` (`x = "s"`), `E3-single` (`x = 'c'`);
  - `E4` to `E8`;
  - `E9-minus`, `E9-not`, `E9-length`;
  - `E10-minus`, `E10-not`;
  - `E11` to `E20`.
- [x] `BINOP_ROWS`: 21 rows `x = a <op> b`, built from a list of
  `(name, op)` pairs. The ids are `BO-plus`, `BO-minus`, `BO-times`, `BO-div`,
  `BO-floor-div`, `BO-power`, `BO-mod`, `BO-bit-and`, `BO-bit-xor`,
  `BO-bit-or`, `BO-right-shift`, `BO-left-shift`, `BO-concat`, `BO-less`,
  `BO-leq`, `BO-greater`, `BO-geq`, `BO-equal`, `BO-neq`, `BO-and`, `BO-or`.
- [x] `CALL_ROWS`: `C1` to `C23`, with `C12-string` (`o:m"s"`) and
  `C12-table` (`o:m{}`). 24 rows.
- [x] `NAME_ROWS`: `N1` to `N15`. 15 rows.
- [x] `LAYOUT_ROWS`: `L1` to `L6`. 6 rows.
- [x] `EDGE_ROWS`: `EA1` to `EA13`. 13 rows. Generated programs are built with
  string operations, never typed out:
  - `EA1`: the doc's `saludar` program, comments included:
    `"-- Definición de la función\nfunction saludar(texto)\n    print(texto)\nend\n\n-- Llamada a la función\nsaludar(\"¡Hola, mundo!\")\n"`.
  - `EA2`: `"local entrada\n\nif entrada == nil then\n    print(\"Valor indefinido\")\nelse\n    print(\"Valor definido\")\nend\n"`.
  - `EA3`: `"x = " + "(" * 50 + "1" + ")" * 50`.
  - `EA4`: `"while x do " * 50 + "end " * 50`.
  - `EA5`: `"if x then " * 50 + "end " * 50`.
  - `EA6`: `"t = " + "{" * 50 + "}" * 50`.
  - `EA7`: `"x = 1\n" * 200`.
  - `EA8`: `"x = " + " + ".join(["1"] * 200)`.
  - `EA9`: `"f = " + "function() return " * 10 + "end " * 10` (each
    function returns the next one; a bare `function()` is not a statement).
  - `EA10` to `EA12`: as in the spec. `EA11` is `"-- a\n\n-- b\n"`.
  - `EA13`: `"f()\n(g)()"` (the greedy `(` of spec §4.1).
- [x] `ACCEPT_ROWS`: all the tables above concatenated, **188 rows**. Assert
  the count at import time, so a lost table is noticed at once.
- [x] `PRODUCTION_ROWS`: `ACCEPT_ROWS` without `EDGE_ROWS` (175 rows). Only
  this list is used for coverage in P7, because the spec ties coverage to
  §5.

## 4. Reject rows (`real_grammar_cases.py`, spec §7)

- [x] `REJECT_ROWS`: a list of
  `(case_id, source, position, lexeme, contains, exact)`.
  - `position` is `(line, col)`, or `None` for the EOF rows.
  - `lexeme` is the found lexeme as shown in the message (`"final de archivo"`
    at EOF).
  - `contains` is a set of shown items that must be in the list.
  - `exact` is the full ordered list, or `None`.
- [x] Rows `R1` to `R39`, copied from spec §7. `R39` is
  `"a = f\n(g).x = 1"`, `(2, 7)`, `"="`, `{EOF, "id"}`.
  The three doc rows have
  `exact` set and `contains` empty:
  - `R1`: `"local 1;"`, `(1, 7)`, `"1"`,
    `["error", "function", "id", "pcall", "print", "warn", "xpcall"]`.
  - `R2`: `'print(45"this")'`, `(1, 9)`, `"this"`,
    `["and", "or", "&", "|", "~", ")", ",", "..", "/", "==", "//", ">=", ">", "<<", "<=", "<", "-", "%", "~=", "+", "^", ">>", "*"]`.
  - `R3`: `"local i = 0;\n\nwhile (i < 5) do\n    p == [i];3\n    i = i + 1;\nend"`,
    `(4, 7)`, `"=="`, `["=", ":", ",", "[", "(", "."]`.
  - `R33`: `"local = 1"`, `(1, 7)`, `"="`, the same list as `R1`.
- [x] The EOF rows are `R4` to `R10` and `R37`, with `position = None`.
- [x] Assert 49 rows at import time.
- [x] All positions in spec §7 were checked against the real lexer on
  2026-10-25. Keep `test_reject_positions_match_lexer` (section 6) so they stay
  right if the lexer changes.

## 5. Output rows (`real_grammar_cases.py`, spec §8)

- [x] `OUTPUT_ROWS`: a list of `(case_id, source, expected)`.
  - `expected` is the exact stdout line without the newline, or a callable that
    checks the line (only for `O8`).
  - Sources are taken from the accept and reject tables by id (look them up in
    a dict built from the rows), so the doc programs exist in one place only.
- [x] `SUCCESS = "El analisis sintactico ha finalizado exitosamente."`
- [x] `O1`: `EA1`, `SUCCESS`. `O2`: `EA2`, `SUCCESS`. `O6`: `L1`, `SUCCESS`.
  `O7`: `""`, `SUCCESS`.
- [x] `O3`: `R1`,
  `'<1:7> Error sintactico: se encontro: "1"; se esperaba: "error", "function", "id", "pcall", "print", "warn", "xpcall".'`
- [x] `O4`: `R2`,
  `'<1:9> Error sintactico: se encontro: "this"; se esperaba: "and", "or", "&", "|", "~", ")", ",", "..", "/", "==", "//", ">=", ">", "<<", "<=", "<", "-", "%", "~=", "+", "^", ">>", "*".'`
- [x] `O5`: `R3`,
  `'<4:7> Error sintactico: se encontro: "=="; se esperaba: "=", ":", ",", "[", "(", ".".'`
- [x] `O8`: `R4`, a check that the line starts with `<`, matches `ERROR_RE`,
  and contains `se encontro: "final de archivo"`.
- [x] Assert 8 rows at import time.

## 6. Property tests (`test_real_grammar_properties.py`, spec §4)

These tests don't use `lua_parser`, so they run even when the grammar is not
LL(1). Each one builds its own `processed_grammar()`.

- [x] `test_P1_grammar_is_ll1`: `check_LL1_condition()` is `True`. On failure,
  the message lists every non-terminal whose prediction sets overlap, with
  the shared tokens. Compute this in the test by comparing every pair of
  sets, the same way spec 004 §6 does.
- [x] `test_P2_all_nonterminals_reachable`: BFS from `CHUNK` over the right
  sides. The set reached equals the set of keys. Name the unreachable ones in
  the message.
- [x] `test_P3_no_undefined_or_empty`: every right-side symbol with an
  uppercase letter is a key of the grammar. Every lexer token type is
  lowercase, so such a symbol is meant to be a non-terminal, and a missing key
  is a misspelling. The message names it. Also check that no key maps to `[]`
  and no production is `[]`. Misspelled terminals are P5's job.
- [x] `test_P4_all_nonterminals_productive`: the fixed-point algorithm. Start
  with no productive symbols, and mark a non-terminal productive when one of
  its productions has only terminals, `ε` and productive non-terminals. Repeat
  until nothing changes. All keys end up productive.
- [x] `test_P5_terminals_are_lexer_tokens`: every symbol that is not a key and
  not `ε` is a key of `DISPLAY`. List the bad ones with the non-terminal that
  uses them.
- [x] `test_P6_chunk_is_start_symbol`: `next(iter(lua_grammar())) == "CHUNK"`,
  and `get_initial_symbol()` returns `"CHUNK"`.
- [x] `test_P8_every_exception_resolves_a_conflict`: on
  `processed_grammar(with_exceptions=False)`, every entry `{A: {i: t}}` of
  `pred_exceptions` has `A` in the grammar, a valid index `i`, `t` in the raw
  `predict[A][i]`, and `t` in another raw set of `A`. The message names the
  production for each bad entry.
- [x] `test_P7_every_production_is_covered`: uses `lua_parser`, so it skips
  while the grammar is not LL(1).
  - Build a subclass of `ASDR`. For each key `A`, override `parse_A` to record
    `(A, i)` on entry, where `i` is the index of the prediction set of `A` that
    contains `self.cur_tok.type`, and then call the original method.
  - Parse every row of `PRODUCTION_ROWS`. Ignore rows that raise, since their
    own test already reports them.
  - Assert the recorded pairs equal all `(A, i)` pairs of the grammar. The
    message lists the missing ones as `A → production`, so the missing case is
    obvious.
- [x] `test_case_sources_lex_cleanly`: parametrized over every source in
  `ACCEPT_ROWS` and `REJECT_ROWS` (226 rows, ids as in the tables). `lex`
  doesn't fail. This proves every case is free of lexical errors, as the doc
  promises for the real input.
- [x] `test_reject_positions_match_lexer`: parametrized over the `REJECT_ROWS`
  with a position (31 rows). Some token in `lex(source)` is at that
  `(line, col)` and has `lexeme` as its lexeme.
- [x] `test_display_is_consistent`: `DISPLAY` has no repeated shown values,
  and `"print"`, `"pcall"`, `"xpcall"`, `"error"` and `"warn"` are keys. This
  test **fails while `print` is commented out** of the lexer (spec K6).

## 7. Parse tests (`test_real_grammar_parse.py`, spec §5 to §7)

All tests use `lua_parser` and take `ASDR` from it.

- [x] `test_accepts`: parametrized over `ACCEPT_ROWS` (188 rows). `parse`
  returns without raising. On `SyntacticalError`, fail with the source and the
  message, so the report shows where it was rejected.
- [x] `test_rejects`: parametrized over `REJECT_ROWS` (39 rows).
  - `pytest.raises(SyntacticalError)` around `parse`.
  - `error_parts(err.value.message)` gives `(line, col, lexeme, shown)`.
  - Assert the lexeme, the position (when it is not `None`) and `contains <=
    set(shown)`.
  - When `exact` is set, assert `shown == exact` (order included).
- [x] `test_reject_expected_list_order`: parametrized over `REJECT_ROWS`
  (39 rows). `is_doc_order(shown)` is `True` (spec §8 cross-check). Kept
  separate from `test_rejects`, so an order mistake doesn't hide a wrong
  position.
- [x] `test_reports_only_first_error`: R3 and R36, plus a copy of R36 with a
  second error on a line 4 (`"\nlocal d = = 4"`). The error is on the
  earlier line in all three. 3 rows: `R3`, `R36`, `R36-second-error`.
- [x] `test_parser_reads_to_end`: parametrized over `STRUCTURE_ROWS` and
  `LAYOUT_ROWS` (13 rows). Use a lexer wrapper that counts how often
  `tokenize` returns `$`. After `main()`, it is at least 1, so a parser that
  stops before the end can't pass.

## 8. Output tests (`test_real_grammar_output.py`, spec §8)

- [x] `run_main(project_copy, source)`: runs
  `[sys.executable, "main.py"]` with `cwd=project_copy`, `input=source`,
  `capture_output=True`, `text=True`, `timeout=20`. Returns the completed
  process.
- [x] `test_main_output`: parametrized over `OUTPUT_ROWS` (8 rows).
  - The process's `stdout.splitlines()` has exactly one line.
  - The line equals `expected`, or `expected(line)` is `True` for `O8`.
  - Don't check the exit code (spec §8).
  - On failure, show the whole stdout and stderr.
- [x] `test_main_output` also requests `lua_parser`, only for its skip. While
  the grammar is not LL(1), the 8 rows are skipped with the same reason,
  instead of failing on `main.py`'s "Cannot procede" text.
- [x] `test_platform_output` (2026-10-25, spec §8.1): parametrized over `PLATFORM_ROWS`, one row per `*.in` in `syntax/test_files/`, with ids `platform-NN`. The source is passed as read from the file, and stdout must be exactly `[first line of the output file]`. Assert 10 rows at import time; update it when new feedback is added.
- [x] `R14` (2026-10-25) checks `_EXP_LIST` exactly, so hiding `function` and `...` is tested by an R row too.

## 8b. Prediction-set exception unit tests (`test_pred_exceptions.py`, spec §4.1)
_Done on 2026-10-25._

- [x] `DANGLING_ELSE` (spec 004 E8, with `S'` renamed to `Sp`) and
  `GREEDY_ELSE = {"Sp": {1: "e"}}`.
- [x] `_processed(grammar, exceptions, set_them)` and `_plain_predict(grammar)`
  (the step-by-step pipeline without exceptions).
- [x] X1: `test_set_pred_exceptions_stores_mapping`,
  `test_set_pred_exceptions_computes_nothing`.
- [x] X2: `test_no_exceptions_gives_plain_predict`, 3 rows: `never-set`,
  `none`, `empty`.
- [x] X3: `test_exception_removes_token_from_its_set`.
- [x] X4: `test_exception_resolves_conflict`.
- [x] X5: `test_exception_touches_nothing_else`.
- [x] X6: `test_exceptions_mapping_not_modified`.
- [x] X7: `test_several_non_terminals`.
- [x] X8: `test_apply_twice_is_idempotent`.
- [x] X9: `test_apply_after_compute_predict_set`.

## 9. Counts

- [x] `pytest tests/test_real_grammar_properties.py --collect-only -q` lists
  8 + 226 + 31 + 1 = **266** tests.
- [x] `pytest tests/test_real_grammar_parse.py --collect-only -q` lists
  187 + 39 + 39 + 3 + 13 = **281** tests.
- [x] `pytest tests/test_real_grammar_output.py --collect-only -q` lists
  8 + 10 = **18** tests.
- [x] `pytest tests/test_pred_exceptions.py --collect-only -q` lists **12** tests.
- [x] `pytest tests --collect-only -q` lists **1713** (2026-10-25: spec 005 has 333 tests and the output file 18).

## 10. First run and xfail workflow (spec §11)
_First run on 2026-10-25: 1254 passed, 286 skipped, 2 xfailed across all suites. Only P1 and `test_display_is_consistent` fail, so they got strict xfail decorators; every `KNOWN_FAILURES` dict is still empty, because the parse and output tests are skipped while the grammar is not LL(1). A dry run with `check_LL1_condition` forced to `True` (a throwaway pytest plugin outside the repo) ran the skipped parse tests: 161 failed, all real (EXP has no PREFIXEXP yet, and the error message still shows raw token types), with no harness errors._

- [x] Run the three files with no marks. While `final_grammar` is not LL(1),
  expect P1 to fail, P7 and the parse and output tests to be skipped, and the
  rest of the property tests to give real results.
- [x] Save the list of failing ids with their exception types. For a timeout,
  confirm the exception is `pytest.fail.Exception` before using it as
  `raises`.
- [x] Add a `KNOWN_FAILURES` entry for each failing row, or a strict `xfail`
  decorator for a test that isn't parametrized.
- [ ] Expected xfails come from spec §3.4. While those gaps exist:
  - `test_display_is_consistent`, and R1, R33 and O3 (`print` not a keyword);
  - every `test_rejects` row with `exact`, every row of
    `test_reject_expected_list_order`, and every `test_rejects` row whose
    `contains` uses a shown symbol (raw token types in the message);
  - O3 to O5 and O8 (`error: ` prefix).
- [x] Every `reason` describes only the **symptom** (for example "R15
  accepted", "O3 output differs", "P1 grammar not LL(1)"), never the cause or a
  fix. Every mark has `strict=True`.
- [x] Rerun. Expect only passes, xfails and skips: no failures, no errors, no
  XPASS.
- [x] Check that `git status` shows no change to `syntax/ASDR.py` after the
  run, which proves no test wrote outside the temporary folders.
- [x] Check that the five earlier suites still pass.
- [ ] Each time the grammar becomes LL(1) again, rerun. The skipped tests now
  give real results. Repeat this section for them.

_Second run on 2026-10-25, after `pred_exceptions`: the grammar is LL(1), so nothing is skipped any more. P1 passes and its xfail mark was removed. 1391 passed, 169 failed, 1 xfailed. The failures are real and not marked yet, because the grammar is still being edited: 99 accept rows (`EXP` has no `PREFIXEXP`, so `x = y` is rejected), all 39 + 39 reject rows (that, plus raw token types in the message), 6 output rows (same causes plus the `error: ` prefix), P7, and 3 more parse rows. Mark them once the grammar settles._

## 11. Maintenance (recurring)

- [ ] Before editing any test, re-read `main.py` (`final_grammar` and the
  `__main__` block), `ASDR_base.py` and `lexer/lexer.py`, and compare them with
  spec.md (AGENTS.md).
- [ ] When P7 lists a production that no case covers, add an accept row for it
  to the matching table in section 3 **and** to the spec's table in the same
  change.
- [ ] When an accept or reject row starts failing after a grammar change,
  treat it as a grammar bug first. Change the row only when the grader shows
  otherwise, and update the spec in the same change.
- [ ] When the error format changes, only `ERROR_RE` and `error_parts`
  change.
- [ ] When a known limitation of spec §9 (K1 to K9) is settled by the grader,
  move it into a table here and in the spec, and update the memory note in
  `lua-parser-grader-rules`.
- [ ] When `pred_exceptions` changes, P8 checks every entry still resolves a
  real conflict. If a production is inserted before an index used there,
  P8 fails instead of silently removing the wrong token.
- [ ] When a bug is fixed and its test turns XPASS (strict), remove its
  `KNOWN_FAILURES` entry or decorator.
- [ ] Don't add tests for the out-of-scope inputs in spec §10 unless the spec
  is updated first.
