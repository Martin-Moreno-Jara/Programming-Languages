"""Case tables of spec 006 §5 to §8 (tasks §3 to §5). Data only, no tests."""
import re

# ---------------------------------------------------------------------------
# Accept rows (spec §5, §6): (case_id, source)
# ---------------------------------------------------------------------------
STRUCTURE_ROWS = [
    ("B1", ""),
    ("B2", "x = 1"),
    ("B3", "x = 1 y = 2 z = 3"),
    ("B4", "return"),
    ("B5", "x = 1 return x"),
    ("B6", ";;;"),
    ("B7", "x = 1;;; y = 2"),
]

STATEMENT_ROWS = [
    ("S1", ";"),
    ("S2", "x = 1"),
    ("S3", "a, b, c = 1, 2, 3"),
    ("S4", "a, b = f()"),
    ("S5", "f()"),
    ("S6", "obj:m(1)"),
    ("S7", "::top::"),
    ("S8", "while true do break end"),
    ("S9", "goto top"),
    ("S12", "while x < 10 do x = x + 1 end"),
    ("S13", "repeat x = x - 1 until x == 0"),
    ("S14", "if x then end"),
    ("S15", "if x then y = 1 else y = 2 end"),
    ("S16", "if a then elseif b then end"),
    ("S17", "if a then elseif b then elseif c then else end"),
    ("S18", "for i = 1, 10 do end"),
    ("S19", "for i = 10, 1, -1 do end"),
    ("S20", "for k in f() do end"),
    ("S21", "for k, v in f(t) do end"),
    ("S22", "for a, b, c in f, s, i do end"),
    ("S23", "function f() end"),
    ("S24", "function a.b.c() end"),
    ("S25", "function a:m() end"),
    ("S26", "function a.b:m(x) end"),
    ("S27", "local x"),
    ("S28", "local x, y = 1, 2"),
    ("S29", "local function f() end"),
    ("S30", "global x"),
    ("S31", "global x, y = 1, 2"),
    ("S32", "global function g() end"),
]

ATTRIB_ROWS = [
    ("AT1", "local x <const> = 5"),
    ("AT2", "local f <close> = g()"),
    ("AT3", "local a <const>, b, c <close> = 1, 2, 3"),
    ("AT4", "global x <const> = 1"),
    ("AT5", "local x <anything>"),
]

RETURN_ROWS = [
    ("RT1", "return"),
    ("RT2", "return 1"),
    ("RT3", "return 1, 2, 3"),
    ("RT4", "return;"),
    ("RT5", "return f();"),
    ("RT6", "function f() return end"),
    ("RT7", "while x do return 1 end x = 2"),
    ("RT8", "if x then return 1 elseif y then return 2 else return 3 end"),
    ("RT9", "while x do return end"),
    ("RT10", "repeat return until x"),
]

FUNCTION_ROWS = [
    ("F1", "function f() end"),
    ("F2", "function f(a) end"),
    ("F3", "function f(a, b, c) end"),
    ("F4", "function f(...) end"),
    ("F5", "function f(a, ...) end"),
    ("F6", "function f(...args) end"),
    ("F7", "function f(a, ...rest) end"),
    ("F8", "x = function() end"),
    ("F9", "x = function(a, ...) return a end"),
    ("F10", "f(function() end)"),
    ("F11", "function f() function g() end end"),
    ("F12", "x, y = 1, function() end"),
]

TABLE_ROWS = [
    ("T1", "t = {}"),
    ("T2", "t = {1, 2, 3}"),
    ("T3", "t = {x = 1, y = 2}"),
    ("T4", 't = {[1] = "a", [k .. "x"] = 2}'),
    ("T5", "t = {1; 2; 3}"),
    ("T6", "t = {1, x = 2; [3] = 4}"),
    ("T7", "t = {1, 2,}"),
    ("T8", "t = {1;}"),
    ("T9", "t = {{}, {{}}}"),
    ("T10", "t = {f(), a.b, (x)}"),
    ("T11", "t = {x}"),
    ("T12", "t = {x == 1, y .. z}"),
    ("T13", "t = {x = y}"),
    ("T14", "t = {function() end}"),
    ("T15", "t = {[1] = function() end}"),
    ("T16", "t = {f = function() end, 2}"),
]

