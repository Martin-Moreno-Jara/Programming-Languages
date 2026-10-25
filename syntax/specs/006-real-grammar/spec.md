# Spec 006 — Testing the real Lua grammar

## 1. Purpose and scope

This spec describes how to test that the parser built from `final_grammar` in
`main.py` accepts exactly the Lua 5.5 programs that the course grader accepts,
and that it reports the first syntax error in the format the assignment asks
for.

Sources of truth, in this order:

1. The assignment document,
   `syntax/docs/Analizador Sintáctico - Lenguaje Lua.docx` (called "the doc"
   below). Its examples are the only outputs confirmed by the grader.
2. The scope document, `lexer/docs/Alcance - Lenguaje Lua.docx`: all of
   chapter 3 of the reference manual is in scope.
3. The Lua 5.5 reference manual, §3 (the language) and §9 (the complete
   syntax).

- **In scope:** `final_grammar`, the parser that `ASDR_generator` generates
  from it, the error message of `ASDR_base`, and what `main.py` prints.
- **Out of scope:** FIRST, FOLLOW, prediction sets, the LL(1) check and the
  code generator themselves (specs 001 to 005). Lexical errors, since the doc
  says the input has none.

## 2. Interface under test

```python
from main import final_grammar, pred_exceptions

g = Grammar(final_grammar)
g.set_pred_exceptions(pred_exceptions)   # tokens removed by hand, see §4.1
g.process_grammar()
g.check_LL1_condition()          # must be True
ASDR_generator(g).generate()     # writes ./syntax/ASDR.py

parser = ASDR(Lexer(source))     # the real lexer, not a fake one
parser.main()                    # returns, or raises SyntacticalError
```

and, for the output tests:

```
python3 main.py < program.lua    # prints exactly one line
```

Things the tests have to work around:

- `generate()` writes to `./syntax/ASDR.py` relative to the working
  directory. As in spec 005, the parser is generated in a temporary folder and
  loaded as a `syntax.*` module, so the real `syntax/ASDR.py` is never
  overwritten. The grammar doesn't change between cases, so the parser is
  generated **once per test module**.
- `main.py` also regenerates `./syntax/ASDR.py` every time it runs. The output
  tests copy `main.py`, `syntax/`, `lexer/` and `exceptions/` into a temporary
  folder and run `main.py` there.
- The grader runs Python 3.9, so `main.py` must run on it. The tests
  themselves don't need to.

## 3. What "correct" means

### 3.1 Accept or reject

A program is accepted when it matches the syntax of manual §9, with these
changes from the doc:

- `print`, `pcall`, `xpcall`, `error` and `warn` are their own token types in
  the lexer, but **syntactically they are identifiers**. They are valid
  wherever a `Name` is valid: variables, fields, parameters, function names,
  labels, method names, loop variables.
- Bitwise operators are **binary only**. Unary `~` (`x = ~y`) is a syntax
  error. Binary `~` (`x = a ~ b`) is valid.
- Line breaks and `;` never matter (`local a = 4 global b = 5` is valid).
- Semantic errors are not syntax errors. The doc's own example
  `x = "n"+a-true*(vari[3] % 70)` must be accepted.

The parser only recognises programs. It builds no tree, so precedence and
associativity are not checked. Only acceptance is.

### 3.2 The error message

On the first syntax error, parsing stops, and exactly one line is reported:

```
<line:col> Error sintactico: se encontro: "<lexeme>"; se esperaba: "<t1>", "<t2>", ....
```

- `line:col` is the position of the token where the error was found.
- `<lexeme>` is that token's **lexeme**, not its type. A string's lexeme has
  no quotes (doc: `se encontro: "this"`). At the end of input it is
  `final de archivo`.
- The expected list is every token that would have been valid at that point.
  Each one is in double quotes and shown like this:

| Token type | Shown as |
|------------|----------|
| keyword (`if`, `end`, `print`, ...) | the keyword itself: `"if"` |
| `id` | `"id"` |
| `tkn_num` | `"valor_numerico"` |
| `tkn_str` | `"cadena_de_caracteres"` |
| any operator or symbol (`tkn_plus`, `tkn_closing_par`, ...) | the symbol: `"+"`, `")"` |
| `$` (end of input) | `"final de archivo"` |

