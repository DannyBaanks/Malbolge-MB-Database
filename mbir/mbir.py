"""
MBIR — Shared Semantic Runtime Contract, MBIR_VERSION 0.

Provides:
- instruction encoding/decoding (the frozen binary contract),
- a validation/disassembly pass (instruction boundaries, operand widths,
  jump targets),
- the mnemonic table with stack/state/error effects.

This module defines the CONTRACT. It does NOT execute MBIR; execution is the
reference VM (A03) and, later, the Malbolge-hosted runtime (A04).

Numeric model (frozen): unsigned 8-bit modular arithmetic mod 256.
"""
from __future__ import annotations

MBIR_VERSION = 0

# Opcodes
HALT = 0x00
PUSH_CONST = 0x01
POP = 0x02
DUP = 0x03
LOAD_LOCAL = 0x04
STORE_LOCAL = 0x05
ADD = 0x06
SUB = 0x07
MUL = 0x08
CMP_EQ = 0x09
CMP_LT = 0x0A
CMP_GT = 0x0B
JUMP = 0x0C
JUMP_IF_FALSE = 0x0D
CALL = 0x0E
RETURN = 0x0F
OUT_BYTE = 0x10
IN_BYTE = 0x11

MNEMONICS = {
    HALT: "HALT",
    PUSH_CONST: "PUSH_CONST",
    POP: "POP",
    DUP: "DUP",
    LOAD_LOCAL: "LOAD_LOCAL",
    STORE_LOCAL: "STORE_LOCAL",
    ADD: "ADD",
    SUB: "SUB",
    MUL: "MUL",
    CMP_EQ: "CMP_EQ",
    CMP_LT: "CMP_LT",
    CMP_GT: "CMP_GT",
    JUMP: "JUMP",
    JUMP_IF_FALSE: "JUMP_IF_FALSE",
    CALL: "CALL",
    RETURN: "RETURN",
    OUT_BYTE: "OUT_BYTE",
    IN_BYTE: "IN_BYTE",
}

# operand spec: ("u8"|"u24"|"u8,u8"|None)
OPERANDS = {
    HALT: None,
    PUSH_CONST: "u8",
    POP: None,
    DUP: None,
    LOAD_LOCAL: "u8",
    STORE_LOCAL: "u8",
    ADD: None,
    SUB: None,
    MUL: None,
    CMP_EQ: None,
    CMP_LT: None,
    CMP_GT: None,
    JUMP: "u24",
    JUMP_IF_FALSE: "u24",
    CALL: "u8,u8",
    RETURN: None,
    OUT_BYTE: None,
    IN_BYTE: None,
}


def operand_width(spec) -> int:
    if spec is None:
        return 0
    n = 0
    for part in spec.split(","):
        if part == "u8":
            n += 1
        elif part == "u24":
            n += 3
        else:
            raise ValueError("unknown operand spec: %s" % part)
    return n


def encode_instruction(opcode: int, operands) -> bytes:
    """Encode a single instruction into MBIR bytes."""
    spec = OPERANDS.get(opcode)
    if spec is None and opcode not in OPERANDS:
        raise ValueError("unknown opcode: 0x%02X" % opcode)
    out = bytearray([opcode])
    if spec is not None:
        parts = spec.split(",")
        if len(parts) == 1 and parts[0] == "u8":
            if not isinstance(operands, int):
                raise TypeError("u8 operand expected int, got %r" % (operands,))
            if not (0 <= operands <= 0xFF):
                raise ValueError("u8 operand out of range: %s" % operands)
            out.append(operands)
        elif len(parts) == 1 and parts[0] == "u24":
            if not isinstance(operands, int):
                raise TypeError("u24 operand expected int, got %r" % (operands,))
            if not (0 <= operands <= 0xFFFFFF):
                raise ValueError("u24 operand out of range: %s" % operands)
            out += operands.to_bytes(3, "little")
        elif len(parts) == 2:
            a, b = operands
            for v in (a, b):
                if not isinstance(v, int) or not (0 <= v <= 0xFF):
                    raise ValueError("u8 operand out of range: %r" % (v,))
            out.append(a)
            out.append(b)
        else:
            raise ValueError("unsupported spec: %s" % spec)
    return bytes(out)


def encode(instructions) -> bytes:
    """Encode a list of (opcode, operands) tuples into a single MBIR blob."""
    out = bytearray()
    for opcode, operands in instructions:
        out += encode_instruction(opcode, operands)
    return bytes(out)


def decode(blob: bytes):
    """Decode a MBIR blob into a list of (mnemonic, operands, offset).

    Raises MBIRDecodeError on malformed bytecode.
    """
    instrs = []
    i = 0
    n = len(blob)
    while i < n:
        start = i
        opcode = blob[i]
        i += 1
        if opcode not in OPERANDS:
            raise MBIRDecodeError("BAD_OPCODE: 0x%02X at offset %d" % (opcode, start))
        spec = OPERANDS[opcode]
        mnemonic = MNEMONICS[opcode]
        width = operand_width(spec)
        if i + width > n:
            raise MBIRDecodeError("BAD_OPERAND: %s at offset %d truncated (need %d bytes)" % (mnemonic, start, width))
        raw = blob[i:i + width]
        i += width
        if spec is None:
            operands = ()
        elif spec == "u8":
            operands = raw[0]
        elif spec == "u24":
            operands = int.from_bytes(raw, "little")
        elif spec == "u8,u8":
            operands = (raw[0], raw[1])
        else:
            raise MBIRDecodeError("BAD_OPERAND: unsupported spec %s" % spec)
        instrs.append((mnemonic, operands, start))
    return instrs


def instruction_boundaries(blob: bytes) -> list:
    """Return the set of byte offsets that are opcode starts (valid jump targets)."""
    return [d[2] for d in decode(blob)]


def validate(blob: bytes):
    """Validate a MBIR blob. Returns the decoded instruction list.

    Raises MBIRDecodeError if structurally malformed. Jump/call target
    validity is checked by the executing VM (A03), since it needs frame state.
    """
    return decode(blob)


class MBIRDecodeError(Exception):
    pass