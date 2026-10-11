import pytest

from lexer import Lexer, LexicalError

KEYWORDS = {
    # Lua reserved words
    "and", "break", "do", "else", "elseif", "end", "false", "for", "function",
    "global", "goto", "if", "in", "local", "nil", "not", "or", "repeat",
    "return", "then", "true", "until", "while",
    # Built-in functions treated as keywords by the course
    "dofile", "error", "ipairs", "load", "loadfile", "next", "pairs", "pcall",
    "print", "select", "tonumber", "tostring", "warn", "xpcall",
}

OPERATORS = {
    "&": "tkn_bit_and",
    "|": "tkn_bit_or",
    "~": "tkn_bitex_or",
    ">>": "tkn_right_shift",
    "<<": "tkn_left_shift",
    ";": "tkn_semicolon",
    ":": "tkn_colon",
    ",": "tkn_comma",
    ".": "tkn_period",
    "::": "tkn_goto",
    "..": "tkn_concat",
    "...": "tkn_varargs",
    "{": "tkn_opening_key",
    "}": "tkn_closing_key",
    "[": "tkn_opening_bra",
    "]": "tkn_closing_bra",
    "(": "tkn_opening_par",
    ")": "tkn_closing_par",
    "#": "tkn_length",
    "+": "tkn_plus",
    "-": "tkn_minus",
    "*": "tkn_times",
    "/": "tkn_div",
    "//": "tkn_floor_div",
    "^": "tkn_power",
    "%": "tkn_mod",
    "==": "tkn_equal",
    "~=": "tkn_neq",
    "<=": "tkn_leq",
    ">=": "tkn_geq",
    ">": "tkn_greater",
    "<": "tkn_less",
    "=": "tkn_assign",
}


# 1. LexicalError
def test_lexical_error_stores_fields():
    error = LexicalError("m", 3, 7)
    assert error.message == "m"
    assert error.line == 3
    assert error.col == 7


def test_lexical_error_is_exception():
    with pytest.raises(Exception) as exc_info:
        raise LexicalError("m", 1, 1)
    assert isinstance(exc_info.value, LexicalError)


# 2. Lexer.__init__
def test_init_state():
    lexer = Lexer("x")
    assert lexer.data == "x"
    assert lexer.line == 1
    assert lexer.pos == 0
    assert lexer.last_pos == 0


def test_init_keywords():
    assert len(KEYWORDS) == 37
    assert Lexer("x").keywords_set == KEYWORDS


def test_init_operator_table():
    assert len(OPERATORS) == 33
    assert Lexer("x").operand_symbols_dict == OPERATORS


def test_init_digits_set():
    assert Lexer("x").digits_set == set("0123456789")


def test_init_alfabetic_set():
    expected = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
    assert Lexer("x").alfabetic_set == expected


# 3. peek(offset)
def test_peek_current():
    assert Lexer("abc").peek() == "a"


def test_peek_offset():
    assert Lexer("abc").peek(2) == "c"


def test_peek_past_end():
    assert Lexer("abc").peek(3) is None


def test_peek_empty_input():
    assert Lexer("").peek() is None


def test_peek_respects_pos():
    lexer = Lexer("abc")
    lexer.pos = 1
    assert lexer.peek() == "b"


# 4. calc_inline_pos(start)
def test_calc_inline_pos_first_char():
    assert Lexer("").calc_inline_pos(0) == 1


def test_calc_inline_pos_first_line():
    assert Lexer("").calc_inline_pos(6) == 7


def test_calc_inline_pos_after_newline():
    lexer = Lexer("")
    lexer.last_pos = 10
    assert lexer.calc_inline_pos(13) == 4


# 5. _mode_keyword_id(start)
@pytest.mark.parametrize("keyword", sorted(KEYWORDS))
def test_keyword_each(keyword):
    assert Lexer(keyword)._mode_keyword_id(0) == f"<{keyword},1,1>"


def test_keyword_case_upper():
    assert Lexer("PRINT")._mode_keyword_id(0) == "<id,PRINT,1,1>"