- **Order:** the list is sorted by the **internal token-type name**, and then
  each entry is shown as in the table. All four doc examples follow this rule.
  For example, `"and", "or", "&", "|", "~", ")"` comes from
  `and < or < tkn_bit_and < tkn_bit_or < tkn_bitex_or < tkn_closing_par`.
  The doc's text says "lexicographic order" but doesn't say of what (§9, K7).
- Entries are separated by `", "` and the line ends with `.`.
- No token appears twice in the list.

### 3.3 The success message

When the program is accepted, `main.py` prints exactly:

```
El analisis sintactico ha finalizado exitosamente.
```

### 3.4 Current gaps

At the time of writing, three things don't match §3.2. The tests that depend
on them start as xfail (§11):

- `main.py:226` prints `error: ` before the message.
- `ASDR_base.format_error_message` puts the raw expected token types in the
  message (`tkn_closing_par` instead of `")"`), unsorted and not quoted.
- `print` is commented out of the keyword set in `lexer/lexer.py:81`, so it is
  lexed as `id`. The doc's expected lists name `"print"` separately (doc
  examples R1 and R33), so the lexer and the grader disagree (§9, K6).

## 4. Grammar property cases (P)

These check `final_grammar` itself, without parsing any program.

| ID | Property | Why |
|----|----------|-----|
| P1 | `check_LL1_condition()` is `True` | The recursive descent parser needs it |
| P2 | Every non-terminal is reachable from `CHUNK` | A leftover non-terminal is dead code or a missing reference |
| P3 | Every non-terminal used on a right side has an entry, and no entry has an empty list of productions | A typo in a name gives a parser that crashes instead of rejecting |
| P4 | Every non-terminal is productive (it derives at least one string of terminals) | A non-terminal that can only recurse never finishes |
| P5 | Every terminal is a real lexer token type: a value of the lexer's symbol table, a keyword of `keywords_set`, `id`, `tkn_num`, `tkn_str`, or `ε` | A misspelled token (`tkn_semilocon`) can never be matched |
| P6 | `CHUNK` is the first key | The generator uses the first key as the start symbol |
| P7 | **Coverage:** every production of every non-terminal is used by at least one accept case of §5 | Each production is exercised at least once |
| P8 | Every entry of `pred_exceptions` names a real non-terminal and production, and its token is in that production's **raw** prediction set and in the raw set of another production of the same non-terminal | An exception left behind after a grammar change (wrong index, token no longer there, or a conflict that no longer exists) |

How P7 is measured: wrap every `parse_A` method of the generated parser. On
entry, the current token picks exactly one production of `A`, because the
grammar is LL(1): the one whose prediction set contains it. Record that
`(A, production index)`. Run all accept cases and compare the recorded pairs
with all pairs of the grammar. The failure message lists the productions that
were never used, so new accept cases can be added for them.

### 4.1 Prediction-set exceptions

Some conflicts come from Lua itself and no LL(1) grammar can remove them
(K3 in §9 was one). They are resolved the way Lua does it, by removing a
token by hand from one prediction set after the sets are computed:

```python
pred_exceptions = {"PREFIXEXP_PRIME": {3: "tkn_opening_par"}}  # main.py
g.set_pred_exceptions(pred_exceptions)
g.process_grammar()   # FIRST, FOLLOW, predict, then apply_pred_exceptions()
```

`{A: {i: t}}` removes token `t` from `predict[A][i]`. Here, `(` after a
prefix expression always continues it as a call and never ends it (Lua's
greedy rule).

Unit tests for the two new `Grammar` methods (`test_pred_exceptions.py`),
using the dangling-else grammar of spec 004 E8 with `{"Sp": {1: "e"}}`:

| ID | What it checks |
|----|----------------|
| X1 | `set_pred_exceptions` stores the mapping and computes nothing |
| X2 | With no exceptions (never set, `None` or `{}`), `process_grammar` gives exactly the prediction sets of the step-by-step pipeline |
| X3 | The token is removed from that one set: `Sp` becomes `[{e}, {$}]` |
| X4 | The grammar goes from not LL(1) to LL(1) |
| X5 | FIRST, FOLLOW, the grammar and every other prediction set are unchanged |
| X6 | The mapping passed in is not modified |
| X7 | Exceptions on several non-terminals at once, including removing `$` |
| X8 | Applying twice gives the same result as applying once |
| X9 | `apply_pred_exceptions` after `compute_predict_set` equals `process_grammar` |

