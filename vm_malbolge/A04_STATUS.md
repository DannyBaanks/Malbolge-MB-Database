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

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Full MBIR VM in Malbolge | conditional dispatch of an opcode byte needs an N-entry table. DONE for 3 handlers (0x00→HALT, 0x01→`P` marker, else→echo, `byte_dispatch2.hell`); the full 18-opcode MBIR dispatch (HALT/PUSH_CONST/OUT_BYTE/…) still requires chaining a discriminator per opcode — one decrement + one `SUBROUTINE_FLAGn` site each. |
| MBIR→HeLL code generator | `vm_malbolge/tools/mbir_gen.py` was rewritten 3 times in-session and still produces malformed HeLL; dropped, not committed. |

## Blockers to unblock next

1. **Byte-dispatch table.** DONE 2026-09-11: 3 handlers chain (0x00→HALT, 0x01→`P`, else→echo) in `byte_dispatch2.hell`. Pattern per opcode: one increment/decrement + one `SUBROUTINE_FLAGn` site, with trailing `R_SUBROUTINE_FLAGn` restore on non-last exit sites. Next: real handler for 0x01 (PUSH_CONST) instead of the `P` marker, then a 4th opcode.
2. **MBIR program from stdin.** MBIR bytecode lives in Malbolge data cells, copied from stdin. The batch-input idiom in `min3_echo1.hell` already shows the way (one byte per iteration). The missing piece is a loop that writes them into consecutive cells.

## Next concrete step (lowest risk)

3-way dispatch DONE 2026-09-11 (`byte_dispatch2.hell`). Next:

```
read byte B
if B == 0x00 → HALT                 (done)
if B == 0x01 → OUT 'P' marker       (done; replace marker with real PUSH_CONST handler)
else        → echo B                (done)
```

Chain another opcode (e.g. `0x10` per MBIR contract) the same way: one
decrement (B-2 … B-k) + one `SUBROUTINE_FLAGn` site, trailing
`R_SUBROUTINE_FLAGn` on non-last exit sites.

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
