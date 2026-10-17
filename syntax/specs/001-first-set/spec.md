# Spec 001 — Testing the FIRST set computation

## 1. Purpose and scope

This spec describes how to test that the FIRST sets of a grammar are computed
correctly by `syntax/main.py`.

- **In scope:** the functions `first_of_sequence` and `compute_first_set`.
- **Out of scope:** checking whether the grammar is LL(1), FOLLOW sets,
  prediction sets and the parser itself. A grammar that is not LL(1) (left
  recursive, ambiguous, with common prefixes...) still has well-defined FIRST
  sets, so such grammars are valid test inputs here.

## 2. Grammar format and interface under test

A grammar is a Python dictionary `dict[str, list[list[str]]]`:

- Each **key** is a non-terminal.
- Each **value** is the list of productions (alternatives) of that
  non-terminal. Each production is a list of symbols, read left to right.
- The string `"ε"` stands for the empty production and is written as the
  production `["ε"]`. It is never a key.
- Any symbol that is **not** a key of the dictionary is a terminal.

Example, `S → a B | ε`, `B → b`:

```python
grammar = {
    "S": [["a", "B"], ["ε"]],
    "B": [["b"]],
}
```

The caller prepares two values before calling the functions:

```python
first = {nt: set() for nt in grammar}   # one empty set per non-terminal
non_terminals_set = set(grammar)
```

The functions under test receive everything as parameters:

```python
compute_first_set(grammar, first, non_terminals_set)        # fills first in place, returns nothing
first_of_sequence(sequence, first, non_terminals_set)       # returns FIRST(sequence), only reads first
```

`sequence` is a single production, such as `["X", "y"]`. Combining the results
of all productions of a non-terminal is `compute_first_set`'s job.

The tests assume the functions use only what they receive as parameters, not
the module-level `grammar`, `first` or `non_terminals_set`.

## 3. What "correct" means

FIRST(X) is the set of terminals that can appear first in some string derived
from X. If X can derive the empty string (X is *nullable*), then ε also belongs
to FIRST(X).

For a production `A → Y1 Y2 ... Yn`, FIRST(A) receives:

1. FIRST(Y1) without ε.
2. If Y1 is nullable, also FIRST(Y2) without ε, and so on to the right.
3. The process stops at the first symbol that is not nullable. A terminal is
   never nullable.
4. ε is added to FIRST(A) only if **all** of Y1 ... Yn are nullable, or if the
   production is `["ε"]`.

How the tests check results:

- They compare sets **exactly**. A missing symbol is an error, and so is an
  extra one.
- They check **every** non-terminal of the grammar, not only the start symbol.
- After the computation, the keys of `first` are exactly the non-terminals of
  the grammar. No terminals are added as keys.

## 4. Unit tests for `first_of_sequence`

`first_of_sequence` computes FIRST of **one** production. Each test:

1. Declares the helper non-terminals (`X`, `Y`, `Z`) and fills `first` by hand
   with their FIRST sets, as if they had already been computed.
2. Calls `first_of_sequence(sequence, first, non_terminals_set)` once.
3. Checks the returned set, and checks that `first` was not modified at all.

Lowercase letters are terminals.

| ID  | Sequence    | Preset FIRST of helpers         | Expected result | What it checks                                    |
|-----|-------------|---------------------------------|-----------------|---------------------------------------------------|
| U1  | `a`         | —                               | {a}             | A single terminal                                 |
| U2  | `b c`       | —                               | {b}             | Only the first terminal of a sequence counts      |
| U3  | `ε`         | —                               | {ε}             | Empty production                                  |
| U4  | `X`         | X = {x, ε}                      | {x, ε}          | A single nullable non-terminal keeps ε            |
| U5  | `a X`       | X = {x}                         | {a}             | Symbols after a leading terminal are ignored      |
| U6  | `X y`       | X = {x}                         | {x}             | A non-nullable non-terminal stops the scan (y must not appear) |
| U7  | `X y`       | X = {x, ε}                      | {x, y}          | A nullable non-terminal lets the next terminal in |
| U8  | `X Y`       | X = {x, ε}, Y = {y, ε}          | {x, y, ε}       | Fully nullable sequence gives ε                   |
| U9  | `X Y Z`     | X = {x, ε}, Y = {y, ε}, Z = {z} | {x, y, z}       | Chain of nullables, ending in a non-nullable one (no ε) |
| U10 | `X Y w`     | X = {x, ε}, Y = {y}             | {x, y}          | Scan stops at the non-nullable Y (w must not appear) |
| U11 | `X y`       | X = {} (not computed yet)       | {}              | A non-terminal with an empty FIRST so far contributes nothing and is not nullable, which is the situation on the first pass |

