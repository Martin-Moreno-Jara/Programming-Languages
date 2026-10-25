# Tasks 005 — Code generator tests

Each task below becomes one piece of setup, one test function, or one row of a
parametrized test. Tick the box when it is written and behaves as described.

**Legend**
- `conftest.py::name` / `test_code_generator.py::name`: the file (in
  `syntax/tests/`) and the function, fixture or constant to write.
- **row**: one `pytest.param` in a data table. Its `id` is shown in backticks.
- Grammars are written as in the other suites: `{"S": [["a", "B"], ["ε"]]}`,
  with the start symbol as the first key. `ε` is `EPS` and `$` is `END`.
- Expected errors are written `(line, col, lexeme, {expected tokens})`.
- **xfail**: a test that fails against the current code gets an entry in
  `KNOWN_FAILURES` under `"<test function>::<param id>"`, which becomes
  `xfail(reason=<symptom>, raises=<exception>, strict=True)`. See section 11.

All expected values in sections 6 to 8 were checked against the current code
on 2026-10-23.

## 1. Setup (spec §2, §9)
_Done on 2026-10-23._

- [x] `conftest.py`: also insert the **project root** (the parent of
  `SYNTAX_ROOT`) into `sys.path`. The generator, `ASDR_base` and the
  generated file import `syntax.…`, `lexer.lexer` and
  `exceptions.custom_exceptions`, which only resolve from there.
- [x] Check that the 803 existing tests still pass after that change.
- [x] Create `syntax/tests/test_code_generator.py`. Don't add an `__init__.py`.
- [x] Imports: `ast`, `copy`, `importlib.util`, `itertools`, `sys`, `pytest`,
  `syntax` (the package itself), `syntax.grammar.Grammar`,
  `syntax.code_generator_script.ASDR_generator`, `lexer.lexer.Lexer` and
  `Token`, and `exceptions.custom_exceptions.SyntacticalError`.
- [x] `EPS = "ε"` and `END = "$"`.
- [x] `pytestmark = pytest.mark.timeout(5)` (spec §7, termination).
- [x] `KNOWN_FAILURES: dict[str, tuple[str, type[BaseException]]] = {}`.
- [x] `_params(test_name, rows)`: turns `(case_id, *values)` tuples into
  `pytest.param(*values, id=case_id)`, adding the xfail mark when
  `f"{test_name}::{case_id}"` is in `KNOWN_FAILURES`. Every parametrized test
  uses it.

## 2. Fixtures and helpers (spec §2, §9)
_Done on 2026-10-23._

- [x] Fixture `out_dir(tmp_path, monkeypatch)`: creates `tmp_path / "syntax"`,
  calls `monkeypatch.chdir(tmp_path)`, and returns the `syntax` folder. Every
  test that calls `generate` or `write_program` uses it, so the real
  `syntax/ASDR.py` is never touched.
- [x] `_processed(grammar)`: `g = Grammar(copy.deepcopy(grammar))`, then
  `g.process_grammar()`, then return `g`.
- [x] `_generate(grammar, out_dir)`: builds `g = _processed(grammar)`, calls
  `ASDR_generator(g).generate()`, and returns `(g, source)` where `source` is
  the text of `out_dir / "ASDR.py"`.
- [x] Fixture `load_parser(monkeypatch)`: returns a function `load(path)`
  that imports the generated file and returns its `ASDR` class.
  - Use a unique module name from a counter, for example
    `f"syntax._generated_{n}"`. It must start with `syntax.` so that
    `from .ASDR_base import ASDR_base` resolves to the real
    `syntax/ASDR_base.py`, but it must not be `syntax.ASDR`, so the real
    generated module is never replaced.
  - `importlib.util.spec_from_file_location(name, path)`,
    `module_from_spec`, `monkeypatch.setitem(sys.modules, name, module)`, then
    `spec.loader.exec_module(module)`.
