# A04C — Cellular MBIR Experiments

A04C uses the existing CoEvo-Mu engine as a substrate for testing whether
cellular primitives can implement parts of the MBIR execution loop. The
speculative question: could a small fixed neighborhood rule realize
tick-level state transitions without a host-level fetch/decode?

## Files

- `A04C_COEVO_AUDIT.md` — the audited substrate mechanics.
- `HOST_BOUNDARY.md` — what the host may and may not do.
- `M0_SPEC.md` — the MBIR microprogram specification (opcodes 0x01/0x10).
- `STATE_ENCODING.md` — how bits are located in (x, y, z, t).
- `VERDICTS.md` — PASS/FAIL per phase.
- `evidence/` — run logs and hashes.

## Status footer

This is proposed-garage-managed evidence and remains secondary to the
canonical A04 gateway (a real Malbolge runtime executes MBIR). For now
A04 is far downstream of byte-transport; we document what works but claim
nothing beyond the demonstrated tests.