Out of scope: an unknown non-terminal or production index, and removing a
token that isn't in the set. For the real grammar these are caught by P8.

## 5. Accept cases by production

Each case is one Lua program, parsed with the real lexer, and `main()` must
return without raising. The cases follow manual §9 production by production,
not the names in `final_grammar`, so they stay valid when the grammar is
refactored. Line breaks inside a program are written as `↵`.

### 5.1 Program structure (B)

`chunk ::= block`, `block ::= {stat} [retstat]`

| ID | Program | What it checks |
|----|---------|----------------|
| B1 | (empty input) | A block can be empty |
| B2 | `x = 1` | One statement |
| B3 | `x = 1 y = 2 z = 3` | Several statements, no separators |
| B4 | `return` | A block made of only a return |
| B5 | `x = 1 return x` | Statements followed by a return |
| B6 | `;;;` | Only empty statements |
| B7 | `x = 1;;; y = 2` | Empty statements between statements |

### 5.2 Statements (S)

| ID | Program | Production |
|----|---------|------------|
| S1 | `;` | `';'` |
| S2 | `x = 1` | `varlist '=' explist`, one variable |
| S3 | `a, b, c = 1, 2, 3` | `varlist '=' explist`, several of each |
| S4 | `a, b = f()` | More variables than expressions |
| S5 | `f()` | `functioncall` |
| S6 | `obj:m(1)` | `functioncall`, method form |
| S7 | `::top::` | `label` |
| S8 | `while true do break end` | `break` |
| S9 | `goto top` | `goto Name` |
| S10 | `do end` | `do block end`, empty block |
| S11 | `do x = 1 end` | `do block end` |
| S12 | `while x < 10 do x = x + 1 end` | `while exp do block end` |
| S13 | `repeat x = x - 1 until x == 0` | `repeat block until exp` |
| S14 | `if x then end` | `if`, no `elseif`, no `else` |
| S15 | `if x then y = 1 else y = 2 end` | `if ... else` |
| S16 | `if a then elseif b then end` | One `elseif` |
| S17 | `if a then elseif b then elseif c then else end` | Several `elseif` and an `else` |
| S18 | `for i = 1, 10 do end` | Numeric `for` without a step |
| S19 | `for i = 10, 1, -1 do end` | Numeric `for` with a step |
| S20 | `for k in f() do end` | Generic `for`, one name |
| S21 | `for k, v in f(t) do end` | Generic `for`, several names |
| S22 | `for a, b, c in f, s, i do end` | Generic `for`, several expressions |
| S23 | `function f() end` | `function funcname funcbody` |
| S24 | `function a.b.c() end` | `funcname` with dots |
| S25 | `function a:m() end` | `funcname` with a colon |
| S26 | `function a.b:m(x) end` | `funcname` with dots and a colon |
| S27 | `local x` | `local attnamelist` without values |
| S28 | `local x, y = 1, 2` | `local attnamelist '=' explist` |
| S29 | `local function f() end` | `local function Name funcbody` |
| S30 | `global x` | `global attnamelist` |
| S31 | `global x, y = 1, 2` | `global` with values (the doc uses `global b = 5`) |
| S32 | `global function g() end` | `global function Name funcbody` |
| S33 | `global *` | `global '*'` |
| S34 | `global <const> *` | `global attrib '*'` |

### 5.3 Attributes (AT)

`attrib ::= '<' Name '>'`, only **after** a name (the prefix form is in §9,
K4).

| ID | Program | What it checks |
|----|---------|----------------|
| AT1 | `local x <const> = 5` | Attribute after the name |
| AT2 | `local f <close> = g()` | The other standard attribute |
| AT3 | `local a <const>, b, c <close> = 1, 2, 3` | Attributes on some names of a list |
| AT4 | `global x <const> = 1` | Attribute in a `global` declaration |
| AT5 | `local x <anything>` | Any `Name` is syntactically valid, checking it is semantic |

### 5.4 Return (RT)

`retstat ::= return [explist] [';']`, always the last statement of its block.