- [x] `FakeLexer(types, positions=None)`: a class with `tokenize()`.
  - Token `i` is `Token(types[i], types[i], 1, i + 1)`, so the lexeme equals
    the type and every token is on line 1, one column apart.
  - After the last one it returns `Token(END, END, 1, len(types) + 1)`, and
    keeps returning that same `$` token on every later call.
- [x] `_run(grammar, lexer, out_dir, load_parser)`: generates, loads, and
  calls `ASDR(lexer).main()`. It returns `None` or lets `SyntacticalError`
  escape.
- [x] `_error_parts(message)`: the **only** place that knows the layout of
  `format_error_message`. It parses `<line:col> … se encontro: "<lexeme>"; se
  esperaba: <expected>.` with one regex and returns
  `(line, col, lexeme, expected_tokens)`. `expected_tokens` comes from
  `_expected_tokens`. If the wording changes, only this helper changes.
- [x] `_expected_tokens(text)`: splits on `", "`, drops one pair of
  surrounding double quotes from each item if present, and returns a set. It
  must accept both `"a", "b"` and a bare `a`, because the current code writes
  both forms. Remove only **one** trailing `.`, never `rstrip(".")`, so
  tokens like `..` survive.
- [x] `_class_def(source)`: `ast.parse(source)`, then return the
  `ClassDef` named `ASDR`.
- [x] `_methods(class_def)`: a dict from method name to `FunctionDef`.
- [x] `_branches(func)`: walks the `if`/`elif` chain of a `parse_A` method and
  returns `(branches, else_body)`.
  - Each branch is `(tokens, body)`. `tokens` is the set of string constants
    in `self.cur_tok.type in [...]`. `body` is a list of descriptors:
    `("call", X)` for `self.parse_X()`, `("match", t)` for
    `self.match(t)`, and `("pass",)` for `pass`.
  - An `elif` is an `If` that is the only statement in the previous `orelse`.
- [x] `_expected_body(production, non_terminals)`: the descriptors the spec
  expects for one production: `("pass",)` for ε, `("call", X)` for a
  non-terminal, `("match", t)` otherwise.

## 3. Grammar table (spec §4)
_Done on 2026-10-23._

- [x] `test_code_generator.py::GRAMMARS`: a dict from name to grammar, with
  copies written in this file (don't import them from `main.py` or other
  test files):
  - `G1`: `{"S": [["a"]]}`
  - `G2`: `{"S": [["a"], ["b"], ["c"]]}`
  - `G3`: `{"S": [["A", "b"]], "A": [["a"], [EPS]]}`
  - `G4`: `{"S": [["a", "b", "c"]]}`
  - `G5`: `{"S": [["A", "B"]], "A": [["a"]], "B": [["b"]]}`
  - `G6`: `{"S": [["a", "A", "b", "B"]], "A": [["x"]], "B": [["y"]]}`
  - `G7`: `{"S": [["a", "a"]]}`
  - `G8`: `{"S": [["A"]], "A": [["a"], [EPS]]}`
  - `G9`: `{"S": [["a"]], "U": [["u"], [EPS]]}`
  - `G10`: `{"S": [["'"], ['"'], ["\\"]]}`
  - `G11`: `{"S": [["if", "E", "then", "S", "end"], ["x"]], "E": [["x", "==", "x"], ["y", "..", "y"]]}`
  - `G12`: `{"B": [["b"]], "A": [["B"]]}`
  - `G13-grammar1`: `grammar1` from `main.py`.
  - `G13-grammar2`: `grammar2` from `main.py`.
  - `G13-expression`: `E → T Ep`, `Ep → + T Ep | ε`, `T → F Tp`,
    `Tp → * F Tp | ε`, `F → ( E ) | id`.
  - `G13-lua`: `Chunk → Block`, `Block → Stat Block | ε`,
    `Stat → if Exp then Block end | Name = Exp`, `Exp → Name | Number`.
- [x] `test_grammars_are_ll1`: parametrized over `G_ROWS`, asserts every
  grammar passes `check_LL1_condition()` (spec §8 puts non-LL(1) grammars out
  of scope). 16 rows.
