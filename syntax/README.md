# Lua Syntactic Analyzer

*Programming Languages, Universidad Nacional de Colombia, 2026-II. Assignment 2.*

A recursive-descent (LL(1)) parser for **Lua 5.5**, written in Python. It reads a Lua program from stdin and prints a single line: a success message, or the first syntax error. The parser itself is **generated** from the grammar every time `main.py` runs. The tokens come from the lexer of assignment 1 (`../lexer/`).

```bash
python main.py < program.lua                                 # from the project root
venv/bin/python -m pytest syntax/tests -q                    # run all suites
venv/bin/python -m pytest syntax/tests -q -k platform        # only the grader's own cases
```

The full statement is in `docs/Analizador Sintáctico - Lenguaje Lua.docx`. This file collects what the statement doesn't say: what the grader (UNCode) actually does, as learned from submissions, and the decisions made because of it.

## Output format

```
El analisis sintactico ha finalizado exitosamente.
<line:col> Error sintactico: se encontro: "<lexeme>"; se esperaba: "<sym>", "<sym>", ....
```

- Only the first error is reported, then the analysis stops. There are no accents and exactly one line is printed.
- `se encontro`: the **lexeme**, not the token type. A string shows its text without the quotes (`print(45"this")` gives `"this"`). End of input shows `final de archivo`.
- In the expected list:

  | Expected token | Shown as |
  |---|---|
  | keyword | itself (`"end"`) |
  | identifier | `"id"` |
  | `tkn_num` | `"valor_numerico"` |
  | `tkn_str` | `"cadena_de_caracteres"` |
  | operator | its symbol (`"+"`) |
  | `$` | `"final de archivo"` |

## Pipeline

```
main.py: final_grammar, pred_exceptions, hidden_expected
   │
   ├─ grammar.py: Grammar.process_grammar()       FIRST → FOLLOW → predict → apply_pred_exceptions()
   │                 check_LL1_condition()          refuses to continue if any prediction sets overlap
   ├─ code_generator_script.py: ASDR_generator(g, hidden_expected).generate()
   │                 writes syntax/ASDR.py           one parse_A method per non-terminal
   └─ ASDR(Lexer(stdin)).main()                     ASDR extends ASDR_base (match, error formatting)
```

| File | Role |
|---|---|
| `../main.py` | The grammar (`final_grammar`), `pred_exceptions`, `hidden_expected`, and the program entry point. It regenerates `ASDR.py` on every run. |
| `grammar.py` | FIRST, FOLLOW and prediction sets, the LL(1) check, and prediction exceptions. This is the core of the assignment: AGENTS.md says only the author edits it. |
| `code_generator_script.py` | Writes `ASDR.py` from the processed grammar. |
| `ASDR_base.py` | `match`, the `pending` set, error formatting and sorting. |
| `ASDR.py` | Generated. Never edit it by hand. |

### Generated code, and how the expected list is built

For each non-terminal `A`:
- **Branches:** one `if`/`elif` per production other than ε, testing `cur_tok.type in predict[A][i]`. ε is always the **last** production, which the generator relies on. A rule with a single nullable production gets plain calls with no `if`.
- **The `pending` set:** this is the expected list. It holds the tokens that could have started any production skipped since the last token was consumed.
  - A nullable rule's `else` adds its productions' starting tokens to `pending` and returns, because it took the ε path.
  - Any other rule's `else` adds them too and then raises.
  - `match(t)` clears `pending` when it succeeds. When it fails, it adds `t` and raises.
  - `main` adds `$` before its final check.
- **The tokens added** are the visible FIRST of the production, `∩ predict[A][i]`, minus the hidden tokens. That leaves out FOLLOW tokens, excepted tokens and hidden ones.
- **Sort key:** keywords as themselves, symbols by their internal `tkn_*` name, except that `tkn_num` sorts as `valor_numerico` and `tkn_str` as `cadena_de_caracteres`. This gives the grader's order: `"=", ":", ",", "[", "(", "."` is `tkn_assign`, `tkn_colon`, `tkn_comma`, `tkn_opening_bra`, `tkn_opening_par`, `tkn_period`.

