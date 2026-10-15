# vm_malbolge — MBIR middleware boundary and Malbolge probes

## Status (Milestones A04, A05, A05b, P0, P1, P2 CMP_EQ, Unified ALU, M2 loader/ALU/CF, P2 CMP_LT)

The toolchain and primitives are verified on the real Malbolge name Classic
runner and Python reference oracle. MBIR is a backend-neutral middleware boundary between language
frontends (Python, Rust, COBOL, PITÓN, Fortran, etc.) and execution substrates
such as native Malbolge, Rustbolge, Javolge, Pibolge, or other Bolge engines.
This repository does **not** claim that MBIR is an omnilingual VM, nor that
every backend must implement all source-language semantics.

- **Milestone 2 (`vm_malbolge/M2_LOADER_STATUS.md`)**: Stored-Program MBIR VM in Pure Malbolge with dedicated in-memory RAM cells (`prog_0..prog_3`), program loader from STDIN, Program Counter (`PC`) execution decoupling, and double-C2 operand recovery with 100% bit-exact step parity across 4/4 vectors, size 40,309 bytes (< 59,049 limit with 18,740 bytes headroom).
- **Milestone M2 ALU (`vm_malbolge/M2_ALU_STATUS.md`)**: One stored 7-byte program, then a single ADD (0x02) or SUB (0x03) for operands in `{0,1,2,3,4}`. 8/8 oracle/C parity, 56,361 bytes, 2,688 bytes of file headroom. Single-shot only: not a general subtractor, not chained programs, and not the 14 streaming ALU vectors.
- **Milestone M2 CF (`vm_malbolge/M2_CF_STATUS.md`)**: Five fixed 11-byte shapes. JMP emits the immediate loaded from RAM, JZ distinguishes condition 0 from 1, and CALL emits the callee byte then the byte after the call. 5/5 oracle/C parity, 55,819 bytes, 3,230 bytes of file headroom. Not a general program counter, and the JMP target is not a selector.
- **Milestone Unified ALU (`vm_malbolge/ALU_STATUS.md`)**: Complete Unified Arithmetic Logic Unit in Pure Malbolge executing both `ADD` (Opcode 0x02) and `SUB` (Opcode 0x03) simultaneously in the same binary image with 100% bit-exact step parity across 14/14 vectors (including cross-arithmetic chained sequential expressions), size 54,691 bytes (< 59,049 limit with 4,358 bytes headroom).
- **Milestone P2 relational ordering — `CMP_LT` (`vm_malbolge/LT_STATUS.md`)**: **12/12 DEMONSTRATED on both engines.** Canonical image `vm_malbolge/src/mbir_cmp_lt.mb` (compiled from `vm_malbolge/src/mbir_cmp_lt.hell` via LMAO v0.6.0) achieves 100% bit-exact pass across all 9 ordered comparison pairs over $\{0,1,2\}^2$ plus all 3 baselines (12/12) on both `tools/oracle_classic.py` and `runners/malbolge-original/malbolge`. Size: 57,511 bytes (< 59,049 limit with 1,538 bytes headroom). Resolves historical 11/12 plateau via dedicated `LT_B1` comparison flag in `.CODE` (with unused `COUNTER2_1` purged) and clean arithmetic underflow discrimination without flag leakage. Full differential evidence in `vm_malbolge/evidence/lt_12_12_harness.json`.
- **Milestone P2 relational ordering — `CMP_GT` (`vm_malbolge/GT_STATUS.md`)**: **12/12 DEMONSTRATED on both engines.** Canonical image `vm_malbolge/src/mbir_cmp_gt.mb` (compiled from `vm_malbolge/src/mbir_cmp_gt.hell` via LMAO v0.6.0) achieves 100% bit-exact pass across all 9 ordered comparison pairs over $\{0,1,2\}^2$ plus all 3 baselines (12/12) on both `tools/oracle_classic.py` and `runners/malbolge-original/malbolge`. Size: 57,511 bytes (< 59,049 limit with 1,538 bytes headroom). Implemented via dedicated `GT_B1` comparison flag in `.CODE` and symmetrical fall-through underflow routing ($b=2 \\to 00$, $b=1 \\to a=2$, $b=0 \\to a \\ge 1$). Full differential evidence in `vm_malbolge/evidence/gt_12_12_harness.json`.
- **Milestone P2 (`vm_malbolge/P2_STATUS.md`)**: Comparison Kernel executing `CMP_EQ` (Opcode 0x02), 2-phase boolean equality evaluation (`a == b -> 1`, `a != b -> 0`), 100% bit-exact step parity on 7/7 vectors.
- **Milestone P1 (`vm_malbolge/P1_STATUS.md`)**: Arithmetic Kernel executing `SUB` (Opcode 0x02), 2-phase operand popping and subtraction evaluation (`a - b`), 100% bit-exact step parity on 7/7 vectors.
- **Milestone P0 (`vm_malbolge/P0_STATUS.md`)**: Arithmetic Kernel executing `ADD` (Opcode 0x02), 2-phase operand popping and ternary digital sum evaluation, 100% bit-exact step parity on 7/7 vectors.
- **Milestone A05b (`vm_malbolge/A05_STATUS.md`)**: 2-Slot LIFO Stack Machine with dynamic depth tracking and multi-cycle execution sustaining clean LIFO popping order (`BA`).
- **Milestone A04 (`vm_malbolge/A04_STATUS.md`)**: In-register byte classification gate.

