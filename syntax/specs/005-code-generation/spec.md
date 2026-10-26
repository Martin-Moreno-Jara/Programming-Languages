# Spec 005 — Testing the parser code generator

## 1. Purpose and scope

This spec describes how to test that `ASDR_generator` in
`syntax/code_generator_script.py` writes a correct recursive descent parser
for a given LL(1) grammar.

- **In scope:** `ASDR_generator` (`populate_lines`, `write_program`,
  `generate`) and the behavior of the parser it generates, the class `ASDR`.
- **Out of scope:** FIRST, FOLLOW, prediction sets and the LL(1) check
  (specs 001 to 004), the lexer, and `ASDR_base` on its own. `ASDR_base.match`
  and `format_error_message` are used by the generated parser. Since the
  doc's formatting moved there (2026-10-25), `format_expected_symbol`,
  `format_error_message` and `match` have unit tests too.

## 2. Interface under test

```python
g = Grammar(grammar)
g.process_grammar()                 # FIRST, FOLLOW and prediction sets
ASDR_generator(g).generate()        # writes ./syntax/ASDR.py

parser = ASDR(lexer)                # imported from the generated file
parser.main()                       # returns, or raises SyntacticalError
```

Things the tests have to work around:

- The output path `./syntax/ASDR.py` is relative to the **current working
  directory**. Tests change the working directory to a temporary folder that
  has a `syntax/` subfolder, so the real `syntax/ASDR.py` is never
  overwritten.
- `code_generator_script.py` uses `from .grammar import Grammar`, and the
  generated file uses `from .ASDR_base import ASDR_base`. Both only work when
  imported as part of the `syntax` package, with the project root on
  `sys.path`. Tests load the generated file as the module `syntax.ASDR`, for
  example with `importlib`, so that `.ASDR_base` resolves to the real
  `syntax/ASDR_base.py`.
- The parser reads tokens with `lexer.tokenize()`. Most tests pass in a
  **fake lexer** that returns a fixed list of `Token` objects (from
  `lexer/lexer.py`). The list ends with a `$` token, and the fake lexer keeps
  returning `$` after that, like the real one.

## 3. What "correct" means

Correctness is checked at two levels.

### 3.1 Structure of the generated code

Read the generated file and inspect it, for example with `ast.parse`:

- The file is valid Python.
- It defines `class ASDR(ASDR_base)`.
- There is exactly one `parse_A` method for **every** non-terminal `A`,
  including non-terminals that the start symbol never reaches.
- The expected list of an error is `self.pending`. It holds the tokens that
  could have started an alternative skipped since the last token was
  consumed. Rules that take an ε path add to it, `match` clears it after
  consuming a token, and every error adds its own tokens before raising.
- If `A` has a single production and it derives ε, `parse_A` has no `if`:
  it calls that production's non-terminals in order, or is `pass` for a
  lone ε.
- Otherwise `parse_A` has one `if`/`elif` branch per production of `A` other
  than a lone ε (the grammar puts ε last), in the order of the grammar.
  Branch `i` tests `self.cur_tok.type` against exactly the tokens of
  `predict[A][i]`.
- Inside a branch, the symbols of the production appear in order:
  `self.parse_X()` for a non-terminal `X` and `self.match('t')` for a
  terminal `t`.
- The final `else` starts with `self.pending|=set([...])`. The list holds the
  **raw token types** that start each branch:
  `(FIRST(production) − {ε}) ∩ predict[A][i]`. That leaves out FOLLOW(A) and
  the tokens removed by prediction exceptions. The list is sorted so the
  file is the same on every run.
  - `ASDR_generator(grammar, hidden_expected)` takes an optional
    `{A: {i: tokens}}`. The tokens keep their place in the branch test of
    production `i`, but are left out of `pending`. Because the generator uses a
    visible FIRST (`compute_visible_first`), they also stay out of every rule
    that starts with `A`. With no `hidden_expected`, visible FIRST is FIRST
    without ε, and the output is unchanged.
  - If `A` is nullable, that is the whole `else`.
  - Otherwise it then raises
    `SyntacticalError(self.format_error_message(self.report_expected_symbols()))`.
- `main`'s final check adds `"$"` to `pending` and raises the same way.
  `match(t)` adds `t` to `pending` and raises the same way.