def test_keyword_case_mixed():
    assert Lexer("wHILe")._mode_keyword_id(0) == "<id,wHILe,1,1>"


def test_id_digits_underscore():
    assert Lexer("my_Var1")._mode_keyword_id(0) == "<id,my_Var1,1,1>"


def test_id_leading_underscore():
    assert Lexer("_f")._mode_keyword_id(0) == "<id,_f,1,1>"


def test_id_trailing_digit():
    assert Lexer("vari8")._mode_keyword_id(0) == "<id,vari8,1,1>"


def test_id_stops_at_symbol():
    lexer = Lexer("abc(x")
    assert lexer._mode_keyword_id(0) == "<id,abc,1,1>"
    assert lexer.pos == 3


def test_keyword_prefix_is_id():
    assert Lexer("ifx")._mode_keyword_id(0) == "<id,ifx,1,1>"


def test_keyword_inside_word_is_id():
    assert Lexer("endif")._mode_keyword_id(0) == "<id,endif,1,1>"


def test_id_at_eof():
    lexer = Lexer("while")
    assert lexer._mode_keyword_id(0) == "<while,1,1>"
    assert lexer.pos == 5


# 6. _mode_num(start) - decimal
def test_num_integer():
    lexer = Lexer("16 ")
    assert lexer._mode_num(0) == "<tkn_num,16,1,1>"
    assert lexer.pos == 2


def test_num_decimal():
    assert Lexer("3.145 ")._mode_num(0) == "<tkn_num,3.145,1,1>"


# A dot needs at least one digit after it to be part of the number
def test_num_trailing_dot():
    lexer = Lexer("3. ")
    assert lexer._mode_num(0) == "<tkn_num,3,1,1>"
    assert lexer.pos == 1


def test_num_followed_by_concat(lex_all):
    assert lex_all("10..20") == ["<tkn_num,10,1,1>", "<tkn_concat,1,3>", "<tkn_num,20,1,5>"]


def test_num_two_dots_longest_match():
    lexer = Lexer("120.075.389")
    assert lexer._mode_num(0) == "<tkn_num,120.075,1,1>"
    assert lexer.pos == 7


def test_num_stops_at_invalid_char():
    lexer = Lexer("8.9!")
    assert lexer._mode_num(0) == "<tkn_num,8.9,1,1>"
    assert lexer.pos == 3


def test_num_stops_at_symbol():
    lexer = Lexer("6=")
    assert lexer._mode_num(0) == "<tkn_num,6,1,1>"
    assert lexer.pos == 1


def test_num_at_eof():
    assert Lexer("5")._mode_num(0) == "<tkn_num,5,1,1>"


# 6. _mode_num(start) - scientific notation
def test_num_exp_lower():
    assert Lexer("1e10 ")._mode_num(0) == "<tkn_num,1e10,1,1>"


def test_num_exp_upper():
    assert Lexer("1E10 ")._mode_num(0) == "<tkn_num,1E10,1,1>"


def test_num_exp_negative():
    assert Lexer("2.5e-3 ")._mode_num(0) == "<tkn_num,2.5e-3,1,1>"


def test_num_exp_positive():
    assert Lexer("4E+2 ")._mode_num(0) == "<tkn_num,4E+2,1,1>"


def test_num_exp_after_trailing_dot():
    lexer = Lexer("3.e1 ")
    assert lexer._mode_num(0) == "<tkn_num,3,1,1>"
    assert lexer.pos == 1


# No digits after e: longest match keeps only the number, the e is left for the next token
@pytest.mark.parametrize("src, lexeme, end", [("1e ", "1", 1), ("1e+ ", "1", 1), ("1ex ", "1", 1), ("2.5e- ", "2.5", 3)])
def test_num_exp_missing_digits(src, lexeme, end):
    lexer = Lexer(src)
    assert lexer._mode_num(0) == f"<tkn_num,{lexeme},1,1>"
    assert lexer.pos == end


# 6. _mode_num(start) - hexadecimal
def test_num_hex_upper_digits():
    assert Lexer("0xFF ")._mode_num(0) == "<tkn_num,0xFF,1,1>"


