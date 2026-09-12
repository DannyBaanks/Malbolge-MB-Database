"""MBIR — shared semantic runtime contract package."""

from . import mbir
from .mbir import (
    MBIR_VERSION,
    HALT, PUSH_CONST, POP, DUP, LOAD_LOCAL, STORE_LOCAL,
    ADD, SUB, MUL, CMP_EQ, CMP_LT, CMP_GT,
    JUMP, JUMP_IF_FALSE, CALL, RETURN, OUT_BYTE, IN_BYTE,
    OPERANDS, MNEMONICS, operand_width,
    MBIRDecodeError, encode, decode, validate, instruction_boundaries,
)
from .mbir_ref import MBIRRefVM, MBIRError, source_hash

__all__ = [
    "mbir", "MBIRRefVM", "MBIRError", "source_hash", "MBIR_VERSION",
    "HALT", "PUSH_CONST", "POP", "DUP", "LOAD_LOCAL", "STORE_LOCAL",
    "ADD", "SUB", "MUL", "CMP_EQ", "CMP_LT", "CMP_GT", "JUMP",
    "JUMP_IF_FALSE", "CALL", "RETURN", "OUT_BYTE", "IN_BYTE",
    "OPERANDS", "MNEMONICS", "operand_width",
    "MBIRDecodeError", "encode", "decode", "validate",
    "instruction_boundaries",
]
