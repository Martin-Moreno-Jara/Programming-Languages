# Programming Languages (2026-II)

Coursework for **Programming Languages** at Universidad Nacional de Colombia, semester 2026-II.

## About the course

The course studies how programming languages are defined and processed: how source code is split into tokens (lexical analysis), how those tokens form valid structures (syntactic analysis), and what those structures mean (semantic analysis). The practices build these stages for a real language, **Lua 5.5**. They cover sections 2 (basic concepts) and 3 (the language) of the Lua reference manual, leaving out metatables, garbage collection and coroutines.

The practices are submitted to an automatic grading platform (UNcode). Each program reads source code from standard input and writes its result to standard output in the exact format the assignment specifies. The allowed languages are Python 3.9, C/C++ and Java.

## Practices

| # | Practice | Folder | Description |
|---|---|---|---|
| 1 | Lexical analyzer | [`lexer/`](lexer/) | Turns Lua source code into a list of tokens |
| 2 | Syntactic analyzer | [`syntax/`](syntax/) | Checks that the tokens form a valid Lua program |

### 1. Lexical analyzer

A Python lexer for Lua. It reads a program from stdin and prints one token per line: keywords, identifiers, numbers, strings, operators and symbols, each with its line and column. Whitespace and comments (single-line and block) are skipped, and the lexer stops at the first lexical error. Each token is the longest valid match, numbers include scientific notation and hexadecimals, and some built-in functions (`print`, `error`, `pcall`…) are treated as keywords, as the course requires.

```bash
cd lexer
python main.py < program.lua
python -m pytest test-strategy -q   # run the test suite
```

The [lexer README](lexer/README.md) covers its architecture, the decisions behind the less obvious rules, and the test strategy.

### 2. Syntactic analyzer

A recursive-descent LL(1) parser for Lua, built on the lexer of practice 1. It reads a program from stdin and prints a single line: a success message, or the first syntax error with its position, the token found and the sorted list of tokens expected there. The grammar lives in `main.py`. From it, the parser computes the FIRST, FOLLOW and prediction sets, checks that the grammar is LL(1), and generates the parser code (`syntax/ASDR.py`) on every run. Where the grader's reference parser differs from the Lua manual (for example, comparisons are non-associative and call arguments only use parentheses), the grammar follows the grader, as found through submissions. It passes all 40 platform tests.

```bash
python main.py < program.lua                # from the project root
python -m pytest syntax/tests -q            # run the test suite
```

The [syntactic analyzer README](syntax/README.md) covers the pipeline, the expression grammar, what the grader was found to expect, the submission history and the test strategy.
