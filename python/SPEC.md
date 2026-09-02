# Python MB — Specification

## Target Subset (Incremental)

### Subset v0 — Minimal Expressions

```python
print(2 + 3)
```

Operations: integer addition of two literals.

### Subset v1 — Variables

```python
x = 5
print(x + 2)
```

Operations: variable assignment, variable access, addition.

### Subset v2 — Comparison

```python
if 5 > 3:
    print(7)
```

Operations: comparison, conditional branching.

### Subset v3 — Functions

```python
def add(a, b):
    return a + b

print(add(2, 3))
```

Operations: function definition, call, arguments, return.

### Subset v4 — Recursion

```python
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(6))
```

Operations: recursive calls, multiple returns.

## MalPy Bytecode (Design Phase)

Custom bytecode designed for Malbolge execution. Not CPython bytecode.

### Opcode Set (Tentative)

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

### Bytecode Format

```
[opcode: 1 byte] [operand: variable width]
```

Stored in Malbolge data cells (not executed, so not encrypted by `crazy`).

## Constraints

1. Must fit in Malbolge memory (59049 cells for Original, ~1T for Unshackled)
2. Bytecode stored in data cells (never executed directly)
3. VM dispatch loop written in Malbolge instructions
4. Arithmetic via Malbolge's `crazy` operation or lookup tables