- [x] `G_ROWS`: `[(name, grammar) for name, grammar in GRAMMARS.items()]`,
  16 rows.

## 4. Structural tests (spec §3.1, §4)
_Done on 2026-10-23._

Each test is parametrized with `_params("<test name>", G_ROWS)`, uses
`out_dir`, and calls `_generate`. That makes 16 rows per test, 112 in total.

- [x] `test_generated_file_is_valid_python`: `ast.parse(source)` doesn't
  raise. The message on failure includes the source.
- [x] `test_generated_class_extends_base`: there is a `ClassDef` named `ASDR`
  whose only base is the name `ASDR_base`.
- [x] `test_one_method_per_nonterminal`: the set of method names starting with
  `parse_` equals `{f"parse_{A}" for A in grammar}`. `main` is also present.
  This includes `U` in G9 and `A` in G12, which the start symbol never reaches.
- [x] `test_branches_match_predict_sets`: for every `A`, `_branches` returns
  one branch per production, in grammar order, and branch `i` tests exactly
  `g.predict[A][i]`. Compare sets **and** list lengths, so a duplicated token
  is caught. For G9, `U`'s ε branch tests the empty set.
- [x] `test_branch_bodies_follow_productions`: for every `A` and every `i`,
  the body of branch `i` equals `_expected_body(grammar[A][i], set(grammar))`.
  This covers order (G6), repeats (G7), ε (G3, G8, G9) and escaping (G10:
  the `match` argument equals the token exactly).
- [x] `test_else_names_union_of_predict_sets`: for every `A`, `else_body` is a
  single `raise SyntacticalError(self.format_error_message(<text>))`, and
  the argument is a list literal equal to `sorted(union, key=...)`, where
  `union` is the union of `g.predict[A]` (raw token types; `ASDR_base` formats
  them) and the key maps `tkn_num` to `valor_numerico` and `tkn_str` to
  `cadena_de_caracteres`. Updated on 2026-10-25.
- [x] `test_else_list_sort_order`: one grammar with `tkn_num`, `tkn_str`,
  `tkn_plus`, `id`, `true`, `tkn_varargs` and `and`. The list is
  `and, tkn_str, id, tkn_plus, tkn_varargs, true, tkn_num`.
- [x] `test_main_parses_start_symbol` also checks the final raise is
  `self.format_error_message(['$'])`.
- [x] `ASDR_base` unit tests (2026-10-25, the formatting moved there):
  - `test_format_expected_symbol`: 40 rows. `tkn_num`, `tkn_str`, `$`, a
    keyword, a built-in, `id`, a plain token, and one row per symbol of the
    lexer's `operand_symbols_dict`, each expected in double quotes. The base's
    table can't drift from the lexer's.
  - `test_format_error_message`: 5 rows (one token, several, order kept, the
    `","` token, `$`).
  - `test_format_error_message_at_end_of_input`: a `$` lexeme is shown as
    `final de archivo`.
  - `test_match_names_the_one_expected_token`: `match` reports its token
    quoted and shown.
- [x] `test_main_parses_start_symbol`: `main` has, in order,
  1. `self.cur_tok = self.lexer.tokenize()`,
  2. `self.parse_<start>()` where `<start>` is the first key (G12: `parse_B`),
  3. an `if self.cur_tok.type != "$"` whose body raises `SyntacticalError`.

## 5. Unit tests for each method (spec §1)
_Done on 2026-10-23._

`AGENTS.md` asks for every method to be tested. These are small and not
parametrized.

- [x] `test_init_sets_header`: `ASDR_generator(g).lines` starts with the
  three imports, a blank line, and the `class ASDR(ASDR_base):` line, and
  `.eps == EPS`. It doesn't write any file.
- [x] `test_populate_lines_does_not_write`: after `populate_lines()` on G1,
  `out_dir` is still empty and `lines` is longer than the header.
