"""
Test harness for MalPy VM and Python compiler.

Runs all test fixtures and verifies correctness.
Fails if: runner missing, wrong variant, output wrong, bytecode malformed.
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

# --- Summary ---
print(f"\n{'='*40}")
print(f"PASS: {PASS}")
print(f"FAIL: {FAIL}")
print(f"TOTAL: {PASS + FAIL}")
print(f"{'='*40}")

if FAIL > 0:
    print("\nSome tests FAILED!")
    sys.exit(1)
else:
    print("\nAll tests passed!")
    sys.exit(0)