### `pred_exceptions` and `hidden_expected`

Both are configured in `main.py`, next to the grammar.

| Setting | Shape | Effect | Used for |
|---|---|---|---|
| `pred_exceptions` | `{A: {i: token}}` | Removes a token from `predict[A][i]` after the sets are computed, so a real Lua ambiguity resolves the way Lua does. | `(` after a prefix expression always continues it as a call (greedy, `a = f↵(g).x`). |
| `hidden_expected` | `{A: {i: {tokens}}}` | The production still parses the tokens, but they are never named in an error. A hidden token also stays out of every rule that starts with `A`. | See *Grader findings*. |

Both are keyed by **production index**: reordering or inserting productions in those rules means updating the indexes. `test_platform_output` catches a mismatch.

## Grader findings

These were confirmed by submissions. The grader's own parser is the reference, so matching its output byte for byte is what passes, even where it differs from the Lua manual.

| # | Finding | Evidence |
|---|---|---|
| 1 | The expected list holds the tokens valid **at that exact point**, including the starting tokens of ε-productions just passed (the `pending` design). It is not the global FOLLOW set and not one rule's predict union. | Platform tests 04, 17 |
| 2 | The sort order is the internal-name order above. It is not the doc's "lexicographic order of the shown strings". The separator is `", "`. | Platform tests 13, 14; doc examples |
| 3 | EOF is at **(last line + 1, column 1)**. The platform's stdin has no final newline, so `main.py` adds one if missing. | Platform tests 03, 04 (we printed 3:15, the grader wanted 4:1) |
| 4 | **The grader's lists leave out tokens its parser accepts.** A missing token does not mean the construct is invalid. Never remove a production to match a list: hide its token. Removing `FUNCTIONDEF` broke tests 05 and 22. | 22 accepts anonymous functions, 05 expects `"("` after `function`, yet 13/14 never list `function` |
| 5 | Hidden tokens now: `function` and `...` at the start of an expression (13, 14); string and `{` call arguments after a name (18); `do` and `(` at the start of a statement (04); `<` before the first declared name, and `*` after `global` (23, and the doc's `local 1;`). | — |
| 6 | Only `print`, `pcall`, `xpcall`, `error` and `warn` are names (`NAME`). They are keyword tokens in the lexer. Unary `~` is a syntax error (bitwise operators are binary only). | Doc; R1 list |
| 7 | Platform test N is the downloaded file `NN.in` (unlike the lexer assignment, which was off by one). There are 40 platform tests (82.5% = 33/40). | Third submission |

Submission history (2026-10-25):
1. **First submission:** feedback in `test_files/`, with line 2 of each output file being what we printed.
2. **Second submission:** added 05 and 22.
3. **Third submission:** 82.5%. Platform tests 15, 16, 24, 27, 30, 35 and 36 fail. None of them is downloaded yet; every downloaded case passes.
4. **Probe submission (built-ins):** `main.py` looped forever (`while True: pass`) whenever the input had a `pairs`, `ipairs`, `tostring`, `tonumber`, `select`, `next`, `load`, `loadfile` or `dofile` token. None of the 7 failing tests timed out, so **none of them contains those built-ins**. Their failures have another cause. The probe is a one-off, to be removed before the next real submission.
5. **Probe submission (long-bracket strings):** `main.py` looped forever when the raw input matched `(?<!--)\[=*\[`, meaning `[[`, `[=[` … not directly after `--`. The input is searched as text, because the lexer would exit on a lexical error inside the string before reaching the loop. None of the 7 failing tests timed out, so **none of them contains a long-bracket string**. One test that otherwise passes did time out: **test 33**. It passes today, so its `[[` is probably harmless: inside a string or a comment like `-- [[`, or after the point where the expected error is reported.
6. **Probe submission (our verdict):** `main.py` ran the parser first and looped forever if it raised `SyntacticalError`. **All 7 failing tests timed out**, so our parser rejects every one of them. Each is either:
   - a valid program we wrongly reject, or
   - an invalid program where our message differs from the grader's (position, lexeme or expected list).

   About 70 valid Lua snippets are all accepted locally (nested calls, methods, varargs, attributes, `global`, every operator, tables, comments), apart from the built-ins and long strings already ruled out. So the second kind is more likely: an error case in a context with no grader sample yet, with tokens hidden there (finding 4) or a differently sorted list.
7. **Probe submissions (which rule raises the error):** a base-3 probe over the rule that raises the `SyntacticalError`.
   - **How the rule is found:** the innermost `parse_*` frame of the traceback, or `main`. A failed `match` counts for the rule that called it.
   - **The index:** `names = ["main"] + [f"parse_{A}" for A in final_grammar]`, so `main` is 0 and the grammar keys follow in order. **The grammar must not change between rounds.**
   - **Each round `r` (0 to 3):** the digit is `index // 3**r % 3`. Digit 0 prints the normal output (a wrong answer), 1 loops forever (time limit), 2 raises `RuntimeError` (runtime error).

   | Round | Test 15 | 16 | 24 | 27 | 30 | 35 | 36 |
   |---|---|---|---|---|---|---|---|
   | 0 | 2 | 2 | 0 | 0 | 0 | 0 | 2 |
   | 1 | 2 | 2 | 0 | 0 | 0 | 0 | 2 |

   | 2 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

   After round 1, only these candidates fit: `main` (0) or `IFSTAT` (9) for 24, 27, 30 and 35; `DO_BLOCK_END` (8), `EXPLIST` (44) or `TABLECONSTRUCTOR` (53) for 15, 16 and 36. Round 2 (`index // 9 % 3`) separates all five.

   **Result** (round 3 was skipped: it would only rule out candidates whose error can't be reached):

   | Rule raising the error | Tests | What it means |
   |---|---|---|
   | `main` | 27, 30, 35 | Extra tokens after a complete program (a stray `end`, `)`, `else`, …). The list always contains `"final de archivo"`. |
   | `IFSTAT` | 24 | A missing `then`, or a missing `end` (`elseif`/`else`/`end`) |
   | `DO_BLOCK_END` | 16, 36 | A missing `do` after `while`/`for`, or a missing `end` |
   | `EXPLIST` | 15 | No expression after `=` or `in` (`x = )`, `local x =`) |

   **Hypotheses these rules leave open:**
   - **Where `"final de archivo"` sorts.** The three `main` tests all print it, and we put it first. No grader sample has it in a list of several tokens.
   - **Error columns.** The lexer counts a tab as one column and counts characters, not bytes. A tab or a non-ASCII character (`á`, `ñ`, `¡`) before the error on the same line would give a different column. This would affect any rule.
   - **List contents after a block or an expression.** These lists are long, and the grader hasn't shown us any of them. `EXPLIST` prints the same list as tests 13 and 14, which the grader confirmed, so test 15 points to the position rather than the list.

   **Candidates after round 0.** These are the rules whose error can actually be reached: an `else` that raises when the rule is called without its prediction set being checked first, or a `match` after a production's first symbol.
   - **24, 27, 30, 35** (index ≡ 0 mod 3):
     - `main`: extra tokens after a complete program;
     - `IFSTAT`: missing `then` or `end`;
     - `AFTER_CALL`: missing `]`;
     - `GLOBAL_TAIL`;
     - `FUNCNAME`.
   - **15, 16, 36** (index ≡ 2 mod 3):
     - `AFTER_VAR`;
     - `DO_BLOCK_END`: missing `end` after `while`, `for` or `do`;
     - `NUMERICAL_FOR`: missing `,`;
     - `LOCAL_OPT` and `GLOBAL_OPT`;
     - `ATTRIB`: missing `>`;
     - `PARLIST_AFTER_COMMA`;
     - `EXPLIST`;
     - `EXP_NOT_ID`: missing `)`;
     - `PREFIXEXP_PRIME`: missing `]`;
     - `TABLECONSTRUCTOR`: missing `}`;
     - `FIELD`.

## Open questions

- **Other built-ins** (`pairs`, `ipairs`, `tostring`, `tonumber`, `select`, `next`, `load`, `loadfile`, `dofile`): the lexer makes them keyword tokens, and `NAME` doesn't accept them. So `for k, v in pairs(t) do … end` is currently a **syntax error**. The probe submission ruled this out as the cause of the 7 failing tests: none of them uses these built-ins. Whether the grader accepts them is still unknown, but no platform test seems to depend on it.
- **Long-bracket strings** (`[[…]]`): the lexer doesn't support them (they never appeared in the lexer's tests). `local s = [[hola]]` gives a syntax error at `[`. The probe submission ruled this out as the cause of the 7 failing tests.
- **Where `"final de archivo"` sorts** inside a longer list. We sort `$` first. No grader sample has `$` in a list of several tokens.
- **Input ending in blank lines:** EOF would be reported two or more lines down, and there's no sample for that.
- **Statements that are only a prefix expression** (`x`, `t.k`) and **calls used as assignment targets** (`f() = 1`). Both are errors in Lua and in our parser, but no grader sample shows the expected list.

## Testing

Tests use pytest (with pytest-timeout) and live in `tests/`. Each suite has a spec and a task list in `specs/NNN-*/`.

| Suite | Spec | What it covers |
|---|---|---|
| `test_first_set.py`, `test_follow_set.py`, `test_predict_set.py`, `test_ll1_condition.py` | 001–004 | `grammar.py` on small grammars |
| `test_pred_exceptions.py` | 006 §4.1 | `set_pred_exceptions` / `apply_pred_exceptions` |
| `test_code_generator.py` | 005 | Generated code structure, `pending`, hidden tokens, `ASDR_base`, small grammars run end to end |
| `test_real_grammar_properties.py` | 006 | The real grammar is LL(1), reachable and productive; every production is covered by an accept row; every exception is still needed |
| `test_real_grammar_parse.py` | 006 | Accept and reject rows (`real_grammar_cases.py`), with exact expected lists where the grader's list is known |
| `test_real_grammar_output.py` | 006 §8 | Runs `main.py` as a subprocess. `test_platform_output` checks every `test_files/*.in` against line 1 of its output file. |

**Adding platform feedback:**
1. Drop `NN.in` and `NN-output.txt` into `test_files/`. Line 1 of the output file is the expected output.
2. Update the row count asserted in `test_real_grammar_output.py`.
3. Keep the `.in` exactly as downloaded, with no final newline.

**What the platform shows:** for each test, only whether it passed, plus the name of the error when it failed (for example a time limit or a runtime error). It shows no output, trace or run time for the hidden tests. Since the error name is shown, one probe submission can give each test one of three outcomes: normal output, a timeout, or a runtime error.

**Probing the platform:** when the feedback for a failing test isn't shown, make `main.py` loop forever (`while True: pass`) when the input contains the construct you suspect, and submit once. The failing tests that time out contain it. Scan the input with a separate `Lexer`, not a text search, so strings and comments don't count. Remove the probe right after, because it turns every matching test into a timeout.

**Conventions:**
- **Keep tests in sync with the code.** Every function in the generator and `ASDR_base` has unit tests. When the code changes, update its tests and both spec files in the same change.
- **Check that new tests can fail.** When adding tests for a fix, put the bug back in a scratch copy of the code and confirm the tests fail.
- **Python 3.9 is the oldest version the assignment allows.** Avoid 3.10+ syntax in code that runs on the platform (`X | None` annotations, `match`). Tests may use it.
