# Test Plan – Lua Lexical Analyzer

## 1. Goal
Check that the lexer turns Lua source code (from stdin) into the token list required by the course spec, one token per line, and stops with the right message on the first lexical error.

| Kind | Format | Example |
|---|---|---|
| Keyword | `<keyword,line,col>` | `<local,1,1>` |
| Identifier | `<id,lexeme,line,col>` | `<id,edad,1,7>` |
| Number | `<tkn_num,lexeme,line,col>` | `<tkn_num,3.145,2,18>` |
| String | `<tkn_str,content,line,col>` (no delimiters) | `<tkn_str,Hola, Lua,1,7>` |
| Operator/symbol | `<tkn_name,line,col>` | `<tkn_geq,3,8>` |
| Lexical error | `>>> Error lexico (linea: X, posicion: Y)` | then stop |

Lines and columns start at 1. Column = position of the token's **first** character. A number or string lexeme is printed exactly as it appears in the source.

## 2. Test layout
- Tool: **pytest**. Tests go in `test-strategy/`:
  - `test_lexer.py`: unit tests. Uses `from lexer import Lexer, LexicalError` and builds a `Lexer("…")` for each case. No stdin is involved.
  - `test_main.py`: end-to-end tests. Runs `python main.py` with `subprocess`, sends the input through stdin and compares the full stdout.
- When `tokenize()` finds a lexical error it prints the message and calls `exit()`. Unit tests catch this with `pytest.raises(SystemExit)` and read the printed text with `capsys`.
- Tests check spec behaviour. Tests that fail because of a known bug (section 6) are marked `xfail` with a reason. When the bug is fixed, the mark is removed.

## 3. Unit tests – `lexer.py`

### 3.1 `LexicalError`
- It stores `message`, `line` and `col`. `LexicalError("m", 3, 7)` → `.line == 3`, `.col == 7`.
- It can be raised and caught as an `Exception`.

### 3.2 `Lexer.__init__`
- Starts at `line = 1`, `pos = 0`, `last_pos = 0`.
- The keyword set contains: `and break do else elseif end error false for function global goto if in local nil not or print pcall repeat return then true until warn while`.
- The operator dictionary has **all 33** symbols from the spec table, each with the correct `tkn_` name (e.g. `"//" → tkn_floor_div`, `"::" → tkn_goto`, `"..." → tkn_varargs`).
- `digits_set` holds exactly the ASCII digits `0-9`. `alfabetic_set` holds exactly the ASCII letters `a-z`, `A-Z` and `_`. `_process_token` uses them to classify a token's first character.

### 3.3 `peek(offset)`
- `Lexer("abc").peek()` → `"a"`. `peek(2)` → `"c"`.
- Reading past the end gives `None`: `peek(3)` → `None`. `Lexer("").peek()` → `None`.
- Respects the current `pos`: after `pos = 1`, `peek()` → `"b"`.

### 3.4 `calc_inline_pos(start)`
- `last_pos = 0`, `start = 0` → `1`. `start = 6` → `7`.
- After a newline: `last_pos = 10`, `start = 13` → `4`.

### 3.5 `_mode_keyword_id(start)`
- Keywords: `"while"` → `<while,1,1>`. Every word in the keyword set is checked once.
- Case sensitivity: `"PRINT"` → `<id,PRINT,1,1>`. `"wHILe"` → `<id,wHILe,1,1>`.
- Digits and underscores: `"my_Var1"` → `<id,my_Var1,1,1>`. `"_f"` → `<id,_f,1,1>`. `"vari8"` → `<id,vari8,1,1>`.
- Stops at a non-word character: `"abc(x"` → `<id,abc,1,1>`, and `pos` ends at 3.
- A keyword is not split out of a longer word: `"ifx"` → `<id,ifx,…>`. `"endif"` → `<id,endif,…>`.
- A word at the very end of the input does not crash.

