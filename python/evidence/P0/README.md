# Python MB — P0 Evidence

## Test 1: Crazy Operation Verification

The crazy operation is Malbolge's native arithmetic primitive. It's a ternary lookup table:

```python
CRAZY_TBL = [
    [1, 0, 0],
    [1, 0, 2],
    [2, 2, 1]
]
crazy(a, b) = sum of CRAZY_TBL[b%3][a%3] * 3^i for each trit
```

**Result**: `DEMONSTRATED` — produces deterministic results for all tested inputs.

## Test 2: Hello World Baseline

The canonical Hello World program demonstrates:
- 14 `crazy` operations (arithmetic computation)
- 10 `rot` operations (rotation/movement)
- 13 `out` operations (output)
- 6 `nop` operations (self-modification padding)
- 1 `jmp` operation (control flow)
- 1 `end` operation (halt)

**Result**: `DEMONSTRATED` — 48 steps, output "Hello, world.", status HALTED.

## Test 3: Determinism

3 identical runs produce identical output and step count.

**Result**: `DEMONSTRATED`

## Key Insight

The crazy operation IS the arithmetic of Malbolge. Every character in "Hello, world." is computed through `crazy(a, mem[d])` and rotation before output. This proves Malbolge executes real computation, not just constant printing.

## What is NOT Demonstrated

- General-purpose addition (no native add instruction)
- Arbitrary arithmetic on runtime values
- These require P1 (Stack VM) where we build addition from primitives

## Evidence Files

- `run_20260902.json` — full evidence record
- `run_hello_world_trace.json` — step-by-step trace of first 60 steps
