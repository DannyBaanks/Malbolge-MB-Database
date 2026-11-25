#!/usr/bin/env python3
"""B2T0 -- a strict binary-to-ternary cell codec for 10-trit Malbolge cells.

The codec packs a byte stream into 15-bit groups.  Because

    2**15 = 32768 < 59049 = 3**10

every 15-bit group fits in one 10-trit cell.  The cell value is the integer
value of the group; its trits are the base-3 digits of that integer.  This is
a transport codec, not a Malbolge interpreter and not an IR.

Container format (little-endian):

    magic       4 bytes   b"B2T0"
    version     1 byte    0
    flags       1 byte    0
    bit_length  8 bytes   original bit length (multiple of 8 for byte input)
    word_count  4 bytes   number of 10-trit cells
    crc32       4 bytes   CRC-32 of the original byte stream
    payload     word_count * 2 bytes, each cell value as uint16

Only cell values 0..32767 are valid payload.  Values 32768..59048 are
reserved for a future escape/control space and are rejected by this version.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

MAGIC = b"B2T0"
VERSION = 0
HEADER = struct.Struct("<4sBBQII")
CHUNK_BITS = 15
CHUNK_LIMIT = 1 << CHUNK_BITS  # 32768
CELL_TRITS = 10
CELL_BASE = 3**CELL_TRITS  # 59049
RESERVED_FROM = CHUNK_LIMIT


class B2TError(ValueError):
    """Raised when a container or cell is not canonical B2T0."""


@dataclass(frozen=True)
class Encoded:
    """Result of encoding a byte stream."""

    data: bytes
    bit_length: int
    words: tuple[int, ...]
    container: bytes

    @property
    def cells(self) -> tuple[int, ...]:
        return self.words

    def trits(self) -> tuple[tuple[int, ...], ...]:
        return tuple(word_to_trits(word) for word in self.words)


def bits_from_bytes(data: bytes) -> list[int]:
    """Return bits in stream order, most-significant bit of each byte first."""
    bits: list[int] = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def bytes_from_bits(bits: Sequence[int]) -> bytes:
    """Inverse of bits_from_bytes.  Requires a whole number of bytes."""
    if len(bits) % 8:
        raise B2TError("bit length must be a multiple of 8")
    out = bytearray()
    for offset in range(0, len(bits), 8):
        value = 0
        for bit in bits[offset : offset + 8]:
            if bit not in (0, 1):
                raise B2TError("bit stream contains a non-bit value")
            value = (value << 1) | bit
        out.append(value)
    return bytes(out)


def pack_bits(bits: Sequence[int]) -> tuple[tuple[int, ...], int]:
    """Pack bits into 15-bit cells.  Returns (cells, padding_bits)."""
    for bit in bits:
        if bit not in (0, 1):
            raise B2TError("bit stream contains a non-bit value")
    padding = (-len(bits)) % CHUNK_BITS
    padded = list(bits) + [0] * padding
    words: list[int] = []
    for offset in range(0, len(padded), CHUNK_BITS):
        value = 0
        for bit in padded[offset : offset + CHUNK_BITS]:
            value = (value << 1) | bit
        if value >= CHUNK_LIMIT:
            raise B2TError("internal error: 15-bit chunk exceeded its limit")
        words.append(value)
    return tuple(words), padding


def unpack_bits(words: Sequence[int], bit_length: int) -> list[int]:
    """Unpack 10-trit cells back into exactly bit_length bits."""
    if bit_length < 0:
        raise B2TError("negative bit length")
    total_bits = len(words) * CHUNK_BITS
    if bit_length > total_bits:
        raise B2TError("bit length exceeds the cell payload")
    if total_bits - bit_length >= CHUNK_BITS:
        raise B2TError("payload contains an extra cell")
    expected_words = (bit_length + CHUNK_BITS - 1) // CHUNK_BITS
    if len(words) != expected_words:
        raise B2TError(
            f"word count {len(words)} is not canonical for {bit_length} bits"
        )

    padding = total_bits - bit_length
    bits: list[int] = []
    for index, word in enumerate(words):
        if not isinstance(word, int) or word < 0:
            raise B2TError("cell value must be a non-negative integer")
        if word >= CELL_BASE:
            raise B2TError(f"cell value {word} is outside the 10-trit space")
        if word >= RESERVED_FROM:
            raise B2TError(
                f"cell value {word} is reserved (valid payload is 0..32767)"
            )
        if index == len(words) - 1 and padding:
            mask = (1 << padding) - 1
            if word & mask:
                raise B2TError("padding bits are not zero")
        bits.extend((word >> shift) & 1 for shift in range(CHUNK_BITS - 1, -1, -1))
    return bits[:bit_length]


def encode_bytes(data: bytes) -> Encoded:
    """Encode bytes into a canonical B2T0 container."""
    bit_length = len(data) * 8
    words, _padding = pack_bits(bits_from_bytes(data))
    payload = b"".join(struct.pack("<H", word) for word in words)
    header = HEADER.pack(
        MAGIC,
        VERSION,
        0,
        bit_length,
        len(words),
        zlib.crc32(data) & 0xFFFFFFFF,
    )
    return Encoded(
        data=data,
        bit_length=bit_length,
        words=words,
        container=header + payload,
    )


def decode_container(container: bytes) -> bytes:
    """Decode a canonical B2T0 container and verify its CRC."""
    if len(container) < HEADER.size:
        raise B2TError("container is shorter than the header")
    magic, version, flags, bit_length, word_count, crc = HEADER.unpack_from(container)
    if magic != MAGIC:
        raise B2TError(f"bad magic {magic!r}")
    if version != VERSION:
        raise B2TError(f"unsupported version {version}")
    if flags != 0:
        raise B2TError(f"unsupported flags 0x{flags:02x}")
    if bit_length % 8:
        raise B2TError("B2T0 byte containers require a multiple-of-8 bit length")
    if word_count != (bit_length + CHUNK_BITS - 1) // CHUNK_BITS:
        raise B2TError("non-canonical word count")
    expected_length = HEADER.size + word_count * 2
    if len(container) != expected_length:
        raise B2TError(
            f"container length {len(container)} != expected {expected_length}"
        )
    words = tuple(
        struct.unpack_from("<H", container, HEADER.size + 2 * index)[0]
        for index in range(word_count)
    )
    bits = unpack_bits(words, bit_length)
    data = bytes_from_bits(bits)
    actual_crc = zlib.crc32(data) & 0xFFFFFFFF
    if actual_crc != crc:
        raise B2TError(
            f"CRC mismatch: header 0x{crc:08x}, decoded 0x{actual_crc:08x}"
        )
    return data


def word_to_trits(word: int) -> tuple[int, ...]:
    """Return the 10 trits of a cell, least-significant trit first."""
    if not isinstance(word, int) or not 0 <= word < CELL_BASE:
        raise B2TError(f"cell value {word!r} is outside 0..59048")
    return tuple((word // (3**index)) % 3 for index in range(CELL_TRITS))


def trits_to_word(trits: Sequence[int]) -> int:
    """Convert 10 trits (least-significant first) into a cell value."""
    if len(trits) != CELL_TRITS:
        raise B2TError(f"expected {CELL_TRITS} trits, got {len(trits)}")
    word = 0
    for index, trit in enumerate(trits):
        if trit not in (0, 1, 2):
            raise B2TError(f"invalid trit {trit!r} at position {index}")
        word += trit * (3**index)
    return word


def encode_file(input_path: Path, output_path: Path) -> Encoded:
    encoded = encode_bytes(input_path.read_bytes())
    output_path.write_bytes(encoded.container)
    return encoded


def decode_file(input_path: Path, output_path: Path) -> bytes:
    data = decode_container(input_path.read_bytes())
    output_path.write_bytes(data)
    return data


def inspect_container(container: bytes) -> dict[str, object]:
    """Return a JSON-friendly description of a canonical container."""
    data = decode_container(container)
    _, _version, _flags, bit_length, word_count, crc = HEADER.unpack_from(container)
    words = tuple(
        struct.unpack_from("<H", container, HEADER.size + 2 * index)[0]
        for index in range(word_count)
    )
    return {
        "format": MAGIC.decode("ascii"),
        "version": VERSION,
        "bit_length": bit_length,
        "byte_length": len(data),
        "word_count": word_count,
        "crc32": f"0x{crc:08x}",
        "sha256": hashlib.sha256(data).hexdigest(),
        "cells": list(words),
        "trits": [list(word_to_trits(word)) for word in words],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b2t",
        description="B2T0: pack bytes into 10-trit Malbolge cells and back.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    encode = sub.add_parser("encode", help="encode a file into a .b2t container")
    encode.add_argument("input", type=Path)
    encode.add_argument("-o", "--output", type=Path)
    encode.add_argument(
        "--cells",
        action="store_true",
        help="also print the cell values (comma-separated)",
    )

    decode = sub.add_parser("decode", help="decode a .b2t container into bytes")
    decode.add_argument("input", type=Path)
    decode.add_argument("-o", "--output", type=Path)

    inspect = sub.add_parser("inspect", help="show container metadata and cells")
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--json", action="store_true", help="print JSON")

    return parser


def _default_encoded_path(path: Path) -> Path:
    return path.with_name(path.name + ".b2t")


def _default_decoded_path(path: Path) -> Path:
    if path.suffix == ".b2t":
        return path.with_suffix("")
    return path.with_name(path.name + ".decoded")


def _cmd_encode(args: argparse.Namespace) -> int:
    output = args.output or _default_encoded_path(args.input)
    encoded = encode_file(args.input, output)
    print(
        f"encoded {args.input} -> {output} "
        f"({len(encoded.data)} bytes, {encoded.bit_length} bits, "
        f"{len(encoded.words)} cells)"
    )
    if args.cells:
        print(",".join(str(word) for word in encoded.words))
    return 0


def _cmd_decode(args: argparse.Namespace) -> int:
    output = args.output or _default_decoded_path(args.input)
    data = decode_file(args.input, output)
    print(f"decoded {args.input} -> {output} ({len(data)} bytes)")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    report = inspect_container(args.input.read_bytes())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"format={report['format']} version={report['version']}")
        print(
            f"bytes={report['byte_length']} bits={report['bit_length']} "
            f"cells={report['word_count']} crc32={report['crc32']}"
        )
        print(f"sha256={report['sha256']}")
        print("cells=" + ",".join(str(cell) for cell in report["cells"]))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "encode":
            return _cmd_encode(args)
        if args.command == "decode":
            return _cmd_decode(args)
        if args.command == "inspect":
            return _cmd_inspect(args)
    except (B2TError, OSError) as exc:
        print(f"b2t: error: {exc}", file=sys.stderr)
        return 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
