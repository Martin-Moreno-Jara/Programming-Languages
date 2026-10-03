# Test Tasks – Lua Lexical Analyzer

Each task below becomes one pytest test, or one row of a parametrized test. Tick the box when the test is written and behaves as described.

**Legend**
- `test_lexer.py::name`: unit test file and function name (in `test-strategy/`).
- `test_main.py::name`: end-to-end test.
- **xfail**: the spec behaviour isn't implemented yet. Mark it with `@pytest.mark.xfail(reason=…)` and remove the mark once the bug is fixed.
- `Lexer(src).method(0)` means: build a fresh lexer on `src`, call the method with `start = 0`, and check the return value (and `pos` when listed). `_process_token()` takes no arguments; it starts at the lexer's current `pos`.
- Python string literals are used for inputs, so `"\n"` is a newline and `"\\n"` is a literal backslash followed by `n`.

## 0. Setup
- [x] `test-strategy/conftest.py`: put the project root on `sys.path` so `from lexer import Lexer, LexicalError` works.
- [x] Helper `lex_all(src) -> list[str]`: calls `Lexer(src).tokenize()` until `EOFError` or `SystemExit`. Returns every token, plus the error line if one was printed (captured stdout).
- [x] Helper `run_main(stdin: str) -> str`: runs `python main.py` from the project root with `subprocess.run(..., input=stdin, capture_output=True, text=True)` and returns stdout.
- [x] Helper `run_main_process(stdin: str) -> CompletedProcess`: same as `run_main`, but returns the full result (stdout, stderr, returncode). Used where the exit code is checked.

## 1. `LexicalError`
- [x] `test_lexer.py::test_lexical_error_stores_fields`: `LexicalError("m", 3, 7)` → `.message == "m"`, `.line == 3`, `.col == 7`.
- [x] `test_lexer.py::test_lexical_error_is_exception`: `raise LexicalError("m", 1, 1)` is caught by `except Exception`.

## 2. `Lexer.__init__`
- [x] `test_lexer.py::test_init_state`: `Lexer("x")` → `line == 1`, `pos == 0`, `last_pos == 0`, `data == "x"`.
- [x] `test_lexer.py::test_init_keywords`: `keywords_set == {and, break, do, else, elseif, end, error, false, for, function, global, goto, if, in, local, nil, not, or, print, pcall, repeat, return, then, true, until, warn, while}` (27 words).
- [x] `test_lexer.py::test_init_operator_table`: `operand_symbols_dict` has exactly the 33 spec entries (`& → tkn_bit_and`, `| → tkn_bit_or`, `~ → tkn_bitex_or`, `>> → tkn_right_shift`, `<< → tkn_left_shift`, `; → tkn_semicolon`, `: → tkn_colon`, `, → tkn_comma`, `. → tkn_period`, `:: → tkn_goto`, `.. → tkn_concat`, `... → tkn_varargs`, `{ → tkn_opening_key`, `} → tkn_closing_key`, `[ → tkn_opening_bra`, `] → tkn_closing_bra`, `( → tkn_opening_par`, `) → tkn_closing_par`, `# → tkn_length`, `+ → tkn_plus`, `- → tkn_minus`, `* → tkn_times`, `/ → tkn_div`, `// → tkn_floor_div`, `^ → tkn_power`, `% → tkn_mod`, `== → tkn_equal`, `~= → tkn_neq`, `<= → tkn_leq`, `>= → tkn_geq`, `> → tkn_greater`, `< → tkn_less`, `= → tkn_assign`).
- [x] `test_lexer.py::test_init_digits_set`: `Lexer("x").digits_set == set("0123456789")`.
- [x] `test_lexer.py::test_init_alfabetic_set`: `Lexer("x").alfabetic_set` == every ASCII letter (`a-z`, `A-Z`) plus `_`.

## 3. `peek(offset)`
- [x] `test_lexer.py::test_peek_current`: `Lexer("abc").peek()` → `"a"`.
- [x] `test_lexer.py::test_peek_offset`: `Lexer("abc").peek(2)` → `"c"`.
- [x] `test_lexer.py::test_peek_past_end`: `Lexer("abc").peek(3)` → `None`.
- [x] `test_lexer.py::test_peek_empty_input`: `Lexer("").peek()` → `None`.
- [x] `test_lexer.py::test_peek_respects_pos`: `lx = Lexer("abc"); lx.pos = 1; lx.peek()` → `"b"`.

