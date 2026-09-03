"""
MBIR reference VM conformance tests (A03).

Implements and tests the full MBIR_VERSION 0 semantic model in
mbir/mbir_ref.py, matching docs/MBIR_CONTRACT.md:

- positive fixtures (arith, locals, branch, loop, calls, recursion, io),
- deterministic traces,
- negative cases: stack underflow, bad opcode, bad target, bad slot,
  no-frame RETURN, truncated operand.

A small label-based assembler resolves JUMP/CALL targets so tests read clearly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mbir
import mbir_ref
from mbir import (
    HALT, PUSH_CONST, POP, DUP, LOAD_LOCAL, STORE_LOCAL,
    ADD, SUB, MUL, CMP_EQ, CMP_LT, CMP_GT,
    JUMP, JUMP_IF_FALSE, CALL, RETURN, OUT_BYTE, IN_BYTE,
)
from mbir_ref import MBIRRefVM, MBIRError

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


def asm(program):
    """Assemble a program into MBIR bytes.

    Program is a list where:
      - a bare string           = label at the current offset,
      - (opcode, operands) tuple = an instruction,
    and jump/call operands may be a symbolic label (resolved to absolute offset).
    """
    offsets = {}
    raw = []  # (start_offset, opcode, operands)
    pc = 0
    for item in program:
        if isinstance(item, str):
            offsets[item] = pc
            continue
        op, operands = item
        raw.append((pc, op, operands))
        pc += 1 + mbir.operand_width(mbir.OPERANDS[op])

    def resolve(operands):
        if isinstance(operands, str):
            return offsets[operands]
        if isinstance(operands, tuple):
            return tuple(resolve(o) if isinstance(o, str) else o for o in operands)
        return operands

    out = bytearray()
    for _, op, operands in raw:
        out += mbir.encode_instruction(op, resolve(operands))
    return bytes(out)


def run_prog(program, input_bytes=b"", trace=False):
    blob = asm(program)
    vm = MBIRRefVM(trace=trace).load(blob, input_bytes)
    r = vm.run()
    return r, blob


def expect_error(program, reason, name, input_bytes=b""):
    try:
        run_prog(program, input_bytes)
        check(name, False, "did not raise")
    except MBIRError as e:
        check(name, e.reason == reason, "got reason=%r want=%r" % (e.reason, reason))


print("=== MBIR reference VM conformance ===\n")

# --- 1. Basic arithmetic (modular) ---
r, _ = run_prog([(PUSH_CONST, 200), (PUSH_CONST, 100), (ADD, ()), (OUT_BYTE, ()), (HALT, ())])
check("ADD wraps mod 256 (200+100=44)", r["output"] == chr(44) and r["status"] == "HALTED", repr(r))
r, _ = run_prog([(PUSH_CONST, 5), (PUSH_CONST, 10), (SUB, ()), (OUT_BYTE, ()), (HALT, ())])
check("SUB wraps mod 256 (5-10=251)", r["output_bytes"] == [251], repr(r))
r, _ = run_prog([(PUSH_CONST, 16), (PUSH_CONST, 3), (MUL, ()), (OUT_BYTE, ()), (HALT, ())])
check("MUL (16*3=48)", r["output_bytes"] == [48], repr(r))

# --- 2. Comparisons ---
r, _ = run_prog([(PUSH_CONST, 3), (PUSH_CONST, 5), (CMP_LT, ()), (OUT_BYTE, ()), (HALT, ())])
check("CMP_LT (3<5=1)", r["output_bytes"] == [1])
r, _ = run_prog([(PUSH_CONST, 9), (PUSH_CONST, 9), (CMP_EQ, ()), (OUT_BYTE, ()), (HALT, ())])
check("CMP_EQ (9==9=1)", r["output_bytes"] == [1])
r, _ = run_prog([(PUSH_CONST, 7), (PUSH_CONST, 2), (CMP_GT, ()), (OUT_BYTE, ()), (HALT, ())])
check("CMP_GT (7>2=1)", r["output_bytes"] == [1])

# --- 3. Locals ---
# x = 9; store local 0; load it; duplicate; add; out -> 18
r, _ = run_prog([
    (PUSH_CONST, 9), (STORE_LOCAL, 0), (LOAD_LOCAL, 0), (DUP, ()), (ADD, ()), (OUT_BYTE, ()), (HALT, ()),
])
check("locals + dup (9+9=18)", r["output_bytes"] == [18], repr(r))
# POP discards
r, _ = run_prog([(PUSH_CONST, 1), (PUSH_CONST, 2), (POP, ()), (OUT_BYTE, ()), (HALT, ())])
check("POP (leaves 1)", r["output_bytes"] == [1], repr(r))

# --- 4. Branch behavior ---
# if (5>3) out 7 else out 9
# PUSH 5, PUSH 3, CMP_GT -> 1; JUMP_IF_FALSE T_false; OUT 7; JUMP end; T_false: OUT 9; end: HALT
# We need concrete targets; use asm with two-pass bytecode and a fixed layout.
prog_branch = [
    (PUSH_CONST, 5), (PUSH_CONST, 3), (CMP_GT, ()),
    (JUMP_IF_FALSE, "L_FALSE"),
    (PUSH_CONST, 7), (OUT_BYTE, ()), (JUMP, "L_END"),
    "L_FALSE", (PUSH_CONST, 9), (OUT_BYTE, ()),
    "L_END", (HALT, ()),
]
r, blob = run_prog(prog_branch)
check("branch true -> 7", r["output_bytes"] == [7], repr(r))
# branch false: 1 > 5 false
prog_branch_f = [
    (PUSH_CONST, 1), (PUSH_CONST, 5), (CMP_GT, ()),
    (JUMP_IF_FALSE, "L_FALSE"),
    (PUSH_CONST, 7), (OUT_BYTE, ()), (JUMP, "L_END"),
    "L_FALSE", (PUSH_CONST, 9), (OUT_BYTE, ()),
    "L_END", (HALT, ()),
]
r, _ = run_prog(prog_branch_f)
check("branch false -> 9", r["output_bytes"] == [9], repr(r))

# --- 5. Loop ---
# count: x=0; loop: out x; x=x+1; if x<5 loop; halt  -> outputs 0,1,2,3,4
prog_loop = [
    (PUSH_CONST, 0), (STORE_LOCAL, 0),
    "LOOP", (LOAD_LOCAL, 0), (OUT_BYTE, ()),
    (LOAD_LOCAL, 0), (PUSH_CONST, 1), (ADD, ()), (STORE_LOCAL, 0),
    (LOAD_LOCAL, 0), (PUSH_CONST, 5), (CMP_LT, ()),
    (JUMP_IF_FALSE, "END"),
    (JUMP, "LOOP"),
    "END", (HALT, ()),
]
r, _ = run_prog(prog_loop)
check("loop outputs 0..4", r["output_bytes"] == [0, 1, 2, 3, 4], repr(r["output_bytes"]))

# --- 6. Calls (function add) ---
# add(a,b): load0, load1, add, return. main: push 2,3, call addr nargs=2 -> 5
prog_call = [
    (PUSH_CONST, 2), (PUSH_CONST, 3),
    (CALL, ("add", 2)),
    (OUT_BYTE, ()), (HALT, ()),
    "add", (LOAD_LOCAL, 0), (LOAD_LOCAL, 1), (ADD, ()), (RETURN, ()),
]
r, _ = run_prog(prog_call)
check("call add(2,3)=5", r["output_bytes"] == [5], repr(r))

# --- 7. Recursion (fib): fib(6)=8 ---
# fib(n): if n<2 return n; else fib(n-1)+fib(n-2)
prog_fib = [
    (PUSH_CONST, 6),
    (CALL, ("fib", 1)),
    (OUT_BYTE, ()), (HALT, ()),
    # fib:
    "fib",
    (LOAD_LOCAL, 0), (PUSH_CONST, 2), (CMP_LT, ()),
    (JUMP_IF_FALSE, "recurse"),
    (LOAD_LOCAL, 0), (RETURN, ()),  # base: return n
    "recurse",
    (LOAD_LOCAL, 0), (PUSH_CONST, 1), (SUB, ()), (CALL, ("fib", 1)),
    (LOAD_LOCAL, 0), (PUSH_CONST, 2), (SUB, ()), (CALL, ("fib", 1)),
    (ADD, ()), (RETURN, ()),
]
r, _ = run_prog(prog_fib)
check("recursion fib(6)=8", r["output_bytes"] == [8], repr(r["output_bytes"]))

# --- 8. I/O ---
# echo input bytes until EOF (0xFF), skipping the EOF marker
prog_io = [
    "LOOP",
    (IN_BYTE, ()), (DUP, ()), (PUSH_CONST, 0xFF), (CMP_EQ, ()),
    (JUMP_IF_FALSE, "KEEP"),
    (POP, ()), (JUMP, "END"),
    "KEEP", (OUT_BYTE, ()), (JUMP, "LOOP"),
    "END", (HALT, ()),
]
r, _ = run_prog(prog_io, input_bytes=b"Hi")
check("io echo 'Hi'", r["output_bytes"] == [ord('H'), ord('i')], repr(r["output_bytes"]))

# --- 9. Determinism + trace ---
r1, blob = run_prog(prog_fib, trace=True)
r2, _ = run_prog(prog_fib, trace=True)
check("deterministic output", r1["output_bytes"] == r2["output_bytes"])
check("deterministic steps", r1["steps"] == r2["steps"])
check("deterministic trace", r1["trace"] == r2["trace"])
check("trace non-empty", bool(r1["trace"]))
check("trace records opcode+pc", all("pc" in e and "op" in e for e in r1["trace"]))

# --- 10. Source-content hash ---
h = mbir_ref.source_hash(os.path.join(os.path.dirname(mbir_ref.__file__), "mbir_ref.py"))
check("source hash is 64 hex chars", isinstance(h, str) and len(h) == 64)

# --- 11. Negative cases ---
# stack underflow: OUT on empty
expect_error([(OUT_BYTE, ()), (HALT, ())], "STACK_UNDERFLOW", "underflow OUT empty")
# underflow ADD with <2
expect_error([(PUSH_CONST, 1), (ADD, ()), (HALT, ())], "STACK_UNDERFLOW", "underflow ADD 1 value")
# bad opcode (raw blob)
try:
    MBIRRefVM().load(bytes([0x99, HALT])).run()
    check("bad opcode 0x99", False, "did not raise")
except MBIRError as e:
    check("bad opcode 0x99", e.reason == "BAD_OPCODE", repr(e))
# bad target: JUMP to a non-boundary (into the middle of an instruction)
# PUSH_CONST at 0 (len2), JUMP to 1 (middle) -> BAD_TARGET
bad_tgt = mbir.encode([(PUSH_CONST, 5), (JUMP, 1), (HALT, ())])
try:
    MBIRRefVM().load(bad_tgt).run()
    check("jump to non-boundary", False, "did not raise")
except MBIRError as e:
    check("jump to non-boundary", e.reason == "BAD_TARGET", repr(e))
# bad slot: LOAD_LOCAL 5 with no locals
expect_error([(LOAD_LOCAL, 5), (HALT, ())], "BAD_SLOT", "bad slot 5")
# no-frame RETURN
expect_error([(RETURN, ()), (HALT, ())], "NO_FRAME", "return without frame")
# truncated operand (raw blob): PUSH_CONST with no operand byte
try:
    MBIRRefVM().load(bytes([PUSH_CONST])).run()
    check("truncated PUSH_CONST", False, "did not raise")
except MBIRError as e:
    check("truncated PUSH_CONST", e.reason == "BAD_OPERAND", repr(e))
# MAX_STEPS
vm = MBIRRefVM(max_steps=3)
try:
    # infinite-ish loop
    blob = mbir.encode([(JUMP, 0)])
    r = vm.load(blob).run()
    check("max_steps triggers", r["status"] == "MAX_STEPS", repr(r))
except MBIRError as e:
    check("max_steps triggers", e.reason == "MAX_STEPS", repr(e))

# --- Summary ---
print("\n" + "=" * 50)
print("PASS: %d   FAIL: %d   TOTAL: %d" % (PASS, FAIL, PASS + FAIL))
print("=" * 50)
if FAIL > 0:
    sys.exit(1)
print("MBIR reference VM conformance OK.")
sys.exit(0)