# vm_malbolge — MBIR interpreter hosted on real Malbolge

## Status (A04 session progress)

The toolchain and primitives are verified on the real Malbolge name Classic
runner. The full interpreter gate is NOT yet demonstrated.

### Verified artifacts

- `tools/oracle_classic.py`: Classic 3^10 Malbolge interpreter (outputs run 1:1
  with `runners/malbolge-original/malbolge.exe`).
- `tools/runner_doctor.ps1`: runner integrity verification.
- `third_party/lmao`: vendored LMAO assembler; builds with
  `tools/build_lmao.ps1`.
- `vm_malbolge/src/min3_echo1.hell`: byte-store/recover via the verified
  double-CRAZY idiom, runs on **real** Classic Malbolge and echoes stdin byte
  back; oracle & runner outputs agree.
  - Input `41` → output `41` (verified).
- `vm_malbolge/tests/buildrun.py`: HeLL → LMAO → Oracle+Runner compare
  harness (compile + run pipeline).

### Reference sources on this repo

- `third_party/lmao/example_cat_halt_on_eof.hell` — EOF-detect cat.
- `third_party/lmao/example_hello_world.hell` — multi-char output.
- `third_party/lmao/example_digital_root.hell` — decrement-based digit
  classification (demonstrates the data-driven dispatch idiom).
- `third_party/lmao/example_adder.hell` — 3-digit adder (digit data driven).

### Explicitly NOT yet demonstrated

Any claim of a working MBIR-on-Malbolge runtime that interprets MBIR programs
as data: **NOT_DEMONSTRATED** until we ship `runners/malbolge-mbir` (or
equivalent) running the killer corpus from the roadmap. mbir_vm.hell is a
design stub with no working implementation yet; no `A04_MBIR_ON_MALBOLGE =
DEMONSTRATED` will be claimed without green runner evidence.

## Known weirdness

- Windows stdin CRLF: byte `0x0A` read from stdin gets paired with CR — a
  C-runtime stdin reading artifact on Windows; not a Malbolge or HeLL bug.
- The runner's stdout carries a trailing CRLF appended by the Windows wrapper.

## Links

- Toolchain evidence: `docs/TOOLCHAIN.md`, `third_party/PROVENANCE.md`.
- A04 findings/action items: `vm_malbolge/A04_NEXT.md`.