EXPRESSION_ROWS = [
    ("E1-nil", "x = nil"),
    ("E1-false", "x = false"),
    ("E1-true", "x = true"),
    ("E2-int", "x = 42"),
    ("E2-float", "x = 3.14"),
    ("E2-hex", "x = 0xFF"),
    ("E3-double", 'x = "s"'),
    ("E3-single", "x = 'c'"),
    ("E5", "x = y"),
    ("E6", "x = (1)"),
    ("E7", "x = f(1)"),
    ("E8", "x = {}"),
    ("E9-minus", "x = -a"),
    ("E9-not", "x = not a"),
    ("E9-length", "x = #t"),
    ("E10-minus", "x = - - a"),
    ("E10-not", "x = not not a"),
    ("E11", "x = -a ^ 2"),
    ("E12", "x = 1 + 2 * 3 - 4 / 5"),
    ("E13", "x = a .. b .. c"),
    ("E14", "x = (a + b) * c"),
    ("E15", "x = a and b or not c"),
    ("E16", "x = #t + 1"),
    ("E17", 'x = "n"+a-true*(vari[3] % 70)'),
    ("E19", "x = a ~ b"),
    ("E20", "x = a ~= b"),
]

_BINOPS = [
    ("plus", "+"), ("minus", "-"), ("times", "*"), ("div", "/"), ("floor-div", "//"),
    ("power", "^"), ("mod", "%"), ("bit-and", "&"), ("bit-xor", "~"), ("bit-or", "|"),
    ("right-shift", ">>"), ("left-shift", "<<"), ("concat", ".."), ("less", "<"), ("leq", "<="),
    ("greater", ">"), ("geq", ">="), ("equal", "=="), ("neq", "~="), ("and", "and"), ("or", "or"),
]
BINOP_ROWS = [(f"BO-{name}", f"x = a {op} b") for name, op in _BINOPS]

CALL_ROWS = [
    ("C1", "x = a.b"),
    ("C2", "x = a[1]"),
    ("C3", "x = a.b.c[d][e]"),
    ("C4", "a.b = 1"),
    ("C5", "a[i + 1] = 2"),
    ("C6", "a.b[c].d = 3"),
    ("C7", "a, b.c, d[1] = 1, 2, 3"),
    ("C8", "f()"),
    ("C9", "f(1, 2)"),
    ("C13", "f()()"),
    ("C14", "f().x = 1"),
    ("C15", "f()[1] = 2"),
    ("C16", "a.b:c(1):d(2)"),
    ("C20", "a.b.c:d(1)(2)(3)"),
    ("C21", "x = f(g(h(1)))"),
]

NAME_ROWS = [
    ("N1", 'print("hola")'),
    ("N3", "print = 1"),
    ("N4", "local warn = 2"),
    ("N5", "function error() end"),
    ("N6", "local function pcall() end"),
    ("N7", "xpcall(f, error)"),
    ("N8", "t.print = print"),
    ("N9", "a:print()"),
    ("N10", "function t.error:warn() end"),
    ("N11", "function f(print, warn) end"),
    ("N12", "for print = 1, 2 do end"),
    ("N13", "for error, warn in f() do end"),
    ("N14", "t = {print = 1}"),
    ("N15", "::error:: goto error"),
]

LAYOUT_ROWS = [
    ("L1", "local a = 4;\nglobal b = 5;"),
    ("L2", "local a = 4; global b=5;"),
    ("L3", "local a = 4 global b = 5"),
    ("L4", "x\n=\n1"),
    ("L5", "if x\nthen\ny = 1\nend"),
    ("L6", "-- comment\nx = 1 -- another"),
]

EDGE_ROWS = [
    (
        "EA1",
        "-- Definición de la función\nfunction saludar(texto)\n    print(texto)\nend\n\n"
        '-- Llamada a la función\nsaludar("¡Hola, mundo!")\n',
    ),
    (
        "EA2",
        'local entrada\n\nif entrada == nil then\n    print("Valor indefinido")\nelse\n'
        '    print("Valor definido")\nend\n',
    ),
    ("EA3", "x = " + "(" * 50 + "1" + ")" * 50),
    ("EA4", "while x do " * 50 + "end " * 50),
    ("EA5", "if x then " * 50 + "end " * 50),
    ("EA6", "t = " + "{" * 50 + "}" * 50),
    ("EA7", "x = 1\n" * 200),
    ("EA8", "x = " + " + ".join(["1"] * 200)),
    ("EA9", "f = " + "function() return " * 10 + "end " * 10),
    ("EA10", "function f() ; end"),
    ("EA11", "-- a\n\n-- b\n"),
    ("EA12", "return function() return {f = function() return end} end"),
    ("EA13", "f()\n(g)()"),
]