def test_num_hex_upper_prefix():
    assert Lexer("0Xa1 ")._mode_num(0) == "<tkn_num,0Xa1,1,1>"


def test_num_hex_fraction():
    assert Lexer("0x1.8 ")._mode_num(0) == "<tkn_num,0x1.8,1,1>"


def test_num_hex_binary_exp():
    assert Lexer("0x1p4 ")._mode_num(0) == "<tkn_num,0x1p4,1,1>"


def test_num_hex_fraction_binary_exp():
    assert Lexer("0x1.8P-2 ")._mode_num(0) == "<tkn_num,0x1.8P-2,1,1>"


# e is a hex digit here, not an exponent
def test_num_hex_e_is_digit():
    assert Lexer("0x1e2 ")._mode_num(0) == "<tkn_num,0x1e2,1,1>"


# No hex digits after 0x: longest match keeps only the 0, the x is left for the next token
@pytest.mark.parametrize("src", ["0x ", "0xG "])
def test_num_hex_malformed(src):
    lexer = Lexer(src)
    assert lexer._mode_num(0) == "<tkn_num,0,1,1>"
    assert lexer.pos == 1


# 7. _mode_simple_string(start) - short strings
def test_str_double_quotes():
    lexer = Lexer('"Hola, Lua"')
    assert lexer._mode_simple_string(0) == "<tkn_str,Hola, Lua,1,1>"
    assert lexer.pos == 11


def test_str_single_quotes():
    assert Lexer("'abc'")._mode_simple_string(0) == "<tkn_str,abc,1,1>"


def test_str_other_quote_inside():
    assert Lexer("'\"double\" string'")._mode_simple_string(0) == '<tkn_str,"double" string,1,1>'


def test_str_keeps_spaces():
    assert Lexer('"Valor de @: "')._mode_simple_string(0) == "<tkn_str,Valor de @: ,1,1>"


def test_str_escaped_quote():
    lexer = Lexer('"a\\"b" ')
    assert lexer._mode_simple_string(0) == '<tkn_str,a\\"b,1,1>'
    assert lexer.pos == 6


def test_str_escaped_backslash():
    assert Lexer('"x\\\\" ')._mode_simple_string(0) == "<tkn_str,x\\\\,1,1>"


def test_str_empty():
    assert Lexer('"" ')._mode_simple_string(0) == "<tkn_str,,1,1>"


def test_str_adjacent(lex_all):
    assert lex_all("'U''n'") == ["<tkn_str,U,1,1>", "<tkn_str,n,1,4>"]


def test_str_unclosed_eof():
    with pytest.raises(LexicalError) as exc_info:
        Lexer('"Hola')._mode_simple_string(0)
    assert (exc_info.value.line, exc_info.value.col) == (1, 1)


def test_str_unclosed_newline():
    with pytest.raises(LexicalError) as exc_info:
        Lexer('"Ho\nla"')._mode_simple_string(0)
    assert (exc_info.value.line, exc_info.value.col) == (1, 1)


# Column must be relative to the line, not the absolute index
@pytest.mark.parametrize("src", ['x\n  y = "ab', 'x\n  y = "a\nb"'])
def test_str_unclosed_position(src):
    lexer = Lexer(src)
    lexer.pos, lexer.line, lexer.last_pos = 8, 2, 2
    with pytest.raises(LexicalError) as exc_info:
        lexer._mode_simple_string(8)
    assert (exc_info.value.line, exc_info.value.col) == (2, 7)


# 9. _mode_op_symbol(start)
SINGLE_SYMBOLS = sorted(s for s in OPERATORS if len(s) == 1)
DOUBLE_SYMBOLS = sorted(s for s in OPERATORS if len(s) == 2)


@pytest.mark.parametrize("symbol", SINGLE_SYMBOLS)
def test_op_single_each(symbol):
    lexer = Lexer(symbol + " ")
    assert lexer._mode_op_symbol(0) == f"<{OPERATORS[symbol]},1,1>"
    assert lexer.pos == 1