## 4. `calc_inline_pos(start)`
- [x] `test_lexer.py::test_calc_inline_pos_first_char`: `last_pos = 0`, `calc_inline_pos(0)` → `1`.
- [x] `test_lexer.py::test_calc_inline_pos_first_line`: `last_pos = 0`, `calc_inline_pos(6)` → `7`.
- [x] `test_lexer.py::test_calc_inline_pos_after_newline`: `last_pos = 10`, `calc_inline_pos(13)` → `4`.

## 5. `_mode_keyword_id(start)`
- [x] `test_lexer.py::test_keyword_each` (parametrized over all 27 keywords): `Lexer(kw)._mode_keyword_id(0)` → `"<kw,1,1>"`.
- [x] `test_lexer.py::test_keyword_case_upper`: `Lexer("PRINT")._mode_keyword_id(0)` → `"<id,PRINT,1,1>"`.
- [x] `test_lexer.py::test_keyword_case_mixed`: `Lexer("wHILe")._mode_keyword_id(0)` → `"<id,wHILe,1,1>"`.
- [x] `test_lexer.py::test_id_digits_underscore`: `Lexer("my_Var1")._mode_keyword_id(0)` → `"<id,my_Var1,1,1>"`.
- [x] `test_lexer.py::test_id_leading_underscore`: `Lexer("_f")._mode_keyword_id(0)` → `"<id,_f,1,1>"`.
- [x] `test_lexer.py::test_id_trailing_digit`: `Lexer("vari8")._mode_keyword_id(0)` → `"<id,vari8,1,1>"`.
- [x] `test_lexer.py::test_id_stops_at_symbol`: `Lexer("abc(x")._mode_keyword_id(0)` → `"<id,abc,1,1>"`, `pos == 3`.
- [x] `test_lexer.py::test_keyword_prefix_is_id`: `Lexer("ifx")._mode_keyword_id(0)` → `"<id,ifx,1,1>"`.
- [x] `test_lexer.py::test_keyword_inside_word_is_id`: `Lexer("endif")._mode_keyword_id(0)` → `"<id,endif,1,1>"`.
- [x] `test_lexer.py::test_id_at_eof`: `Lexer("while")._mode_keyword_id(0)` → `"<while,1,1>"`, `pos == 5`, no exception.

## 6. `_mode_num(start)`
### Decimal
- [x] `test_lexer.py::test_num_integer`: `Lexer("16 ")._mode_num(0)` → `"<tkn_num,16,1,1>"`, `pos == 2`.
- [x] `test_lexer.py::test_num_decimal`: `Lexer("3.145 ")._mode_num(0)` → `"<tkn_num,3.145,1,1>"`.
- [x] `test_lexer.py::test_num_trailing_dot`: `Lexer("3. ")._mode_num(0)` → `"<tkn_num,3.,1,1>"`.
- [x] `test_lexer.py::test_num_two_dots_longest_match`: `Lexer("120.075.389")._mode_num(0)` → `"<tkn_num,120.075,1,1>"`, `pos == 7`.
- [x] `test_lexer.py::test_num_stops_at_invalid_char`: `Lexer("8.9!")._mode_num(0)` → `"<tkn_num,8.9,1,1>"`, `pos == 3`.
- [x] `test_lexer.py::test_num_stops_at_symbol`: `Lexer("6=")._mode_num(0)` → `"<tkn_num,6,1,1>"`, `pos == 1`.
- [x] `test_lexer.py::test_num_at_eof`: `Lexer("5")._mode_num(0)` → `"<tkn_num,5,1,1>"`. **xfail**: number at EOF raises `TypeError`.

### Scientific notation
- [ ] `test_lexer.py::test_num_exp_lower`: `Lexer("1e10 ")._mode_num(0)` → `"<tkn_num,1e10,1,1>"`. **xfail**: exponent not supported.
- [ ] `test_lexer.py::test_num_exp_upper`: `Lexer("1E10 ")._mode_num(0)` → `"<tkn_num,1E10,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_exp_negative`: `Lexer("2.5e-3 ")._mode_num(0)` → `"<tkn_num,2.5e-3,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_exp_positive`: `Lexer("4E+2 ")._mode_num(0)` → `"<tkn_num,4E+2,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_exp_after_trailing_dot`: `Lexer("3.e1 ")._mode_num(0)` → `"<tkn_num,3.e1,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_exp_missing_digits` (parametrized over `"1e "`, `"1e+ "`, `"1ex "`): `_mode_num(0)` raises `LexicalError` with `line == 1`, `col == 1`. **xfail**.

