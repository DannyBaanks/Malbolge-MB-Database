# vm_malbolge — MBIR middleware boundary and Malbolge probes

## Status (A04 session progress)

The toolchain and primitives are verified on the real Malbolge name Classic
runner. MBIR is a backend-neutral middleware boundary between language
frontends (Python, Rust, COBOL, PITÓN, Fortran, etc.) and execution substrates
such as native Malbolge, Rustbolge, Javolge, Pibolge, or other Bolge engines.
This repository does **not** claim that MBIR is an omnilingual VM, nor that
every backend must implement all source-language semantics.

```text
source program -> frontend/adapter -> MBIR boundary -> backend adapter -> substrate
                         native Malbolge / Rustbolge / Pibolge / ...
```

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

Any claim of a complete MBIR-on-Malbolge runtime that interprets arbitrary
MBIR programs as data: **NOT_DEMONSTRATED**. The demonstrated scope is the
middleware contract, transport primitives, and backend-facing Malbolge
probes. `mbir_vm.hell` remains a design stub; no complete omnilingual VM claim
will be made without green runner evidence.

## Known weirdness

- Windows stdin CRLF: byte `0x0A` read from stdin gets paired with CR — a
  C-runtime stdin reading artifact on Windows; not a Malbolge or HeLL bug.
- The runner's stdout carries a trailing CRLF appended by the Windows wrapper.

## Links

- Toolchain evidence: `docs/TOOLCHAIN.md`, `third_party/PROVENANCE.md`.
- A04 findings/action items: `vm_malbolge/A04_NEXT.md`.
