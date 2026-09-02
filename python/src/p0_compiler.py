"""
P0 Compiler: Python addition expressions → Malbolge programs (prototype).

This prototype explores whether a Python→Malbolge compilation pipeline can be
built. It documents the crazy operation as the Malbolge arithmetic primitive.

CURRENT LIMITATION (NOT an impossibility claim):
Malbolge has no instruction to load arbitrary constants into the accumulator.
The only way to get a value into A is via `in` (stdin) or by reading from
memory (which requires knowing the address). This means general runtime
addition in the target Malbolge program is NOT_DEMONSTRATED by the current
implementation. This is a limitation of this design, not a proof that
Malbolge cannot express general addition.

WHAT THIS DEMONSTRATES:
- The crazy operation as a deterministic ternary arithmetic primitive
- A Python metadata/prototype that records operand→result mappings

WHAT THIS DOES NOT DEMONSTRATE:
- A generated, verified Malbolge addition artifact (program_source = None)
- General runtime addition routine accepting arbitrary operands in Malbolge
- A Malbolge program that computes add(a,b) for any a,b

Note on the anti-fake rule: the arithmetic result here is computed by Python
(`result = a + b`). No Malbolge program implements the operation. Therefore
anti_fake_satisfied is set False until a real Malbolge artifact demonstrates
operand-dependent behavior.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

# Malbolge instruction set (ASCII values 33-126)
# crazy(a, mem[d]) is the only arithmetic operation
# out(a) outputs a % 256 as a character
# in reads a character from stdin to a
# jmp mem[d] sets c = mem[d]
# mov a = mem[d]
# rot a = rotate(mem[d])
# nop does nothing
# end halts

MEM_SIZE = 3 ** 10  # 59049

# Crazy table (ternary lookup)
CRAZY_TBL = [
    [1, 0, 0],
    [1, 0, 2],
    [2, 2, 1],
]

def crazy(a, b):
    """Compute crazy(a, b) — the Malbolge arithmetic primitive."""
    result = 0
    p = 1
    for _ in range(10):
        result += CRAZY_TBL[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return result

def generate_addition_program(a, b):
    """
    Generate a Malbolge program that outputs the character chr(a + b).
    
    The program uses the crazy operation to compute a known result.
    Since we can't load arbitrary constants, we use a fixed program
    structure that happens to produce the correct output for (a, b).
    
    For P0, we use the Hello World program as a baseline and note that
    the crazy operation produces deterministic arithmetic results.
    """
    result = a + b
    if result < 0 or result > 255:
        raise ValueError(f"Result {result} out of range for character output")
    
    # For the actual arithmetic demonstration, we note that:
    # 1. crazy(33, 33) = 29497 (from our evidence)
    # 2. The Hello World program uses crazy 14 times to compute output
    # 3. Each output character passes through crazy(a, mem[d]) before printing
    
    # The program we generate uses the existing Hello World structure
    # but we document that for arbitrary (a, b), we would need a
    # different approach (lookup table, dispatch, or input-based).
    
    return {
        "type": "addition",
        "operands": [a, b],
        "result": result,
        "result_char": chr(result),
        "method": "crazy_operation_with_known_inputs",
        "constraint": "Malbolge cannot load arbitrary constants; this uses fixed inputs",
        "program_source": None,  # Would be the actual Malbolge source
        "verified": False,
    }

def compute_crazy_table():
    """Precompute the full crazy lookup table for reference."""
    table = {}
    for a in range(59049):
        for b in range(min(100, 59049)):  # Sample for reference
            table[(a, b)] = crazy(a, b)
    return table

# Test cases
test_cases = [
    (0, 0, 0),
    (1, 1, 2),
    (2, 3, 5),
    (3, 4, 7),
    (4, 4, 8),
    (10, 20, 30),
    (50, 50, 100),
    (100, 155, 255),
]

print("=== P0: Addition via Crazy Operation ===\n")

# Show crazy operation properties
print("Crazy operation as arithmetic primitive:")
for a, b, expected in test_cases:
    c = crazy(a, b)
    print(f"  crazy({a}, {b}) = {c} (expected sum = {a+b}, match = {c == a+b})")

print(f"\nNote: crazy(a,b) != a+b in general")
print(f"crazy is a ternary lookup, not addition")
print(f"For P0, we demonstrate the pipeline, not general addition\n")

# Generate programs for each test case
programs = []
for a, b, expected in test_cases:
    prog = generate_addition_program(a, b)
    programs.append(prog)
    print(f"  {a} + {b} = {prog['result']} ({prog['result_char']!r})")

print(f"\nGenerated {len(programs)} programs")
print(f"All results match expected: {all(p['result'] == p['operands'][0] + p['operands'][1] for p in programs)}")

# Save evidence
evidence = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "milestone": "P0",
    "evidence_kind": "FRONTEND",
    "host_language": "Python",
    "description": "Addition via crazy operation — metadata/prototype exploration",
    "limitation": "general runtime addition in the target Malbolge program = NOT_DEMONSTRATED by the current implementation",
    "method": "crazy_operation_with_known_inputs",
    "test_cases": [
        {
            "a": a, "b": b, "expected": exp,
            "crazy_result": crazy(a, b),
            "sum_correct": a + b == exp,
            "crazy_matches_sum": crazy(a, b) == exp,
        }
        for a, b, exp in test_cases
    ],
    "programs": programs,
    "summary": {
        "pipeline_demonstrated": False,
        "generated_verified_malbolge_artifact": False,
        "general_runtime_addition_in_malbolge": "NOT_DEMONSTRATED",
        "crazy_as_primitive": "DEMONSTRATED — deterministic ternary lookup",
        "anti_fake_satisfied": False,
        "reason_anti_fake_false": "result computed by host Python; no Malbolge artifact implements the operation",
    },
    "runtime": {
        "name": "python-compiler-p0",
        "variant": "original",
    },
}

evidence_path = Path(__file__).parent / "run_p0_compiler.json"
with open(evidence_path, "w") as f:
    json.dump(evidence, f, indent=2)

print(f"\nEvidence saved to {evidence_path}")
print(f"\nVerdict: P0 = NOT_DEMONSTRATED (no verified Malbolge addition artifact)")
print(f"Reason: result computed by host Python; program_source = None; verified = False")
print(f"Next: A01 runner doctor, then a real Malbolge artifact via MBIR")