### Hexadecimal
- [ ] `test_lexer.py::test_num_hex_upper_digits`: `Lexer("0xFF ")._mode_num(0)` → `"<tkn_num,0xFF,1,1>"`. **xfail**: hex not supported.
- [ ] `test_lexer.py::test_num_hex_upper_prefix`: `Lexer("0Xa1 ")._mode_num(0)` → `"<tkn_num,0Xa1,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_hex_fraction`: `Lexer("0x1.8 ")._mode_num(0)` → `"<tkn_num,0x1.8,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_hex_binary_exp`: `Lexer("0x1p4 ")._mode_num(0)` → `"<tkn_num,0x1p4,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_hex_fraction_binary_exp`: `Lexer("0x1.8P-2 ")._mode_num(0)` → `"<tkn_num,0x1.8P-2,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_hex_e_is_digit`: `Lexer("0x1e2 ")._mode_num(0)` → `"<tkn_num,0x1e2,1,1>"`. **xfail**.
- [ ] `test_lexer.py::test_num_hex_malformed` (parametrized over `"0x "`, `"0xG "`): raises `LexicalError` with `line == 1`, `col == 1`. **xfail**.

## 7. `_mode_string(start)`: short strings
- [x] `test_lexer.py::test_str_double_quotes`: `Lexer('"Hola, Lua"')._mode_string(0)` → `"<tkn_str,Hola, Lua,1,1>"`, `pos == 11`.
- [x] `test_lexer.py::test_str_single_quotes`: `Lexer("'abc'")._mode_string(0)` → `"<tkn_str,abc,1,1>"`.
- [x] `test_lexer.py::test_str_other_quote_inside`: `Lexer("'\"double\" string'")._mode_string(0)` → `'<tkn_str,"double" string,1,1>'`.
- [x] `test_lexer.py::test_str_keeps_spaces`: `Lexer('"Valor de @: "')._mode_string(0)` → `"<tkn_str,Valor de @: ,1,1>"`.
- [x] `test_lexer.py::test_str_escaped_quote`: `Lexer('"a\\"b" ')._mode_string(0)` → `'<tkn_str,a\\"b,1,1>'`, `pos == 6`. **xfail**: the string stops at the escaped quote.
- [x] `test_lexer.py::test_str_escaped_backslash`: `Lexer('"x\\\\" ')._mode_string(0)` → `"<tkn_str,x\\\\,1,1>"` (source `x\\` kept as written).
- [x] `test_lexer.py::test_str_empty`: `Lexer('"" ')._mode_string(0)` → `"<tkn_str,,1,1>"`.
- [x] `test_lexer.py::test_str_adjacent`: `lex_all("'U''n'")` → `["<tkn_str,U,1,1>", "<tkn_str,n,1,4>"]`.
- [x] `test_lexer.py::test_str_unclosed_eof`: `Lexer('"Hola')._mode_string(0)` raises `LexicalError(line=1, col=1)`. **xfail**: raises `IndexError`.
- [x] `test_lexer.py::test_str_unclosed_newline`: `Lexer('"Ho\nla"')._mode_string(0)` raises `LexicalError(line=1, col=1)`. **xfail**: the newline is accepted inside the string.

## 8. Long-bracket strings (through `lex_all` / `tokenize`)
- [ ] `test_lexer.py::test_long_str_basic`: `lex_all("[[hola]]")` → `["<tkn_str,hola,1,1>"]`. **xfail**: long strings not supported.
- [ ] `test_lexer.py::test_long_str_level`: `lex_all("[==[a]]b]==]")` → `["<tkn_str,a]]b,1,1>"]`. **xfail**.
- [ ] `test_lexer.py::test_long_str_multiline_positions`: `lex_all("[[a\nb]]x")` → 2 tokens. The first starts with `"<tkn_str,a"` and ends with `",1,1>"`. The second is `"<id,x,2,4>"`. **xfail**.
- [ ] `test_lexer.py::test_long_str_skips_first_newline`: `lex_all("[[\nhi]]")` → `["<tkn_str,hi,1,1>"]`. **xfail**.
- [ ] `test_lexer.py::test_long_str_no_escapes`: `lex_all("[[a\\nb]]")` → `["<tkn_str,a\\nb,1,1>"]` (literal backslash-n kept). **xfail**.
- [ ] `test_lexer.py::test_long_str_empty`: `lex_all("[[]]")` → `["<tkn_str,,1,1>"]`. **xfail**.
- [ ] `test_lexer.py::test_plain_bracket_is_symbol`: `lex_all("a[1]\n")` → `["<id,a,1,1>", "<tkn_opening_bra,1,2>", "<tkn_num,1,1,3>", "<tkn_closing_bra,1,4>"]`.
- [ ] `test_lexer.py::test_long_str_invalid_delimiter`: `lex_all("[=x")` → `[">>> Error lexico (linea: 1, posicion: 1)"]`. **xfail**.
- [ ] `test_lexer.py::test_long_str_unclosed`: `lex_all("[[abc")` → `[">>> Error lexico (linea: 1, posicion: 1)"]`. **xfail**.

