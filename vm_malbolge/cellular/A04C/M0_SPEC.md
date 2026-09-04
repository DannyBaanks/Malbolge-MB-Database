# A04C — CELLULAR_MBIR_M0 specification

## MBIR_BYTES for M0.v0

The frozen MBIR bytecode contract defines:

| Opcode | Encoding | Mnemonic |
|--------|----------|----------|
| 0x00   | single byte | HALT |
| 0x01 + u8 | 2 bytes | PUSH_CONST <u8> |
| 0x10   | single byte | OUT_BYTE |

Source of truth: `mbir/mbir.py` and `docs/MBIR_CONTRACT.md` (MBIR_VERSION = 0).

## Microprogram M0.v0

Bytes in order (hex):

```
01 41  10  00
```

Meaning:

```
PUSH_CONST 0x41  ; push 65
OUT_BYTE        ; pop and emit as byte
HALT
```

Expected reference output (MBIR reference VM `mbir_ref.py`): byte 65 ->
stdout "A" then HALT.

## Control / reference target

Oracle: `tools/oracle_classic.py` is the Malbolge reference oracle for
Classic variant; the MBIR reference is `mbir/mbir_ref.py` (MBIRRefVM).

Comparator: run `python -m` style:

```
py -c "import sys; sys.path.insert(0, 'mbir'); import mbir, mbir_ref; \
      blob = bytes([1, 65, 16, 0]); vm = mbir_ref.MBIRRefVM().load(blob); \
      r = vm.run(); print(r['output_bytes'], r['status'])"
```

Expected: `[65] HALTED`.

## What M0 signally locks in

- Single "value 65" case — chosen because it emits the printable 'A'.
- No CALL, no loops, no arithmetic (unlike A03 range tests, the goal is
  stability and replay, not richness).

Follow-ons:
- M0.1 = PUSH_CONST 0x42 OUT HALT ('B').
- M0.2 = PUSH_CONST 0 (HALT zero program edge case).
- M0.3 = held-out constant selected deterministically.
