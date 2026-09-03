# Python MB — Status

## Current State

**Status**: `REFERENCE_FRONTEND`
**Highest Milestone**: P2 (Python AST to MalPy bytecode — FRONTEND_DEMONSTRATED)
**Primary Target**: Unshackled (design choice, not a demonstrated bound)
**Classic Path**: optional research track
**Malbolge-hosted runtime**: `NOT_DEMONSTRATED` (until A04)

## Milestones

| ID | Name | Status | Evidence |
|----|------|--------|----------|
| P0 | Arithmetic Kernel | NOT_DEMONSTRATED | No verified Malbolge addition artifact (program_source=None) |
| P1 | Stack VM (reference) | REFERENCE_DEMONSTRATED | Python reference VM, 5 bytecodes, 5 correct results |
| P2 | MalPy Bytecode frontend | FRONTEND_DEMONSTRATED | Python AST -> bytecode -> REFERENCE VM -> correct output |
| P3 | Variables + Control Flow | NOT_STARTED | — |
| P4 | Functions | NOT_STARTED | — |
| P5 | Recursion | NOT_STARTED | — |
| P6 | Python Lexer in Malbolge | NOT_STARTED | — |
| P7 | Parser in Malbolge | NOT_STARTED | — |
| P8 | python.mb Interpreter | NOT_STARTED | — |

## Honest Status Summary

```text
PYTHON_REFERENCE_VM                = DEMONSTRATED (Python host)
PYTHON_AST_TO_MALPY_BYTECODE       = DEMONSTRATED (restricted subset)
MALBOLGE_HOSTED_MALPY_VM           = NOT_DEMONSTRATED
PYTHON_MB_INTERPRETER              = NOT_DEMONSTRATED
GENERAL_RUNTIME_ADDITION_IN_MALBOLGE = NOT_DEMONSTRATED (current impl)
```

The P1 VM is a valid **reference VM / semantic oracle**. The P2 compiler is a
valid **frontend**. Neither demonstrates the VM running inside Malbolge. Do not
discard them; they are the oracle for the real runtime port (A04).

## Blockers for P3+

1. A Malbolge-hosted MBIR VM must execute (A04) before any Python completion claim
2. The MBIR contract is frozen (A02, MBIR_VERSION 0); the A03 reference VM must
   implement and test its full semantic model
3. Classic Malbolge (3^10) is a design constraint for this track; Unshackled is the primary target by choice, not proven necessity
4. Frontend needs to lower the Python subset to MBIR (not a second bytecode)

## Shared MBIR

The frozen language-neutral contract is `docs/MBIR_CONTRACT.md` (MBIR_VERSION 0).
Encoder/decoder: `mbir/mbir.py`. Conformance: `mbir/tests/test_mbir.py` (23/23).

## Runners

| Runner | Variant | Status | SHA256 |
|--------|---------|--------|--------|
| bolge19 | Unshackled (3^19) | BUILT (manifest claim; doctor pending A01) | `58D0B5E8...` |
| malbolge-engine | Original (3^10) | COPIED (manifest claim; doctor pending A01) | `9A7AD87E...` |

## Toolchain

- **Selected**: LMAO (HeLL -> Original Malbolge) — for early work
- **Variant boundary**: LMAO targets Original only. For Unshackled, need LMFAO or custom.
- **Alternative**: Python-based code generation (current approach for P0-P2 reference/frontend)

## Evidence

- `evidence/P0/` — crazy operation reference, Hello World trace, prototype (NOT_DEMONSTRATED for Malbolge arithmetic)
- `evidence/P1/` — REFERENCE_MODEL VM execution (5 fixtures + underflow negatives)
- `evidence/P2/` — FRONTEND Python compiler (6 sources)
- `tests/test_harness.py` — 21/21 passing reference tests

## Evidence kinds used

- P1: `REFERENCE_MODEL` (host_language=Python)
- P2: `FRONTEND` (host_language=Python)
- No `MALBOLGE_RUNTIME` evidence exists yet — none is claimed.