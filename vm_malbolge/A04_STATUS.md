# A04 — Current Status (verbatim, no polish)

## What is demonstrated

| item | evidence |
|---|---|
| MBIR contract frozen (v0) | `docs/MBIR_CONTRACT.md`, 18 opcodes, tested by 23/23 (`mbir/tests/test_mbir.py`) + 28/28 (`mbir/tests/test_mbir_ref.py`) |
| MBIR reference VM works silently on `python.exe` | `mbir/mbir_ref.py` runs fib(6), branches, calls, I/O |
| LMAO v0.6.0 builds Malbolge from HeLL | `tools/build_lmao.ps1` + `third_party/lmao/` — Hello World assembles and runs |
| Byte echo works on the REAL malbolge.exe | `vm_malbolge/src/min3_echo1.hell` → hex41 → hex41, 25991 steps, verified |
| Cell store/recover path re-run | `vm_malbolge/src/min3_echo1.hell` + `vm_malbolge/evidence/cell_store_recover_smoke.json` — 4/4 OK for `00`, `41`, `7a`, `ff` on oracle AND runner. The established double-CRAZY path stores the input through `tmp2/tmp4`, recovers `tmp2`, and emits it. |
| Dedicated MBIR-owned cell pair (stack_scratch/stack_top) | `vm_malbolge/src/cell_stack_top.hell` + `vm_malbolge/evidence/cell_stack_top_smoke.json` — 4/4 OK on oracle AND runner. NEW cells (not the example's tmp1..tmp4) store and return one byte. Two-level store (scratch → top) + 2x C2-crazy recovery. First attempt (one-level store) produced the deterministic wrong map 00→54/41→67/7a→dd/ff→55, which fleshes out the `crazy`-writes-both-destinations semantics: keep as evidence. NOT yet wired into opcode dispatch. |
| Primitive byte transport is provable | host never computes contents; only the Malbolge CPU does |
| Cellular substrate proves selectability | `vm_malbolge/cellular/A04C/evidence/` (private tree, transport + gate + holdout) |
| Conditional branch EOF-vs-not-EOF (via value-jump to C20/C21) | `vm_malbolge/src/byte_branch_wip.hell` + `vm_malbolge/evidence/byte_branch_{A,eof}.json` — same artifact, two distinct control paths via jump-on-value **only** for the EOF sentinel. All N byte values take the same (echo) path — see `byte_branch_smoke.json`. |
| Byte-VALUE dispatch 0x00-vs-nonzero (digital_root decrement idiom, single carry pad) | `vm_malbolge/src/byte_dispatch1.hell` + `vm_malbolge/evidence/byte_dispatch1_{00,A,eof,smoke}.json` — 12/12 OK on oracle_classic AND runners/malbolge-original (normal LMAO layout): 0x00→HALT empty (28078 steps), 10 nonzero values→verbatim echo (e.g. 0x41→`A`, 26789 steps), EOF→empty. Distinct paths AND distinct outputs per value class. Built only from verbatim digital_root idioms (ENTRY copy, inc/dec, flag-branch, print recover) + dual decrement exit (increment two-site pattern). |
| 3-way byte-VALUE dispatch (0x00 / 0x01 / other) | `vm_malbolge/src/byte_dispatch2.hell` + `vm_malbolge/evidence/byte_dispatch2_{01,smoke}.json` — 12/12 OK on oracle AND runner: 0x00→empty (29033 steps), 0x01→`P` marker (29525 steps), other nonzero→echo (e.g. 0x41→`A`, 28230 steps), EOF→empty. Three distinct value classes, three paths, three outputs. Reuses dispatch1 pipeline + a 3rd decrement site. **Key idiom fix:** a multi-site subroutine exit needs a trailing `R_SUBROUTINE_FLAGn` on every non-last site (increment two-site pattern); without it the 3rd site hangs. |
| Full 18-opcode MBIR dispatch (generated) | `vm_malbolge/tools/mbir_dispatch_gen.py` → `vm_malbolge/src/byte_dispatch18.hell` + `vm_malbolge/evidence/byte_dispatch18_smoke.json` — 21/21 OK on oracle AND runner: every MBIR_VERSION 0 opcode byte 0x00..0x11 takes a distinct handler (0x00 HALT; 0x01..0x11 → marker bytes; non-opcode → echo; EOF → empty). The dispatch is now generated mechanically (parameterized decrement-chain + N `SUBROUTINE_FLAGn` sites), not hand-written. This resolves the "byte-dispatch table" blocker at the classifier level. |
| Partial `PUSH_CONST` operand path | `vm_malbolge/tools/mbir_dispatch_gen.py --opcodes 0001 --push-const-out` → `vm_malbolge/src/byte_push_const_out.hell` + `vm_malbolge/evidence/byte_push_const_out_smoke.json` — 4/4 OK on oracle AND runner: `01 xx` consumes the following byte and emits `xx`; `00` halts; unlisted `41` echoes. This demonstrates operand consumption/output behavior, but explicitly does not claim a stack or fetch loop. |

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Full MBIR VM in Malbolge | dispatch (classification) is DONE for all 18 opcodes as marker handlers, and a partial `PUSH_CONST` operand path is now demonstrated. What remains is a real value stack, separate `OUT_BYTE` handling, arithmetic, control flow, operand truncation/error behavior, and a fetch-loop over a multi-byte program, plus a stdin→cells loader. |
| MBIR→HeLL code generator | for instructions: the dispatch *skeleton* generator now exists (`vm_malbolge/tools/mbir_dispatch_gen.py`, verified). A full MBIR-program → HeLL generator (loader + real handlers lowering through MBIR) is still open. |
| Two-fetch `01 <operand> 10` probe | `vm_malbolge/evidence/byte_twofetch_negative.json` — WIP assembled, but station-2 cases disagreed between oracle and real runner (`014110`: oracle `471e26e5e5ffff`, runner empty). Generator/source were deleted; no second-fetch claim. |

## Blockers to unblock next

1. **Byte-dispatch table.** DONE 2026-09-11: full 18-opcode table generated (`mbir_dispatch_gen.py` → `byte_dispatch18.hell`, 21/21). Each opcode = one decrement + one `SUBROUTINE_FLAGn` site, trailing `R_SUBROUTINE_FLAGn` on non-last exit sites.
2. **MBIR program from stdin.** MBIR bytecode lives in Malbolge data cells, copied from stdin. The batch-input idiom in `min3_echo1.hell` already shows the way (one byte per iteration). The missing piece is a loop that writes them into consecutive cells.

## Next concrete step (lowest risk)

Dispatch is fully done (18 opcodes, generated, 21/21). A partial operand path
now passes 4/4, but it is not yet a stack or stream loop. The next milestone is
to separate the two operations with a one-deep stack:

```
read opcode B
B==0x00 HALT                  (this is exactly what dispatch already does)
B==0x01 PUSH_CONST: read operand byte O, store O in stack cell, loop
B==0x10 OUT_BYTE:   recover stack cell, OUT it, loop
EOF      HALT
```

Key new pieces vs the current classifier: (1) a fetch LOOP that re-reads the
next opcode (needs per-iteration reset of value/value_C1/save cells back to C1),
(2) reading an operand inside a handler, and (3) preserving that operand in a
real stack cell until the separate `OUT_BYTE` handler. The combined
`byte_push_const_out.hell` probe is not evidence for separate stack semantics.
The proven `min3_echo1.hell` cell route is the implementation basis: duplicate
its tmp2/tmp4 copy/recovery path into a dedicated `stack_top` cell instead of
reusing `save_B`, whose dispatch continuation is not safely reusable.

## Toolchain traps (measured 2026-09-11, all on runners/malbolge-original)

- **LMAO `-f` layout is runner-flaky, layout-dependent.** `-f` builds of
  `byte_dispatch0_v2` / `dec_microA` / `byte_dispatch1` assemble rc=0 and run
  CORRECTLY on oracle_classic, but the C runner halts early with empty output
  (byte_dispatch1-fast: fixed 13038 steps for every input; microA-fast: 3193).
  Other `-f` builds (baseline `byte_branch_wip`, `byte_dispatch0_v1`,
  `example_simple_hello_world`) agree on both engines. Rule: verify dispatch
  work on NORMAL-layout builds on both engines; treat any `-f`-only result as
  suspect until both engines agree. `vm_malbolge/tests/buildrun.py` uses `-f`
  — do not trust a runner FAIL from it alone for these programs.
- **`ROT X` loads `rotr(X)`, not `X`.** Only C0/C1/C2 are rotation-symmetric.
  Constant loads need pre-rotated form `ROT (c << 1)`. Cost us one full debug
  cycle (standalone `ROT 'Z'` printed garbage).
- **No `R_*` restores between subroutine return and flag-branch.**
  digital_root branches IMMEDIATELY on `return_from_*`; our extra
  `R_CRAZY R_MOVED` desynchronized shared CODE phases (standalone dec(0)
  broke, dec(1) passed by luck).
- **Multi-site subroutine exit needs a trailing `R_SUBROUTINE_FLAGn` on every
  non-last site.** The decrement exit `SUBROUTINE_FLAG1 ret1 / SUBROUTINE_FLAG2
  ret2 / SUBROUTINE_FLAG3 ret3` (all 2-token) HANGS on the 3rd-site call; the
  increment two-site form `SUBROUTINE_FLAG1 ret1 R_SUBROUTINE_FLAG1 /
  SUBROUTINE_FLAG2 ret2` is the correct shape. (2 sites happened to work
  without the trailing R — the 3rd exposed the requirement.)

## Golden rule (same)

No commits that claim demonstrated = yes unless the probe output saved as evidence shows the actual correctness on the runner.
