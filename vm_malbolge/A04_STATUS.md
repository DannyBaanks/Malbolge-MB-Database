# A04 — Current Status (verbatim, no polish)

## What is demonstrated

| item | evidence |
|---|---|
| MBIR contract frozen (v0) | `docs/MBIR_CONTRACT.md`, 18 opcodes, tested by 23/23 (`mbir/tests/test_mbir.py`) + 28/28 (`mbir/tests/test_mbir_ref.py`) |
| MBIR reference VM works silently on `python.exe` | `mbir/mbir_ref.py` runs fib(6), branches, calls, I/O |
| LMAO v0.6.0 builds Malbolge from HeLL | `tools/build_lmao.ps1` + `third_party/lmao/` — Hello World assembles and runs |
| Byte echo works on the REAL malbolge.exe | `vm_malbolge/src/min3_echo1.hell` → hex41 → hex41, 25991 steps, verified |
| Primitive byte transport is provable | host never computes contents; only the Malbolge CPU does |
| Cellular substrate proves selectability | `vm_malbolge/cellular/A04C/evidence/` (private tree, transport + gate + holdout) |
| Conditional branch EOF-vs-not-EOF (via value-jump to C20/C21) | `vm_malbolge/src/byte_branch_wip.hell` + `vm_malbolge/evidence/byte_branch_{A,eof}.json` — same artifact, two distinct control paths via jump-on-value **only** for the EOF sentinel. All N byte values take the same (echo) path — see `byte_branch_smoke.json`. |
| Byte-VALUE dispatch 0x00-vs-nonzero (digital_root decrement idiom, single carry pad) | `vm_malbolge/src/byte_dispatch1.hell` + `vm_malbolge/evidence/byte_dispatch1_{00,A,eof,smoke}.json` — 12/12 OK on oracle_classic AND runners/malbolge-original (normal LMAO layout): 0x00→HALT empty (28078 steps), 10 nonzero values→verbatim echo (e.g. 0x41→`A`, 26789 steps), EOF→empty. Distinct paths AND distinct outputs per value class. Built only from verbatim digital_root idioms (ENTRY copy, inc/dec, flag-branch, print recover) + dual decrement exit (increment two-site pattern). |
| 3-way byte-VALUE dispatch (0x00 / 0x01 / other) | `vm_malbolge/src/byte_dispatch2.hell` + `vm_malbolge/evidence/byte_dispatch2_{01,smoke}.json` — 12/12 OK on oracle AND runner: 0x00→empty (29033 steps), 0x01→`P` marker (29525 steps), other nonzero→echo (e.g. 0x41→`A`, 28230 steps), EOF→empty. Three distinct value classes, three paths, three outputs. Reuses dispatch1 pipeline + a 3rd decrement site. **Key idiom fix:** a multi-site subroutine exit needs a trailing `R_SUBROUTINE_FLAGn` on every non-last site (increment two-site pattern); without it the 3rd site hangs. |
| Full 18-opcode MBIR dispatch (generated) | `vm_malbolge/tools/mbir_dispatch_gen.py` → `vm_malbolge/src/byte_dispatch18.hell` + `vm_malbolge/evidence/byte_dispatch18_smoke.json` — 21/21 OK on oracle AND runner: every MBIR_VERSION 0 opcode byte 0x00..0x11 takes a distinct handler (0x00 HALT; 0x01..0x11 → marker bytes; non-opcode → echo; EOF → empty). The dispatch is now generated mechanically (parameterized decrement-chain + N `SUBROUTINE_FLAGn` sites), not hand-written. This resolves the "byte-dispatch table" blocker at the classifier level. |

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Full MBIR VM in Malbolge | dispatch (classification) is DONE for all 18 opcodes as marker handlers. What remains is SEMANTIC EXECUTION: operand reading (PUSH_CONST/LOAD_LOCAL/…), a value stack, arithmetic (ADD/SUB/MUL/CMP), control flow (JUMP/JUMP_IF_FALSE/CALL/RETURN), and a fetch-loop over a multi-byte program. Each of these is a real handler replacing the marker, plus a stdin→cells loader. |
| MBIR→HeLL code generator | for instructions: the dispatch *skeleton* generator now exists (`vm_malbolge/tools/mbir_dispatch_gen.py`, verified). A full MBIR-program → HeLL generator (loader + real handlers lowering through MBIR) is still open. |

## Blockers to unblock next

1. **Byte-dispatch table.** DONE 2026-09-11: full 18-opcode table generated (`mbir_dispatch_gen.py` → `byte_dispatch18.hell`, 21/21). Each opcode = one decrement + one `SUBROUTINE_FLAGn` site, trailing `R_SUBROUTINE_FLAGn` on non-last exit sites.
2. **MBIR program from stdin.** MBIR bytecode lives in Malbolge data cells, copied from stdin. The batch-input idiom in `min3_echo1.hell` already shows the way (one byte per iteration). The missing piece is a loop that writes them into consecutive cells.

## Next concrete step (lowest risk)

Dispatch is fully done (18 opcodes, generated, 21/21). Next milestone is a
REAL semantic handler — the smallest honest increment is a 1-deep-stack
`PUSH_CONST … OUT_BYTE` pair in a stream loop:

```
read opcode B
B==0x00 HALT                  (this is exactly what dispatch already does)
B==0x01 PUSH_CONST: read operand byte O, store O in stack cell, loop
B==0x10 OUT_BYTE:   recover stack cell, OUT it, loop
EOF      HALT
```

Key new pieces vs the current classifier: (1) a fetch LOOP that re-reads the
next opcode (needs per-iteration reset of value/value_C1/save cells back to C1
— digital_root's `restore_initial_state` idiom), and (2) reading an operand
byte inside a handler. Both are small lifts from proven idioms; neither is yet
demonstrated. The `P`/`O` markers in `byte_dispatch18.hell` are the placeholders
these replace.

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
