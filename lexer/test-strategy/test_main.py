import re

import pytest

from conftest import PROJECT_ROOT

TEST_CASES_DIR = PROJECT_ROOT / "test-cases"


# 14. End-to-end: reference examples (docs/output_format.txt)
def test_ref1_matricula(run_main):
    src = (
        "local matricula = 9\n"
        "\n"
        "if matricula>=8 then\n"
        '   print("Ya acabando la carrera :)")\n'
        "end\n"
    )
    assert run_main(src).splitlines() == [
        "<local,1,1>",
        "<id,matricula,1,7>",
        "<tkn_assign,1,17>",
        "<tkn_num,9,1,19>",
        "<if,3,1>",
        "<id,matricula,3,4>",
        "<tkn_geq,3,13>",
        "<tkn_num,8,3,15>",
        "<then,3,17>",
        "<print,4,4>",
        "<tkn_opening_par,4,9>",
        "<tkn_str,Ya acabando la carrera :),4,10>",
        "<tkn_closing_par,4,37>",
        "<end,5,1>",
    ]


def test_ref2_c_comment_error(run_main):
    src = 'print("Hola, Lua") /* un comentario (◕‿◕) */\n'
    assert run_main(src).splitlines() == [
        "<print,1,1>",
        "<tkn_opening_par,1,6>",
        "<tkn_str,Hola, Lua,1,7>",
        "<tkn_closing_par,1,18>",
        "<tkn_div,1,20>",
        "<tkn_times,1,21>",
        "<id,un,1,23>",
        "<id,comentario,1,26>",
        "<tkn_opening_par,1,37>",
        ">>> Error lexico (linea: 1, posicion: 38)",
    ]


def test_ref3_indentation(run_main):
    # The spec prints <retornar,6,6>; treated as a typo for <return,6,6>
    src = "print    \n    false\n     in\n\n print  end\n     return \n"
    assert run_main(src).splitlines() == [
        "<print,1,1>",
        "<false,2,5>",
        "<in,3,6>",
        "<print,5,2>",
        "<end,5,9>",
        "<return,6,6>",
    ]


def test_ref4_case_sensitivity(run_main):
    src = "PRINT print \n\nPrint Mi_Variable\n\n\nwHILe WHILE while    \n"
    assert run_main(src).splitlines() == [
        "<id,PRINT,1,1>",
        "<print,1,7>",
        "<id,Print,3,1>",
        "<id,Mi_Variable,3,7>",
        "<id,wHILe,6,1>",
        "<id,WHILE,6,7>",
        "<while,6,13>",
    ]


def test_ref5_comments(run_main):
    src = (
        "until\n"
        "   repeat in false o else\n"
        "\n"
        "   --this is for videogames enjoyers\n"
        "         in true Nene -- perfect\n"
        "   \n"
        "   --[[ I don´t have enough creativity\n"
        "      to write comments\n"
        "   ]] \n"
        "   v\n"
    )
    assert run_main(src).splitlines() == [
        "<until,1,1>",
        "<repeat,2,4>",
        "<in,2,11>",
        "<false,2,14>",
        "<id,o,2,20>",
        "<else,2,22>",
        "<in,5,10>",
        "<true,5,13>",
        "<id,Nene,5,18>",
        "<id,v,10,4>",
    ]


def test_ref6_edad(run_main):
    src = (
        "local edad = 16\n"
        "\n"
        "if edad>=18 then\n"
        '  print("Eres mayor de edad.")\n'
        "end\n"
    )
    assert run_main(src).splitlines() == [
        "<local,1,1>",
        "<id,edad,1,7>",
        "<tkn_assign,1,12>",
        "<tkn_num,16,1,14>",
        "<if,3,1>",
        "<id,edad,3,4>",
        "<tkn_geq,3,8>",
        "<tkn_num,18,3,10>",
        "<then,3,13>",
        "<print,4,3>",
        "<tkn_opening_par,4,8>",
        "<tkn_str,Eres mayor de edad.,4,9>",
        "<tkn_closing_par,4,30>",
        "<end,5,1>",
    ]


def test_ref7_negative_and_quotes(run_main):
    src = (
        "local my_Var1 = 2\n"
        "local my_Var2 = -3.145\n"
        "string = '\"double\" string'\n"
        "string2 = \"'single' string\"\n"
        "\n"
        "-- another single comment\n"
    )
    assert run_main(src).splitlines() == [
        "<local,1,1>",
        "<id,my_Var1,1,7>",
        "<tkn_assign,1,15>",
        "<tkn_num,2,1,17>",
        "<local,2,1>",
        "<id,my_Var2,2,7>",
        "<tkn_assign,2,15>",
        "<tkn_minus,2,17>",
        "<tkn_num,3.145,2,18>",
        "<id,string,3,1>",
        "<tkn_assign,3,8>",
        '<tkn_str,"double" string,3,10>',
        "<id,string2,4,1>",
        "<tkn_assign,4,9>",
        "<tkn_str,'single' string,4,11>",
    ]


