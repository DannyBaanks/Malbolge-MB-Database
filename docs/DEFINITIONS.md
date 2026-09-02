# Definitions

## Core Terms

### Malbolge (Original)
A brainfuck-family esoteric language created by Ben Olmstead in 2001. Memory: 59049 cells (3^10), each holding a 10-trit ternary value. Instructions are encoded as values 33-126 (printable ASCII). After execution, each instruction cell is encrypted via the `crazy` operation. Self-modifying by design.

### Malbolge Unshackled
A variant where the rotation width is extended from 10 to 19-20 trits, giving 3^19 or 3^20 addressable cells (~1 trillion). The `crazy` operation operates on wider words. This makes the memory space effectively unbounded for practical purposes, enabling Turing-complete computation. Requires a custom interpreter (typically `fast20.c` or `Unshackled-20.c`).

### Malbolge20
A variant formalized by Nagoya University with 20-trit words. Includes toolchain support (assembler, compiler from C subset). Different from Unshackled in specification details but shares the wider memory model.

### .mb File
A file containing Malbolge source code. The extension does not specify which variant — the file must declare which machine it targets. Never execute a `.mb` automatically on a different variant.

### MB (Multi Backend)
In this repository, "MB" refers to the concept of implementing multiple language runtimes as Malbolge programs. The "multi backend" is the collection of different Malbolge variants (Original, Unshackled, Malbolge20) that can serve as execution targets.

## Artifact Classification

### python.mb (target)
A Malbolge program that interprets Python. The Python source code is processed by lexer/parser/runtime implemented AS Malbolge code. The interpretation must occur inside the `.mb`, not on the host.

### python.mb (NOT this)
- A Python program that interprets Malbolge (wrong direction)
- A compiler that translates Python to Malbolge (wrong direction, though useful as tooling)
- A Python bytecode VM that runs on the host (not Malbolge-hosted)

## Status Codes

| Status | Meaning |
|--------|---------|
| `NOT_STARTED` | Track registered, no work begun |
| `RESEARCH` | Investigating feasibility, prior art, architecture |
| `DESIGNED` | Architecture and subset defined, implementation not started |
| `BOOTSTRAPPED` | Minimal infrastructure exists (runners, build tools) |
| `PARTIAL_RUNTIME` | Some operations execute correctly on Malbolge |
| `EXECUTABLE` | Complete program runs on Malbolge but limited subset |
| `LANGUAGE_SUBSET` | Recognizable Python subset works end-to-end |
| `INTERPRETER_DEMONSTRATED` | Full interpreter runs inside `.mb` |
| `VERIFIED` | Independent reproduction confirms claims |
| `BLOCKED` | Cannot proceed (documented blocker) |
| `NOT_DEMONSTRATED` | Insufficient evidence for any positive claim |