| ID | Program | What it checks |
|----|---------|----------------|
| RT1 | `return` | Without values |
| RT2 | `return 1` | One value |
| RT3 | `return 1, 2, 3` | Several values |
| RT4 | `return;` | Optional `;` without values |
| RT5 | `return f();` | Optional `;` with a value |
| RT6 | `function f() return end` | Return as the last statement of a function body |
| RT7 | `do return 1 end x = 2` | Return closes the inner block only. The outer block goes on |
| RT8 | `if x then return 1 elseif y then return 2 else return 3 end` | Return at the end of each branch |
| RT9 | `while x do return end` | Return before `end` |
| RT10 | `repeat return until x` | Return before `until` |

### 5.5 Function bodies and parameters (F)

`funcbody ::= '(' [parlist] ')' block end`,
`parlist ::= namelist [',' varargparam] | varargparam`,
`varargparam ::= '...' [Name]`

| ID | Program | What it checks |
|----|---------|----------------|
| F1 | `function f() end` | No parameters |
| F2 | `function f(a) end` | One parameter |
| F3 | `function f(a, b, c) end` | Several parameters |
| F4 | `function f(...) end` | Only varargs |
| F5 | `function f(a, ...) end` | Names and varargs |
| F6 | `function f(...args) end` | Named varargs (new in 5.5) |
| F7 | `function f(a, ...rest) end` | Names and named varargs |
| F8 | `x = function() end` | `functiondef` as an expression |
| F9 | `x = function(a, ...) return a end` | `functiondef` with parameters and a return |
| F10 | `f(function() end)` | `functiondef` as an argument |
| F11 | `function f() function g() end end` | A function nested in a function |

### 5.6 Tables (T)

`tableconstructor ::= '{' [fieldlist] '}'`,
`fieldlist ::= field {fieldsep field} [fieldsep]`,
`field ::= '[' exp ']' '=' exp | Name '=' exp | exp`, `fieldsep ::= ',' | ';'`

| ID | Program | What it checks |
|----|---------|----------------|
| T1 | `t = {}` | Empty table |
| T2 | `t = {1, 2, 3}` | Positional fields |
| T3 | `t = {x = 1, y = 2}` | `Name '=' exp` fields |
| T4 | `t = {[1] = "a", [k .. "x"] = 2}` | `'[' exp ']' '=' exp` fields |
| T5 | `t = {1; 2; 3}` | `;` as separator |
| T6 | `t = {1, x = 2; [3] = 4}` | All three field kinds and both separators |
| T7 | `t = {1, 2,}` | Trailing `,` |
| T8 | `t = {1;}` | Trailing `;` |
| T9 | `t = {{}, {{}}}` | Nested tables |
| T10 | `t = {f(), a.b, (x)}` | Prefix expressions as positional fields |
| T11 | `t = {x}` | A name alone is a positional field, not the start of `x = ...` |
| T12 | `t = {x == 1, y .. z}` | A name followed by an operator other than `=` |
| T13 | `t = {x = y}` | A name field whose value is a name |

### 5.7 Expressions (E)

`exp ::= nil | false | true | Numeral | LiteralString | '...' | functiondef |
prefixexp | tableconstructor | exp binop exp | unop exp`

| ID | Program | What it checks |
|----|---------|----------------|
| E1 | `x = nil`, `x = false`, `x = true` | Each constant (three programs) |
| E2 | `x = 42`, `x = 3.14`, `x = 0xFF` | Numbers |
| E3 | `x = "s"`, `x = 'c'` | Strings with both quote kinds |
| E4 | `function f(...) x = ... end` | `'...'` as an expression |
| E5 | `x = y` | A name as an expression |
| E6 | `x = (1)` | Parentheses |
| E7 | `x = f(1)` | A call as an expression |
| E8 | `x = {}` | A table as an expression |
| E9 | `x = -a`, `x = not a`, `x = #t` | Each allowed unary operator (three programs) |
| E10 | `x = - - a`, `x = not not a` | Repeated unary operators |
| E11 | `x = -a ^ 2` | Unary operator then binary operator |
| E12 | `x = 1 + 2 * 3 - 4 / 5` | A chain of binary operators |
| E13 | `x = a .. b .. c` | A chain of the same operator |
| E14 | `x = (a + b) * c` | Parentheses inside a binary expression |
| E15 | `x = a and b or not c` | Logical operators mixed |
| E16 | `x = #t + 1` | Unary inside binary |
| E17 | `x = "n"+a-true*(vari[3] % 70)` | The doc's semantic-error example is syntactically valid |
| E18 | `x = function() end .. {}` | Odd operands are still valid syntax |
| E19 | `x = a ~ b` | Binary `~` is allowed (only unary `~` is not) |
| E20 | `x = a ~= b` | `~=` is one token, not `~` then `=` |