PRODUCTION_ROWS = (
    STRUCTURE_ROWS + STATEMENT_ROWS + ATTRIB_ROWS + RETURN_ROWS + FUNCTION_ROWS + TABLE_ROWS
    + EXPRESSION_ROWS + BINOP_ROWS + CALL_ROWS + NAME_ROWS + LAYOUT_ROWS
)
ACCEPT_ROWS = PRODUCTION_ROWS + EDGE_ROWS
assert len(PRODUCTION_ROWS) == 162, len(PRODUCTION_ROWS)
assert len(ACCEPT_ROWS) == 175, len(ACCEPT_ROWS)

# ---------------------------------------------------------------------------
# Reject rows (spec §7): (case_id, source, position, lexeme, contains, exact)
# ---------------------------------------------------------------------------
EOF = "final de archivo"
_LOCAL_LIST = ["error", "function", "id", "pcall", "print", "warn", "xpcall"]
# After `,` in a variable list: only a name, since `(` can't start a prefix expression (platform test 04)
_NAME_LIST = ["error", "id", "pcall", "print", "warn", "xpcall"]
_R2_LIST = [
    "and", "or", "&", "|", "~", ")", ",", "..", "/", "==", "//", ">=", ">", "<<", "<=", "<",
    "-", "%", "~=", "+", "^", ">>", "*",
]
# The start of a single expression, as the grader lists it: `function` is only valid in an expression list or a
# field value, and `...` is never a value (platform tests 13, 14)
_EXP_LIST = [
    "cadena_de_caracteres", "error", "false", "id", "nil", "not", "pcall", "print", "#", "-", "{", "(",
    "true", "valor_numerico", "warn", "xpcall",
]
# The start of an expression list (after `=`, `in`, `return`, `(`): the same plus `function` (platform test 15)
_EXPLIST_START = _EXP_LIST[:3] + ["function"] + _EXP_LIST[3:]
# After a statement's name, as the grader lists it: call arguments are only `( … )` (platform test 18)
_AFTER_NAME_LIST = ["=", ":", ",", "[", "(", "."]
# After a condition in parentheses: no call suffixes after `( exp )`, so a C-style `{` fails at once (platform test 24)
_IF_GROUPING_LIST = [
    "and", "or", "then", "&", "|", "~", "..", "/", "==", "//", ">=", ">", "<<", "<=", "<", "-", "%", "~=", "+", "^",
    ">>", "*",
]
# After `x = ( exp )` at the top level: operators, `,` and the statement starts, but no call suffixes (platform test 35)
_AFTER_GROUPING_LIST = [
    "and", "break", "error", EOF, "for", "function", "global", "goto", "id", "if", "local", "or", "pcall", "print",
    "repeat", "return", "&", "|", "~", ",", "..", "/", "==", "//", ">=", "::", ">", "<<", "<=", "<", "-", "%", "~=",
    "+", "^", ">>", ";", "*", "warn", "while", "xpcall",
]
# The start of a statement, as the grader lists it: no `do … end` statement and no `(` (platform tests 04, 16)
_STATEMENT_START = [
    "break", "error", "for", "function", "global", "goto", "id", "if", "local", "pcall", "print", "repeat",
    "return", "::", ";", "warn", "while", "xpcall",
]
_TOP_STATEMENT_LIST = _STATEMENT_START[:2] + [EOF] + _STATEMENT_START[2:]
_BLOCK_STATEMENT_LIST = _STATEMENT_START[:1] + ["end"] + _STATEMENT_START[1:]
# After `x = a < b`: every binary operator except the comparisons, which are non-associative (platform test 36)
_AFTER_COMPARISON_LIST = [
    "and", "break", "error", EOF, "for", "function", "global", "goto", "id", "if", "local", "or", "pcall", "print",
    "repeat", "return", "&", "|", "~", ":", ",", "..", "/", "//", "::", "<<", "-", "%", "[", "(", ".", "+", "^", ">>",
    ";", "*", "warn", "while", "xpcall",
]
R3_SOURCE = "local i = 0;\n\nwhile (i < 5) do\n    p == [i];3\n    i = i + 1;\nend"
R36_SOURCE = "local a = 1\nlocal b = 2\nlocal c = = 3"

