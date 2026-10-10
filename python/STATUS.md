# Python MB — Status

## Current State

**Status**: `REFERENCE_FRONTEND`
**Highest Milestone**: P3 (Python subset → MBIR_VERSION 0 — FRONTEND_DEMONSTRATED on the host reference VM)
**Primary Target**: Unshackled
**Classic Path**: MBIR interpreter in progress via LMAO/HeLL
**Malbolge-hosted runtime**: `PARTIAL_DEMONSTRATED` (A04/A05/A05b multi-cycle fetch loop & 2-slot LIFO stack demonstrated — see vm_malbolge/A05_STATUS.md)

## Session log

Session of 2026-10-10:

- P3 frontend `python/src/p3_compiler.py` lowers assignment, `print`, modular `+` `-` `*`, one comparison, `if`/`else`/`elif`, and `while` to MBIR_VERSION 0.
- 15/15 sources HALT on `mbir/mbir_ref.py` with the expected raw bytes. Recorded in `python/evidence/P3/run_p3_compiler.json`.
- The compiler does not constant-fold: both `if` arms stay in the blob, and the `while` case has one `OUT_BYTE`.
- Malbolge-hosted execution of this frontend remains NOT_DEMONSTRATED. Functions and `python.mb` were not started.

Session of 2026-10-07:

- Completed Milestone A04 acceptance gate:
  - Implemented generator `vm_malbolge/tools/mbir_a04_gate_gen.py` and probe `vm_malbolge/src/mbir_a04_gate.hell`.
  - Reconciled dispatch reset flag sequencing, symmetric `MOVED` restoration, and unconditional carry reset.
  - Verified 7/7 vectors with 100% bit-exact output and exact step counts across Python Classic oracle, native Malbolge runner, and `mbir-zig`.
  - Recorded evidence in `vm_malbolge/evidence/mbir_a04_gate_smoke.json` and `vm_malbolge/evidence/mbir_zig_oracle_a04_gate.json`.
- Completed Milestone A05 re-entrant multi-cycle fetch loop:
  - Discovered and proved Universal 3-Crazy Reset Theorem (`crz(C0, crz(C2, crz(C1, X))) == C1` for all 59,049 words).
  - Streamlined data cell architecture (saved >12,000 bytes and ~20,000 init steps).
  - Verified 8/8 vectors with arbitrary sequential output ('AB', 'ABC', 'hello') in `vm_malbolge/evidence/mbir_a05_multicycle_smoke.json`.
- Completed Milestone A05b 2-slot LIFO stack machine:
  - Dynamic stack depth state machine (`SLOT0_FLAG`, `SLOT1_FLAG`).
  - Isolated slot storage cells (`stack_top`, `stack_top_1`) and scratch cells.
  - Verified 7/7 vectors including `01 41 01 42 10 10 00` -> `42 41` ("BA" LIFO order) bit-exact across Zig, Python Oracle, and native C runner.
  - Recorded evidence in `vm_malbolge/evidence/mbir_a05_lifo_smoke.json` and `vm_malbolge/evidence/mbir_zig_oracle_a05_lifo.json`.

Session of 2026-09-02 evening / 2026-09-03 (extends carries forward A00–A04):

- Reviewed Cobalt/CoEvo (cellular) ecosystem as a possible alternative
  implementation site for A04-specific concept execution.
- Created `vm_malbolge/cellular/` (`srv/interpreter coupling`):
  - Verified *byte-transport* (A04 case) under fixed 2-cell signature rule on the
    substrate (real engine infrastructure).
  - Verified *token advance* under the same rule.
  - Verified composition (both planes coexist).
  - Verified cargos hold under rule scrutiny.
  - Held-out values reproducible.
  Determinism / replay proven.
  - One observable local gate relation: data flow only when controller token present.
- Verified HeLL / LMAO + Malbolge execution pipeline: build of assembled program runs on
  runable Classic runner with exact byte echo.
- Updated audit status, committed mob `3785eca` + `b44cc77` + `f464c2d`.

## Remaining

The next operational milestone: Arithmetic Kernel (Milestone P0 / `ADD` 0x02) popping
operands from `stack_top_1` and `stack_top` and pushing the ternary digital-root sum,
followed by in-memory bytecode loader. See `vm_malbolge/A05_STATUS.md`.

## Evidence-Backed Progress

