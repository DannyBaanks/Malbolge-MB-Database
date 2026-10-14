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
- **Milestone P2 relational ordering — `CMP_LT` (`vm_malbolge/LT_STATUS.md`)**: **best 11/12, dual-engine, and `12/12` is `NOT_DEMONSTRATED`.** Fork `vm_malbolge/src/mbir_cmp_lt.hell` + generator `vm_malbolge/tools/mbir_cmp_lt_gen.py` (a fork of `mbir_p2_cmp_gen.py`; the frozen `CMP_EQ` image is untouched). Harness `vm_malbolge/tests/lt_harness.py`: 9 ordered pairs over `{0,1,2}` (print `01` iff `a < b`, else `00`) plus the 3 baselines, each vector run on **both** `tools/oracle_classic.py` and `runners/malbolge-original/malbolge` and compared on output **and** step count. Eight images are committed with a per-image manifest (`vm_malbolge/evidence/lt_*_harness.json`); seven score 11/12, each failing exactly one entry — `lt_head11_probe`/`lt_f62_line448_decop1`/`lt_f62_line448_rfcwns2` fail `(0,1)`, `lt_f59_cand_B` fails `(1,2)`, `lt_f59_cand_C` fails `(2,2)`, `lt_f59_cand_A`/`lt_f59_cand_D` fail `(2,2)` while already emitting the third symbol `02` — and `lt_a7c9_probe` is the earlier 9/12. The baselines pass on both engines, so the VM core is intact; the failure is the comparator's output routing. Structural laws measured, not opined: the printed digit is a pure function of the single cell the shared `ROT` reads (`0/3/6 -> 00/01/02`, F47/F48/F56/F58); an exhaustive 3^10 scan finds no cell encoding the LT table at decision time (F59) and no read-only route reaches 12/12 at any fold depth (F60/F63); no one- or two-fold composition reproduces `a+b*LT` over the nine pairs (F61); `(0,1)` and `(2,2)` are **one computation** — 0 pointer-divergent steps out of 79,790, with all 7 `a`-divergent folds in the filler and none in the editable region (F72). Quantified negatives kept: the full one-character edit space is 5,234,616 variants (~3,900 CPU-hours) and is **not** swept, while the 5,580 direct-live and 186 seed edits (5,766 variants) are swept with **0 fixes** — the single apparent hit is degenerate (halts at step 2, prints `00` to all 12 vectors, 6/12). Re-measured 2026-10-14: on the 11/12 base both engines agree on all twelve vectors **including the failing one** (`cmp_lt(2,2)` -> `01` @79,790 steps), and a fresh LMAO build of the same `.hell` produced a third instance differing only in the 503-byte tail window, which is never read. Raw output of all four runs (with working-file and blob hashes): `vm_malbolge/evidence/lt_recheck_2026-10-14.txt`. The same file records that the fork's canonical image `vm_malbolge/src/mbir_cmp_lt.mb` is still **8/12** today (`(0,1)`, `(0,2)`, `(1,2)` print `00`; `(2,2)` prints `01`; engines agree on all four), i.e. the 11/12 results live in `evidence/artifacts/`, not in the fork's `.hell`.
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

`CMP_LT` at 12/12: **NOT_DEMONSTRATED** — the measured ceiling is 11/12, reached by
seven committed images out of the eight manifests in `LT_STATUS.md` (and re-measured
today), and the routes that were ruled out are ruled
out by measurement, not by opinion: no read-only pointer retarget at any fold depth
(F59/F60/F63), no one- or two-fold composition of `a+b*LT` (F61), no single-character
edit among the 5,766 swept (F72), and `(0,1)`/`(2,2)` provably one computation (F72).
The full one-edit space (5,234,616 variants) has **not** been swept; the filler seed
**pair** and the F72 battery on bases A/D have **not** been run. `CMP_GT`: not
started.

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