## 9. `_mode_op_symbol(start)`
- [x] `test_lexer.py::test_op_single_each` (parametrized over the 23 one-character symbols, input `sym + " "`): `_mode_op_symbol(0)` → `"<tkn_name,1,1>"`, `pos == 1`.
- [x] `test_lexer.py::test_op_double_each` (parametrized over `>> << :: .. // == ~= <= >=`, input `sym + " "`): → correct name, `pos == 2`.
- [x] `test_lexer.py::test_op_varargs`: `Lexer("... ")._mode_op_symbol(0)` → `"<tkn_varargs,1,1>"`, `pos == 3`.
- [x] `test_lexer.py::test_op_no_invalid_pair`: `Lexer("<>")._mode_op_symbol(0)` → `"<tkn_less,1,1>"`, `pos == 1`.
- [x] `test_lexer.py::test_op_run_equals`: `lex_all("==== ")` → `["<tkn_equal,1,1>", "<tkn_equal,1,3>"]`.
- [x] `test_lexer.py::test_op_run_geq_assign`: `lex_all(">== ")` → `["<tkn_geq,1,1>", "<tkn_assign,1,3>"]`.
- [x] `test_lexer.py::test_op_at_eof`: `Lexer(")")._mode_op_symbol(0)` → `"<tkn_closing_par,1,1>"`.

## 10. `_handle_comments()` and `_handle_multiline_comments(...)`
- [x] `test_lexer.py::test_comment_single_line`: `lx = Lexer("-- hi\nx"); lx._handle_comments()` → `pos == 5` (on the `\n`).
- [x] `test_lexer.py::test_comment_single_line_eof`: `Lexer("-- hi")._handle_comments()` → `pos == 5`, no exception.
- [x] `test_lexer.py::test_comment_block_inline`: `Lexer("--[[ a ]]x")._handle_comments()` → `pos == 9`.
- [x] `test_lexer.py::test_comment_block_multiline`: `Lexer("--[[a\nb\n]]x")._handle_comments()` → `pos == 10`, `line == 3`, `last_pos == 8`.
- [x] `test_lexer.py::test_comment_block_level`: `Lexer("--[==[ a ]] b ]==]x")._handle_comments()` → `pos == 18`.
- [x] `test_lexer.py::test_comment_block_empty`: `Lexer("--[[]]x")._handle_comments()` → `pos == 6`.
- [x] `test_lexer.py::test_comment_space_before_bracket`: `Lexer("-- [[\nx")._handle_comments()` → `pos == 5` (single-line).
- [x] `test_lexer.py::test_comment_bad_level_is_single_line`: `Lexer("--[=x\ny")._handle_comments()` → `pos == 5` (single-line).
- [x] `test_lexer.py::test_comment_bad_level_two_equals_is_single_line`: `Lexer("--[==x\ny")._handle_comments()` → `pos == 6` (single-line).
- [x] `test_lexer.py::test_comment_block_unclosed`: `lx = Lexer("x\n  --[[ open"); lx.pos, lx.line, lx.last_pos = 4, 2, 2; lx._handle_comments()` raises `LexicalError(line=2, col=3)`.
- [x] `test_lexer.py::test_multiline_handler_direct`: `lx = Lexer("--[[a]]x"); lx.pos = 2; lx._handle_multiline_comments(1, 1)` → `pos == 7`.
- [x] `test_lexer.py::test_multiline_handler_level`: `lx = Lexer("--[==[a]]b]==]x"); lx.pos = 6; lx._handle_multiline_comments(1, 1, 2)` → `pos == 14`.
- [x] `test_lexer.py::test_multiline_handler_newlines`: `lx = Lexer("--[[a\nb]]x"); lx.pos = 2; lx._handle_multiline_comments(1, 1)` → `pos == 9`, `line == 2`, `last_pos == 6`.
- [x] `test_lexer.py::test_multiline_handler_unclosed`: `lx = Lexer("--[[abc"); lx.pos = 2; lx._handle_multiline_comments(1, 1)` raises `LexicalError(line=1, col=1)`.