- `ASDR_base.report_expected_symbols` returns `pending` sorted by type
  name, except that `tkn_num`, `tkn_str` and `$` sort as `valor_numerico`,
  `cadena_de_caracteres` and `final de archivo` (the grader's order; platform tests 13, 14, 27, 30). It doesn't change `pending`.
- `ASDR_base` shows them as the assignment doc asks:
  - `format_expected_symbol` shows a lexer symbol as itself (`tkn_plus` as
    `"+"`), `tkn_num` as `"valor_numerico"`, `tkn_str` as
    `"cadena_de_caracteres"`, `$` as `"final de archivo"`, and any other
    token unchanged, always in double quotes.
  - `format_error_message` joins them with `", "` in the order given, and
    shows a `$` lexeme as `final de archivo`.
- `main` reads the first token, calls `parse_S` for the start symbol `S` (the
  first key of the grammar), and then raises `SyntacticalError` if the
  current token is not `$`.

### 3.2 Behavior of the generated parser

Run `ASDR(fake_lexer).main()`:

- **Accept:** for every token sequence in the language, `main` returns
  without raising.
- **Reject:** for every sequence not in the language, `main` raises
  `SyntacticalError`. The error is about the **first** wrong token: the
  message contains that token's line, column and lexeme, and the token or
  tokens that were expected there.

## 4. Structural cases (G)

Each case builds a grammar, generates the file and checks the points in
§3.1.

| ID  | Grammar | What it checks |
|-----|---------|----------------|
| G1  | S → a | Smallest grammar: one non-terminal, one production |
| G2  | S → a \| b \| c | Several alternatives give one `if` and two `elif` branches, in order |
| G3  | S → A b<br>A → a \| ε | An ε production gets no branch; the `else` adds `a` to `pending` and doesn't raise |
| G4  | S → a b c | A production with terminals only |
| G5  | S → A B<br>A → a<br>B → b | A production with non-terminals only |
| G6  | S → a A b B<br>A → x<br>B → y | Terminals and non-terminals mixed, order kept |
| G7  | S → a a | The same terminal twice gives two `match` calls |
| G8  | S → A<br>A → a \| ε | A prediction set that contains `$` |
| G9  | S → a<br>U → u \| ε | Unreachable `U` still gets `parse_U` |
| G10 | S → ' \| " \| \\ | Tokens that need escaping are written correctly |
| G11 | S → if E then S end \| x<br>E → x == x \| y .. y | Multi-character tokens and keywords |
| G12 | B → b<br>A → B | The start symbol is the first key, even when it isn't alphabetically first |
| G13 | `grammar1` and `grammar2` in `main.py`, the expression grammar of spec 004 E1 (with `E'` and `T'` renamed to `Ep` and `Tp`, see §8), and the Lua-like grammar of spec 004 E2 | Realistic grammars |
| G14 | S → A b<br>A → ε | A rule whose only production is ε gives `pass` |
| G15 | S → A B<br>A → a \| ε<br>B → b \| ε | A single nullable production gives plain calls with no `if` |
| G16 | S → A x<br>A → y \| B<br>B → b \| ε | A nullable production that isn't ε gets a branch that tests FOLLOW(A) too; `pending` leaves FOLLOW out |

Two more cases check `pending`. In G16, `parse_A` adds `b` and `y` but not `x`. With `S → a | b` and an exception that removes `b` from the second production, the second branch tests `[]` and `pending` gets only `a`.

## 5. Behavior cases

The grammars come from §4. Token sequences are written as token types and
always end with `$`.

### 5.1 Accept (A)

| ID | Grammar | Input | What it checks |
|----|---------|-------|----------------|
| A1 | G1 | a | Shortest string |
| A2 | G2 | a; b; c | Each alternative is reachable |
| A3 | G3 | b; a b | The ε alternative and the non-ε alternative |
| A4 | G8 | (empty) | Empty input when the start symbol is nullable |
| A5 | grammar2 | c; a c; b c; a b c | Optional parts in all combinations |
| A6 | Expression grammar | id + id * ( id ) | Nesting across several non-terminals |
| A7 | Expression grammar | ( ( ( id ) ) ) with 50 levels | Deep recursion completes |
| A8 | Lua-like grammar | a nested if block | Keywords and right recursion in `Block` |
| A9 | G14 | b | A rule that is only ε |
| A10 | G15 | (empty); a; b; a b | A nullable start symbol with plain calls |
| A11 | G16 | x; y x; b x | Each path through a nullable production |

### 5.2 Reject (R)

| ID | Grammar | Input | Expected error |
|----|---------|-------|----------------|
| R1 | G1 | b | At the first token, expecting `a` (the `else` branch of `parse_S`) |
| R2 | G4 | a x c | At `x`, expecting `b` (a failed `match` in the middle of a production) |
| R3 | G4 | a b | At `$`, expecting `c` (input ends too early) |
| R4 | G1 | a a | At the second `a`, expecting `$` (extra tokens after a full parse) |
| R5 | G1 | (empty) | At `$` (empty input, start symbol not nullable) |
| R6 | G3 | c | At `c`, expecting both `a` and `b` (the error names the whole union) |
| R7 | Expression grammar | id + | At `$` (fails inside a recursive call) |
| R8 | Expression grammar | ( id | At `$`, expecting `)`, `*` and `+` (`Tp` and `Ep` took ε there) |
| R9 | grammar2 | d | At `d`, expecting `a`, `b` and `c` (pending builds up across rules) |
| R10 | grammar2 | a d | At `d`, expecting `b` and `c` but not `a` (`match` clears pending) |
| R11 | G16 | z | At `z`, expecting `b`, `x` and `y` |
| R12 | G16 | b b | At the second `b`, expecting only `x` |
| R13 | G15 | a a | At the second `a`, expecting `b` and `$` (`main` adds `$` to pending) |

The tests check the line, column and lexeme in the message, and which tokens
are named as expected. They don't check the rest of the wording.

## 6. End-to-end cases (E)

A few cases use the real `Lexer` instead of the fake one. They take Lua-like
source text, use a grammar whose terminals are lexer token types (`id`,
`tkn_num`, `tkn_assign`, keywords, and so on), and run `generate`, the
import and `main()`.

| ID | Source | Expected |
|----|--------|----------|
| E1 | `x = 1` | Accepted |
| E2 | `if x then y = 2 end` | Accepted |
| E3 | `if x then y = 2` | Error at the end of input, expecting `end`, `id` and `if` |
| E4 | `x = = 1` | Error at the second `=`, with its line and column |
| E5 | Code spread over several lines with an error on line 3 | The error reports line 3 |

## 7. Properties checked across cases

- **Deterministic.** Two fresh generators for the same grammar write
  identical files.
- **Grammar unchanged.** `grammar`, `first`, `follow` and `predict` are the
  same before and after generating.
- **Overwrites.** Generating into a folder that already has an `ASDR.py`
  replaces it completely.
- **Isolation.** Every test uses its own temporary folder and its own
  `Grammar` object. No test depends on another having run first.
- **Termination.** Every test has a time limit, so a parser stuck in a loop
  fails instead of hanging the suite.

## 8. Out of scope (behavior not defined)

- Non-terminal names that are not valid Python identifiers (`E'`,
  `exp-list`).
- Grammars that are not LL(1), or a `Grammar` whose prediction sets were never
  computed.
- Calling `generate()` twice on the same generator object. It appends to
  `self.lines` again, so the file would contain the class twice.
- Running from a working directory with no `syntax/` folder.
- The exact wording of the error message, which belongs to
  `ASDR_base.format_error_message`.
- Grammar shapes that are out of scope in specs 001 to 004 (empty productions
  `[]`, ε inside a longer production, a non-terminal with no productions).

## 9. Test organization

- File: `syntax/tests/test_code_generator.py`.
- Fixtures: a temporary `syntax/` output folder with the working directory
  changed to it, a loader that imports the generated file as `syntax.ASDR`,
  and a fake lexer built from a list of token types.
- Reuse the helpers in `conftest.py` where they fit, such as `new_grammar`.
- Use `pytest.mark.parametrize` for the G, A, R and E tables.
- Failing tests get an xfail mark as in specs 001 to 004. The reason describes
  only the symptom, never the cause or a fix.
- Run with `pytest tests` from `syntax/`.
- If `ASDR_generator` changes (new methods, a different output path or a
  different shape of generated code), update this spec and its tests to match
  (see `syntax/AGENTS.md`).