REJECT_ROWS = [
    ("R1", "local 1;", (1, 7), "1", set(), _LOCAL_LIST),
    ("R2", 'print(45"this")', (1, 9), "this", set(), _R2_LIST),
    ("R3", R3_SOURCE, (4, 7), "==", set(), _AFTER_NAME_LIST),
    ("R4", "if x then y = 1", None, EOF, {"end", "elseif", "else"}, None),
    ("R5", "repeat x = 1", None, EOF, {"until"}, None),
    ("R6", "function f() x = 1", None, EOF, {"end"}, None),
    ("R7", "f(1, 2", None, EOF, {")", ","}, None),
    ("R8", "x = t[1", None, EOF, {"]"}, None),
    ("R9", "x = {1, 2", None, EOF, {"}"}, None),
    ("R10", "x = 1 +", None, EOF, {"id", "valor_numerico", "("}, None),
    ("R11", "if x y = 1 end", (1, 6), "y", {"then"}, None),
    ("R12", "while x y() end", (1, 9), "y", {"do"}, None),
    ("R13", "return 1 x = 2", (1, 10), "x", {EOF, ";", ","}, None),
    ("R14", "x = = 1", (1, 5), "=", set(), _EXPLIST_START),
    ("R15", "x = ~y", (1, 5), "~", {"id", "-", "not", "#"}, None),
    ("R16", "x = a ~ ~b", (1, 9), "~", {"id", "-"}, None),
    ("R17", "for i = 1 do end", (1, 11), "do", {","}, None),
    ("R18", "for in t do end", (1, 5), "in", {"id"}, None),
    ("R19", "function f(a,) end", (1, 14), ")", {"id", "..."}, None),
    ("R20", "function (a) end", (1, 10), "(", {"id"}, None),
    ("R21", "goto end", (1, 6), "end", {"id"}, None),
    ("R22", "::l x = 1", (1, 5), "x", {"::"}, None),
    ("R23", "local function a.b() end", (1, 17), ".", {"("}, None),
    ("R24", "global x, *", (1, 11), "*", {"id"}, None),
    ("R25", "f())", (1, 4), ")", {EOF}, None),
    ("R26", "x = 1 2", (1, 7), "2", {EOF}, None),
    ("R27", "local x <const = 1", (1, 16), "=", {">"}, None),
    ("R28", "if x then else elseif y then end", (1, 16), "elseif", {"end"}, None),
    ("R29", "x. = 2", (1, 4), "=", {"id"}, None),
    ("R30", "t = {[1] 2}", (1, 10), "2", {"="}, None),
    ("R31", "function f() return 1 end end", (1, 27), "end", {EOF}, None),
    ("R32", "x, = 1", (1, 4), "=", set(), _NAME_LIST),
    ("R33", "local = 1", (1, 7), "=", set(), _LOCAL_LIST),
    ("R34", "x = ()", (1, 6), ")", {"id", "valor_numerico"}, None),
    ("R35", "a.b:c = 1", (1, 7), "=", {"("}, None),
    ("R36", R36_SOURCE, (3, 11), "=", {"id", "valor_numerico"}, None),
    ("R37", "x = 1\n\n\ny = ", None, EOF, {"id"}, None),
    ("R38", "t = {1,, 2}", (1, 8), ",", {"}"}, None),
    ("R39", "a = f\n(g).x = 1", (2, 7), "=", {EOF, "id"}, None),
    ("R40", "x = function() end .. {}", (1, 20), "..", {EOF, ","}, None),
    ("R41", "while function() end do end", (1, 7), "function", set(), _EXP_LIST),
    ("R42", "x = 1, = 2", (1, 8), "=", set(), _EXPLIST_START),
    ("R43", "if (x > 5) { print(x) }", (1, 12), "{", set(), _IF_GROUPING_LIST),
    ("R44", "x = (a) )", (1, 9), ")", set(), _AFTER_GROUPING_LIST),
    ("R45", "x = (t).k", (1, 8), ".", set(), _AFTER_GROUPING_LIST),
    ("R46", "x = (f)(1)", (1, 8), "(", set(), _AFTER_GROUPING_LIST),
    ("R47", "do end", (1, 1), "do", set(), _TOP_STATEMENT_LIST),
    ("R48", "do = 5", (1, 1), "do", set(), _TOP_STATEMENT_LIST),
    ("R49", "while x do do end end", (1, 12), "do", set(), _BLOCK_STATEMENT_LIST),
    # Constructs the reference grammar rejects, unlike the 5.5 manual (README, Grader findings 5 and 5c)
    ("R50", "global *", (1, 8), "*", set(), _LOCAL_LIST),
    ("R51", "global <const> *", (1, 8), "<", set(), _LOCAL_LIST),
    ("R52", "local <const> x", (1, 7), "<", set(), _LOCAL_LIST),
    ("R53", "global <const> x", (1, 8), "<", set(), _LOCAL_LIST),
    ("R54", "function f(...) x = ... end", (1, 21), "...", set(), _EXPLIST_START),
    ("R55", "x = f(...)", (1, 7), "...", {"id", "function", ")"}, None),
    ("R56", "t = {...}", (1, 6), "...", {"id", "function", "}", "["}, None),
    ("R57", 'f"str"', (1, 2), "str", set(), _AFTER_NAME_LIST),
    ("R58", "f{1, 2}", (1, 2), "{", set(), _AFTER_NAME_LIST),
    ("R59", 'print "hola"', (1, 7), "hola", set(), _AFTER_NAME_LIST),
    ("R60", 'o:m"s"', (1, 4), "s", set(), ["("]),
    ("R61", "o:m{}", (1, 4), "{", set(), ["("]),
    ("R62", 'x = f"s"', (1, 6), "s", {"(", "["}, None),
    ("R63", "x = f{}", (1, 6), "{", {"(", "["}, None),
    ("R64", "(f)()", (1, 1), "(", set(), _TOP_STATEMENT_LIST),
    ("R65", '("s"):upper()', (1, 1), "(", set(), _TOP_STATEMENT_LIST),
    ("R66", "(a).b = 1", (1, 1), "(", set(), _TOP_STATEMENT_LIST),
    ("R67", "a, (b).c = 1, 2", (1, 4), "(", set(), _NAME_LIST),
    ("R68", "x = a < b < c", (1, 11), "<", set(), _AFTER_COMPARISON_LIST),
    ("R69", "x = a == b == c", (1, 12), "==", set(), _AFTER_COMPARISON_LIST),
]
assert len(REJECT_ROWS) == 69, len(REJECT_ROWS)

