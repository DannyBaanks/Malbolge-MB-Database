# A04C — Evidence Index

All artifacts in this directory are produced by A04C experiments on the
loadable CoEvo-Mu cellular-substrate (external, provided via
`MB_COEVO_SUBSTRATE`). The substrate is read-only here — we import its
`substrate.py`; we never modify the upstream engine.

Files:

- `a04c_evidence.json` — recorded outputs for the three C4/C5/C6 runs
  (transport over 9 bytes, control advance, composition).
- `traces/` — raw traces as produced by the engine; committed only hashes
  in the root README to keep the repo light.

All hashes are SHA-256 over the JSON payloads.

## Runbook

```
cd <repo-root>
py vm_malbolge/cellular/src/c4_value_transport.py
py vm_malbolge/cellular/src/c5_control_advance.py
py vm_malbolge/cellular/src/c6_composition.py
py vm_malbolge/cellular/src/c11_heldout.py
py vm_malbolge/cellular/src/c13_coherence.py
```

Exit code 0 with "PASS" for every experiment is the expected state.

## What's reused

- `substrate.py` (read_cells, write_cells, decode_rule, encode_rule, step,
  evolve, signature_index, OFFSETS) — imported as a module.
- No modifications to the upstream engine.

## What is new

- `coevo_adapter.py` (HOST-side glue, no MBIR logic)
- `c4_value_transport.py` (byte transport via rule {2})
- `c5_control_advance.py` (token advance via rule {2})
- `c6_composition.py` (both primitives under one rule set)
- `c11_heldout.py` (held-out + deterministic replay + negative control)
- `c13_coherence.py` (cell-count invariants)
- `a04c_run_all.py` (whole-suite harness)
