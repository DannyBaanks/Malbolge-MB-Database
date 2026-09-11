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

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Full MBIR VM in Malbolge | conditional dispatch of an opcode byte needs an N-entry table. DONE for 2 handlers (0x00→HALT vs nonzero→echo, `byte_dispatch1.hell`); N-opcode dispatch (HALT/PUSH_CONST/OUT_BYTE/…) still requires extending the decrement-branch chain per opcode. |
| MBIR→HeLL code generator | `vm_malbolge/tools/mbir_gen.py` was rewritten 3 times in-session and still produces malformed HeLL; dropped, not committed. |

## Blockers to unblock next

1. **Byte-dispatch table.** DONE first case 2026-09-11: `B == 0x00`→HALT vs else→echo (`byte_dispatch1.hell`, decrement-branch chain, no `Jmp[+value]` needed — one decrement per discriminator). Next: chain a second discriminator (e.g. `B == 0x01`→PUSH_CONST marker) reusing the same shape.
2. **MBIR program from stdin.** MBIR bytecode lives in Malbolge data cells, copied from stdin. The batch-input idiom in `min3_echo1.hell` already shows the way (one byte per iteration). The missing piece is a loop that writes them into consecutive cells.

## Next concrete step (lowest risk)

~~Extend `byte_branch_wip.hell` using the `tmp4_was_C21/jump-table` machinery~~ DONE
2026-09-11 as `byte_dispatch1.hell` (digital_root architecture instead: the
cat-style tmp4 pad and the carry pad cannot share C21 — the second pad user
breaks; digital_root avoids the tmp4 pad entirely via increment-overflow EOF
test). Next: third handler, e.g.

```
read byte B
if B == 0x00 → HALT            (done)
if B == 0x01 → OUT 'P' marker  (next: second decrement-branch on B-1)
else        → echo B           (done)
```

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

## Golden rule (same)

No commits that claim demonstrated = yes unless the probe output saved as evidence shows the actual correctness on the runner.