## 11. `_cleanse_input()`
- [x] `test_lexer.py::test_cleanse_whitespace`: `Lexer(" \t\r\v\fx")._cleanse_input()` → `pos == 5`, `line == 1`.
- [x] `test_lexer.py::test_cleanse_newlines`: `Lexer("\n\nab")._cleanse_input()` → `pos == 2`, `line == 3`, `last_pos == 2`.
- [x] `test_lexer.py::test_cleanse_mixed`: `Lexer("-- a\n\n--[[b]]  -- c\n  x")._cleanse_input()` → `pos == 22`, `line == 4`, `last_pos == 20`.
- [x] `test_lexer.py::test_cleanse_keeps_single_minus`: `Lexer("- 3")._cleanse_input()` → `pos == 0`.
- [x] `test_lexer.py::test_cleanse_empty`: `Lexer("")._cleanse_input()` → `pos == 0`, no exception.

## 12. `_process_token()`
- [x] `test_lexer.py::test_process_letter`: `Lexer("abc ")._process_token()` → `"<id,abc,1,1>"`.
- [x] `test_lexer.py::test_process_underscore`: `Lexer("_x ")._process_token()` → `"<id,_x,1,1>"`.
- [x] `test_lexer.py::test_process_digit`: `Lexer("9 ")._process_token()` → `"<tkn_num,9,1,1>"`.
- [x] `test_lexer.py::test_process_leading_dot_is_period`: `lex_all(".5 ")` → `["<tkn_period,1,1>", "<tkn_num,5,1,2>"]`.
- [x] `test_lexer.py::test_process_single_quote`: `Lexer("'a' ")._process_token()` → `"<tkn_str,a,1,1>"`.
- [x] `test_lexer.py::test_process_double_quote`: `Lexer('"a" ')._process_token()` → `"<tkn_str,a,1,1>"`.
- [x] `test_lexer.py::test_process_symbol`: `Lexer("+ ")._process_token()` → `"<tkn_plus,1,1>"`.
- [x] `test_lexer.py::test_process_reads_current_pos`: `lx = Lexer("ab cd "); lx.pos = 3; lx._process_token()` → `"<id,cd,1,4>"`.
- [x] `test_lexer.py::test_process_long_string`: `Lexer("[[a]] ")._process_token()` → `"<tkn_str,a,1,1>"`. **xfail**.
- [x] `test_lexer.py::test_process_long_string_level`: `Lexer("[=[a]=] ")._process_token()` → `"<tkn_str,a,1,1>"`. **xfail**.
- [x] `test_lexer.py::test_process_unknown_char` (parametrized over `@ ? ! $ ` ` ñ ◕ ¡ ٣ é`): `Lexer(ch)._process_token()` raises `LexicalError(line=1, col=1)`. `٣` (non-ASCII digit) and `é` (non-ASCII letter) are not in `digits_set` / `alfabetic_set`.
- [x] `test_lexer.py::test_process_unknown_char_position`: `lx = Lexer("ab\n  @"); lx.pos, lx.line, lx.last_pos = 5, 2, 3; lx._process_token()` raises `LexicalError(line=2, col=3)`.
- [x] `test_lexer.py::test_process_at_eof`: `Lexer("")._process_token()` raises `LexicalError(line=1, col=1)` (no `TypeError` on `peek() is None`).

## 13. `tokenize()`
- [x] `test_lexer.py::test_tokenize_sequence`: `lx = Lexer("a b\nc")`. Three calls → `"<id,a,1,1>"`, `"<id,b,1,3>"`, `"<id,c,2,1>"`.
- [x] `test_lexer.py::test_tokenize_eof_after_tokens`: on the same lexer, a fourth call raises `EOFError`.
- [x] `test_lexer.py::test_tokenize_position_after_cleanse`: `Lexer("  -- c\n\t x ").tokenize()` → `"<id,x,2,3>"` (start is read after `_cleanse_input()`).
- [x] `test_lexer.py::test_tokenize_empty`: `Lexer("").tokenize()` raises `EOFError`.
- [x] `test_lexer.py::test_tokenize_only_comments`: `Lexer("  -- c\n--[[x]]\n").tokenize()` raises `EOFError`.
- [x] `test_lexer.py::test_tokenize_error_exits`: `Lexer("@").tokenize()` raises `SystemExit`, and captured stdout is `">>> Error lexico (linea: 1, posicion: 1)\n"`.
- [x] `test_lexer.py::test_tokenize_never_unexpected_error` (parametrized over `"x = 5"`, `"a..."`, `")"`, `'"abc'`, `'x = "a\\"b"'`, `"[[hola]]"`): no line from `lex_all(src)` starts with `"Unexpected error"`. **xfail** only for `"x = 5"`, `'"abc'` and `'x = "a\\"b"'` (they still crash).

