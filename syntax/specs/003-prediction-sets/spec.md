# Spec 003 — Testing the prediction set computation

## 1. Purpose and scope

This spec describes how to test that the prediction sets of a grammar are
computed correctly by the `Grammar` class in `syntax/grammar.py`.

- **In scope:** the method `Grammar.compute_predict_set`, the getter
  `Grammar.get_predict_set`, and the empty `predict` dictionary the
  constructor builds for them.
- **Out of scope:** the FIRST and FOLLOW computations (covered by specs 001
  and 002), checking whether the grammar is LL(1) (`check_LL1_condition`, which
  needs its own spec), building the parse table and the parser itself.
- A grammar that is not LL(1) still has well-defined prediction sets: the sets
  of one non-terminal simply overlap. Such grammars are valid test inputs, and
  the tests check the overlapping sets like any others. They do **not** check
  that the sets are disjoint.

## 2. Grammar format, interface and output format

The grammar format is the same as in spec 001 §2 and spec 002 §2:

- a dictionary `dict[str, list[list[str]]]`;
- `"ε"` is written as the production `["ε"]`;
- any symbol that is not a key is a terminal;
- **the first key is the start symbol**;
- the end-of-input marker is `"$"`.

The caller builds a `Grammar` object and makes sure its FIRST and FOLLOW sets
are complete and correct before computing the prediction sets:

```python
g = Grammar(grammar)       # g.predict == {nt: [] for nt in grammar}
g.compute_first_set()      # or fill g.first by hand
g.compute_follow_set()     # or fill g.follow by hand
g.compute_predict_set()    # fills g.predict in place, returns nothing
predict = g.get_predict_set()   # returns g.predict itself, not a copy
```

**Output format.** After the call, `predict[A]` is a **list of sets**:

- `predict[A][i]` is the prediction set of the production `grammar[A][i]`;
- the list has exactly one entry per production, in the same order as the
  productions in the grammar;
- each entry is a Python `set` of strings.

Example, for `S → a B | ε` and `B → b`:

```python
grammar = {"S": [["a", "B"], ["ε"]], "B": [["b"]]}
# after the call:
predict == {"S": [{"a"}, {"$"}], "B": [{"b"}]}
```

The method only **reads** `g.grammar`, `g.first` and `g.follow` and must not
change them. The tests assume it uses only the object's own state, so two
`Grammar` objects never affect each other.

## 3. What "correct" means

The prediction set of a production `A → α` is the set of tokens that, when
seen as the next input, tell the parser to choose that production. It is built
like this:

1. Take FIRST(α), the FIRST of the whole production (spec 001 §3), without ε.
2. If α is nullable, also add FOLLOW(A). A production is nullable when it is
   `["ε"]` or when every symbol in it is a nullable non-terminal.

So:

- A production that starts with a terminal predicts just that terminal.
- A production `["ε"]` predicts exactly FOLLOW(A).
- A production that starts with a nullable non-terminal keeps scanning to the
  right, just like FIRST does. It only uses FOLLOW(A) of the **left side**,
  never FOLLOW of a symbol inside the production.

How the tests check results:

- They compare sets **exactly**. A missing token is an error, and so is an
  extra one.
- They check **every** production of **every** non-terminal.
- The keys of `predict` are exactly the non-terminals of the grammar.
- `predict[A]` has exactly as many entries as `grammar[A]` has productions,
  in the same order, and every entry is a set.
- **ε never appears** in any prediction set.
- Only terminals and `$` appear in prediction sets. A non-terminal name never
  does.
- `grammar`, `first` and `follow` are exactly the same before and after the
  call.

## 4. Rule-level tests with hand-written FIRST and FOLLOW (P cases)

Most tests do not call `compute_first_set` or `compute_follow_set`. They give
the correct FIRST and FOLLOW sets, written by hand, so a failure here can only
come from the prediction computation. Each test:

1. Builds a `Grammar` object and fills its `first` and `follow` with the
   hand-written sets.
2. Calls `compute_predict_set` once.
3. Compares the whole `predict` dictionary against the expected one, and checks
   the properties in §3.

Uppercase names are non-terminals, everything else is a terminal. The first
non-terminal listed is the start symbol. In the "Expected" column, the sets of
a non-terminal are listed in the order of its productions.

