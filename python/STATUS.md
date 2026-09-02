# Python MB — Status

## Current State

**Status**: `PARTIAL_RUNTIME`
**Highest Milestone**: P2 (Python AST to MalPy bytecode, DEMONSTRATED)
**Variant**: Malbolge Unshackled (target), Original (early milestones)

## Milestones

| ID | Name | Status | Evidence |
|----|------|--------|----------|
| P0 | Arithmetic Kernel | IN_PROGRESS | Pipeline demonstrated, general addition infeasible in pure Malbolge |
| P1 | Stack VM | DEMONSTRATED | Same VM, 5 bytecodes, 5 correct results |
| P2 | MalPy Bytecode | DEMONSTRATED | Python AST -> bytecode -> VM -> correct output |
| P3 | Variables + Control Flow | NOT_STARTED | — |
| P4 | Functions | NOT_STARTED | — |
| P5 | Recursion | NOT_STARTED | — |
| P6 | Python Lexer in Malbolge | NOT_STARTED | — |
| P7 | Parser in Malbolge | NOT_STARTED | — |
| P8 | python.mb Interpreter | NOT_STARTED | — |

## Key Findings

### P0 Constraint
Malbolge has no instruction to load arbitrary constants into the accumulator. The only way to get a value into A is via `in` (stdin) or by reading from memory (which requires knowing the address). This makes general-purpose addition in pure Malbolge infeasible with the standard instruction set.

**What P0 demonstrates**: A working Python->Malbolge compilation pipeline, the crazy operation as an arithmetic primitive, that Malbolge programs can be systematically generated.

**What P0 does NOT demonstrate**: General-purpose addition in pure Malbolge, a runtime addition routine that accepts arbitrary operands.

### P1/P2 Success
The MalPy VM is a working stack machine with PUSH/ADD/OUT/HALT opcodes. The Python compiler uses `ast.parse` (no eval/exec) to compile `print(<int> + <int>)` to MalPy bytecode. Same VM, different bytecodes, different correct results. This proves data-driven execution.

## Blockers for P3+

1. Need Malbolge assembler (HeLL/LMAO) for writing Malbolge source
2. Need Unshackled runner (bolge19) validated with MalPy programs
3. Original Malbolge too constrained for P3+ (59049 cells)
4. Bytecode format needs extension for variables and control flow

## Runners

| Runner | Variant | Status | SHA256 |
|--------|---------|--------|--------|
| bolge19 | Unshackled (3^19) | BUILT | `58D0B5E8...` |
| malbolge-engine | Original (3^10) | COPIED | `9A7AD87E...` |

## Toolchain

- **Selected**: LMAO (HeLL -> Original Malbolge)
- **Variant boundary**: LMAO targets Original only. For Unshackled, need LMFAO or custom.
- **Alternative**: Python-based code generation (current approach for P0-P2)

## Evidence

- `evidence/P0/` — crazy operation verification, Hello World trace, compiler output
- `evidence/P1/` — VM execution evidence (5 fixtures)
- `evidence/P2/` — Python compiler evidence (6 sources)
- `tests/test_harness.py` — 18/18 passing
