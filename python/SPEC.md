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

## Bytecode — MBIR (frozen)

The shared runtime contract is **MBIR_VERSION 0** (`docs/MBIR_CONTRACT.md`,
`mbir/mbir.py`). It is language-neutral and shared across all language tracks.

See:
- `docs/MBIR_CONTRACT.md` — full contract (opcodes, encoding, semantics)
- `mbir/mbir.py` — encoder/decoder + static validation
- `mbir/tests/test_mbir.py` — conformance tests (23/23 PASS)

For Python-specific lowering, the frontend maps the subset below onto MBIR
instructions (PUSH_CONST / LOAD_LOCAL / STORE_LOCAL / ADD / SUB / MUL /
CMP_* / JUMP / JUMP_IF_FALSE / CALL / RETURN / OUT_BYTE / IN_BYTE).

The old tentative "MalPy bytecode" opcode table in this file is superseded by
MBIR. Do not introduce a second, Python-only bytecode.

## Constraints

1. Must fit in Malbolge memory (59049 cells for Original, ~1T for Unshackled)
2. Bytecode stored in data cells (never executed directly)
3. VM dispatch loop written in Malbolge instructions
4. Arithmetic via Malbolge's `crazy` operation or lookup tables
