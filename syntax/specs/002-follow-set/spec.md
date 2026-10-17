# Spec 002 — Testing the FOLLOW set computation

## 1. Purpose and scope

This spec describes how to test that the FOLLOW sets of a grammar are computed
correctly by `syntax/main.py`.

- **In scope:** the function `compute_follow_set`.
- **Out of scope:** the FIRST computation (covered by spec 001), checking
  whether the grammar is LL(1), prediction sets and the parser itself. A
  grammar that is not LL(1) (left recursive, with common prefixes...) still has
  well-defined FOLLOW sets, so such grammars are valid test inputs here.

## 2. Grammar format and interface under test

The grammar format is the same as in spec 001 §2: a dictionary
`dict[str, list[list[str]]]`. Keys are non-terminals, `"ε"` is written as the
production `["ε"]`, and any symbol that is not a key is a terminal.

One extra rule matters for FOLLOW: **the first key of the dictionary is the
start symbol.** The function has no start-symbol parameter, so the order of
the first key carries that meaning.

The end-of-input marker is the string `"$"`.

The caller prepares these values before calling the function:

```python
first = {...}                            # FIRST sets, already complete and correct
follow = {nt: set() for nt in grammar}   # one empty set per non-terminal
non_terminals_set = set(grammar)
```

```python
compute_follow_set(grammar, first, follow, non_terminals_set)   # fills follow in place, returns nothing
```

The function only **reads** `first` and must not change it. The tests assume
it uses only what it receives as parameters, not the module-level `grammar`,
`first`, `follow` or `non_terminals_set`.

## 3. What "correct" means

FOLLOW(A) is the set of terminals that can appear immediately to the right of
A in some sentential form derived from the start symbol. `$` stands for "the
end of the input".

The sets are built with these rules:

1. `$` belongs to FOLLOW(start).
2. For every production `A → α B β`, where B is a non-terminal: FIRST(β)
   without ε goes into FOLLOW(B).
3. If β is empty (B is the last symbol) or β is nullable, then everything in
   FOLLOW(A) also goes into FOLLOW(B).
4. Rules 2 and 3 are applied again and again until no set changes.

How the tests check results:

- They compare sets **exactly**. A missing symbol is an error, and so is an
  extra one.
- They check **every** non-terminal of the grammar, not only the start symbol.
- After the computation, the keys of `follow` are exactly the non-terminals of
  the grammar. No terminals are added as keys.
- **ε never appears** in any FOLLOW set.
- `first` is exactly the same before and after the call.

## 4. Rule-level tests with hand-written FIRST sets (F cases)

Most tests do not call `compute_first_set`. They give the correct FIRST sets,
written by hand, so that a failure here can only come from the FOLLOW
computation. Each test:

1. Builds the grammar, the hand-written `first`, an empty `follow` and
   `non_terminals_set`.
2. Calls `compute_follow_set` once.
3. Compares the whole `follow` dictionary against the expected one, and checks
   the properties in §3.

Uppercase names are non-terminals, everything else is a terminal. The first
non-terminal listed is the start symbol.

| ID  | Grammar | Given FIRST | Expected FOLLOW | What it checks |
|-----|---------|-------------|-----------------|----------------|
| F1  | S → a | S = {a} | S = {$} | Base case: the start symbol gets only $ |
| F2  | S → A b<br>A → a | S = {a}, A = {a} | S = {$}, A = {b} | A terminal after a non-terminal. $ goes to the start symbol only |
| F3  | S → a A<br>A → b | S = {a}, A = {b} | S = {$}, A = {$} | A non-terminal at the end of a production gets FOLLOW of the left side |
| F4  | S → A B<br>A → a<br>B → b | S = {a}, A = {a}, B = {b} | S = {$}, A = {b}, B = {$} | Followed by a non-nullable non-terminal: A gets FIRST(B) and nothing from FOLLOW(S) |
| F5  | S → A B c<br>A → a<br>B → b \| ε | S = {a}, A = {a}, B = {b, ε} | S = {$}, A = {b, c}, B = {c} | The scan skips the nullable B to reach c. ε is not copied |
| F6  | S → A B<br>A → a<br>B → b \| ε | S = {a}, A = {a}, B = {b, ε} | S = {$}, A = {b, $}, B = {$} | Because the rest of the production is nullable, A also gets FOLLOW(S) |
| F7  | S → x A B C<br>A → a<br>B → b \| ε<br>C → c \| ε | S = {x}, A = {a}, B = {b, ε}, C = {c, ε} | S = {$}, A = {b, c, $}, B = {c, $}, C = {$} | A long nullable tail |
| F8  | S → A a A<br>A → x | S = {x}, A = {x} | S = {$}, A = {a, $} | The same non-terminal appears twice in one production. Both occurrences count |
| F9  | S → A x \| B<br>B → A y<br>A → a | S = {a}, B = {a}, A = {a} | S = {$}, B = {$}, A = {x, y} | A non-terminal used in productions of different non-terminals collects from all of them |
| F10 | S → A z<br>A → b B<br>B → c C<br>C → d | S = {b}, A = {b}, B = {c}, C = {d} | S = {$}, A = B = C = {z} | Inheritance travels through several levels |
| F11 | S → A z<br>A → B C<br>B → b<br>C → c \| ε | S = {b}, A = {b}, B = {b}, C = {c, ε} | S = {$}, A = {z}, B = {c, z}, C = {z} | Inheritance through a nullable tail, one level down |
| F12 | S → A t<br>A → a B<br>B → b A \| ε | S = {a}, A = {a}, B = {b, ε} | S = {$}, A = {t}, B = {t} | A cycle: FOLLOW(A) and FOLLOW(B) feed each other. The computation must still finish |
| F13 | S → ( S ) \| x | S = {(, x} | S = {$, )} | The start symbol also appears on a right-hand side. It keeps $ and gains ) |
| F14 | S → A<br>A → b S c \| d | S = {b, d}, A = {b, d} | S = {$, c}, A = {$, c} | The start symbol gains c from a deeper rule, and it flows back down to A |
| F15 | S → a<br>U → u | S = {a}, U = {u} | S = {$}, U = {} | A non-terminal that is never used keeps an empty FOLLOW set, and its key is still there |
| F16 | S → A E<br>A → a<br>E → ε | S = {a}, A = {a}, E = {ε} | S = {$}, A = {$}, E = {$} | A tail that only derives ε adds nothing of its own (no ε), so A only inherits |
| F17 | E → E + T \| T<br>T → id | E = {id}, T = {id} | E = {$, +}, T = {$, +} | Direct left recursion |
| F18 | L → x L \| ε | L = {x, ε} | L = {$} | A non-terminal at the end of its own production (it inherits from itself). Must finish |
| F19 | S → A A<br>A → a \| ε | S = {a, ε}, A = {a, ε} | S = {$}, A = {a, $} | A nullable non-terminal followed by itself |
| F20 | Chunk → Block<br>Block → Stat Block \| ε<br>Stat → if Exp then Block end \| Name = Exp<br>Exp → Name \| Number | Chunk = {if, Name, ε}, Block = {if, Name, ε}, Stat = {if, Name}, Exp = {Name, Number} | Chunk = {$}, Block = {$, end}, Stat = {if, Name, $, end}, Exp = {then, if, Name, $, end} | A small Lua-like grammar. Multi-character terminals (`if`, `then`, `end`, `Name`, `=`) are single symbols |

