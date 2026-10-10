# Python MB Track

A Malbolge-hosted Python interpreter. The `.mb` file contains a lexer, parser, and runtime that processes Python source code inside Malbolge execution.

## Distinction

This is NOT:
- A Python program that runs Malbolge (wrong direction)
- A compiler that translates Python to Malbolge (useful tooling, but different goal)
- A Python bytecode VM on the host (not Malbolge-hosted)

This IS:
- A Malbolge program that interprets Python semantics
- The Malbolge code IS the interpreter
- Running `python.mb` with Python source produces results

## Target Architecture

```
Python source
      │
      ▼
Python frontend (in Malbolge)
      │
      ▼
MalPy bytecode (data cells, not executed)
      │
      ▼
Python VM (in Malbolge)
      │
      ▼
Result
```

## Primary Reference

MalbolgeLISP proves this pattern is possible: a Lisp interpreter written as Malbolge Unshackled source code, with bytecode stored in data cells.

## Prior Art

See `research/prior-art.md` for the complete survey.

Key finding: **No project implements a Python interpreter that runs ON Malbolge.** pyMalbolge compiles Python TO Malbolge20 (different direction, different variant).

## Status

P3 (`src/p3_compiler.py`) lowers assignment, `print`, modular arithmetic, comparisons, `if`/`else`/`elif`, and `while` to MBIR and runs them on the host reference VM. See `STATUS.md`. A Malbolge-hosted `python.mb` is not demonstrated.