**Binary operators (BO).** One program `x = a <op> b` per operator, 21 cases:
`+ - * / // ^ % & ~ | >> << .. < <= > >= == ~= and or`.

### 5.8 Prefix expressions, variables and calls (C)

`var ::= Name | prefixexp '[' exp ']' | prefixexp '.' Name`,
`prefixexp ::= var | functioncall | '(' exp ')'`,
`functioncall ::= prefixexp args | prefixexp ':' Name args`,
`args ::= '(' [explist] ')' | tableconstructor | LiteralString`

| ID | Program | What it checks |
|----|---------|----------------|
| C1 | `x = a.b` | Field access |
| C2 | `x = a[1]` | Index |
| C3 | `x = a.b.c[d][e]` | Mixed chain of fields and indexes |
| C4 | `a.b = 1` | Field as an assignment target |
| C5 | `a[i + 1] = 2` | Index with an expression as a target |
| C6 | `a.b[c].d = 3` | Chain as a target |
| C7 | `a, b.c, d[1] = 1, 2, 3` | Mixed targets in one assignment |
| C8 | `f()` | Call with no arguments |
| C9 | `f(1, 2)` | Call with several arguments |
| C10 | `f"str"` | String argument without parentheses |
| C11 | `f{1, 2}` | Table argument without parentheses |
| C12 | `o:m"s"`, `o:m{}` | Method call with string and table arguments |
| C13 | `f()()` | Calling the result of a call |
| C14 | `f().x = 1` | Field of a call result as a target |
| C15 | `f()[1] = 2` | Index of a call result as a target |
| C16 | `a.b:c(1):d(2)` | Chain of method calls |
| C17 | `(f)()` | Parenthesised expression called |
| C18 | `("s"):upper()` | Method call on a parenthesised string |
| C19 | `(a).b = 1` | Field of a parenthesised expression as a target |
| C20 | `a.b.c:d "x" {1} (2)` | Long chain with all three argument kinds |
| C21 | `x = f(g(h(1)))` | Nested calls |
| C22 | `function f(...) g(...) end` | Varargs as an argument |
| C23 | `a, (b).c = 1, 2` | A parenthesised prefix expression as a later assignment target |

### 5.9 Built-in names (N)

`print`, `pcall`, `xpcall`, `error` and `warn` behave as `Name` (§3.1).

| ID | Program | What it checks |
|----|---------|----------------|
| N1 | `print("hola")` | Call |
| N2 | `print "hola"` | Call with a string argument |
| N3 | `print = 1` | Assignment target |
| N4 | `local warn = 2` | Local name |
| N5 | `function error() end` | Function name |
| N6 | `local function pcall() end` | Local function name |
| N7 | `xpcall(f, error)` | As an argument |
| N8 | `t.print = print` | Field name and value |
| N9 | `a:print()` | Method name |
| N10 | `function t.error:warn() end` | Parts of a `funcname` |
| N11 | `function f(print, warn) end` | Parameter names |
| N12 | `for print = 1, 2 do end` | Numeric `for` variable |
| N13 | `for error, warn in f() do end` | Generic `for` variables |
| N14 | `t = {print = 1}` | Field name in a table |
| N15 | `::error:: goto error` | Label and `goto` |

### 5.10 Layout (L)

| ID | Program | What it checks |
|----|---------|----------------|
| L1 | `local a = 4;↵global b = 5;` | Doc example, one statement per line |
| L2 | `local a = 4; global b=5;` | Doc example, one line |
| L3 | `local a = 4 global b = 5` | No separators at all |
| L4 | `x↵=↵1` | A statement split over lines |
| L5 | `if x↵then↵y = 1↵end` | Keywords on separate lines |
| L6 | `-- comment↵x = 1 -- another` | Comments are skipped by the lexer |

## 6. Edge accept cases (EA)