| ID  | Grammar | Given FIRST | Given FOLLOW | Expected prediction sets | What it checks |
|-----|---------|-------------|--------------|--------------------------|----------------|
| P1  | S → a | S = {a} | S = {$} | S: [{a}] | Base case: a single terminal production |
| P2  | S → a B \| b<br>B → c | S = {a, b}, B = {c} | S = {$}, B = {$} | S: [{a}, {b}]<br>B: [{c}] | Productions that start with a terminal predict only that terminal |
| P3  | S → A b<br>A → a \| ε | S = {a, b}, A = {a, ε} | S = {$}, A = {b} | S: [{a, b}]<br>A: [{a}, {b}] | An ε production predicts FOLLOW of its left side |
| P4  | S → a S \| ε | S = {a, ε} | S = {$} | S: [{a}, {$}] | The ε production of the start symbol predicts $ |
| P5  | S → A b<br>A → a | S = {a}, A = {a} | S = {$}, A = {b} | S: [{a}]<br>A: [{a}] | A non-nullable leading non-terminal hides the rest (b must not appear) |
| P6  | S → A B \| x A d<br>A → a \| ε<br>B → b | S = {a, b, x}, A = {a, ε}, B = {b} | S = {$}, A = {b, d}, B = {$} | S: [{a, b}, {x}]<br>A: [{a}, {b, d}]<br>B: [{b}] | After a nullable first symbol, the scan uses the rest of the production, not FOLLOW of that symbol (d must not appear in S's first set) |
| P7  | S → A B c<br>A → a \| ε<br>B → b \| ε | S = {a, b, c}, A = {a, ε}, B = {b, ε} | S = {$}, A = {b, c}, B = {c} | S: [{a, b, c}]<br>A: [{a}, {b, c}]<br>B: [{b}, {c}] | A long nullable prefix, ending in a terminal (no FOLLOW(S) added) |
| P8  | S → T z<br>T → A B<br>A → a \| ε<br>B → b \| ε | S = {a, b, z}, T = {a, b, ε}, A = {a, ε}, B = {b, ε} | S = {$}, T = {z}, A = {b, z}, B = {z} | S: [{a, b, z}]<br>T: [{a, b, z}]<br>A: [{a}, {b, z}]<br>B: [{b}, {z}] | A production made only of nullable non-terminals adds FOLLOW of its left side (z in T's set) |
| P9  | S → A x<br>A → B \| y<br>B → b \| ε | S = {b, y, x}, A = {b, y, ε}, B = {b, ε} | S = {$}, A = {x}, B = {x} | S: [{b, y, x}]<br>A: [{b, x}, {y}]<br>B: [{b}, {x}] | A production that is nullable only through another non-terminal (A → B) |
| P10 | S → E F<br>E → ε<br>F → f \| ε | S = {f, ε}, E = {ε}, F = {f, ε} | S = {$}, E = {f, $}, F = {$} | S: [{f, $}]<br>E: [{f, $}]<br>F: [{f}, {$}] | A nullable start symbol: $ appears in the set of a production that is not `["ε"]` |
| P11 | E → E + T \| T<br>T → id | E = {id}, T = {id} | E = {$, +}, T = {$, +} | E: [{id}, {id}]<br>T: [{id}] | Not LL(1), left recursion. The overlapping sets are still computed correctly |
| P12 | S → a b \| a c | S = {a} | S = {$} | S: [{a}, {a}] | Not LL(1), common prefix |
| P13 | S → A a<br>A → a \| ε | S = {a}, A = {a, ε} | S = {$}, A = {a} | S: [{a}]<br>A: [{a}, {a}] | Not LL(1): an ε production's FOLLOW overlaps a sibling's FIRST |
| P14 | S → a \| a | S = {a} | S = {$} | S: [{a}, {a}] | Two identical productions still get one entry each |
| P15 | Chunk → Block<br>Block → Stat Block \| ε<br>Stat → if Exp then Block end \| Name = Exp<br>Exp → Name \| Number | Chunk = {if, Name, ε}, Block = {if, Name, ε}, Stat = {if, Name}, Exp = {Name, Number} | Chunk = {$}, Block = {$, end}, Stat = {if, Name, $, end}, Exp = {then, if, Name, $, end} | Chunk: [{if, Name, $}]<br>Block: [{if, Name}, {$, end}]<br>Stat: [{if}, {Name}]<br>Exp: [{Name}, {Number}] | A small Lua-like grammar. Multi-character terminals (`if`, `end`, `Name`) are single symbols |
| P16 | S → a<br>U → u \| ε | S = {a}, U = {u, ε} | S = {$}, U = {} | S: [{a}]<br>U: [{u}, {}] | An unused non-terminal: its ε production predicts an empty set, and the entry is still there |
| P17 | S → c \| a \| b \| ε | S = {a, b, c, ε} | S = {$} | S: [{c}, {a}, {b}, {$}] | Entries follow the order of the productions, not alphabetical or any other order |
| P18 | S → a A<br>A → b \| ε | S = {a}, A = {b, ε} | S = {$}, A = {$} | S: [{a}]<br>A: [{b}, {$}] | A leading terminal ends the scan, even if the rest of the production is nullable ($ must not appear in S's set) |

## 5. Full-pipeline tests (E cases)

A smaller group runs the real pipeline: build a new `Grammar` object, call
`compute_first_set`, then `compute_follow_set`, then `compute_predict_set`,
and compare the whole `predict` dictionary. These tests check that the three
methods work together, the way the parser will use them.

**E1. The grammar currently in `main.py`.**
```
A → B C | ant A all
B → big C | bus A boss | ε
C → cat | cow
```
Expected: A: [{big, bus, cat, cow}, {ant}], B: [{big}, {bus}, {cat, cow}],
C: [{cat}, {cow}].
(A → B C gets FIRST(C) because B is nullable. B → ε gets FOLLOW(B) = {cat, cow}.)

**E2. Classic expression grammar.** A well-known textbook result.
```
E  → T E'
E' → + T E' | ε
T  → F T'
T' → * F T' | ε
F  → ( E ) | id
```
Expected: E: [{(, id}], E': [{+}, {$, )}], T: [{(, id}], T': [{*}, {+, $, )}],
F: [{(}, {id}]

**E3. The grammar that is commented out in `main.py`.**
```
S → A B C
A → a | ε
B → b | ε
C → c
```
Expected: S: [{a, b, c}], A: [{a}, {b, c}], B: [{b}, {c}], C: [{c}]

**E4. The Lua-like grammar from P15**, with FIRST and FOLLOW computed instead of
written by hand. Expected: the same prediction sets as P15.

If an E case fails while the matching P case and the FIRST and FOLLOW tests
(specs 001 and 002) pass, the problem is in how the methods connect, not in
the prediction rules themselves.

## 6. Properties checked across all grammars

**Initial state.** For every P and E grammar, a new `Grammar` object has one
empty list per non-terminal in `predict`.

**Getter.** `get_predict_set()` returns the object's own `predict` dictionary
(the same object, not a copy), both before and after `compute_predict_set`.

**Shape.** After every P and E test:

- the keys of `predict` are exactly the non-terminals;
- each `predict[A]` has one entry per production of A;
- every entry is a set.

**Contents.** After every P and E test:

- no prediction set contains ε;
- no prediction set contains a non-terminal name.

**Inputs unchanged.** `grammar`, `first` and `follow` are the same before and
after `compute_predict_set`. For E cases, the snapshot of `first` and `follow`
is taken after they are computed, so only the prediction call is checked.

**Output independent of inputs.** The prediction sets must be separate
objects from the FIRST and FOLLOW sets. After the call, adding a token to any
entry of `predict` must not change `first` or `follow`. This matters because
the parser (or a later step that builds the parse table) may modify
`predict`, and that must never corrupt the FIRST and FOLLOW sets it came from.

**Order independence.** The result must not depend on the order of the keys,
**except the first key**, which is the start symbol and always stays first.
Every P and E grammar is run with the other keys in several orders: every
permutation when the grammar has at most 4 non-terminals, otherwise as written
and reversed. The order of the **productions** inside each non-terminal is
never changed, because the output is aligned with it.

**Same result on fresh runs.** Two `Grammar` objects built from the same
inputs give equal prediction sets. What happens when `compute_predict_set` is
called a second time on the same object, whose `predict` is already filled,
is not defined (see §7).

**Isolation.** Every test builds its own `Grammar` object from a private copy
of the grammar. Running the full pipeline must not modify the dictionary
passed to the constructor, and computing the prediction sets on one object
must not change another object's `predict`. No test depends on another test
having run before it.

**Termination.** As in spec 002, every test has a time limit, so a call that
never returns fails instead of hanging the suite.

## 7. Out of scope (well-formed inputs only)

These inputs and questions are not tested. Their behavior is not defined yet:

- Whether the grammar is LL(1), i.e. whether the prediction sets of one
  non-terminal are disjoint (`check_LL1_condition`), and conflict reporting.
- Building the parse table from the prediction sets.
- Calling `compute_predict_set` on an object whose `predict` is not empty,
  for example a second time on the same object.
- An empty production `[]`.
- ε mixed into a longer production, such as `["a", "ε"]`.
- A non-terminal with no productions (`"A": []`).
- An empty grammar `{}`.
- A start symbol other than the first key.
- Incomplete or incorrect FIRST or FOLLOW sets passed as input.

## 8. Test organization

- File: `syntax/tests/test_predict_set.py`.
- Reuse the patterns from `conftest.py`: a helper that builds a `Grammar` on a
  private copy of the grammar, with FIRST and FOLLOW either copied from a
  hand-written preset (P cases) or computed (E cases), plus the existing
  `new_grammar` and `reorder` helpers.
- Use `pytest.mark.parametrize` for the P table (section 4), the E table
  (section 5) and the key orders (section 6).
- Failing tests get an xfail mark as in specs 001 and 002. The reason text
  describes only the symptom (for example "prediction set of A → ε is missing
  $"), never the cause or a fix.
- Run with `pytest syntax/tests`.
- If a function is added to or removed from the prediction computation, update
  this spec and its tests to match (see `syntax/AGENTS.md`).
