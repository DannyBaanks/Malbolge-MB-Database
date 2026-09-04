# A04C — HOST/CELL Boundary Contract

This document defines, in one place, every permission and prohibition that
governs the A04C experiment. If the rules here are violated, the claimed
breakthrough is not demonstrated.

## Host responsibilities (allowed)

The HOST is the Python caller that owns the experiment. Host is allowed to:

1. Read MBIR program bytes from disk or stdin.
2. Initialize the cellular universe (place live cells at chosen coordinates).
3. Call `substrate.step()` or `substrate.evolve()` to advance ticks.
4. Inspect the live set after ticks and read state information off it.
5. Enforce resource bounds (max ticks, max cells) without changing rules.
6. Compare the *produced cellular trace* against a separately-computed
   reference result AFTER execution, for the purpose of PASS/FAIL verdict.
7. Hash artifacts and write evidence.

## Host MUST NOT (prohibitions)

The host must NOT:

- Decode an MBIR opcode semantically. That means: the host must go out of its
  way to NEVER compute which opcode is active at tick t for the purpose of
  deciding what the cells should become.
- Execute ADD as a Python `+`.
- Decide a branch based on MBIR semantics (`JUMP_IF_FALSE`, `CALL`, etc.)
  computed in Python.
- Emulate a VM memory array.
- Compute the next program counter value.
- Mutate cells after a tick to reflect a precomputed expected VM state.
- Fabricate an output cell that meets the desired MBIR output by writing
  directly (the output must emerge from the CA rule dynamics).

## Canonical discipline

> If the cellular rule evolves deterministically from an initial state and a
> fixed rule table, and the observed output matches the reference result, the
> demonstration holds. If the output was produced by the host, the
> demonstration fails.

## Practical test for simultaneous failure

Somebody replaying the trace must be able (in principle) to verify:

```
input_bytes = MBIR_PROGRAM
cells_at_t0 = ENC(input_bytes)          # rule: ENC depends on MBIR program
trace = step(rules=FIXED_RULE, cells_at_t0)
output = DECODE(last trace state)
```

ENC may depend on the input bytes. DECODE may inspect the final state. But:
- the RULE must be FIXED for all test cases in the experiment,
- ENCODE may not dispatch per-opcode (it may lay out program bytes verbatim),
- DECODE may not redo the ADD for `"2+3=5"`.

This is the same data-flow that the A04 gate would apply if the substrate
were Malbolge.