| Claim | State | Notes |
|-------|-------|-------|
| Malbolge rendering toolchain (LMAO) | WORKING | `third_party/lmao` built, smoke-tested on real runner |
| Byte-level storage/recovery primitive | WORKING | `vm_malbolge/src/min3_echo1.hell` verified on classic runner (`runners/malbolge-original/malbolge.exe`) |
| MBIR one-deep stack fetch loop (A04) | DEMONSTRATED | `vm_malbolge/src/mbir_a04_gate.hell` + `vm_malbolge/evidence/mbir_a04_gate_smoke.json` (7/7 PASS, bit-exact on oracle, runner, and zig) |
| MBIR re-entrant multi-cycle fetch loop (A05) | DEMONSTRATED | `vm_malbolge/src/mbir_a05_multicycle.hell` + `vm_malbolge/evidence/mbir_a05_multicycle_smoke.json` (8/8 PASS, bit-exact sequential output 'AB', 'ABC', 'hello', exact 6,046 step scaling) |
| MBIR 2-slot LIFO stack machine (A05b) | DEMONSTRATED | `vm_malbolge/src/mbir_a05_lifo.hell` + `vm_malbolge/evidence/mbir_a05_lifo_smoke.json` (7/7 PASS, bit-exact 'BA' LIFO inversion on oracle, runner, and zig) |
| MBIR interpreter (arithmetic, control flow, in-memory loader) | NOT_DEMONSTRATED | P0 ADD arithmetic kernel and loader needed |

## Next Runtime Steps

1. Encode MULTI-byte stdin loader (read program bytes into a data array)
2. Implement dispatch table and instruction handlers
3. Demonstrate the killer corpus on the declared Malbolge runner

## Milestones

| ID | Name | Status | Evidence |
|----|------|--------|----------|
| P0 | Arithmetic Kernel | NOT_DEMONSTRATED | No verified Malbolge addition artifact (program_source=None) |
| P1 | Stack VM (reference) | REFERENCE_DEMONSTRATED | Python reference VM, 5 bytecodes, 5 correct results |
| P2 | MalPy Bytecode frontend | FRONTEND_DEMONSTRATED | Python AST -> bytecode -> REFERENCE VM -> correct output |
| P3 | Variables + Control Flow | FRONTEND_DEMONSTRATED | `python/src/p3_compiler.py` → MBIR reference VM. 15 sources in `python/evidence/P3/run_p3_compiler.json`. Host only. |
| P4 | Functions | NOT_STARTED | — |
| P5 | Recursion | NOT_STARTED | — |
| P6 | Python Lexer in Malbolge | NOT_STARTED | — |
| P7 | Parser in Malbolge | NOT_STARTED | — |
| P8 | python.mb Interpreter | NOT_STARTED | — |

## Honest Status Summary

```text
PYTHON_REFERENCE_VM                = DEMONSTRATED (Python host)
PYTHON_AST_TO_MALPY_BYTECODE       = DEMONSTRATED (restricted subset, P2)
PYTHON_SUBSET_TO_MBIR              = DEMONSTRATED (P3, host MBIR reference VM)
MALBOLGE_HOSTED_MALPY_VM           = NOT_DEMONSTRATED
PYTHON_MB_INTERPRETER              = NOT_DEMONSTRATED
GENERAL_RUNTIME_ADDITION_IN_MALBOLGE = NOT_DEMONSTRATED (current impl)
```

The P1 VM is a valid **reference VM / semantic oracle**. The P2 compiler is a
valid **frontend** onto the old MalPy opcodes. The P3 compiler is a valid
**frontend** onto MBIR_VERSION 0. None of them demonstrates the VM running
inside Malbolge.

## Blockers for a Python completion claim

1. A Malbolge-hosted MBIR VM must execute this frontend's programs before any
   `python.mb` completion claim. P3 runs on `mbir/mbir_ref.py` only.
2. The MBIR contract is frozen (A02, MBIR_VERSION 0). P3 encodes with
   `mbir/mbir.py` and does not add a second bytecode.
3. Classic Malbolge (3^10) is a design constraint for this track; Unshackled is the primary target by choice, not proven necessity
4. P4 functions, P5 recursion, and P6–P8 (lexer, parser, `python.mb`) are not started.

## Shared MBIR

The frozen language-neutral contract is `docs/MBIR_CONTRACT.md` (MBIR_VERSION 0).
Encoder/decoder: `mbir/mbir.py` (A02). Reference VM: `mbir/mbir_ref.py` (A03),
implementing the full semantic model — the oracle the Malbolge-hosted runtime
(A04) must match. Conformance: `mbir/tests/test_mbir.py` (23/23) +
`mbir/tests/test_mbir_ref.py` (28/28).

A03_MBIR_REFERENCE_CONFORMANCE = DEMONSTRATED. A04_MBIR_ON_MALBOLGE =
NOT_DEMONSTRATED.

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
- `evidence/P2/` — FRONTEND Python compiler (6 sources, MalPy opcodes)
- `evidence/P3/` — FRONTEND Python subset → MBIR (15 sources, host reference VM)
- `tests/test_harness.py` — 50/50 passing reference tests

## Evidence kinds used

- P1: `REFERENCE_MODEL` (host_language=Python)
- P2: `FRONTEND` (host_language=Python, MalPy opcodes)
- P3: `FRONTEND` (host_language=Python, MBIR_VERSION 0, oracle `mbir_ref.py`)
- No `MALBOLGE_RUNTIME` evidence exists yet for this frontend — none is claimed.