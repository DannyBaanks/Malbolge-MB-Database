# Python MB — P1 Evidence

## Status: NOT_STARTED

P1 (Stack VM) design is documented in `python/SPEC.md`.

## Planned Opcode Set

| Opcode | Name | Effect |
|--------|------|--------|
| 0 | HALT | Stop execution |
| 1 | PUSH_CONST | Push constant to stack |
| 2 | LOAD_VAR | Push variable value to stack |
| 3 | STORE_VAR | Pop stack, store in variable |
| 4 | ADD | Pop two, push sum |
| 5 | SUB | Pop two, push difference |
| 6 | MUL | Pop two, push product |
| 7 | PRINT | Pop one, output value |
| 8 | JUMP | Unconditional jump |
| 9 | JUMP_IF | Conditional jump |
| 10 | CALL | Call function |
| 11 | RETURN | Return from function |
| 12 | CMP_GT | Compare greater than |

## Blocking Issues

1. No Malbolge assembler available for writing Malbolge source
2. Need HeLL/LMAO toolchain or custom assembler
3. Original Malbolge (59049 cells) may be too small for stack VM
4. Unshackled runner (fast20.c) not yet built in this repository
