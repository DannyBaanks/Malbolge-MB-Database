# A03 — MBIR Reference VM Conformance Evidence

## Verdict

```text
A03_MBIR_REFERENCE_CONFORMANCE = DEMONSTRATED
```

## What was implemented

`mbir/mbir_ref.py` — `MBIRRefVM`, the authoritative REFERENCE implementation
of the full MBIR_VERSION 0 semantic model defined in `docs/MBIR_CONTRACT.md`
and the A02 contract. It is the oracle that the Malbolge-hosted runtime (A04)
must match, and it lets frontends validate lowering.

## Semantic coverage (matches the contract)

- **Numeric model**: unsigned 8-bit modular arithmetic (ADD/SUB/MUL wrap mod 256)
- **VM state**: pc, value stack, per-frame locals, call stack, input cursor,
  output stream, status
- **All 18 opcodes**: HALT, PUSH_CONST, POP, DUP, LOAD_LOCAL, STORE_LOCAL,
  ADD, SUB, MUL, CMP_EQ, CMP_LT, CMP_GT, JUMP, JUMP_IF_FALSE, CALL, RETURN,
  OUT_BYTE, IN_BYTE
- **Jump targeting**: JUMP/JUMP_IF_FALSE/CALL validate the target is an
  instruction boundary (else BAD_TARGET)
- **Call frames**: CALL(addr, nargs) pops args, pushes frame; RETURN restores
  caller (else NO_FRAME)
- **I/O**: IN_BYTE pushes next input byte or 0xFF on EOF; OUT_BYTE emits v & 0xFF
- **Deterministic traces**: identical (blob, input) -> identical
  (output, steps, status, trace)
- **Source-content hashing**: `source_hash()` SHA-256 of mbir_ref.py bytes

## Conformance result

```text
PASS: 28   FAIL: 0   TOTAL: 28   (test_mbir_ref.py, exit 0)
```

Positive fixtures:
- modular arithmetic (wrap: 200+100=44, 5-10=251, 16*3=48)
- comparisons (LT/EQ/GT)
- locals + DUP (9+9=18), POP
- branch true/false
- loop (outputs 0,1,2,3,4)
- call add(2,3)=5
- **recursion fib(6)=8** (validates frame integrity + multiple calls)
- I/O echo "Hi"

Determinism:
- identical output/steps/trace across runs; trace records (pc, op, stack, locals)

Negative cases (all correct MBIRError reason):
- STACK_UNDERFLOW (OUT empty, ADD with 1 value)
- BAD_OPCODE (0x99)
- BAD_TARGET (jump into instruction middle)
- BAD_SLOT (LOAD_LOCAL 5 with no locals)
- NO_FRAME (RETURN with empty call stack)
- BAD_OPERAND (truncated PUSH_CONST)
- MAX_STEPS

## Compatibility

The legacy `python/src/p1_vm.py` MalPyVM remains intact and its reference
harness still passes (21/21). For MBIR semantics the authoritative reference is
now `mbir/mbir_ref.py`; MalPyVM remains the Python-frontend reference model
(P1/P2). Both are REFERENCE_MODEL evidence (host_language = Python).

## Evidence kinds

- `REFERENCE_MODEL` — mbir_ref.py conformance.

## Artifact hashes (this record)

Source-content SHA-256 (implementation provenance):

```
89CD1E43C5CAB59E640E8B3689CD53F32A558CEEC3347B815F68E1194F50F90B  mbir/mbir_ref.py
B517A7A98DBD962C79D76E7B4A73C581031F726CF4FB58BE09EB5E0C360CD502  mbir/tests/test_mbir_ref.py
```

## Next phase

```text
A04_MBIR_ON_MALBOLGE = NOT_DEMONSTRATED
(an immutable Malbolge artifact executes multiple distinct MBIR programs as data)
```