| ID | Program | What it checks |
|----|---------|----------------|
| EA1 | The doc's first example: `function saludar(texto)` ... `saludar("¡Hola, mundo!")`, with its comments | Doc example, accepted |
| EA2 | The doc's `local entrada` / `if entrada == nil then` ... `end` example | Doc example, accepted |
| EA3 | `x = ` followed by 50 `(`, `1`, and 50 `)` | Deep recursion in expressions |
| EA4 | 50 nested `do ... end` | Deep recursion in blocks |
| EA5 | 50 nested `if x then ... end` | Deep recursion through `if` |
| EA6 | 50 nested tables `{{{...}}}` | Deep recursion in tables |
| EA7 | 200 statements `x = 1` in a row | Long statement list |
| EA8 | `x = 1 + 1 + ... + 1` with 200 terms | Long operator chain |
| EA9 | `f = function() return function() return ... end end`, 10 levels | Nested function bodies |
| EA10 | `function f() ; end` | A body with only an empty statement |
| EA11 | Only comments and blank lines | Same as empty input |
| EA12 | `return function() return {f = function() return end} end` | Return, functions and tables mixed |
| EA13 | `f()↵(g)()` | `(` on the next line continues the call chain, read as `f()(g)()` (§4.1) |

Every EA case has a time limit (§11), so a parser that loops forever fails
instead of hanging.

## 7. Reject cases (R)

Each case gives the program, the found lexeme and position, and the expected
list.

- For the doc examples (marked **doc**), the whole line is fixed by the
  grader. The test compares the complete message.
- For the other cases, the test checks the position and the lexeme exactly,
  and checks that the expected list **contains** the tokens shown. These
  lists come from the manual, not from the grader, so only the tokens that
  are obviously in the list are required.
- At the end of input the lexeme is `final de archivo`. The doc doesn't say
  which position to report there (§9, K9), so EOF cases don't check the
  position.

| ID | Program | At | Found | Expected (contains) |
|----|---------|----|-------|---------------------|
| R1 **doc** | `local 1;` | 1:7 | `1` | exactly `"error", "function", "id", "pcall", "print", "warn", "xpcall"` |
| R2 **doc** | `print(45"this")` | 1:9 | `this` | exactly `"and", "or", "&", "\|", "~", ")", ",", "..", "/", "==", "//", ">=", ">", "<<", "<=", "<", "-", "%", "~=", "+", "^", ">>", "*"` |
| R3 **doc** | `local i = 0;↵↵while (i < 5) do↵    p == [i];3↵    i = i + 1;↵end` | 4:7 | `==` | exactly `"=", ":", ",", "[", "(", "."` |
| R4 | `if x then y = 1` | EOF | `final de archivo` | `"end"`, `"elseif"`, `"else"` |
| R5 | `repeat x = 1` | EOF | `final de archivo` | `"until"` |
| R6 | `function f() x = 1` | EOF | `final de archivo` | `"end"` |
| R7 | `f(1, 2` | EOF | `final de archivo` | `")"`, `","` |
| R8 | `x = t[1` | EOF | `final de archivo` | `"]"` |
| R9 | `x = {1, 2` | EOF | `final de archivo` | `"}"` |
| R10 | `x = 1 +` | EOF | `final de archivo` | `"id"`, `"valor_numerico"`, `"("` |
| R11 | `if x y = 1 end` | 1:6 | `y` | `"then"` |
| R12 | `while x y() end` | 1:9 | `y` | `"do"` |
| R13 | `return 1 x = 2` | 1:10 | `x` | `"final de archivo"`, `";"`, `","` |
| R14 | `x = = 1` | 1:5 | `=` | `"id"`, `"nil"`, `"valor_numerico"`, `"("` |
| R15 | `x = ~y` | 1:5 | `~` | `"id"`, `"-"`, `"not"`, `"#"` |
| R16 | `x = a ~ ~b` | 1:9 | `~` | `"id"`, `"-"` (binary `~` was accepted, the unary one is not) |
| R17 | `for i = 1 do end` | 1:11 | `do` | `","` |
| R18 | `for in t do end` | 1:5 | `in` | `"id"` |
| R19 | `function f(a,) end` | 1:14 | `)` | `"id"`, `"..."` |
| R20 | `function (a) end` | 1:10 | `(` | `"id"` |
| R21 | `goto end` | 1:6 | `end` | `"id"` |
| R22 | `::l x = 1` | 1:5 | `x` | `"::"` |
| R23 | `local function a.b() end` | 1:17 | `.` | `"("` |
| R24 | `global x, *` | 1:11 | `*` | `"id"` |
| R25 | `f())` | 1:4 | `)` | `"final de archivo"` |
| R26 | `x = 1 2` | 1:7 | `2` | `"final de archivo"` |
| R27 | `local x <const = 1` | 1:16 | `=` | `">"` |
| R28 | `if x then else elseif y then end` | 1:16 | `elseif` | `"end"` |
| R29 | `x. = 2` | 1:4 | `=` | `"id"` |
| R30 | `t = {[1] 2}` | 1:10 | `2` | `"="` |
| R31 | `function f() return 1 end end` | 1:27 | `end` | `"final de archivo"` |
| R32 | `x, = 1` | 1:4 | `=` | `"id"`, `"("` |
| R33 | `local = 1` | 1:7 | `=` | exactly the R1 list |
| R34 | `x = ()` | 1:6 | `)` | `"id"`, `"valor_numerico"` |
| R35 | `a.b:c = 1` | 1:7 | `=` | `"("` |
| R36 | `local a = 1↵local b = 2↵local c = = 3` | 3:11 | `=` | `"id"`, `"valor_numerico"` (checks the line number) |
| R37 | `x = 1↵↵↵y = ` | EOF | `final de archivo` | `"id"` (EOF after blank lines) |
| R38 | `t = {1,, 2}` | 1:8 | `,` | `"}"` |
| R39 | `a = f↵(g).x = 1` | 2:7 | `=` | `"final de archivo"`, `"id"` (read greedily as `a = f(g).x`, then a second `=`, as in Lua) |