- [x] `test_write_program_writes_lines`: set `gen.lines = ["x", "y"]` and call
  `write_program()`. The file is exactly `"x\ny\n"`.
- [x] `test_generate_is_populate_then_write`: for G3, the file from
  `generate()` equals the file from a fresh generator that calls
  `populate_lines()` and then `write_program()`.

## 6. Accept tests (spec §5.1)
_Done on 2026-10-23._

- [x] `test_parser_accepts`: parametrized over `ACCEPT_ROWS`, rows
  `(case_id, grammar_name, token_types)`. Calls `_run` with a `FakeLexer`
  and asserts it returns without raising. Also assert the lexer was read up
  to `$`, so a parser that stops early can't pass.
- [x] Row `A1-shortest`: G1, `["a"]`.
- [x] Rows `A2-alt-a`, `A2-alt-b`, `A2-alt-c`: G2, `["a"]`, `["b"]`, `["c"]`.
- [x] Rows `A3-epsilon`, `A3-non-epsilon`: G3, `["b"]` and `["a", "b"]`.
- [x] Row `A4-empty-nullable`: G8, `[]`.
- [x] Rows `A5-c`, `A5-ac`, `A5-bc`, `A5-abc`: G13-grammar2, `["c"]`,
  `["a", "c"]`, `["b", "c"]`, `["a", "b", "c"]`.
- [x] Row `A6-expression`: G13-expression,
  `id + id * ( id )` split on spaces.
- [x] Row `A7-deep-nesting`: G13-expression, 50 `(`, then `id`, then 50 `)`.
- [x] Row `A8-lua-nested-if`: G13-lua,
  `if Name then if Name then Name = Number end end` split on spaces.
- [x] Check that there are 14 rows.

## 7. Reject tests (spec §5.2)
_Done on 2026-10-23._

- [x] `test_parser_rejects`: parametrized over `REJECT_ROWS`, rows
  `(case_id, grammar_name, token_types, expected)`. Runs `_run` inside
  `pytest.raises(SyntacticalError)` and asserts
  `_error_parts(err.value.message) == expected`.
- [x] Row `R1-wrong-first-token`: G1, `["b"]`, `(1, 1, "b", {"a"})`.
- [x] Row `R2-wrong-mid-production`: G4, `["a", "x", "c"]`, `(1, 2, "x", {"b"})`.
- [x] Row `R3-ends-early`: G4, `["a", "b"]`, `(1, 3, "final de archivo", {"c"})`.
- [x] Row `R4-extra-tokens`: G1, `["a", "a"]`, `(1, 2, "a", {"final de archivo"})`.
- [x] Row `R5-empty-not-nullable`: G1, `[]`, `(1, 1, "final de archivo", {"a"})`.
- [x] Row `R6-union-named`: G3, `["c"]`, `(1, 1, "c", {"a", "b"})`.
- [x] Row `R7-inside-recursion`: G13-expression, `["id", "+"]`,
  `(1, 3, "final de archivo", {"(", "id"})`.
- [x] Row `R8-missing-close-paren`: G13-expression, `["(", "id"]`,
  `(1, 3, "final de archivo", {")"})`.
- [x] Check that there are 8 rows.

## 8. End-to-end tests with the real lexer (spec §6)
_Done on 2026-10-23._

- [x] `LEXER_GRAMMAR`: `Chunk → Block`, `Block → Stat Block | ε`,
  `Stat → if Exp then Block end | id tkn_assign Exp`, `Exp → id | tkn_num`.
  The terminals are the token types the lexer produces.
- [x] `test_end_to_end`: parametrized over `E2E_ROWS`, rows
  `(case_id, source, expected)`, where `expected` is `None` for accepted
  input. Run `_run(LEXER_GRAMMAR, Lexer(source), ...)`. With `None`, assert it
  returns. Otherwise assert the `SyntacticalError` parts equal `expected`.
