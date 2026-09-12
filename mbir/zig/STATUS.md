# MBIR Zig backend status

Version: MBIR_VERSION 0
Date: 2026-09-12

## Verdict

`ZIG_MBIR_V0_DEMONSTRATED`

Scope explicitly covered: the 18-opcode MBIR_VERSION 0 execution model,
external program/input files, deterministic result envelope, and differential
comparison against the Python reference VM.

Scope not covered: source-language frontends, Malbolge-hosted execution,
dynamic output over 4096 bytes, and any claim that MBIR is an omnilingual VM.

## Evidence

- Toolchain: Zig 0.16.0.
- Native tests: 9/9 PASS via `zig build test`.
- Native build: PASS via `zig build -Doptimize=ReleaseSafe`.
- Differential run 1: 22/22 PASS via `py tests\differential.py --manifest evidence\m3_differential.json`.
- Differential run 2: 22/22 PASS via `py tests\differential.py --manifest evidence\m3_differential_second.json`.
- Hashes: `evidence/hashes.json`.
- Contract regression executed separately:
  - `py mbir/tests/test_mbir.py` → 23/23 PASS.
  - `py mbir/tests/test_mbir_ref.py` → 28/28 PASS.

## Contract coverage

Positive corpus includes arithmetic wrap-around, all three comparisons,
locals, duplicate/pop, branching, loops, calls, recursive `fib(6)`, byte I/O,
and repeated EOF. Negative corpus includes stack underflow, `BAD_OPCODE`,
`BAD_TARGET`, `BAD_SLOT`, `NO_FRAME`, truncation and `MAX_STEPS`.

## Remaining risks

- The runner compares output bytes exactly, so paths with newline munging are
  part of the host transport, not MBIR semantics.
- The current external runner is intentionally file-based. Streaming or IPC
  transports are future work and require new evidence.
