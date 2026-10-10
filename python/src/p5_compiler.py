"""
P5: direct recursion → MBIR_VERSION 0.

Same lowering as P4, except a function may call itself. The reference VM
already keeps one frame per call, so fib(6) is eight, not a folded byte.
print still emits the raw byte. No eval, no exec, no constant fold.

This is FRONTEND evidence on the host reference VM.
MALBOLGE_HOSTED_EXECUTION = NOT_DEMONSTRATED.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mbir import mbir as M
from p4_compiler import P4Compiler, run_mbir


class P5Compiler(P4Compiler):
    """P4 plus a direct self-call."""

    def _compile_call(self, node, assigned: set) -> None:
        if node.keywords or not isinstance(node.func, ast.Name):
            raise SyntaxError("only a direct function call is accepted")
        name = node.func.id
        if name == "print":
            raise SyntaxError("print is a statement")
        if name not in self._funcs:
            raise SyntaxError("unknown function %s" % name)
        if self._current is None and name not in self._defined:
            raise SyntaxError("function %s is not defined yet" % name)
        params = self._funcs[name].args.args
        if len(node.args) != len(params):
            raise SyntaxError("wrong number of arguments for %s" % name)
        for arg in node.args:
            self._compile_expr(arg, assigned)
        self._emit(M.CALL, ("fn_%s" % name, len(params)))


FIB = (
    "def fib(n):\n"
    "    if n < 2:\n"
    "        return n\n"
    "    return fib(n - 1) + fib(n - 2)\n"
)
FACT = (
    "def fact(n):\n"
    "    if n < 2:\n"
    "        return 1\n"
    "    return n * fact(n - 1)\n"
)
DOWN = (
    "def down(n):\n"
    "    if n > 0:\n"
    "        print(n)\n"
    "        return down(n - 1)\n"
    "    return 0\n"
)

CASES = [
    (FIB + "print(fib(6))", b"\x08", "fib(6)"),
    (FIB + "print(fib(0))", b"\x00", "fib(0)"),
    (FIB + "print(fib(1))", b"\x01", "fib(1)"),
    (FIB + "print(fib(7))", b"\x0d", "fib(7)"),
    (FIB + "print(fib(6))\nprint(fib(3))", b"\x08\x02", "fib(6) and fib(3)"),
    (FACT + "print(fact(5))", b"\x78", "fact(5)"),
    (DOWN + "print(down(3))", b"\x03\x02\x01\x00", "countdown"),
    (
        "def add(a, b):\n    return a + b\nprint(add(2, 3))",
        b"\x05",
        "non-recursive call still works",
    ),
]


def _record(compiler: P5Compiler, source: str, expected: bytes, desc: str) -> dict:
    blob = compiler.compile(source)
    result = run_mbir(blob)
    observed = result["output"].encode("latin-1")
    decoded = M.decode(blob)
    return {
        "source": source,
        "description": desc,
        "bytecode_hex": blob.hex(),
        "bytecode_sha256": hashlib.sha256(blob).hexdigest(),
        "mnemonics": [item[0] for item in decoded],
        "expected_hex": expected.hex(),
        "observed_hex": observed.hex(),
        "steps": result["steps"],
        "status": result["status"],
        "verdict": "PASS" if observed == expected and result["status"] == "HALTED" else "FAIL",
    }


def main() -> None:
    compiler = P5Compiler()
    results = []
    for source, expected, desc in CASES:
        try:
            record = _record(compiler, source, expected, desc)
        except Exception as exc:
            record = {"source": source, "description": desc, "error": str(exc), "verdict": "ERROR"}
        results.append(record)
        print("%s [%s] steps=%s" % (desc, record["verdict"], record.get("steps")))
    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "milestone": "P5",
        "evidence_kind": "FRONTEND",
        "host_language": "Python",
        "mbir_version": M.MBIR_VERSION,
        "description": "Python direct recursion -> MBIR CALL/RETURN -> MBIR reference VM",
        "compiler": "P5Compiler (ast.parse, no eval/exec, no constant fold)",
        "oracle": "mbir.mbir_ref.MBIRRefVM",
        "compiler_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "host_eval_exec": False,
        "constant_fold": False,
        "tests": results,
        "summary": {
            "all_pass": all(item["verdict"] == "PASS" for item in results),
            "lowers_to_mbir": True,
            "execution_on_malbolge_hosted_runtime": "NOT_DEMONSTRATED",
            "python_mb_interpreter": "NOT_DEMONSTRATED",
        },
    }
    path = Path(__file__).resolve().parents[1] / "evidence" / "P5" / "run_p5_compiler.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("evidence %s" % path)
    if not evidence["summary"]["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