- [x] Row `E1-assignment`: `"x = 1"`, `None`.
- [x] Row `E2-if-block`: `"if x then y = 2 end"`, `None`.
- [x] Row `E3-missing-end`: `"if x then y = 2"`, `(1, 16, "final de archivo", {"end"})`.
- [x] Row `E4-double-assign`: `"x = = 1"`, `(1, 5, "=", {"id", "valor_numerico"})`.
- [x] Row `E5-error-on-line-3`: `"x = 1\ny = 2\nz = then\n"`,
  `(3, 5, "then", {"id", "valor_numerico"})`.

## 9. Properties (spec §7)
_Done on 2026-10-23._

- [x] `test_generation_is_deterministic`: parametrized over `G_ROWS`.
  Generate into `out_dir`, read the file, generate again from a **new**
  `Grammar` and a new generator, and assert both texts are equal.
- [x] `test_grammar_is_not_modified`: parametrized over `G_ROWS`. Snapshot
  deep copies of `g.grammar`, `g.first`, `g.follow` and `g.predict` after
  `process_grammar()`, run `ASDR_generator(g).generate()`, and assert all
  four are unchanged.
- [x] `test_generate_overwrites_existing_file`: write `"STALE"` to
  `out_dir / "ASDR.py"`, generate G1, and assert the file doesn't contain
  `"STALE"` and equals a clean generation of G1.
- [x] `test_generators_do_not_share_lines`: build the generators for G1 and
  G2 **before** either generates. Generate G1, read the file, then generate
  G2. Generate G1 again with a third, fresh generator and assert the file
  equals the first G1 file. This catches `lines` being shared between
  instances.

## 10. Counts
_Done on 2026-10-23._

- [x] `pytest tests/test_code_generator.py --collect-only -q` lists 241 tests:
  16 LL(1) + 112 structural + 1 sort order + 4 unit + 47 `ASDR_base` + 14 accept + 8 reject + 5 end-to-end +
  16 deterministic + 16 unmodified + 2 single property tests.
- [x] `pytest tests --collect-only -q` lists 1044 (803 + 241), before spec 006.

## 11. First run and xfail workflow (spec §9)
_Done on 2026-10-23: all 193 pass against the current code, so `KNOWN_FAILURES` stays empty and no marks were added. Four deliberate bugs in a throwaway copy of the generator (no `elif`, no `pass` for ε, every branch using the first prediction set, no `$` check in `main`) each made 17 to 67 tests fail._

- [x] Run `pytest tests/test_code_generator.py -v` with no marks and save the
  list of failing ids with their exception types.
- [x] For a test that times out, confirm the exception is
  `pytest.fail.Exception` before using it as `raises`.
- [x] Add a `KNOWN_FAILURES` entry for each failing row, or an `xfail`
  decorator for a failing test that isn't parametrized.
- [x] Every `reason` describes only the **symptom** (e.g. "R4 accepted",
  "parse_U missing"), never the cause or a fix. Every mark has
  `strict=True`, and `raises` is the exception actually seen.
- [x] Rerun. Expect only passes and xfails: no failures, no errors, no XPASS.
- [x] Check that `syntax/ASDR.py` is unchanged after the run (`git status`),
  which proves no test wrote outside `tmp_path`.
- [x] Check that the other four suites still pass.

## 12. Maintenance (recurring)

- [ ] Before editing any test, re-read `code_generator_script.py` and
  `ASDR_base.py` and compare them with spec.md (AGENTS.md).
- [ ] When the generator gains, loses or renames a method, add or remove its
  unit test in section 5, and update spec.md and this file in the same change.
- [ ] When the output path or the shape of the generated code changes, update
  `out_dir`, `load_parser` or `_branches`, and spec §3.1.
- [ ] When `format_error_message` changes its wording, update only
  `_error_parts`.
- [ ] When a bug is fixed and its test turns XPASS (strict), remove its
  `KNOWN_FAILURES` entry or decorator.
- [ ] Don't add tests for the out-of-scope inputs in spec §8 unless the spec
  is updated first.