```text
source program -> frontend/adapter -> MBIR boundary -> backend adapter -> substrate
                         native Malbolge / Rustbolge / Pibolge / ...
```

### Verified artifacts

- `tools/oracle_classic.py`: Classic 3^10 Malbolge interpreter (outputs run 1:1
  with the native runner, re-verified 2026-10-14 on all twelve `CMP_LT` vectors
  of the 11/12 base — identical output and identical step count).
- `runners/malbolge-original/malbolge`: the **Linux** native C runner, used by
  `vm_malbolge/tests/lt_harness.py` and by every differential manifest recorded in
  `LT_STATUS.md`. The sibling `malbolge.exe` is the historical Windows build; the
  trailing-CRLF notes below are Windows-wrapper artifacts, not Malbolge behaviour.
  Note: `vm_malbolge/tests/buildrun.py` still resolves `third_party/lmao/bin/lmao.exe`
  and `runners/malbolge-original/malbolge.exe` (unchanged Windows code path,
  `[HISTORICAL]` on this host), so on Linux use `lt_harness.py` or point those two
  constants at the native binaries.
- `third_party/lmao/bin/lmao`: vendored LMAO v0.6.0 assembler, working as a native
  Linux binary (`./third_party/lmao/bin/lmao -d -o out.mb in.hell`). Builds are
  **byte-nondeterministic but behaviour-invariant** (`LT_STATUS.md`, Finding 62):
  consecutive builds of one `.hell` yield distinct `.mb` hashes whose bytes differ
  only in an unread tail window, all sharing one output+steps signature — so a `.mb`
  hash is an *instance* hash and canonical identity is
  (.hell sha256, behaviour signature, instance sha256).
- `tools/runner_doctor.ps1`, `tools/build_lmao.ps1`, `tools/bootstrap_runners.ps1`:
  PowerShell-era helpers carried over from the Windows host. The Linux harnesses do
  not invoke them and their current behaviour on this host was **not** re-verified
  here (`NOT_DEMONSTRATED` on this host).
- `vm_malbolge/src/min3_echo1.hell`: byte-store/recover via the verified
  double-CRAZY idiom, runs on **real** Classic Malbolge and echoes stdin byte
  back; oracle & runner outputs agree.
  - Input `41` → output `41` (verified).
- `vm_malbolge/tests/buildrun.py`: HeLL → LMAO → Oracle+Runner compare
  harness (compile + run pipeline).
- `vm_malbolge/tests/lt_harness.py`: the `CMP_LT` differential harness (9 ordered
  pairs over `{0,1,2}` + 3 baselines on both engines, output **and** step count).

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

`CMP_LT` at 12/12: **DEMONSTRATED**. The 12/12 milestone is achieved in canonical `vm_malbolge/src/mbir_cmp_lt.mb` with exact dual-engine parity across all 9 comparison vectors over $\{0,1,2\}^2$ and all 3 baselines on both `tools/oracle_classic.py` and `runners/malbolge-original/malbolge` (Finding 74). Evidence in `vm_malbolge/evidence/lt_12_12_harness.json`.

`CMP_GT` at 12/12: **DEMONSTRATED**. The 12/12 milestone is achieved in canonical `vm_malbolge/src/mbir_cmp_gt.mb` with exact dual-engine parity across all 9 comparison vectors over $\{0,1,2\}^2$ and all 3 baselines on both `tools/oracle_classic.py` and `runners/malbolge-original/malbolge` (Finding 75). Evidence in `vm_malbolge/evidence/gt_12_12_harness.json`.

## Known weirdness

- Windows stdin CRLF: byte `0x0A` read from stdin gets paired with CR — a
  C-runtime stdin reading artifact on Windows; not a Malbolge or HeLL bug.
- The runner's stdout carries a trailing CRLF appended by the Windows wrapper.
  `lt_harness.py` strips one trailing `\r\n` or `\n` before comparing, which is why
  the empty-output baseline (`HALT`) reads as empty on both engines.
- `core.autocrlf=true`: the sha256 of a checked-out `.mb`/`.hell` is
  checkout-dependent. For any committed artefact cite the **blob** hash
  (`git show HEAD:<path> | sha256sum`) next to the working-file hash — the eight LT
  manifests do (Finding 55 addendum, Finding 62 erratum).
- LMAO builds are byte-nondeterministic: measured again 2026-10-14, a fresh build of
  `vm_malbolge/evidence/lt_f59_cand_C.hell` produced a third instance (`fb0a775d…`)
  differing from the committed one (`b7bb3a82…`) in the same 503-byte tail window, and
  the harness scored it 11/12 with the identical output+steps signature on all twelve
  vectors.

## Links

- Toolchain evidence: `docs/TOOLCHAIN.md`, `third_party/PROVENANCE.md`.
- A04 findings/action items: `vm_malbolge/A04_NEXT.md`.
- `CMP_LT` ledger (Findings 1-72, append-only, best 11/12): `vm_malbolge/LT_STATUS.md`;
  per-image manifests in `vm_malbolge/evidence/` and images in
  `vm_malbolge/evidence/artifacts/`.
- Repository-level summary of what is demonstrated: root `README.md` (section 5b).