Several alternatives of one non-terminal (for example `A → a | ε`) are no
longer a unit case. Combining alternatives happens in `compute_first_set` and
is covered by the end-to-end grammars (E1, E4, E12…).

## 5. End-to-end tests for `compute_first_set`

Each test builds a fresh `first` and `non_terminals_set`, calls
`compute_first_set` once, and compares the whole `first` dictionary against
the expected one.

**E1. Only terminals.** Base case.
```
S → a b | c
```
Expected: S = {a, c}

**E2. The grammar currently in `main.py`.**
```
A → B C | ant A all
B → big C | bus A boss | ε
C → cat | cow
```
Expected: C = {cat, cow}, B = {big, bus, ε}, A = {ant, big, bus, cat, cow}.
(A gets FIRST(C) because B is nullable. A is not nullable because C is not.)

**E3. Dependency chain.** Information must travel through several levels.
```
S → A
A → B
B → b
```
Expected: S = A = B = {b}

**E4. Nullable prefix.**
```
S → A B c
A → a | ε
B → b | ε
```
Expected: A = {a, ε}, B = {b, ε}, S = {a, b, c}. S has no ε because c is a terminal.

**E5. Whole body nullable.**
```
S → A B
A → a | ε
B → b | ε
```
Expected: A = {a, ε}, B = {b, ε}, S = {a, b, ε}

**E6. Indirectly nullable.** ε reaches S only through other non-terminals.
```
S → A
A → B
B → ε
```
Expected: S = A = B = {ε}

**E7. ε must not leak.**
```
S → A b
A → ε
```
Expected: A = {ε}, S = {b}

**E8. A non-nullable non-terminal blocks the rest.**
```
S → A B
A → a
B → b
```
Expected: A = {a}, B = {b}, S = {a}

**E9. Direct left recursion.**
```
E → E + T | T
T → id | ( E )
```
Expected: E = {id, (}, T = {id, (}

**E10. Mutual (indirect) recursion.**
```
A → B a | x
B → A b | y
```
Expected: A = {x, y}, B = {x, y}

**E11. Recursion with a nullable non-terminal.**
```
A → B A | a
B → b | ε
```
Expected: B = {b, ε}, A = {a, b}. A is not nullable.

**E12. Right recursion with ε (list pattern).**
```
L → x L | ε
```
Expected: L = {x, ε}

**E13. Classic expression grammar.** A well-known textbook result.
```
E  → T E'
E' → + T E' | ε
T  → F T'
T' → * F T' | ε
F  → ( E ) | id
```
Expected: E = T = F = {(, id}, E' = {+, ε}, T' = {*, ε}

**E14. Not LL(1): common prefix.** FIRST is still well defined.
```
S → a b | a c
```
Expected: S = {a}

**E15. Multi-character and punctuation terminals.** A symbol is the whole
string, never split into characters. This matters for Lua tokens.
```
Stat → local Name = Exp | Exp
Exp  → ( Exp ) | Exp == Exp | Name
```
Here `Stat` and `Exp` are non-terminals, and `local`, `Name`, `=`, `(`, `)`
and `==` are terminals.
Expected: Exp = {(, Name}, Stat = {local, (, Name}

## 6. Properties checked across all grammars

**Order independence.** The result must not depend on the order of the keys
in the dictionary. Every E-grammar is run with its non-terminals in several
orders: as written, reversed, and every permutation when the grammar has at
most 4 non-terminals. All orders must give the same expected sets. E3 must
explicitly be tested in bottom-up order (`B`, then `A`, then `S`) and in
top-down order.

**Idempotence.** Calling `compute_first_set` a second time on the same
`first` dictionary must not change the result.

**Isolation.** Every test builds its own `grammar`, `first` and
`non_terminals_set`. No test depends on the module-level variables of
`main.py` or on another test having run before it.

## 7. Out of scope (well-formed grammars only)

These inputs are not tested. Their behavior is not defined yet:

- An empty production `[]`.
- ε mixed into a longer production, such as `["a", "ε"]`.
- A non-terminal with no productions (`"A": []`).
- Symbols that look like non-terminals but are not keys of the grammar. By
  definition these are terminals, and no test relies on this.
- LL(1) conflict detection, FOLLOW sets and prediction sets.

## 8. Test organization

- File: `syntax/tests/test_first_set.py`.
- A helper `fresh(grammar)` returns `(first, non_terminals_set)`, built as in
  section 2.
- A helper that reorders a grammar dictionary is used for the order-independence
  tests.
- Use `pytest.mark.parametrize` for the unit-test table (section 4), the
  end-to-end table (section 5) and the key orders (section 6).
- Run with `pytest syntax/tests`.
- If a function is added to or removed from the FIRST computation, update this
  spec and its tests to match (see `syntax/AGENTS.md`).