def test_ref8_at_sign_error(run_main):
    src = 'print("Valor de @: ",@)\n'
    assert run_main(src).splitlines() == [
        "<print,1,1>",
        "<tkn_opening_par,1,6>",
        "<tkn_str,Valor de @: ,1,7>",
        "<tkn_comma,1,21>",
        ">>> Error lexico (linea: 1, posicion: 22)",
    ]


def test_ref9_longest_match_error(run_main):
    src = '_f 4.559<>6="1"ñvari8\n'
    assert run_main(src).splitlines() == [
        "<id,_f,1,1>",
        "<tkn_num,4.559,1,4>",
        "<tkn_less,1,9>",
        "<tkn_greater,1,10>",
        "<tkn_num,6,1,11>",
        "<tkn_assign,1,12>",
        "<tkn_str,1,1,13>",
        ">>> Error lexico (linea: 1, posicion: 16)",
    ]


# 15. End-to-end: extra spec rules
def test_trailing_comment(run_main):
    assert run_main("nil --comment").splitlines() == ["<nil,1,1>"]


def test_number_period_number(run_main):
    assert run_main("120.075.389\n").splitlines() == [
        "<tkn_num,120.075,1,1>",
        "<tkn_period,1,8>",
        "<tkn_num,389,1,9>",
    ]


def test_number_then_error(run_main):
    assert run_main("8.9!62834127\n").splitlines() == [
        "<tkn_num,8.9,1,1>",
        ">>> Error lexico (linea: 1, posicion: 4)",
    ]


@pytest.mark.xfail(reason="hex and exponent numbers not supported", raises=AssertionError, strict=True)
def test_hex_and_exponent(run_main):
    assert run_main("x = 0xFF + 1e3\n").splitlines() == [
        "<id,x,1,1>",
        "<tkn_assign,1,3>",
        "<tkn_num,0xFF,1,5>",
        "<tkn_plus,1,10>",
        "<tkn_num,1e3,1,12>",
    ]


@pytest.mark.xfail(reason="long-bracket strings not supported", raises=AssertionError, strict=True)
def test_long_string_line_tracking(run_main):
    output = run_main("s = [[multi\nline]] print(s)\n").splitlines()
    assert output[:2] == ["<id,s,1,1>", "<tkn_assign,1,3>"]
    assert output[2].startswith("<tkn_str,multi")
    assert output[-4:] == [
        "<print,2,8>",
        "<tkn_opening_par,2,13>",
        "<id,s,2,14>",
        "<tkn_closing_par,2,15>",
    ]


def test_empty_input(run_main_process):
    result = run_main_process("")
    assert result.stdout == ""
    assert result.returncode == 0


def test_only_comments(run_main_process):
    result = run_main_process("-- a\n--[[ b\n c ]]\n")
    assert result.stdout == ""
    assert result.returncode == 0


def test_eof_after_id(run_main):
    assert run_main("x = y").splitlines() == ["<id,x,1,1>", "<tkn_assign,1,3>", "<id,y,1,5>"]


def test_eof_after_number(run_main):
    assert run_main("x = 5").splitlines() == ["<id,x,1,1>", "<tkn_assign,1,3>", "<tkn_num,5,1,5>"]


def test_eof_after_symbol(run_main):
    assert run_main("f()").splitlines() == [
        "<id,f,1,1>",
        "<tkn_opening_par,1,2>",
        "<tkn_closing_par,1,3>",
    ]


def test_eof_after_string(run_main):
    assert run_main('s = "a"').splitlines() == ["<id,s,1,1>", "<tkn_assign,1,3>", "<tkn_str,a,1,5>"]


def test_crlf_line_endings(run_main):
    assert run_main("a\r\nb\r\n").splitlines() == ["<id,a,1,1>", "<id,b,2,1>"]


def test_nothing_after_error(run_main):
    assert run_main('print("x") @ print\n').splitlines() == [
        "<print,1,1>",
        "<tkn_opening_par,1,6>",
        "<tkn_str,x,1,7>",
        "<tkn_closing_par,1,10>",
        ">>> Error lexico (linea: 1, posicion: 12)",
    ]


# 16. End-to-end: test-cases/*.in
VALID_LINE = re.compile(
    r"^<(id|tkn_num|tkn_str),.*,\d+,\d+>$"
    r"|^<[a-z_]+,\d+,\d+>$"
    r"|^>>> Error lexico \(linea: \d+, posicion: \d+\)$"
)


def _run_case(run_main, name):
    src = (TEST_CASES_DIR / name).read_text(encoding="utf-8")
    return run_main(src).splitlines()


def _case_param(path):
    if path.name == "12.in":
        mark = pytest.mark.xfail(reason="unclosed string crashes", raises=AssertionError, strict=True)
        return pytest.param(path.name, marks=mark)
    return path.name


@pytest.mark.parametrize("name", [_case_param(p) for p in sorted(TEST_CASES_DIR.glob("*.in"))])
def test_cases_well_formed(run_main, name):
    output = _run_case(run_main, name)
    assert not any("Unexpected error" in line for line in output)
    assert all(VALID_LINE.match(line) for line in output)


