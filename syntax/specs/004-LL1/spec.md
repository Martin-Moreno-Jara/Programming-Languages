# Spec 004 — Testing the LL(1) condition check

## 1. Purpose and scope

This spec describes how to test that `Grammar.check_LL1_condition` in
`syntax/grammar.py` correctly says whether a grammar is LL(1), given its
prediction sets.

- **In scope:** the method `Grammar.check_LL1_condition`.
- **Out of scope:** computing FIRST, FOLLOW and prediction sets (specs 001,
  002 and 003), reporting *where* a conflict is, fixing a grammar that is not
  LL(1) (left factoring, removing left recursion), building the parse table
  and the parser itself.

## 2. Interface under test

The grammar and prediction set formats are the same as in spec 003 §2:
`predict[A]` is a list with one set per production of A, in production order.

```python
g = Grammar(grammar)

# Either run the full pipeline...
g.compute_first_set()
g.compute_follow_set()
g.compute_predict_set()
# ...or write the prediction sets by hand into g.predict

g.check_LL1_condition()   # returns True or False
```

The method only **reads** `g.predict`. It returns `True` when the grammar is
LL(1) and `False` when it is not. It does not say which non-terminal or token
caused the conflict.

## 3. What "correct" means

A grammar is **LL(1)** when the parser can always choose a production by
looking at the next token only. In terms of prediction sets:

> For **every** non-terminal, no two of its prediction sets share a token.

So:

- Every **pair** of prediction sets of one non-terminal is compared, not only
  neighbours. With three productions, set 1 is compared with set 2 and with set
  3, and set 2 with set 3.
- `$` counts as a token like any other. Two productions that both predict `$`
  are a conflict.
- The same token in prediction sets of **different** non-terminals is fine.
  `S: [{a}]` and `A: [{a}, {b}]` is LL(1).
- An empty prediction set contains no token, so it never conflicts with
  anything, not even with another empty set.
- A token is the whole string. `=` and `==` are different tokens, and so are
  `end` and `End`.
- One conflict anywhere is enough for `False`, whichever non-terminal it is
  in.

How the tests check results:

- The result must be exactly `True` or `False`, a real `bool`, not just
  something truthy or falsy such as `1`, `None` or a set.
- The check must not change anything: `grammar`, `first`, `follow` and
  `predict` are the same before and after the call.

## 4. Tests with hand-written prediction sets

Most tests don't run the pipeline. They write the prediction sets directly into
`g.predict`, so a failure here can only come from the LL(1) check. The grammar
given to `Grammar(...)` has the same non-terminals and the same number of
productions as the sets. Its productions are otherwise not used. Each test:

1. Builds a `Grammar` object and fills `g.predict` with the given sets.
2. Calls `check_LL1_condition` once.
3. Compares the result with the expected one, and checks the properties in §3.

Uppercase names are non-terminals. Everything else is a token.

### 4.1 L cases: LL(1), expected `True`

