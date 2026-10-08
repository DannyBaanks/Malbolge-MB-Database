# vm_malbolge — MBIR middleware boundary and Malbolge probes

## Status (Milestones A05, A05b, P0, and P1)

The toolchain and primitives are verified on the real Malbolge name Classic
runner and Python reference oracle. MBIR is a backend-neutral middleware boundary between language
frontends (Python, Rust, COBOL, PITÓN, Fortran, etc.) and execution substrates
such as native Malbolge, Rustbolge, Javolge, Pibolge, or other Bolge engines.
This repository does **not** claim that MBIR is an omnilingual VM, nor that
every backend must implement all source-language semantics.

- **Milestone Unified ALU (`vm_malbolge/ALU_STATUS.md`)**: Complete Unified Arithmetic Logic Unit in Pure Malbolge executing both `ADD` (Opcode 0x02) and `SUB` (Opcode 0x03) simultaneously in the same binary image with 100% bit-exact step parity across 14/14 vectors (including cross-arithmetic chained sequential expressions), size 54,691 bytes (< 59,049 limit with 4,358 bytes headroom).
- **Milestone P1 (`vm_malbolge/P1_STATUS.md`)**: Arithmetic Kernel executing `SUB` (Opcode 0x02), 2-phase operand popping and subtraction evaluation ($a - b$), 100% bit-exact step parity on 7/7 vectors.
- **Milestone P0 (`vm_malbolge/P0_STATUS.md`)**: Arithmetic Kernel executing `ADD` (Opcode 0x02), 2-phase operand popping and ternary digital sum evaluation, 100% bit-exact step parity on 7/7 vectors.
- **Milestone A05b (`vm_malbolge/A05_STATUS.md`)**: 2-Slot LIFO Stack Machine with dynamic depth tracking and multi-cycle execution sustaining clean LIFO popping order (`BA`).
- **Milestone A04 (`vm_malbolge/A04_STATUS.md`)**: In-register byte classification gate.

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