## 14. End-to-end: reference examples (`docs/output_format.txt`)
Each task: `run_main(input)` == expected stdout, line by line. The input is exactly as in the spec, with a trailing `\n`.
- [x] `test_main.py::test_ref1_matricula`: `local matricula = 9\n\nif matricula>=8 then\n   print("Ya acabando la carrera :)")\nend\n` → `<local,1,1>` `<id,matricula,1,7>` `<tkn_assign,1,17>` `<tkn_num,9,1,19>` `<if,3,1>` `<id,matricula,3,4>` `<tkn_geq,3,13>` `<tkn_num,8,3,15>` `<then,3,17>` `<print,4,4>` `<tkn_opening_par,4,9>` `<tkn_str,Ya acabando la carrera :),4,10>` `<tkn_closing_par,4,37>` `<end,5,1>`.
- [x] `test_main.py::test_ref2_c_comment_error`: `print("Hola, Lua") /* un comentario (◕‿◕) */\n` → `<print,1,1>` `<tkn_opening_par,1,6>` `<tkn_str,Hola, Lua,1,7>` `<tkn_closing_par,1,18>` `<tkn_div,1,20>` `<tkn_times,1,21>` `<id,un,1,23>` `<id,comentario,1,26>` `<tkn_opening_par,1,37>` `>>> Error lexico (linea: 1, posicion: 38)`.
- [x] `test_main.py::test_ref3_indentation`: `print    \n    false\n     in\n\n print  end\n     return \n` → `<print,1,1>` `<false,2,5>` `<in,3,6>` `<print,5,2>` `<end,5,9>` `<return,6,6>` (the spec prints `retornar`; we treat that as a typo).
- [x] `test_main.py::test_ref4_case_sensitivity`: `PRINT print \n\nPrint Mi_Variable\n\n\nwHILe WHILE while    \n` → `<id,PRINT,1,1>` `<print,1,7>` `<id,Print,3,1>` `<id,Mi_Variable,3,7>` `<id,wHILe,6,1>` `<id,WHILE,6,7>` `<while,6,13>`.
- [x] `test_main.py::test_ref5_comments`: `until\n   repeat in false o else\n\n   --this is for videogames enjoyers\n         in true Nene -- perfect\n   \n   --[[ I don´t have enough creativity\n      to write comments\n   ]] \n   v\n` → `<until,1,1>` `<repeat,2,4>` `<in,2,11>` `<false,2,14>` `<id,o,2,20>` `<else,2,22>` `<in,5,10>` `<true,5,13>` `<id,Nene,5,18>` `<id,v,10,4>`.
- [x] `test_main.py::test_ref6_edad`: `local edad = 16\n\nif edad>=18 then\n  print("Eres mayor de edad.")\nend\n` → `<local,1,1>` `<id,edad,1,7>` `<tkn_assign,1,12>` `<tkn_num,16,1,14>` `<if,3,1>` `<id,edad,3,4>` `<tkn_geq,3,8>` `<tkn_num,18,3,10>` `<then,3,13>` `<print,4,3>` `<tkn_opening_par,4,8>` `<tkn_str,Eres mayor de edad.,4,9>` `<tkn_closing_par,4,30>` `<end,5,1>`.
- [x] `test_main.py::test_ref7_negative_and_quotes`: `local my_Var1 = 2\nlocal my_Var2 = -3.145\nstring = '"double" string'\nstring2 = "'single' string"\n\n-- another single comment\n` → `<local,1,1>` `<id,my_Var1,1,7>` `<tkn_assign,1,15>` `<tkn_num,2,1,17>` `<local,2,1>` `<id,my_Var2,2,7>` `<tkn_assign,2,15>` `<tkn_minus,2,17>` `<tkn_num,3.145,2,18>` `<id,string,3,1>` `<tkn_assign,3,8>` `<tkn_str,"double" string,3,10>` `<id,string2,4,1>` `<tkn_assign,4,9>` `<tkn_str,'single' string,4,11>`.
- [x] `test_main.py::test_ref8_at_sign_error`: `print("Valor de @: ",@)\n` → `<print,1,1>` `<tkn_opening_par,1,6>` `<tkn_str,Valor de @: ,1,7>` `<tkn_comma,1,21>` `>>> Error lexico (linea: 1, posicion: 22)`.
- [x] `test_main.py::test_ref9_longest_match_error`: `_f 4.559<>6="1"ñvari8\n` → `<id,_f,1,1>` `<tkn_num,4.559,1,4>` `<tkn_less,1,9>` `<tkn_greater,1,10>` `<tkn_num,6,1,11>` `<tkn_assign,1,12>` `<tkn_str,1,1,13>` `>>> Error lexico (linea: 1, posicion: 16)`.