**Only the first error.** R3 has a second error on the same line (`3` after
`;`). R36 can be extended with another error on line 4. In both, only the
first error is reported.

## 8. Output cases (O)

These run `main.py` as a subprocess (§2) and compare its whole stdout with
the expected text. They are the only tests that check the success message,
the absence of any prefix, and that exactly one line is printed.

| ID | Input | Expected stdout |
|----|-------|-----------------|
| O1 | EA1 (doc) | `El analisis sintactico ha finalizado exitosamente.` |
| O2 | EA2 (doc) | `El analisis sintactico ha finalizado exitosamente.` |
| O3 | R1 (doc) | `<1:7> Error sintactico: se encontro: "1"; se esperaba: "error", "function", "id", "pcall", "print", "warn", "xpcall".` |
| O4 | R2 (doc) | `<1:9> Error sintactico: se encontro: "this"; se esperaba: "and", "or", "&", "\|", "~", ")", ",", "..", "/", "==", "//", ">=", ">", "<<", "<=", "<", "-", "%", "~=", "+", "^", ">>", "*".` |
| O5 | R3 (doc) | `<4:7> Error sintactico: se encontro: "=="; se esperaba: "=", ":", ",", "[", "(", ".".` |
| O6 | L1 | `El analisis sintactico ha finalizado exitosamente.` |
| O7 | Empty input | `El analisis sintactico ha finalizado exitosamente.` |
| O8 | R4 | One line starting with `<` and containing `se encontro: "final de archivo"` |

(In the O4 row, `\|` is the `|` symbol escaped for the table.)

Checked for every O case:

- Exactly one line on stdout, with no `error: ` prefix and no extra
  messages.
- The exit code is not checked, since the doc says nothing about it.

**Cross-check on all R cases.** For every R case, the expected list in the
message has no repeated entries and is sorted as in §3.2. This catches an
order or rendering mistake even in cases with no fixed list.

## 9. Known limitations (documented, not tested)

These are real differences between Lua and what an LL(1) grammar can do, or
points where the doc is unclear. They have no pass/fail cases. If the grader
shows how it handles them, turn them into cases.

