# vm_malbolge — MBIR Interpreter in Malbolge (HeLL)

Target: implement the MBIR_VERSION 0 interpreter core in Malbolge via the
LMAO toolchain (HeLL assembly), produced and verified on real runners.

This is the A04 work-in-progress directory.

## Layout

- `src/` — HeLL source files (`.hell`)
- `tests/` — harness: `buildrun.py` (compile with LMAO → simulate oracle → run on Classic runner)

## Dialect notes

- Values stored as cells; byte store/recover idiom verified against real runner:
  `store: cell(c1) <- crz(byte, C1)` then `recover: A <- crz(C1, cell)` recovers
  the byte (verified `min3_echo1.hell>: byte 0x41 echoed correctly, 22230 steps, HALTED`).
- Orthogonally: `py vm_malbolge/tests/buildrun.py <file.hell> <hex-input> [--expect=<hex>]`
  compiles and runs against both the Python oracle and a real runner.

## Status

- A04.PHASE.A: LMAO toolchain vendored + built + verified (example_hello_world, cat, echo1).
- A04.PHASE.B: single-byte store/recover idiom on real runner — **DONE** (min3_echo1.hell).
- A04.PHASE.C: dispatch + multi-instruction MBIR subset — IN PROGRESS.

A04 gate itself (full corpus on one immutable artifact) remains NOT_DEMONSTRATED.