## 15. End-to-end: extra spec rules
- [x] `test_main.py::test_trailing_comment`: `nil --comment` → `<nil,1,1>`.
- [x] `test_main.py::test_number_period_number`: `120.075.389\n` → `<tkn_num,120.075,1,1>` `<tkn_period,1,8>` `<tkn_num,389,1,9>`.
- [x] `test_main.py::test_number_then_error`: `8.9!62834127\n` → `<tkn_num,8.9,1,1>` `>>> Error lexico (linea: 1, posicion: 4)`.
- [x] `test_main.py::test_hex_and_exponent`: `x = 0xFF + 1e3\n` → `<id,x,1,1>` `<tkn_assign,1,3>` `<tkn_num,0xFF,1,5>` `<tkn_plus,1,10>` `<tkn_num,1e3,1,12>`. **xfail**.
- [x] `test_main.py::test_long_string_line_tracking`: `s = [[multi\nline]] print(s)\n` → first lines `<id,s,1,1>` `<tkn_assign,1,3>`, then a token starting with `<tkn_str,multi`. The output ends with `<print,2,8>` `<tkn_opening_par,2,13>` `<id,s,2,14>` `<tkn_closing_par,2,15>`. **xfail**.
- [x] `test_main.py::test_empty_input`: `` → empty stdout, exit code 0 (uses `run_main_process`).
- [x] `test_main.py::test_only_comments`: `-- a\n--[[ b\n c ]]\n` → empty stdout, exit code 0 (uses `run_main_process`).
- [x] `test_main.py::test_eof_after_id`: `x = y` (no `\n`) → `<id,x,1,1>` `<tkn_assign,1,3>` `<id,y,1,5>`.
- [x] `test_main.py::test_eof_after_number`: `x = 5` (no `\n`) → `<id,x,1,1>` `<tkn_assign,1,3>` `<tkn_num,5,1,5>`. **xfail**.
- [x] `test_main.py::test_eof_after_symbol`: `f()` (no `\n`) → `<id,f,1,1>` `<tkn_opening_par,1,2>` `<tkn_closing_par,1,3>`.
- [x] `test_main.py::test_eof_after_string`: `s = "a"` (no `\n`) → `<id,s,1,1>` `<tkn_assign,1,3>` `<tkn_str,a,1,5>`.
- [x] `test_main.py::test_crlf_line_endings`: `a\r\nb\r\n` → `<id,a,1,1>` `<id,b,2,1>`.
- [x] `test_main.py::test_nothing_after_error`: `print("x") @ print\n` → `<print,1,1>` `<tkn_opening_par,1,6>` `<tkn_str,x,1,7>` `<tkn_closing_par,1,10>` `>>> Error lexico (linea: 1, posicion: 12)`, with nothing after it.

