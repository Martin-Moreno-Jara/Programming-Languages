# Lua Lexical Analyzer

*Programming Languages, Universidad Nacional de Colombia, 2026-II. Assignment 1.*

A lexer for a subset of **Lua 5.5**, written in Python 3.9 with no external dependencies. It reads Lua source code from standard input and prints one token per line. It stops at the first lexical error.

```bash
python main.py < program.lua
```

## Output format

| Token | Format | Example |
|---|---|---|
| Keyword | `<keyword,line,col>` | `<local,1,1>` |
| Identifier | `<id,lexeme,line,col>` | `<id,edad,1,7>` |
| Number | `<tkn_num,lexeme,line,col>` | `<tkn_num,3.145,2,18>` |
| String | `<tkn_str,content,line,col>` | `<tkn_str,Hola, Lua,1,7>` |
| Operator / symbol | `<tkn_name,line,col>` | `<tkn_geq,3,8>` |
| Lexical error | `>>> Error lexico (linea: X, posicion: Y)` | analysis stops here |

Lines and columns start at 1. A token's position is where its first character is.

## Scope

The assignment covers sections 2 and 3 of the Lua reference manual (metatables, garbage collection and coroutines are left out). The full statement is in `docs/`, with examples in `docs/output_format.txt`.

**Supported:**
- Keywords and identifiers (case-sensitive, ASCII letters, digits and `_`)
- Numbers: integers, decimals, scientific notation (`2.5e-3`), hexadecimals (`0xFF`, `0x1.8p-2`)
- Short strings with `"…"` or `'…'`, including escaped quotes and backslashes
- All 33 operators and symbols from the assignment table
- Comments: single-line `--`, and block comments `--[[ … ]]` / `--[==[ … ]==]`, which can span several lines
- Lexical errors: unknown characters, unclosed strings, line breaks inside a short string, unclosed block comments

**Not supported:** long-bracket strings (`[[…]]`, `[=[…]=]`). The course's test cases never use them (see *Decisions*).

## Architecture

There are two files:

- **`main.py`**: reads stdin, then calls `Lexer.tokenize()` and prints each token until `EOFError`.
- **`lexer.py`**: the `Lexer` class and the `LexicalError` exception.

`Lexer` reads the input string with a cursor (`pos`). It also tracks `line`, and `last_pos`, the index where the current line starts, so `col = start - last_pos + 1`. Each call to `tokenize()` returns one token:

```
tokenize()
 ├─ _cleanse_input()        skip whitespace, newlines (line += 1) and comments
 │    └─ _handle_comments() → _handle_multiline_comments()   for --[[ … ]] / --[=[ … ]=]
 ├─ end of input?  → raise EOFError (main.py stops)
 └─ _process_token()        choose a mode from the first character
      ├─ letter / _    → _mode_keyword_id()     longest identifier, then keyword-set lookup
      ├─ digit         → _mode_num()            hex regex if it starts with 0x, else decimal regex
      ├─ " or '        → _mode_simple_string()  scan to the matching quote, skipping \" and \\
      ├─ known symbol  → _mode_op_symbol()      longest match: tries 3, then 2, then 1 chars
      └─ anything else → raise LexicalError
```

**Design choices:**
- **One mode per token type, chosen by the first character.** Each mode takes the longest valid lexeme, as the spec requires (*principio de subcadena más larga*). For example, `120.075.389` → `120.075`, `.`, `389`.
- **Regexes where they're simplest** (identifiers, numbers) and a hand-written loop where state matters (strings, block comments that span lines and have `=` levels).
- **Lookup tables in `__init__`:** `keywords_set`, `operand_symbols_dict` (symbol → token name) and character sets (`digits_set`, `alfabetic_set`, `hexdigits_set`). Classifying a character is a set lookup, so non-ASCII letters and digits (`ñ`, `é`, `٣`) are rejected, as the spec requires.
- **Errors:** modes raise `LexicalError(message, line, col)`. `tokenize()` catches it, prints the required message and exits, so nothing is printed after an error. Any other exception prints `Unexpected error…`, which always means a bug.
- **Lexemes are printed as they appear in the source:** string lexemes are the text between the quotes, with escape sequences unchanged (`a\"b` stays `a\"b`).

## Decisions

Some rules aren't fully defined by the spec. These were settled against the course's grading platform:

| Rule | Behavior | Why |
|---|---|---|
| Built-in functions as keywords | `dofile error ipairs load loadfile next pairs pcall print select tonumber tostring warn xpcall` are printed as keywords, along with the Lua reserved words | The course treats built-ins as keywords. Each name was confirmed by submission. |
| `type` and `assert` | Identifiers | Making `type` a keyword broke a test, and `assert` made no difference. |
| A dot needs a digit after it | `3.` → `3` + `.`; `10..20` → `10`, `..`, `20` | `10..20` must lex as a concatenation. This is stricter than Lua, which accepts `3.`. |
| Malformed numbers | `3abc` → `tkn_num 3` + `id abc`; `1e` → `1` + `e`; `0xG` → `0` + `xG` | Longest match, as in the spec's `8.9!62834127` example. Lua would report an error, but the course's tests don't expect one. |
| Escape sequences | Kept as written, not interpreted | The spec says lexemes must show escape sequences as they appear in the source. |
| Unclosed string / comment | Error at the opening quote, or at the `--` of the comment | Error position = where the faulty token starts. |
| Spec example 3 prints `retornar` | We print `<return,…>` | Considered a typo in the spec. |
| Tabs | Count as one column | Never contradicted by a test. |

## Testing

Tests use **pytest** and live in `test-strategy/`:

| File | Content |
|---|---|
| `test_lexer.py` | Unit tests for each `Lexer` method (≈185), each on a small `Lexer("…")` input |
| `test_main.py` | End-to-end tests (≈40): runs `main.py` as a subprocess on the spec examples, small inputs for spec rules, and every file in `test-cases/` |
| `conftest.py` | Shared helpers: `lex_all(src)` (tokenizes everything and captures the error line), `run_main(stdin)` |
| `test-plan.md` | What is tested and why, function by function, plus open questions and decisions |
| `test-tasks.md` | One checkbox per test, with the exact input and expected output |

```bash
pip install pytest
python -m pytest test-strategy -q
```

`test-cases/*.in` are the course's public inputs. They have no expected output files, so the tests check selected lines and the overall output format.

**Conventions:**
- Every function in `lexer.py` has unit tests. When a function is added, renamed or removed, its tests and the two `.md` files are updated with it.
- A test for a feature that isn't implemented yet is marked `@pytest.mark.xfail(strict=True)`. When the feature works, the test passes unexpectedly and the run fails, which means the mark should be removed. No tests are currently marked `xfail`.