# Only the first error is reported: (case_id, source, position)
FIRST_ERROR_ROWS = [
    ("R3", R3_SOURCE, (4, 7)),
    ("R36", R36_SOURCE, (3, 11)),
    ("R36-second-error", R36_SOURCE + "\nlocal d = = 4", (3, 11)),
]

# ---------------------------------------------------------------------------
# Output rows (spec §8): (case_id, source, expected line or a check of the line)
# ---------------------------------------------------------------------------
SUCCESS = "El analisis sintactico ha finalizado exitosamente."
# Doc programs live in one place only: output rows take their sources from the tables above
_SOURCES = {row[0]: row[1] for row in ACCEPT_ROWS + REJECT_ROWS}


def _is_eof_error(line: str) -> bool:
    return bool(re.match(r"^<\d+:\d+> Error sintactico: ", line)) and f'se encontro: "{EOF}"' in line


OUTPUT_ROWS = [
    ("O1", _SOURCES["EA1"], SUCCESS),
    ("O2", _SOURCES["EA2"], SUCCESS),
    (
        "O3",
        _SOURCES["R1"],
        '<1:7> Error sintactico: se encontro: "1"; se esperaba: '
        '"error", "function", "id", "pcall", "print", "warn", "xpcall".',
    ),
    (
        "O4",
        _SOURCES["R2"],
        '<1:9> Error sintactico: se encontro: "this"; se esperaba: "and", "or", "&", "|", "~", ")", ",", '
        '"..", "/", "==", "//", ">=", ">", "<<", "<=", "<", "-", "%", "~=", "+", "^", ">>", "*".',
    ),
    ("O5", _SOURCES["R3"], '<4:7> Error sintactico: se encontro: "=="; se esperaba: "=", ":", ",", "[", "(", ".".'),
    ("O6", _SOURCES["L1"], SUCCESS),
    ("O7", "", SUCCESS),
    ("O8", _SOURCES["R4"], _is_eof_error),
]
assert len(OUTPUT_ROWS) == 8, len(OUTPUT_ROWS)