| ID | Topic | What Lua does | Why it isn't tested |
|----|-------|---------------|---------------------|
| K1 | A prefix expression that is not a call, used as a statement: `x`, `t.k`, `(f)`, `f().x` | Syntax error ("syntax error near ...") | The parser only knows the last suffix after it has read the whole prefix expression. Rejecting these needs a check after parsing that the last suffix was a call, not a grammar rule |
| K2 | A call on the left of `=`: `f() = 1`, `a:m() = 2` | Syntax error | Same reason as K1, but checking that the last suffix was **not** a call |
| K3 | `a = f↵(g).x = 1` | Read greedily as one statement, `a = f(g).x = 1`, so the second `=` is the error | **Resolved** by the exception of §4.1, and now tested as EA13 and R39 |
| K4 | An attribute before the first name: `local <const> x`, `global <const> x` | Valid in the 5.5 manual | The doc's R1 list has no `"<"`, so the grader seems not to allow it. If the grammar allows it, R1 and R33 fail |
| K5 | Other built-ins as names: `pairs`, `ipairs`, `tostring`, `tonumber`, `select`, `next`, `load`, `loadfile`, `dofile` | Ordinary names | The lexer gives them their own token types, and the doc lists only the five of §3.1 as identifiers. It is unknown whether the grader accepts `for k, v in pairs(t) do end`. Very common code, so worth asking on Campuswire |
| K6 | `print` as a token | — | The grader treats `print` as its own token (R1 lists `"print"`), but it is commented out of `keywords_set` (`lexer/lexer.py:81`). As an `id`, R1, R33 and O3 lose `"print"` from the list |
| K7 | Order of the expected list | — | The doc says "lexicographic" and "separated by a blank space", but its examples are sorted by token-type name and separated by `", "`. The spec follows the examples. Where `"final de archivo"` (`$`) goes in a sorted list is unknown |
| K8 | Call suffixes in the R3 list | `p{...}` and `p"s"` are valid calls | The grader's list after `p` (`"=", ":", ",", "[", "(", "."`) has no `"{"` and no `"cadena_de_caracteres"`, although C10, C11 and N2 are valid Lua. Matching R3 exactly and accepting C10/C11 may not both be possible |
| K9 | Position of an EOF error | — | The doc doesn't give an example, so it's unknown whether the grader reports the end of the last line or the next line |

## 10. Out of scope (behavior not defined)

- Semantic errors, which must be **accepted**: `break` outside a loop, `goto`
  to a missing label, duplicate labels, `...` outside a vararg function,
  assigning to a `<const>` variable, attribute names other than `const` and
  `close`, operand types.
- Lexical errors (the doc says the input has none).
- Long strings and long comments (`[[...]]`, `--[[...]]`), which never appear
  in the platform tests.
- Precedence and associativity, because no tree is built (§3.1).
- The internals of FIRST, FOLLOW, predict, the LL(1) check and the generator
  (specs 001 to 005).

## 11. Test organization

- Files, all in `syntax/tests/`:
  - `test_real_grammar_properties.py` for §4;
  - `test_real_grammar_parse.py` for §5 to §7;
  - `test_real_grammar_output.py` for §8;
  - `test_pred_exceptions.py` for the X cases of §4.1;
  - `real_grammar_cases.py` (the case tables) and `real_grammar_support.py`
    (shared helpers). These are not collected as tests.
- Import `final_grammar` from `main.py`, so the tests always follow the
  current grammar. The project root is already on `sys.path` (see
  `conftest.py`).
- A session-scoped fixture in `conftest.py` generates the parser once into a
  temporary `syntax/` folder and loads it as a `syntax.*` module. It is the
  same technique as `out_dir` and `load_parser` in `test_code_generator.py`,
  but session-scoped. If P1 fails, the fixture skips every parsing test with
  a clear reason, since no parser can be generated.
- A second session fixture copies the project into a temporary folder for the
  O cases.
- Use `pytest.mark.parametrize` with the IDs of this spec (`S12`, `BO-..`,
  `R27`, ...) for every table.
- Failing cases get a strict xfail mark, as in specs 001 to 005. The reason
  describes only the symptom (for example "R15 accepted"), never the cause or
  a fix. Cases that depend on §3.4 start as xfail.
- Every test has a time limit (`pytest-timeout`), so a parser that loops
  forever fails.
- Run with `pytest tests` from `syntax/`.
- When `final_grammar` changes, only P7 should need new cases. If an accept
  or reject case stops matching, fix the grammar, not the case, unless the
  grader shows otherwise. When the grader's behavior on one of the K points
  becomes known, move it from §9 into a table and update this spec (see
  `syntax/AGENTS.md`).
