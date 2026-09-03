# A02 — MBIR Contract Evidence

## Verdict

```text
A02_MBIR_CONTRACT = DEMONSTRATED
```

## What was frozen

`docs/MBIR_CONTRACT.md` defines **MBIR_VERSION 0**, the language-neutral
shared semantic runtime contract:

- **Numeric model**: unsigned 8-bit modular arithmetic (mod 256), chosen to map
  cleanly to Malbolge's `% 256` output and the 3-trit cell domain.
- **VM state**: pc, stack, locals/frame, call_stack, input cursor, output
  stream, status.
- **18 opcodes**: HALT, PUSH_CONST, POP, DUP, LOAD_LOCAL, STORE_LOCAL, ADD,
  SUB, MUL, CMP_EQ, CMP_LT, CMP_GT, JUMP, JUMP_IF_FALSE, CALL, RETURN,
  OUT_BYTE, IN_BYTE.
- **Encoding**: `[opcode: 1 byte][operands]`; u8 operands (1 byte), u24 jump
  targets (3 bytes, little-endian).
- **Call-frame semantics**: CALL (addr, nargs) pops args, pushes frame;
  RETURN restores caller.
- **I/O behavior**: IN_BYTE pushes next input byte or 0xFF on EOF; OUT_BYTE
  emits `v & 0xFF`.
- **Invalid-bytecode behavior**: BAD_OPCODE, BAD_OPERAND (truncated),
  STACK_UNDERFLOW, BAD_TARGET (non-aligned jump), BAD_SLOT, no-frame RETURN.
- **Runtime identity**: `RUNTIME_SHA` constant, `MBIR_PROGRAM_SHA` variable
  (compile-once/test-many).
- **Frontend discipline**: frontend may not execute arithmetic / resolve input /
  precompute branches; must lower to MBIR.

## Implementation

- `mbir/mbir.py` — encoder, decoder, static validation, instruction-boundary
  detection, operand-width table.
- `mbir/tests/test_mbir.py` — conformance suite.

## Conformance result

```text
MBIR_VERSION = 0
PASS: 23   FAIL: 0   TOTAL: 23   (test_mbir.py, exit 0)
```

Covers:
- version + full opcode inventory,
- operand widths (u8/u24/0),
- 6 positive round-trip fixtures (arith, cmp+jump, locals+dup, call+return, io),
- jump-target boundary detection,
- negative structural cases: bad opcode 0xFF, unassigned 0x12, truncated
  PUSH_CONST / JUMP / CALL, u8/u24 range overflow, unknown opcode.

## Scope

A02 freezes the static binary contract. VM execution semantics (stack
underflow at runtime, invalid jump target at runtime, bad slot, no-frame
RETURN) are validated by the A03 reference VM conformance suite, which
implements and tests the full MBIR semantic model.

## Evidence kinds

- `MBIR_CONFORMANCE` — test_mbir.py.

## Next phase

```text
A03_MBIR_REFERENCE_CONFORMANCE = NOT_DEMONSTRATED
(refactor MalPyVM into mbir_ref.py implementing MBIR semantics + negative tests)
```