# Python MB — Status

## Current State

**Status**: `RESEARCH`
**Highest Milestone**: None completed
**Variant**: Malbolge Unshackled (primary), Original (early milestones as proving ground)

## Milestones

| ID | Name | Status | Evidence |
|----|------|--------|----------|
| P0 | Arithmetic Kernel | NOT_STARTED | — |
| P1 | Stack VM | NOT_STARTED | — |
| P2 | MalPy Bytecode | NOT_STARTED | — |
| P3 | Variables + Control Flow | NOT_STARTED | — |
| P4 | Functions | NOT_STARTED | — |
| P5 | Recursion | NOT_STARTED | — |
| P6 | Python Lexer in Malbolge | NOT_STARTED | — |
| P7 | Parser in Malbolge | NOT_STARTED | — |
| P8 | python.mb Interpreter | NOT_STARTED | — |

## Blockers

1. No Malbolge Unshackled runner available in this repository yet (need fast20.c build)
2. No Malbolge assembler/toolchain for writing Malbolge source (need HeLL/LMAO or custom)
3. Original Malbolge too constrained for P2+ (59049 cells)
4. Python subset v0 not yet validated on Malbolge

## Decisions

- **Variant**: Unshackled primary (Original Malbolge too small for interpreter)
- **Frontend**: Host compiler allowed initially (P0-P5); self-hosted parser target (P6+)
- **Bytecode**: Custom "MalPy" bytecode, not CPython bytecode
- **Reference pattern**: MalbolgeLISP (VM-in-Malbolge with data cells for bytecode)

## Next Actions

1. Build/obtain fast20.c runner
2. Validate Original Malbolge interpreter for P0 (arithmetic)
3. Design MalPy bytecode format
4. Implement P0: arithmetic kernel on Original Malbolge
5. Implement P1: stack VM skeleton
