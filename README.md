# Programming Languages (2026-II)

Coursework for **Programming Languages** at Universidad Nacional de Colombia, semester 2026-II.

## About the course

The course studies how programming languages are defined and processed: how source code is split into tokens (lexical analysis), how those tokens form valid structures (syntactic analysis), and what those structures mean (semantic analysis). The practices build these stages for a real language, **Lua 5.5**. They cover sections 2 (basic concepts) and 3 (the language) of the Lua reference manual, leaving out metatables, garbage collection and coroutines.

The practices are submitted to an automatic grading platform (UNcode). Each program reads source code from standard input and writes its result to standard output in the exact format the assignment specifies. The allowed languages are Python 3.9, C/C++ and Java.

## Practices

| # | Practice | Folder | Description |
|---|---|---|---|
| 1 | Lexical analyzer | [`lexer/`](lexer/) | Turns Lua source code into a list of tokens |

### 1. Lexical analyzer

A Python lexer for Lua. It reads a program from stdin and prints one token per line: keywords, identifiers, numbers, strings, operators and symbols, each with its line and column. Whitespace and comments (single-line and block) are skipped, and the lexer stops at the first lexical error. Each token is the longest valid match, numbers include scientific notation and hexadecimals, and some built-in functions (`print`, `error`, `pcall`…) are treated as keywords, as the course requires.

```bash
cd lexer
python main.py < program.lua
python -m pytest test-strategy -q   # run the test suite
```

The [lexer README](lexer/README.md) covers its architecture, the decisions behind the less obvious rules, and the test strategy.