## 5. Full-pipeline tests (E cases)

A smaller group runs the real pipeline: build fresh `first` and `follow`,
call `compute_first_set`, then call `compute_follow_set`, and compare the whole
`follow` dictionary. These tests check that the two functions work together,
the way the parser will use them.

**E1. The grammar currently in `main.py`.**
```
A → B C | ant A all
B → big C | bus A boss | ε
C → cat | cow
```
Expected: A = {$, all, boss}, B = {cat, cow}, C = {$, all, boss, cat, cow}.
(C gets FOLLOW(A) from `A → B C` and FOLLOW(B) from `B → big C`.)

**E2. Classic expression grammar.** A well-known textbook result.
```
E  → T E'
E' → + T E' | ε
T  → F T'
T' → * F T' | ε
F  → ( E ) | id
```
Expected: E = E' = {$, )}, T = T' = {+, $, )}, F = {*, +, $, )}

**E3. A tail that is nullable only through another non-terminal.**
```
S → A B C
A → a
B → D
D → d | ε
C → c | ε
```
Expected: S = {$}, A = {d, c, $}, B = {c, $}, C = {$}, D = {c, $}

**E4. The Lua-like grammar from F20**, with FIRST computed instead of written
by hand. Expected: the same FOLLOW sets as F20.

If an E case fails while the matching F case (or the FIRST tests of spec 001)
pass, the problem is in how the two functions connect, not in the FOLLOW rules
themselves.

## 6. Properties checked across all grammars

**Termination.** Every test has a time limit. If `compute_follow_set` never
returns, the test fails instead of hanging the whole suite. This matters most
for the cycle cases (F12, F14, F18).

**No ε, exact keys, `first` unchanged.** These checks from §3 run after every
F and E test, not only in a dedicated test.

**Order independence.** The result must not depend on the order of the keys,
**except the first key**, which is the start symbol and always stays first.
Every F and E grammar is run with the other keys in several orders: every
permutation when the grammar has at most 4 non-terminals, otherwise as written
and reversed. F10 must explicitly be tested in the bottom-up order (`S`, then
`C`, `B`, `A`) and in the top-down order (`S`, `A`, `B`, `C`).

**Idempotence.** Calling `compute_follow_set` a second time on the same
`follow` dictionary must not change the result.

**Isolation.** Every test builds its own `grammar`, `first`, `follow` and
`non_terminals_set`. No test depends on the module-level variables of
`main.py` or on another test having run before it, and running the function
leaves those module-level variables unchanged.

## 7. Out of scope (well-formed inputs only)

These inputs are not tested. Their behavior is not defined yet:

- An empty production `[]`.
- ε mixed into a longer production, such as `["a", "ε"]`.
- A non-terminal with no productions (`"A": []`).
- An empty grammar `{}`.
- A start symbol other than the first key.
- A non-terminal that is never used but whose productions mention other
  non-terminals (whether it should add to their FOLLOW sets is not defined
  here).
- Incomplete or incorrect FIRST sets passed as input.
- LL(1) conflict detection and prediction sets.

## 8. Test organization

- File: `syntax/tests/test_follow_set.py`.
- Reuse the `fresh` and `reorder` helpers from `conftest.py`, extended so they
  also build an empty `follow` dictionary.
- Use `pytest.mark.parametrize` for the F table (section 4), the E table
  (section 5) and the key orders (section 6).
- Failing tests get an xfail mark as in spec 001. The reason text describes
  only the symptom (for example "FOLLOW(A) is missing $"), never the cause or
  a fix.
- Run with `pytest syntax/tests`.
- If a function is added to or removed from the FOLLOW computation, update this
  spec and its tests to match (see `syntax/AGENTS.md`).
