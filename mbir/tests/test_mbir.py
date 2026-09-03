"""
MBIR CONTRACT conformance tests (A02).

Covers the frozen binary contract:
- every opcode encodes/decodes with correct operand width,
- positive fixtures round-trip,
- negative structural cases (bad opcode, truncated operand, operand range,
  non-aligned jump target detection).

VM execution semantics (underflow, bad target at runtime, bad slot, no-frame
RETURN) belong to the A03 reference VM conformance, not the static contract.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mbir
from mbir import (
    MBIR_VERSION,
    HALT, PUSH_CONST, POP, DUP, LOAD_LOCAL, STORE_LOCAL,
    ADD, SUB, MUL, CMP_EQ, CMP_LT, CMP_GT,
    JUMP, JUMP_IF_FALSE, CALL, RETURN, OUT_BYTE, IN_BYTE,
    MBIRDecodeError, encode, decode, validate, instruction_boundaries,
)

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  PASS: " + name)
    else:
        FAIL += 1
        print("  FAIL: " + name + " " + detail)


print("=== MBIR CONTRACT conformance ===\n")

# --- Version ---
check("MBIR_VERSION == 0", MBIR_VERSION == 0, "got %r" % MBIR_VERSION)

# --- Opcode inventory ---
expected_opcodes = [
    HALT, PUSH_CONST, POP, DUP, LOAD_LOCAL, STORE_LOCAL,
    ADD, SUB, MUL, CMP_EQ, CMP_LT, CMP_GT,
    JUMP, JUMP_IF_FALSE, CALL, RETURN, OUT_BYTE, IN_BYTE,
]
check("18 opcodes defined", len(mbir.OPERANDS) == 18, "got %d" % len(mbir.OPERANDS))
check("all expected opcodes present", all(o in mbir.OPERANDS for o in expected_opcodes))

# --- Operand widths ---
check("PUSH_CONST width 1", mbir.operand_width(mbir.OPERANDS[PUSH_CONST]) == 1)
check("JUMP width 3", mbir.operand_width(mbir.OPERANDS[JUMP]) == 3)
check("CALL width 2", mbir.operand_width(mbir.OPERANDS[CALL]) == 2)
check("HALT width 0", mbir.operand_width(mbir.OPERANDS[HALT]) == 0)

# --- Round-trip fixtures ---
def roundtrip(name, instrs):
    blob = encode(instrs)
    dec = decode(blob)
    # compare mnemonic + operands (ignore offsets)
    want = [(m, o) for (m, o, _) in dec]
    ok = True
    for (m, o, _), (wm, wo) in zip(dec, instrs):
        m_name = mbir.MNEMONICS[wm]
        if m != m_name or o != wo:
            ok = False
    check("roundtrip " + name, ok, "dec=%r" % (dec,))

roundtrip("2+3 print", [
    (PUSH_CONST, 2), (PUSH_CONST, 3), (ADD, ()), (OUT_BYTE, ()), (HALT, ()),
])
roundtrip("sub+mul", [
    (PUSH_CONST, 10), (PUSH_CONST, 4), (SUB, ()),
    (PUSH_CONST, 3), (MUL, ()), (OUT_BYTE, ()), (HALT, ()),
])
roundtrip("cmp+jump", [
    (PUSH_CONST, 5), (PUSH_CONST, 3), (CMP_GT, ()),
    (JUMP_IF_FALSE, 12), (PUSH_CONST, 7), (OUT_BYTE, ()), (HALT, ()),
])
roundtrip("locals+dup", [
    (PUSH_CONST, 9), (STORE_LOCAL, 0), (LOAD_LOCAL, 0), (DUP, ()),
    (ADD, ()), (OUT_BYTE, ()), (HALT, ()),
])
roundtrip("call+return", [
    (CALL, (8, 2)), (HALT, ()),
    (LOAD_LOCAL, 0), (LOAD_LOCAL, 1), (ADD, ()), (RETURN, ()),
])
roundtrip("io", [
    (IN_BYTE, ()), (OUT_BYTE, ()), (HALT, ()),
])

# --- Jump target boundary detection ---
blob = encode([(PUSH_CONST, 5), (PUSH_CONST, 3), (CMP_GT, ()), (JUMP_IF_FALSE, 9), (PUSH_CONST, 7), (OUT_BYTE, ()), (HALT, ())])
bounds = instruction_boundaries(blob)
check("boundaries found", bounds == [0, 2, 4, 5, 9, 11, 12], "got %r" % bounds)
check("jump target 9 is an instruction boundary", 9 in bounds)

# --- Negative structural cases ---
def expect_decode_error(name, blob, fragment):
    try:
        decode(blob)
        check(name, False, "did not raise")
    except MBIRDecodeError as e:
        check(name, fragment in str(e), "got %r" % (str(e),))

expect_decode_error("bad opcode 0xFF", bytes([0xFF]), "BAD_OPCODE")
expect_decode_error("bad opcode 0x12 (unassigned)", bytes([0x12, 0x00]), "BAD_OPCODE")
expect_decode_error("truncated PUSH_CONST (no operand)", bytes([PUSH_CONST]), "BAD_OPERAND")
expect_decode_error("truncated JUMP (only 2 of 3 bytes)", bytes([JUMP, 0x01, 0x02]), "BAD_OPERAND")
expect_decode_error("truncated CALL (only 1 of 2 bytes)", bytes([CALL, 0x05]), "BAD_OPERAND")

# operand range (u24 too large) must raise on encode
def expect_encode_error(name, instr, fragment):
    try:
        encode([instr])
        check(name, False, "did not raise")
    except ValueError as e:
        check(name, fragment in str(e), "got %r" % (str(e),))

expect_encode_error("PUSH_CONST 300 out of u8 range", (PUSH_CONST, 300), "u8 operand out of range")
expect_encode_error("JUMP target beyond u24", (JUMP, 0x1000000), "u24 operand out of range")

# unknown mnemonic
try:
    encode([(0x40, ())])
    check("unknown opcode 0x40 rejected", False, "did not raise")
except ValueError as e:
    check("unknown opcode 0x40 rejected", "unknown opcode" in str(e), str(e))

# --- Summary ---
print("\n" + "=" * 50)
print("MBIR_VERSION = %d" % MBIR_VERSION)
print("PASS: %d   FAIL: %d   TOTAL: %d" % (PASS, FAIL, PASS + FAIL))
print("=" * 50)
if FAIL > 0:
    sys.exit(1)
print("MBIR CONTRACT conformance OK.")
sys.exit(0)