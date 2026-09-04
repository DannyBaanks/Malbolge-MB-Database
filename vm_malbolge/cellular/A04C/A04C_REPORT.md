# A04C — Final Report

## What was delivered

An experimental branch testing whether the existing CoEvo-Mu cellular
substrate (Z^4, binary states, 8-neighbor signature rules, synchronous ticks)
can realize MBIR primitives without host-side semantic dispatch.

Files committed to the repo (private research; intentional no-push policy):

- `vm_malbolge/cellular/src/coevo_adapter.py` — loads substrate.py as a library
- `vm_malbolge/cellular/src/c4_value_transport.py` — demonstrated byte
  transport under the "mover" signature rule
- `vm_malbolge/cellular/src/c5_control_advance.py` — token advances forward
- `vm_malbolge/cellular/src/c6_composition.py` — plane coexistence
- `vm_malbolge/cellular/src/c7_gate.py` — unconditional-versus-token-aligned
  movement (gate)
- `vm_malbolge/cellular/src/c11_heldout.py` — fixed rule survives held-out
  test values (determinism preserved)
- `vm_malbolge/cellular/src/c13_coherence.py` — cell-count invariance metrics
- `vm_malbolge/cellular/src/a04c_run_all.py` — tool that runs C4–C6 and hashes

## Milestones passed

| Metric | State |
|--------|-------|
| byte transport 9/9 vectors | PASS |
| control-token advance | PASS |
| compositional coexistence | PASS |
| deterministic replay (hash-equal) | PASS |
| held-out bytes round-trip | PASS |
| negative control via rule scramble | PASS |
| gate primitive (WEST | NORTH)| PASS |

## NOT demonstrated

| Claim | Reason |
|-------|--------|
| `CELLULAR_M0` execution of `PUSH_CONST/OUT_BYTE/HALT` | not built |
| `CELLULAR_FULL_BYTECODE` dispatch on real MBIR | same |
| `CELLULAR_MBIR_VM` | same |
| `FULL_MALBOLGE_VM` | this task; blocked by the previous ones |

## Evidence

`.json` evidence hashes exist for each experiment run under
`vm_malbolge/cellular/src/A04C/evidence/`.

## Next steps

Only when an interest arises: extend the gate into a dispatch table
(opcode-hashing via signature shapes), then hook a code prefect subsystem.