| ID | Prediction sets | What it checks |
|----|-----------------|----------------|
| L1 | S: [{a}] | Base case: a single production can't conflict |
| L2 | S: [{a}, {b}] | Two disjoint productions |
| L3 | S: [{c}, {a}, {b}, {$}] | Many disjoint productions, one of them predicting `$` |
| L4 | S: [{a, b, c}, {d, e}] | Disjoint sets with several tokens each |
| L5 | S: [{a}]<br>A: [{a}, {b}] | The same token in different non-terminals is not a conflict |
| L6 | S: [{a}]<br>U: [{u}, {}] | An empty prediction set (an unused non-terminal's ε production, as in spec 003 P16) |
| L7 | S: [{a}]<br>U: [{}, {}] | Two empty sets never overlap |
| L8 | S: [{=}, {==}]<br>T: [{end}, {End}] | Tokens are compared as whole strings, and case matters |
| L9 | Chunk: [{if, Name, $}]<br>Block: [{if, Name}, {$, end}]<br>Stat: [{if}, {Name}]<br>Exp: [{Name}, {Number}] | A small Lua-like grammar (spec 003 P15). Every non-terminal is checked and passes |

### 4.2 N cases: not LL(1), expected `False`

| ID  | Prediction sets | What it checks |
|-----|-----------------|----------------|
| N1  | S: [{a}, {a}] | Two identical sets |
| N2  | S: [{a, b}, {b, c}] | Partial overlap on a single token |
| N3  | S: [{a}, {a, b}] | One set contained in the other |
| N4  | A: [{$}, {a, $}] | The only shared token is `$` |
| N5  | S: [{a}, {b}, {a}] | Conflict between the 1st and 3rd sets, with a clean set in between |
| N6  | S: [{a}, {b}, {b, c}] | Conflict only between the 2nd and 3rd sets |
| N7  | S: [{x}]<br>A: [{a}, {b}]<br>B: [{c}, {c}] | The conflict is only in the **last** non-terminal, so the check must look at all of them |
| N8  | S: [{x}, {x}]<br>A: [{a}, {b}] | The conflict is only in the **first** non-terminal |
| N9  | S: [{a}, {a}]<br>A: [{b}, {b}] | Conflicts in several non-terminals |
| N10 | U: [{}, {a}, {a}] | An empty set doesn't hide a real conflict between the other two |

## 5. Full-pipeline tests (E cases)

A smaller group runs the real pipeline: build a `Grammar`, call
`compute_first_set`, `compute_follow_set` and `compute_predict_set`, then
`check_LL1_condition`. These tests check the method the way the parser will use
it, on real grammars.

| ID | Grammar | Expected | Why |
|----|---------|----------|-----|
| E1 | E → T E'<br>E' → + T E' \| ε<br>T → F T'<br>T' → * F T' \| ε<br>F → ( E ) \| id | True | Classic textbook LL(1) expression grammar |
| E2 | Chunk → Block<br>Block → Stat Block \| ε<br>Stat → if Exp then Block end \| Name = Exp<br>Exp → Name \| Number | True | The Lua-like grammar of L9 / spec 003 E4, with multi-character tokens |
| E3 | A → B C \| ant A all<br>B → big C \| bus A boss \| ε<br>C → cat \| cow | True | The grammar currently in `main.py` |
| E4 | S → A B C<br>A → a \| ε<br>B → b \| ε<br>C → c | True | Nullable productions whose FOLLOW sets don't collide |
| E5 | E → E + T \| T<br>T → id | False | Left recursion: both productions of E predict {id} |
| E6 | S → a b \| a c | False | Common prefix: both productions predict {a} |
| E7 | S → A a<br>A → a \| ε | False | The ε production predicts FOLLOW(A) = {a}, which collides with A → a |
| E8 | S → i E t S S' \| a<br>S' → e S \| ε<br>E → b | False | The "dangling else": S' → ε predicts {e, $}, which collides with S' → e S |

If an E case fails but the matching hand-written case passes, and specs 001
to 003 pass too, the problem is in how the steps connect, not in the LL(1)
check itself.

## 6. Properties checked across all cases

**Real bool.** For every L, N and E case, the result `is True` or `is False`.

**Nothing is changed.** `grammar`, `first`, `follow` and `predict` are the
same before and after the check.

**Repeatable.** Calling the check twice on the same object gives the same
answer both times.

**Order of non-terminals doesn't matter.** Reordering the keys of `predict`
(for L and N cases) or of the grammar (for E cases, with the start symbol kept
first) gives the same answer.

**Order of productions doesn't matter.** Whether two sets overlap doesn't
depend on where they sit in the list. Reordering the sets inside each
`predict[A]` (for L and N cases) or the productions of each non-terminal (for
E cases) gives the same answer. This catches a check that only compares
neighbouring sets: in N5, swapping the sets moves the conflict to a different
pair.

**Matches the definition.** For every case, the answer equals a simple
reference written in the test, which compares every pair of sets of each
non-terminal one by one (§3). This second, independent way of computing the
answer guards against a mistake in the hand-written expected values.

**Isolation.** Every test builds its own `Grammar` object from private copies.
Checking one object doesn't change another, and no test depends on another
test having run first.

**Termination.** As in specs 002 and 003, every test has a time limit, so a
call that never returns fails instead of hanging the suite.

## 7. Out of scope (behavior not defined)

These inputs and questions are not tested:

- Calling the check before `compute_predict_set`, when `predict` still holds
  only empty lists.
- An empty grammar `{}`.
- A `predict` that was filled twice, for example by calling
  `compute_predict_set` twice on the same object (spec 003 §7).
- A malformed `predict`: missing or extra non-terminals, the wrong number of
  sets for a non-terminal, or entries that are not sets.
- Reporting which non-terminal or which tokens are in conflict.
- Grammar shapes that are out of scope in specs 001 to 003 (empty
  productions `[]`, ε inside a longer production, a non-terminal with no
  productions, a start symbol other than the first key).

## 8. Test organization

- File: `syntax/tests/test_ll1_condition.py`.
- Reuse the helpers in `conftest.py`: `new_grammar` for the hand-written cases,
  `predict_grammar` for the E cases, and `reorder` for the order tests.
- Use `pytest.mark.parametrize` for the L and N tables (section 4), the E table
  (section 5) and the orders (section 6).
- Failing tests get an xfail mark as in specs 001 to 003. The reason describes
  only the symptom (for example "N5 reported as LL(1)"), never the cause or a
  fix.
- Run with `pytest tests` from `syntax/`.
- If `check_LL1_condition` changes (renamed, new signature, or it starts
  reporting conflicts), update this spec and its tests to match (see
  `syntax/AGENTS.md`).
