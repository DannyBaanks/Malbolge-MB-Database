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

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Full MBIR VM in Malbolge | conditional dispatch of an opcode byte requires a `Jmp [+value]` idiom; not yet assembled. |
| MBIR→HeLL code generator | `vm_malbolge/tools/mbir_gen.py` produces malformed HeLL (label-block syntax not yet validated); not committed. |

## Blockers to unblock next

1. **The dispatch idiom.** HeLL's `.OFFSET Cx LABEL` + `LABEL: RNop/RNop/Jmp` prefix pattern. First use case: read 1 byte, branch on `byte mod 94` to different handlers. Reference: `example_digital_root.hell` `tmp4` block.
2. **Byte-table lookup.** Needed for `crz` table per opcode handler.
3. **Program memory.** MBIR bytecode must live in Malbolge data cells, addressable by index.
4. **IN/OUT framing.** MBIR programs come from stdin as bytes; output to stdout as bytes.

## Next concrete step (lowest risk)

Reuse the `tmp4` pattern from `example_digital_root.hell` to write `hello_dispatch.hell`:

```
read byte B
if B == 0x00 → HALT
if B == 0x10 → output 'N'
if B == 0x01 → output 0x41
```

If that works → kill the NOT_DEMONSTRATED on "dispatch". Only then code-generate.

## Golden rule (same)

No commits that claim demonstrated = yes unless the probe output saved as evidence shows the actual correctness on the runner.
