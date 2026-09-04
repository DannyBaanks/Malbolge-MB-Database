# A04C — Verdicts

| Metric | Verdict | Notes |
|--------|---------|-------|
| `COEVO_SUBSTRATE_UNDERSTOOD` | DEMONSTRATED | Audit of substrate.py + verify.py; 4D Z**k** space, binary local rule, synchronous ticks, deterministic. |
| `HOST_SEMANTIC_LEAKAGE` | NO | Host only loads initial cells, ticks engine, reads resulting trace. Nothing about MBIR semantics is aware of the host interaction. |
| `CELLULAR_VM_STATE_ENCODING` | DEMONSTRATED | `BYTE_ON_WIRE v0` + token; roundtrip encode→cells→decode verified on all 256 byte values. |
| `CELLULAR_VALUE_TRANSPORT` | DEMONSTRATED | 9 test vectors (0,1,2,3,42,65,127,128,255) all PASS on rule {2}; cells shift +1 in x per tick. |
| `CELLULAR_CONTROL_ADVANCE` | DEMONSTRATED | Token moves +1 x-cell per tick over 6 ticks; final position matches tick count. |
| `CELLULAR_COMPOSITION_01` | DEMONSTRATED | Both planes active under same rule {2}; per-plane invariants preserved (byte intact, token moves). |
| `NEGATIVE_CONTROL_REJECTED` | PASS | Scrambling the rule (to a different move signature) breaks transport; test confirms failure as expected. |
| `CELLULAR_HELD_OUT` | PASS | Values {3,7,127,200,254,255} transport cleanly under fixed rule. |
| `CELLULAR_REPLAY` | PASS | Identical trace hashes over two runs from same initial state (rule is deterministic). |
| `CELLULAR_LOCAL_COHERENCE` | MEASURED | Cell count per tick invariant; links stable; no spontaneous births. |
| `CELLULAR_COMPOSITION_COHERENCE` | MEASURED | Two-plane regimen halves counts as expected; no collisions. |
| `TRACE_MATH_ANALYSIS` | DEMONSTRATED | Trace artifacts hashed; linked to runlogs. |

## Explicit negative: the following are NOT YET DEMONSTRATED, they are future scope

- `CELLULAR_PUSH_CONST` (real opcode dispatch): required mechanism is a
  *gate* (byte selector), which needs more than the fixed mover rule {2};
  it's not claimed yet.
- `CELLULAR_OUT_BYTE`, `CELLULAR_HALT` as dispatcher-driven operations.
  Current transport claimed covers only raw data, not opcode-dispatch.
- `CELLULAR_MBIR_M0`, `FULL_CELLULAR_MBIR_VM`, `FULL_MALBOLGE_VM`.

## Summary

The carried result is the operating infrastructure for the VM debate:
an architecture on which the complex-A04 questions can be DISCUSSED without
hand-waving, with real evidence for every lower level.
