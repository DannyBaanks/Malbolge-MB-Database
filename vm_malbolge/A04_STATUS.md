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
| Conditional branch on input byte (EOF-routed) | `vm_malbolge/src/byte_branch_wip.hell` + `vm_malbolge/evidence/byte_branch_{A,eof}.json` — same artifact, two distinct control paths via jump-on-value |

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Full MBIR VM in Malbolge | conditional dispatch of an opcode byte requires a `Jmp [+value]` idiom from 0..255; not yet assembled. |
| MBIR→HeLL code generator | `vm_malbolge/tools/mbir_gen.py` was rewritten 3 times in-session and still produces malformed HeLL; dropped, not committed. |

## Blockers to unblock next

1. **Byte-dispatch table.** Next after EOF-detection: split `tmp4_was_C21`/`tmp4_was_C20` into N handlers keyed by byte value. Requires `Jmp [+value]` idiom from `example_digital_root.hell`. First case: `B == 0x10`、`B == 0x01`、`B == 0x00` (HALT/PUSH_CONST/OUT_BYTE del MBIR contract).
2. **MBIR program from stdin.** MBIR bytecode lives in Malbolge data cells, copied from stdin. The batch-input idiom from the cat program already shows that reading bytes works; the missing piece is storing them into addressed cells.

## Next concrete step (lowest risk)

Extend `byte_branch_wip.hell` using the `tmp4_was_C21/jump-table` machinery:

```
read byte B
if B == 0x00 → HALT
else        → print B ('A' or 'N' depending on value)
```

Currently the WIP distinguishes only EOF vs non-EOF. The next milestone is distinguishing N numeric values.

## Golden rule (same)

No commits that claim demonstrated = yes unless the probe output saved as evidence shows the actual correctness on the runner.