def test_case_00_keywords(run_main):
    assert _run_case(run_main, "00.in") == [
        "<print,3,1>",
        "<true,3,7>",
        "<until,5,1>",
        "<nil,5,7>",
        "<while,5,11>",
        "<if,5,17>",
        "<else,7,1>",
        "<elseif,7,6>",
        "<error,7,13>",
    ]


def test_case_01_block_comment(run_main):
    output = _run_case(run_main, "01.in")
    assert output[:3] == ["<if,3,1>", "<for,4,6>", "<pcall,4,13>"]
    assert output[-1] == "<id,proof,17,12>"


def test_case_02_strings_and_concat(run_main):
    output = _run_case(run_main, "02.in")
    assert "<tkn_str,¡Hola, bienvenido a la programación en Lua!,3,11>" in output
    assert "<tkn_concat,23,18>" in output
    assert "<tkn_concat,23,26>" in output
    assert output[-1] == "<tkn_closing_par,27,42>"


def test_case_03_longest_match(run_main):
    assert _run_case(run_main, "03.in") == [
        "<tkn_num,4.559,7,1>",
        "<tkn_period,7,6>",
        "<tkn_num,8777,7,7>",
        "<tkn_equal,7,11>",
        "<tkn_assign,7,13>",
        "<tkn_left_shift,7,14>",
        "<tkn_right_shift,7,16>",
        "<tkn_less,7,18>",
        "<tkn_right_shift,7,19>",
        "<tkn_right_shift,7,21>",
        "<tkn_geq,7,23>",
        "<tkn_geq,7,25>",
        "<tkn_assign,7,27>",
        "<tkn_geq,7,28>",
        "<tkn_equal,7,30>",
        "<tkn_assign,7,32>",
        "<tkn_geq,7,33>",
        "<tkn_right_shift,7,35>",
        "<tkn_less,7,37>",
        "<tkn_greater,7,38>",
        "<tkn_num,120.075,7,39>",
        "<tkn_period,7,46>",
        "<tkn_num,389,7,47>",
    ]


def test_case_05_loops(run_main):
    output = _run_case(run_main, "05.in")
    assert output[:3] == ["<local,4,1>", "<id,contador,4,7>", "<tkn_assign,4,16>"]
    assert "<tkn_str,\\n--- Ciclo repeat...until ---,15,7>" in output
    assert "<tkn_minus,33,15>" in output
    assert output[-1] == "<end,35,1>"


def test_case_06_varargs_error(run_main):
    assert _run_case(run_main, "06.in") == [
        "<id,_f,3,1>",
        "<tkn_num,4.559,3,4>",
        "<tkn_varargs,3,9>",
        "<tkn_num,6,3,12>",
        "<tkn_assign,3,13>",
        "<tkn_str,1,3,14>",
        ">>> Error lexico (linea: 3, posicion: 17)",
    ]


def test_case_07_adjacent_strings(run_main):
    assert _run_case(run_main, "07.in") == [
        "<tkn_opening_par,3,1>",
        "<tkn_str,HaBía una Vez,3,2>",
        "<tkn_closing_par,3,17>",
        "<tkn_str,U,3,19>",
        "<tkn_str,n,3,22>",
        "<tkn_str,a fea,3,25>",
        "<tkn_opening_bra,3,33>",
        "<tkn_str,C,3,34>",
        "<tkn_str,ala,3,37>",
        "<tkn_str,b,3,42>",
        "<tkn_str,a,3,45>",
        "<tkn_str,za,3,48>",
        "<tkn_closing_bra,3,52>",
        "<tkn_opening_key,3,53>",
        "<tkn_str,C,3,54>",
        "<tkn_str,ala,3,57>",
        "<tkn_str,b,3,62>",
        "<tkn_str,a,3,65>",
        "<tkn_str,za,3,68>",
        "<tkn_closing_key,3,72>",
    ]


def test_case_08_relational(run_main):
    output = _run_case(run_main, "08.in")
    assert output[:4] == ["<tkn_equal,3,1>", "<return,3,6>", "<id,tkn_equal,3,15>", "<tkn_neq,4,1>"]
    assert output[-3:] == ["<tkn_geq,8,1>", "<return,8,6>", "<id,tkn_geq,8,15>"]


@pytest.mark.xfail(reason="unclosed string crashes", raises=AssertionError, strict=True)
def test_case_12_unclosed_string(run_main):
    output = _run_case(run_main, "12.in")
    assert output[-4:] == [
        "<local,9,1>",
        "<id,mensaje,9,7>",
        "<tkn_assign,9,15>",
        ">>> Error lexico (linea: 9, posicion: 17)",
    ]


def test_case_13_full_program(run_main):
    output = _run_case(run_main, "13.in")
    assert output[:3] == ["<local,4,1>", "<id,CONFIG_ACTIVA,4,7>", "<tkn_assign,4,21>"]
    assert "<warn,12,9>" in output
    assert "<error,19,9>" in output
    assert "<pcall,37,24>" in output
    assert output[-1] == "<end,43,1>"
