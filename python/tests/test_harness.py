"""
REFERENCE test harness for the Python MalPy VM and AST compiler.

This suite tests ONLY the Python reference implementation (REFERENCE_MODEL /
FRONTEND evidence). It does NOT invoke malbolge.exe, bolge19.exe, or any .mb
artifact. Malbolge runtime tests are a separate integration suite (A01/A04).

Fails if: reference VM output is wrong, bytecode is malformed, or a negative
(underflow) case does not raise as expected.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from p1_vm import MalPyVM, assemble
from p2_compiler import MalPyCompiler

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")

print("=== MalPy Test Harness ===\n")

# --- P1 VM Tests ---
print("[P1] MalPy VM")
vm = MalPyVM()

# Test 1: Basic addition
bytecode = assemble([("PUSH", 2), ("PUSH", 3), ("ADD",), ("OUT",), ("HALT",)])
vm.load(bytecode)
r = vm.run()
check("P1 basic addition (2+3=5)", r["output"] == chr(5) and r["halted"])

# Test 2: Different operands
bytecode = assemble([("PUSH", 10), ("PUSH", 20), ("ADD",), ("OUT",), ("HALT",)])
vm.load(bytecode)
r = vm.run()
check("P1 different operands (10+20=30)", r["output"] == chr(30) and r["halted"])

# Test 3: Zero
bytecode = assemble([("PUSH", 0), ("PUSH", 0), ("ADD",), ("OUT",), ("HALT",)])
vm.load(bytecode)
r = vm.run()
check("P1 zero (0+0=0)", r["output"] == chr(0) and r["halted"])

# Test 4: Max value
bytecode = assemble([("PUSH", 100), ("PUSH", 155), ("ADD",), ("OUT",), ("HALT",)])
vm.load(bytecode)
r = vm.run()
check("P1 max value (100+155=255)", r["output"] == chr(255) and r["halted"])

# Test 5: Same VM, different results
b1 = assemble([("PUSH", 2), ("PUSH", 3), ("ADD",), ("OUT",), ("HALT",)])
b2 = assemble([("PUSH", 10), ("PUSH", 20), ("ADD",), ("OUT",), ("HALT",)])
vm.load(b1)
r1 = vm.run()
vm.load(b2)
r2 = vm.run()
check("P1 same VM different results", r1["output"] != r2["output"])

# Test 6: VM determinism
vm.load(b1)
r3 = vm.run()
check("P1 VM determinism", r1["output"] == r3["output"] and r1["steps"] == r3["steps"])

# Test 7: OUT on empty stack must raise (underflow guard)
underflow_raised = False
try:
    vm.load(assemble([("OUT",), ("HALT",)]))
    vm.run()
except RuntimeError as e:
    underflow_raised = "OUT with empty stack" in str(e)
check("P1 OUT empty-stack underflow raises", underflow_raised)

# Test 8: ADD on <2 stack values must raise (underflow guard)
add_underflow_raised = False
try:
    vm.load(assemble([("PUSH", 5), ("ADD",), ("HALT",)]))
    vm.run()
except RuntimeError as e:
    add_underflow_raised = "ADD with fewer than 2" in str(e)
check("P1 ADD underflow raises", add_underflow_raised)

# Test 9: unknown opcode must raise
bad_opcode_raised = False
try:
    vm.load(bytes([0x99, 0x00]))
    vm.run()
except RuntimeError as e:
    bad_opcode_raised = "Unknown opcode" in str(e)
check("P1 unknown opcode raises", bad_opcode_raised)

# --- P2 Compiler Tests ---
print("\n[P2] Python AST Compiler")
compiler = MalPyCompiler()

test_cases = [
    ("print(2 + 3)", chr(5)),
    ("print(3 + 4)", chr(7)),
    ("print(10 + 20)", chr(30)),
    ("print(0 + 0)", chr(0)),
    ("print(100 + 155)", chr(255)),
    ("print(50 + 50)", chr(100)),
]

for source, expected in test_cases:
    bytecode = compiler.compile(source)
    vm.load(bytecode)
    r = vm.run()
    check(f"P2 compile: {source}", r["output"] == expected)

# Test: No eval/exec used
import ast
for source, _ in test_cases:
    tree = ast.parse(source.strip())
    has_eval = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("eval", "exec") for n in ast.walk(tree))
    check(f"P2 no eval/exec in: {source}", not has_eval)

# --- P3 Compiler Tests ---
print("\n[P3] Python subset to MBIR")
from p3_compiler import CASES, P3Compiler, run_mbir
from mbir import mbir as MBIR

p3 = P3Compiler()

def p3_ops(blob):
    return MBIR.decode(blob)

for source, expected, desc in CASES:
    blob = p3.compile(source)
    result = run_mbir(blob)
    observed = result["output"].encode("latin-1")
    check(
        f"P3 {desc}",
        observed == expected and result["status"] == "HALTED" and result["stack"] == [],
        f"got {observed.hex()} status={result['status']} stack={result['stack']}",
    )

add_blob = p3.compile("print(2 + 3)")
add_ops = [item[0] for item in p3_ops(add_blob)]
check(
    "P3 add lowers to MBIR, not the MalPy opcode set",
    add_ops == ["PUSH_CONST", "PUSH_CONST", "ADD", "OUT_BYTE", "HALT"]
    and add_blob != bytes.fromhex("01020103020300"),
)

assign_blob = p3.compile("x = 5\nprint(x + 2)")
assign_ops = [item[0] for item in p3_ops(assign_blob)]
pushed = [item[1] for item in p3_ops(assign_blob) if item[0] == "PUSH_CONST"]
check(
    "P3 assignment stores and reloads, result is not folded",
    assign_ops.count("STORE_LOCAL") == 1
    and assign_ops.count("LOAD_LOCAL") == 1
    and "ADD" in assign_ops
    and pushed == [5, 2],
)

wrap_blob = p3.compile("print(200 + 100)")
wrap_pushed = [item[1] for item in p3_ops(wrap_blob) if item[0] == "PUSH_CONST"]
check("P3 wrapped add keeps both operands", wrap_pushed == [200, 100] and run_mbir(wrap_blob)["output_bytes"] == [44])

sub_blob = p3.compile("print(1 - 2)")
sub_pushed = [item[1] for item in p3_ops(sub_blob) if item[0] == "PUSH_CONST"]
check("P3 wrapped sub keeps both operands", sub_pushed == [1, 2] and run_mbir(sub_blob)["output_bytes"] == [255])

branch_blob = p3.compile("if 5 > 3:\n    print(7)\nelse:\n    print(9)")
branch_ops = p3_ops(branch_blob)
branch_names = [item[0] for item in branch_ops]
branch_pushed = [item[1] for item in branch_ops if item[0] == "PUSH_CONST"]
check(
    "P3 if emits both arms and the comparison",
    "CMP_GT" in branch_names
    and "JUMP_IF_FALSE" in branch_names
    and branch_pushed == [5, 3, 7, 9],
)

loop_blob = p3.compile("x = 3\nwhile x > 0:\n    print(x)\n    x = x - 1")
loop_names = [item[0] for item in p3_ops(loop_blob)]
loop_result = run_mbir(loop_blob)
check(
    "P3 while has one OUT_BYTE and a back edge",
    loop_names.count("OUT_BYTE") == 1
    and loop_names.count("JUMP") == 1
    and loop_names.count("JUMP_IF_FALSE") == 1
    and loop_result["steps"] > 3
    and loop_result["output_bytes"] == [3, 2, 1],
)

taken = p3.compile("x = 1\nif x > 0:\n    print(7)\nelse:\n    print(9)")
other = p3.compile("x = 0\nif x > 0:\n    print(7)\nelse:\n    print(9)")
check(
    "P3 same shape, local decides the arm",
    run_mbir(taken)["output_bytes"] == [7]
    and run_mbir(other)["output_bytes"] == [9]
    and taken != other,
)

def raises_syntax(source):
    try:
        p3.compile(source)
    except SyntaxError:
        return True
    return False

check("P3 rejects an unbound name", raises_syntax("print(x)"))
check("P3 rejects a one-arm assignment", raises_syntax("if 1 > 2:\n    y = 7\nprint(y)"))
check("P3 rejects a function", raises_syntax("def add(a, b):\n    return a + b\n"))
check("P3 rejects a chained comparison", raises_syntax("print(1 < 2 < 3)"))
check("P3 rejects a float", raises_syntax("print(1.5)"))
check("P3 rejects eval", raises_syntax('print(eval("1+2"))'))
check("P3 rejects while-else", raises_syntax("while 0:\n    pass\nelse:\n    print(1)\n"))

# --- Summary ---
print(f"\n{'='*40}")
print(f"PASS: {PASS}")
print(f"FAIL: {FAIL}")
def test_malpy_harness():
    assert FAIL == 0, f"{FAIL} tests failed"


if __name__ == "__main__":
    if FAIL > 0:
        print("\nSome tests FAILED!")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