@pytest.mark.parametrize("symbol", DOUBLE_SYMBOLS)
def test_op_double_each(symbol):
    lexer = Lexer(symbol + " ")
    assert lexer._mode_op_symbol(0) == f"<{OPERATORS[symbol]},1,1>"
    assert lexer.pos == 2


def test_op_varargs():
    lexer = Lexer("... ")
    assert lexer._mode_op_symbol(0) == "<tkn_varargs,1,1>"
    assert lexer.pos == 3


def test_op_no_invalid_pair():
    lexer = Lexer("<>")
    assert lexer._mode_op_symbol(0) == "<tkn_less,1,1>"
    assert lexer.pos == 1


def test_op_run_equals(lex_all):
    assert lex_all("==== ") == ["<tkn_equal,1,1>", "<tkn_equal,1,3>"]


def test_op_run_geq_assign(lex_all):
    assert lex_all(">== ") == ["<tkn_geq,1,1>", "<tkn_assign,1,3>"]


def test_op_at_eof():
    assert Lexer(")")._mode_op_symbol(0) == "<tkn_closing_par,1,1>"


# 10. _handle_comments() and _handle_multiline_comments(...)
def test_comment_single_line():
    lexer = Lexer("-- hi\nx")
    lexer._handle_comments()
    assert lexer.pos == 5


def test_comment_single_line_eof():
    lexer = Lexer("-- hi")
    lexer._handle_comments()
    assert lexer.pos == 5


def test_comment_block_inline():
    lexer = Lexer("--[[ a ]]x")
    lexer._handle_comments()
    print(lexer.pos)
    assert lexer.pos == 9


def test_comment_block_multiline():
    lexer = Lexer("--[[a\nb\n]]x")
    lexer._handle_comments()
    assert (lexer.pos, lexer.line, lexer.last_pos) == (10, 3, 8)


def test_comment_block_level():
    lexer = Lexer("--[==[ a ]] b ]==]x")
    lexer._handle_comments()
    assert lexer.pos == 18


def test_comment_block_empty():
    lexer = Lexer("--[[]]x")
    lexer._handle_comments()
    assert lexer.pos == 6


def test_comment_space_before_bracket():
    lexer = Lexer("-- [[\nx")
    lexer._handle_comments()
    assert lexer.pos == 5


def test_comment_bad_level_is_single_line():
    lexer = Lexer("--[=x\ny")
    lexer._handle_comments()
    assert lexer.pos == 5


def test_comment_bad_level_two_equals_is_single_line():
    lexer = Lexer("--[==x\ny")
    lexer._handle_comments()
    assert lexer.pos == 6


def test_comment_block_unclosed():
    lexer = Lexer("x\n  --[[ open")
    lexer.pos, lexer.line, lexer.last_pos = 4, 2, 2
    with pytest.raises(LexicalError) as exc_info:
        lexer._handle_comments()
    assert (exc_info.value.line, exc_info.value.col) == (2, 3)


def test_multiline_handler_direct():
    lexer = Lexer("--[[a]]x")
    lexer.pos = 2
    lexer._handle_multiline_comments(1, 1)
    assert lexer.pos == 7


def test_multiline_handler_level():
    lexer = Lexer("--[==[a]]b]==]x")
    lexer.pos = 6
    lexer._handle_multiline_comments(1, 1, 2)
    assert lexer.pos == 14


def test_multiline_handler_newlines():
    lexer = Lexer("--[[a\nb]]x")
    lexer.pos = 2
    lexer._handle_multiline_comments(1, 1)
    assert (lexer.pos, lexer.line, lexer.last_pos) == (9, 2, 6)


def test_multiline_handler_unclosed():
    lexer = Lexer("--[[abc")
    lexer.pos = 2
    with pytest.raises(LexicalError) as exc_info:
        lexer._handle_multiline_comments(1, 1)
    assert (exc_info.value.line, exc_info.value.col) == (1, 1)


# 11. _cleanse_input()
def test_cleanse_whitespace():
    lexer = Lexer(" \t\r\v\fx")
    lexer._cleanse_input()
    assert (lexer.pos, lexer.line) == (5, 1)