### 3.6 `_mode_num(start)`
**Decimal**
- Integer: `"16 "` → `<tkn_num,16,1,1>`.
- With a fraction: `"3.145 "` → `<tkn_num,3.145,1,1>`.
- Trailing dot is part of the number: `"3."` → `<tkn_num,3.,1,1>`. A number must **start with a digit**: `.5` is `tkn_period` + `tkn_num` (consistent with the spec's `120.075.389` example).
- Longest match with two dots: `"120.075.389"` → `<tkn_num,120.075,…>`, and `pos` stops on the second `.`.
- Stops before a non-digit: `"8.9!"` → `<tkn_num,8.9,…>`. `"6="` → `<tkn_num,6,…>`.
- Number at the very end of the input: `"5"` → `<tkn_num,5,1,1>`, with no crash.

**Scientific notation**
- `"1e10"` → `<tkn_num,1e10,1,1>`. `"1E10"` → `<tkn_num,1E10,1,1>`.
- Signed exponent: `"2.5e-3"` → `<tkn_num,2.5e-3,…>`. `"4E+2"` → `<tkn_num,4E+2,…>`.
- Mixed with a trailing dot: `"3.e1"` → one number.
- No digits after `e` (`"1e"`, `"1e+"`, `"1ex"`, `"2.5e-"`): longest match, so the number ends before the `e` (`<tkn_num,1,…>`, then the `e` is lexed as the next token). Not a lexical error, like `3abc` → `tkn_num` + `id` (see section 7).

**Hexadecimal**
- `"0xFF"` → `<tkn_num,0xFF,1,1>`. `"0Xa1"` → `<tkn_num,0Xa1,…>` (both upper and lower case are allowed).
- Hex fraction: `"0x1.8"` → one number.
- Binary exponent with `p`/`P`: `"0x1p4"`, `"0x1.8P-2"` → one number.
- No hex digits after `0x` (`"0x"`, `"0xG"`): longest match, so `<tkn_num,0,…>` and the `x` is lexed as the next token. Not a lexical error.
- `e` is a hex digit, not an exponent: `"0x1e2"` → `<tkn_num,0x1e2,…>`.

### 3.7 `_mode_string(start)` – short strings (`"…"` / `'…'`)
- Double quotes: `"\"Hola, Lua\""` → `<tkn_str,Hola, Lua,1,1>`.
- Single quotes: `"'abc'"` → `<tkn_str,abc,1,1>`.
- The other kind of quote inside the string is kept: `'"double" string'` → `<tkn_str,"double" string,…>`.
- Spaces and letter case are kept exactly: `"\"Valor de @: \""` → lexeme `Valor de @: `.
- Escape sequences are kept as written: `"a\"b"` → `<tkn_str,a\"b,…>`. `"x\\"` → `<tkn_str,x\\,…>`.
- Empty string: `""` → `<tkn_str,,1,1>`.
- Strings next to each other: `'U''n'` gives two tokens, `U` then `n`, with the right columns.
- Unclosed string (`"Hola` with no closing quote, or a newline before the closing quote) → `LexicalError` at the opening quote's line and column. The column is relative to the line: `x\n  y = "ab` → (2, 7).

### 3.8 Long-bracket strings (`[[…]]`, `[==[…]==]`)
There is no dedicated method for these yet. They are tested through `_process_token()` / `tokenize()`. If a new method is added for them, these cases move under it.
- `"[[hola]]"` → `<tkn_str,hola,1,1>`.
- With equals signs: `"[==[a]]b]==]"` → `<tkn_str,a]]b,1,1>`. Only the closing bracket with the same number of `=` ends the string.
- Multi-line: `"[[a\nb]]x"` → one string at (1,1), then `x` gets line 2 and the right column. The line counter and `last_pos` are updated inside the string.
- A newline right after the opening bracket is dropped (Lua rule): `"[[\nhi]]"` → lexeme `hi`.
- Escapes are **not** processed: `"[[a\nb]]"`, written with a literal backslash and `n`, keeps `a\nb`.
- Empty: `"[[]]"` → `<tkn_str,,1,1>`.
- A plain `[` is still a symbol: `"a[1]"` → `id`, `tkn_opening_bra`, `tkn_num`, `tkn_closing_bra`.
- `[=` not followed by `[` (e.g. `"[=x"`) → lexical error at the `[` (Lua: "invalid long string delimiter").
- Unclosed: `"[[abc"` → `LexicalError` at the opening bracket.

### 3.9 `_mode_op_symbol(start)`
- Every single-character symbol maps to its name: `+ → tkn_plus`, `( → tkn_opening_par`, `# → tkn_length`, …
- Longest match: `>=` → `tkn_geq`, `==` → `tkn_equal`, `~=` → `tkn_neq`, `//` → `tkn_floor_div`, `..` → `tkn_concat`, `...` → `tkn_varargs`, `::` → `tkn_goto`, `<<` / `>>` → shift tokens.
- Does not combine pairs that are not symbols: `"<>"` → `tkn_less` (the `>` is left for the next token).
- Runs of symbols split by longest match: `"===="` → `tkn_equal`, `tkn_equal`. `">=="` → `tkn_geq`, `tkn_assign`.
- A symbol at the very end of the input (`")"`) → `<tkn_closing_par,1,1>`, with no crash.

### 3.10 `_handle_comments()` and `_handle_multiline_comments(...)`
- Single-line comment: `"-- hi\nx"` → skips up to the `\n` (does not consume it).
- Comment at end of file without a newline → no crash.
- Block comment on one line: `"--[[ a ]]x"` → `pos` ends on `x`.
- Multi-line block comment: the line counter goes up once per `\n` inside it, and `last_pos` is updated.
- With equals signs: `"--[==[ a ]] b ]==]x"` → only `]==]` closes it.
- Empty block comment: `"--[[]]"` → fine.
- `-- [[` (with a space) and `--[=x` are **single-line** comments.
- Unclosed block comment `"--[[ open"` → `LexicalError` at the comment's starting line and column.

### 3.11 `_cleanse_input()`
- Skips spaces, `\t`, `\r`, `\v`, `\f`.
- On `\n`: `line += 1` and `last_pos` points to the start of the new line.
- Skips several comments and blank lines in a row, and stops on the first real character.
- Does **not** skip a single `-` (`"- 3"` stops on `-`).

### 3.12 `_process_token()`
Takes no arguments: it reads the token start from `self.pos` and the first character from `peek()`.
- Sends each kind of input to the right handler: a character in `alfabetic_set` (letter or `_`) → keyword/id, a character in `digits_set` → number, `"` or `'` → short string, `[[` or `[=` → long string, any other known symbol → operator.
- Starts at the current `pos`, not at 0: with `pos = 3` on `"ab cd "` it returns `<id,cd,1,4>`.
- Unknown characters raise `LexicalError` at the right position: `@`, `?`, `!`, `$`, `` ` ``, and non-ASCII characters such as `ñ`, `◕`, `¡`, `é`. Non-ASCII digits (e.g. `٣`) are also errors, because the check is a set lookup, not a regex `\d`.
- At end of input (`peek()` is `None`) it raises `LexicalError` instead of crashing. `tokenize()` normally prevents this case by raising `EOFError` first.

### 3.13 `tokenize()`
Wrapper: calls `_cleanse_input()`, raises `EOFError` if nothing is left, otherwise returns `_process_token()`. Lexical errors and unexpected exceptions are handled here.
- Returns one token string per call, in order.
- The token position is taken **after** whitespace and comments are skipped: `"  -- c\n\t x "` → `<id,x,2,3>`.
- Raises `EOFError` when only whitespace or comments are left, and on empty input.
- On a lexical error: prints `>>> Error lexico (linea: X, posicion: Y)` and exits (`SystemExit`).
- Never prints `Unexpected error ocurred …` for any input. This message means a crash, not a lexical error.

## 4. End-to-end tests – `main.py`

### 4.1 Reference examples (exact output match)
Run each of the 9 examples in `docs/output_format.txt` and compare stdout line by line:
1. `local matricula = 9 …` – keywords, id, `>=`, number, string, several lines.
2. `print("Hola, Lua") /* … (◕‿◕) */` – `/*` is **not** a comment. Error at `◕` (1, 38).
3. Keywords with lots of indentation. The spec shows `<retornar,6,6>`, which looks like a typo. The test expects `<return,6,6>` (to confirm).
4. Case sensitivity (`PRINT`, `wHILe`, `WHILE`, `while`).
5. Single-line and block comments are ignored, and line numbers stay correct after them.
6. `local edad = 16 …` – a full small program.
7. Negative number (`-` is its own `tkn_minus`), strings containing the other quote type, and a trailing comment.
8. `@` gives an error after a few valid tokens, and nothing more is printed.
9. `_f 4.559<>6="1"ñvari8` – longest match plus a non-ASCII error at (1, 16).

### 4.2 Extra spec rules (small hand-written inputs)
- `nil --comment` → only `<nil,1,1>`.
- `120.075.389` → `<tkn_num,120.075,1,1>`, `<tkn_period,1,8>`, `<tkn_num,389,1,9>`.
- `8.9!62834127` → `<tkn_num,8.9,1,1>`, then the error at (1, 4).
- `x = 0xFF + 1e3` → `id`, `tkn_assign`, `<tkn_num,0xFF,1,5>`, `tkn_plus`, `<tkn_num,1e3,1,12>`.
- `s = [[multi\nline]] print(s)` → one `tkn_str` on line 1, then `print` with line 2 positions.
- Empty input, or only comments → no output, exit without a crash.
- No newline at the end of the input (last token is an id, number, symbol or string) → all tokens printed, no crash.
- Windows line endings (`\r\n`) → same output as `\n`.
- After an error, **nothing** else is printed.

### 4.3 Real-world inputs (`test-cases/*.in`, no expected output)
Smoke tests plus spot checks:
- All files: the program finishes, never prints `Unexpected error`, and every output line matches one of the formats in section 1.
- `00`, `01`: keyword recognition, and a block comment that spans lines (`proof` at 17,12).
- `02`, `05`, `13`: full programs – strings with accents and `\n` escapes, `..`, `,`, comments after code.
- `03`: longest match on `4.559.8777===<<>><>>>>>=>==>====>=>><>120.075.389`.
- `06`: `...` followed by a number, then an error at `?`.
- `07`: strings right next to each other, inside `()`, `[]` and `{}`. **Note:** `['C'…]` must stay `tkn_opening_bra`, because the `[` is not followed by `[` or `=`.
- `08`: relational operators, and ids that look like token names.
- `12`: `#######`, `//`, `--[[]]`, an unclosed string → lexical error at the opening quote, not a crash.

## 5. Keeping the plan up to date
- New function in `lexer.py` → add a group to section 3. For example, a long-string handler takes over section 3.8.
- Removed function → delete its group and its tests.
- `main.py` changes → review section 4.

## 6. Known bugs (tests expected to fail for now)
| Input | Expected (spec) | Current output |
|---|---|---|
| `[[hola]]` | `<tkn_str,hola,1,1>` | brackets + `id` |

## 7. Open questions (to confirm with the course staff)
- `return` vs `retornar` in spec example 3.
- Malformed numbers (`1e`, `0xG`, `4..5`, `3abc`): longest match is assumed above (`1` then `id e`), following the spec's `8.9!62834127` rule. Lua itself reports a malformed number. No accepted test case covers this yet.
- How should a long string that spans several lines be printed? Is the raw newline kept in the lexeme?

## 8. Notes
- **Number followed only by a dot (`3.`) – pending decision.** `_mode_num` currently accepts it as one number (`<tkn_num,3.,1,1>`), and `test_num_trailing_dot` checks this. Lua also accepts `3.` as a valid numeral. It is kept as valid for now. If it is changed to invalid, update `test_num_trailing_dot` and the "trailing dot" line in section 3.6. It also affects `4..5`, which currently gives `<tkn_num,4.,1,1>`, `<tkn_period,1,3>`, `<tkn_num,5,1,4>` (see section 7).