## 16. End-to-end: `test-cases/*.in`
- [x] `test_main.py::test_cases_well_formed` (parametrized over all `.in` files): every stdout line matches `^<(id|tkn_num|tkn_str),.*,\d+,\d+>$`, `^<[a-z_]+,\d+,\d+>$` or `^>>> Error lexico \(linea: \d+, posicion: \d+\)$`. No line contains `Unexpected error`. **xfail** for `12.in` only.
- [x] `test_main.py::test_case_00_keywords`: `test-cases/00.in` → exactly `<print,3,1>` `<true,3,7>` `<until,5,1>` `<nil,5,7>` `<while,5,11>` `<if,5,17>` `<else,7,1>` `<elseif,7,6>` `<error,7,13>`.
- [x] `test_main.py::test_case_01_block_comment`: `test-cases/01.in` → starts with `<if,3,1>` `<for,4,6>` `<pcall,4,13>`, and the last line is `<id,proof,17,12>`.
- [x] `test_main.py::test_case_02_strings_and_concat`: `test-cases/02.in` → contains `<tkn_str,¡Hola, bienvenido a la programación en Lua!,3,11>`, `<tkn_concat,23,18>` and `<tkn_concat,23,26>`. The last line is `<tkn_closing_par,27,42>`.
- [x] `test_main.py::test_case_03_longest_match`: `test-cases/03.in` → exactly `<tkn_num,4.559,7,1>` `<tkn_period,7,6>` `<tkn_num,8777,7,7>` `<tkn_equal,7,11>` `<tkn_assign,7,13>` `<tkn_left_shift,7,14>` `<tkn_right_shift,7,16>` `<tkn_less,7,18>` `<tkn_right_shift,7,19>` `<tkn_right_shift,7,21>` `<tkn_geq,7,23>` `<tkn_geq,7,25>` `<tkn_assign,7,27>` `<tkn_geq,7,28>` `<tkn_equal,7,30>` `<tkn_assign,7,32>` `<tkn_geq,7,33>` `<tkn_right_shift,7,35>` `<tkn_less,7,37>` `<tkn_greater,7,38>` `<tkn_num,120.075,7,39>` `<tkn_period,7,46>` `<tkn_num,389,7,47>`.
- [x] `test_main.py::test_case_05_loops`: `test-cases/05.in` → starts with `<local,4,1>` `<id,contador,4,7>` `<tkn_assign,4,16>`. Contains `<tkn_str,\n--- Ciclo repeat...until ---,15,7>` (escape kept) and `<tkn_minus,33,15>`. The last line is `<end,35,1>`.
- [x] `test_main.py::test_case_06_varargs_error`: `test-cases/06.in` → exactly `<id,_f,3,1>` `<tkn_num,4.559,3,4>` `<tkn_varargs,3,9>` `<tkn_num,6,3,12>` `<tkn_assign,3,13>` `<tkn_str,1,3,14>` `>>> Error lexico (linea: 3, posicion: 17)`.
- [x] `test_main.py::test_case_07_adjacent_strings`: `test-cases/07.in` → exactly `<tkn_opening_par,3,1>` `<tkn_str,HaBía una Vez,3,2>` `<tkn_closing_par,3,17>` `<tkn_str,U,3,19>` `<tkn_str,n,3,22>` `<tkn_str,a fea,3,25>` `<tkn_opening_bra,3,33>` `<tkn_str,C,3,34>` `<tkn_str,ala,3,37>` `<tkn_str,b,3,42>` `<tkn_str,a,3,45>` `<tkn_str,za,3,48>` `<tkn_closing_bra,3,52>` `<tkn_opening_key,3,53>` `<tkn_str,C,3,54>` `<tkn_str,ala,3,57>` `<tkn_str,b,3,62>` `<tkn_str,a,3,65>` `<tkn_str,za,3,68>` `<tkn_closing_key,3,72>`.
- [x] `test_main.py::test_case_08_relational`: `test-cases/08.in` → starts with `<tkn_equal,3,1>` `<return,3,6>` `<id,tkn_equal,3,15>` `<tkn_neq,4,1>`, and ends with `<tkn_geq,8,1>` `<return,8,6>` `<id,tkn_geq,8,15>`.
- [x] `test_main.py::test_case_12_unclosed_string`: `test-cases/12.in` → the output ends with `<local,9,1>` `<id,mensaje,9,7>` `<tkn_assign,9,15>` `>>> Error lexico (linea: 9, posicion: 17)`. **xfail**: crashes with `Unexpected error`.
- [x] `test_main.py::test_case_13_full_program`: `test-cases/13.in` → starts with `<local,4,1>` `<id,CONFIG_ACTIVA,4,7>` `<tkn_assign,4,21>`, and contains `<warn,12,9>`, `<error,19,9>` and `<pcall,37,24>`. The last line is `<end,43,1>`.

## 17. xfail index
The bug each group comes from:
- **Number at EOF** (`TypeError`): `test_num_at_eof`, `test_eof_after_number`, `test_tokenize_never_unexpected_error["x = 5"]`.
- **Unclosed string**: `test_str_unclosed_eof`, `test_str_unclosed_newline`, `test_case_12_unclosed_string`, `test_cases_well_formed[12.in]`, `test_tokenize_never_unexpected_error['"abc']`.
- **Escaped quote**: `test_str_escaped_quote`, `test_tokenize_never_unexpected_error['x = "a\\"b"']`.
- **Scientific notation**: all `test_num_exp_*`, `test_hex_and_exponent`.
- **Hexadecimal**: all `test_num_hex_*`, `test_hex_and_exponent`.
- **Long-bracket strings**: all `test_long_str_*` except `test_plain_bracket_is_symbol`, plus `test_process_long_string*` and `test_long_string_line_tracking`.