def test_cleanse_newlines():
    lexer = Lexer("\n\nab")
    lexer._cleanse_input()
    assert (lexer.pos, lexer.line, lexer.last_pos) == (2, 3, 2)


def test_cleanse_mixed():
    lexer = Lexer("-- a\n\n--[[b]]  -- c\n  x")
    lexer._cleanse_input()
    assert (lexer.pos, lexer.line, lexer.last_pos) == (22, 4, 20)


def test_cleanse_keeps_single_minus():
    lexer = Lexer("- 3")
    lexer._cleanse_input()
    assert lexer.pos == 0


def test_cleanse_empty():
    lexer = Lexer("")
    lexer._cleanse_input()
    assert lexer.pos == 0


# 12. _process_token()
def test_process_letter():
    assert Lexer("abc ")._process_token() == "<id,abc,1,1>"


def test_process_underscore():
    assert Lexer("_x ")._process_token() == "<id,_x,1,1>"


def test_process_digit():
    assert Lexer("9 ")._process_token() == "<tkn_num,9,1,1>"


def test_process_leading_dot_is_period(lex_all):
    assert lex_all(".5 ") == ["<tkn_period,1,1>", "<tkn_num,5,1,2>"]


def test_process_single_quote():
    assert Lexer("'a' ")._process_token() == "<tkn_str,a,1,1>"


def test_process_double_quote():
    assert Lexer('"a" ')._process_token() == "<tkn_str,a,1,1>"


def test_process_symbol():
    assert Lexer("+ ")._process_token() == "<tkn_plus,1,1>"


def test_process_reads_current_pos():
    lexer = Lexer("ab cd ")
    lexer.pos = 3
    assert lexer._process_token() == "<id,cd,1,4>"


# "٣" (Arabic-Indic digit) and "é" are outside the ASCII digit/letter sets
@pytest.mark.parametrize("char", ["@", "?", "!", "$", "`", "ñ", "◕", "¡", "٣", "é"])
def test_process_unknown_char(char):
    with pytest.raises(LexicalError) as exc_info:
        Lexer(char)._process_token()
    assert (exc_info.value.line, exc_info.value.col) == (1, 1)


def test_process_unknown_char_position():
    lexer = Lexer("ab\n  @")
    lexer.pos, lexer.line, lexer.last_pos = 5, 2, 3
    with pytest.raises(LexicalError) as exc_info:
        lexer._process_token()
    assert (exc_info.value.line, exc_info.value.col) == (2, 3)


def test_process_at_eof():
    with pytest.raises(LexicalError) as exc_info:
        Lexer("")._process_token()
    assert (exc_info.value.line, exc_info.value.col) == (1, 1)


# 13. tokenize()
def test_tokenize_sequence():
    lexer = Lexer("a b\nc")
    assert lexer.tokenize() == "<id,a,1,1>"
    assert lexer.tokenize() == "<id,b,1,3>"
    assert lexer.tokenize() == "<id,c,2,1>"


def test_tokenize_eof_after_tokens():
    lexer = Lexer("a b\nc")
    for _ in range(3):
        lexer.tokenize()
    with pytest.raises(EOFError):
        lexer.tokenize()


def test_tokenize_position_after_cleanse():
    assert Lexer("  -- c\n\t x ").tokenize() == "<id,x,2,3>"


def test_tokenize_empty():
    with pytest.raises(EOFError):
        Lexer("").tokenize()


def test_tokenize_only_comments():
    with pytest.raises(EOFError):
        Lexer("  -- c\n--[[x]]\n").tokenize()


def test_tokenize_error_exits(capsys):
    with pytest.raises(SystemExit):
        Lexer("@").tokenize()
    assert capsys.readouterr().out == ">>> Error lexico (linea: 1, posicion: 1)\n"


def _crash(reason):
    return pytest.mark.xfail(reason=reason, raises=AssertionError, strict=True)


@pytest.mark.parametrize(
    "src",
    [
        "x = 5",
        "a...",
        ")",
        '"abc',
        'x = "a\\"b"',
    ],
)
def test_tokenize_never_unexpected_error(lex_all, src):
    assert not any(line.startswith("Unexpected error") for line in lex_all(src))
