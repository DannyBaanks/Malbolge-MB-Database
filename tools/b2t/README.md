# B2T0 — Binary ⇄ ternary cell codec

`b2t.py` packs any byte stream into **10-trit cells** and back, with zero loss.

## Why it works

A Malbolge cell holds values `0..59048` (`3^10`).  
A 15-bit group holds values `0..32767` (`2^15`).

Because `2^15 < 3^10`, every 15-bit group fits in one cell:

```text
bits (15) ──► integer 0..32767 ──► cell value 0..59048
```

The cell value is the integer itself; its trits are that integer in base 3.

## Format

The container is a flat binary file:

```text
magic       4 bytes   b"B2T0"
version     1 byte    0
flags       1 byte    0
bit_length  8 bytes   little-endian uint64
word_count  4 bytes   little-endian uint32
crc32       4 bytes   little-endian uint32
payload     word_count * 2 bytes, each cell value as uint16
```

Only cell values `0..32767` are valid payload.  
Values `32768..59048` are **reserved** for a future escape/control layer and are rejected.

## Usage

```bash
# Encode
python3 b2t.py encode input.bin -o input.b2t

# Decode
python3 b2t.py decode input.b2t -o input.restored

# Inspect
python3 b2t.py inspect input.b2t
```

`decode` and `inspect` verify the container’s CRC before returning any data;
`encode` computes and writes it.

## Example

```text
input  = 01020103061000                       # 7 bytes
bits   = 56
cells  = 4
output = 0x05                                 # decoded by mbir_ref
```

## Limitations

- This codec does **not** execute Malbolge.
- It does **not** make data cells valid Malbolge opcodes.
- It adds no compression, no error correction, and no built-in executable meaning.
- Same as MAL-E02: a strict loader like `mb_ref` may reject the resulting data cells because it requires every source cell to encode a valid opcode.

## What this is for

This is the transport layer:

```text
bytes ─► bits ─► 10-trit cells ─► bits ─► bytes
```

It does not decide what those bits mean.  
That belongs to a **dispatcher** or a specific runtime, not to the codec.
