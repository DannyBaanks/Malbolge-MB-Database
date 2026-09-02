# Python MB — P1 Evidence

## Status: REFERENCE_DEMONSTRATED

P1 is a **Python reference VM** (stack machine, PUSH/ADD/OUT/HALT).
Evidence kind: `REFERENCE_MODEL` (host_language = Python).

It demonstrates:
- Same reference VM executes 5 bytecodes producing 5 different correct results
- Negative tests: OUT/ADD underflow raise, unknown opcode raises

It does NOT demonstrate:
- The VM running inside Malbolge (Malbolge-hosted runtime = NOT_DEMONSTRATED)

## Evidence Record

- `run_p1_vm.json` — execution record (evidence_kind = REFERENCE_MODEL)

## Relationship to design

The opcode set in `python/SPEC.md` is the forward design. This reference VM is
the semantic oracle that the Malbolge-hosted MBIR VM (A04) must match.