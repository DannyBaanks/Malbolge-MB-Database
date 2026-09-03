# A04 — MBIR VM on Malbolge

## Status

```text
A04_MBIR_ON_MALBOLGE = NOT_DEMONSTRATED  (in progress; sub-milestones landed)
```

## Sub-milestones (verified)

### A04.a — Toolchain
- Vendored `third_party/lmao` (LMAO 0.6.0, esoteric-programmer/LMAO).
- Build script `tools/build_lmao.ps1` proven; compiled `bin/lmao.exe`
  (sha256 recorded in `docs/TOOLCHAIN.md`).
- Smoke: `example_simple_hello_world.hell` compiled and executed on
  `runners/malbolge-original/malbolge.exe` (Classic), printing
  `"Hello, World!"` in 4646 steps. Exit 0.

### A04.b — Byte store/recover roundtrip on real runner
- `vm_malbolge/src/min3_echo1.hell` compiles via LMAO and on
  `malbolge-original` reads one byte from stdin, encodes it into a data cell
  (`cell = crz(byte, C1)`), recovers it, and writes the byte back to stdout.
- Verified bytes 0x00, 0x20, 0x41, 0x61, 0x7f, 0xff round-trip byte-exact
  (single-byte echo) with a fixed `HALT`.
- Known wart: 0x0A on stdin trips the Windows runner's text-mode CRLF
  mangling (host-side stdin semantics, not a Malbolge bug).

## What A04 still needs (full gate)

- A runtime artifact that accepts multiple distinct MBIR programs *as data*.
- An instruction-fetch/decode loop over a bytecode array.
- Opcode handlers for: PUSH_CONST, ADD, OUT_BYTE, HALT (+more for the corpus).
- Corpora executions covering: arithmetic with distinct values, variables,
  conditionals (true and false), loops, calls, and runtime-influenced output.
- Same-artifact-hash evidence across different MBIR inputs.

## Evidence chain

| Item | Kind | Path |
|------|------|------|
| LMAO provenance | manifest | `docs/TOOLCHAIN.md`, `third_party/PROVENANCE.md` |
| echo1 test logs | runner run | `vm_malbolge/tests/buildrun.py` output (in-line at edit time) |

## Next

Write the dispatch loop + min instruction set (PUSH_CONST/ADD/OUT_BYTE/HALT)
and evidence KB.