# AGENTS.md syntax

## Project

Implementation of a syntactical analyzer (or parser) for HL Lua 5.5 code. Using
a recursive top-down parser (RDSA)

## Context

- The previously implemented lexer must be used for this submission, as each
  test case's input will be Lua code that must be correctly tokenized by the
  lexical analyzer, and each token must then pass to the syntactical analyzer.
- As the approach is a recursive top-down parser, it is a requirement that the
  grammar is LL(1)

## Tech stack

- **Programming language:** Python
- **Dependencies:** Pytest

## Coding style

- Use consistent naming conventions
- Keep the code clean and readable
- Keep comments concise but descriptive, and only where needed.

## Instructions

- Do NOT touch or make any changes to the core implementation code. For this
  submission, that corresponds to the grammar, the computation of first, follow
  and prediction sets. However, the implementation of the parser itself is quite
  straighforward and tedious once the grammar and the sets are done, so you
  could help with that. Besides that, the agent's main task is to design and
  implement test cases for the spec at hand, and offering clarification.

- Keep the testing strategy up to date with the implementation code. That is,
  when a new function is added, it must be unit-tested. If it is removed, the
  tests associated with that function must be removed as well.
- Before performing any action, read the implementation code and be aware of
  changes and differences between it and the tests
