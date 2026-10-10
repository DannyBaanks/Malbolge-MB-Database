"""
P3: Python subset → MBIR_VERSION 0.

Accepts assignment, print, modular + - *, a single comparison, if/else
(elif is the nested else the parser already produces), and while.
Uses ast.parse. Does not call eval or exec. Does not constant-fold.

print emits the raw unsigned byte (OUT_BYTE), the same convention as P2.
200 + 100 is byte 44. 1 - 2 is byte 255.

Pipeline:
  source → ast.parse → MBIR bytes → MBIRRefVM → output

This is FRONTEND evidence on the host reference VM.
MALBOLGE_HOSTED_EXECUTION = NOT_DEMONSTRATED.
Functions, recursion, and python.mb are outside this slice.
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
from mbir.mbir_ref import MBIRRefVM

_BINOPS = {
    ast.Add: M.ADD,
    ast.Sub: M.SUB,
    ast.Mult: M.MUL,
}
_CMPOPS = {
    ast.Eq: M.CMP_EQ,
    ast.Lt: M.CMP_LT,
    ast.Gt: M.CMP_GT,
}


class P3Compiler:
    """Lower the P3 Python subset to MBIR. One value left on the stack per expression."""

    def compile(self, source: str) -> bytes:
        tree = ast.parse(source)
        if not isinstance(tree, ast.Module):
            raise SyntaxError("expected a module")
        self._slots = {}
        self._instrs = []
        self._lab = 0
        self._compile_block(tree.body, set())
        self._emit(M.HALT, None)
        return self._encode()

    def _slot(self, name: str) -> int:
        if name not in self._slots:
            self._slots[name] = len(self._slots)
        return self._slots[name]

    def _label(self) -> str:
        self._lab += 1
        return "L%d" % self._lab

    def _mark(self, name: str) -> None:
        self._instrs.append(("label", name, None))

    def _emit(self, opcode: int, operand) -> None:
        self._instrs.append(("op", opcode, operand))

    def _compile_block(self, stmts, assigned: set) -> set:
        current = set(assigned)
        for stmt in stmts:
            current = self._compile_stmt(stmt, current)
        return current

    def _compile_stmt(self, stmt, assigned: set) -> set:
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                raise SyntaxError("only a single name assignment is accepted")
            name = stmt.targets[0].id
            if name == "print":
                raise SyntaxError("print is reserved")
            self._compile_expr(stmt.value, assigned)
            self._emit(M.STORE_LOCAL, self._slot(name))
            return set(assigned) | {name}

        if isinstance(stmt, ast.Expr):
            self._compile_print(stmt.value, assigned)
            return set(assigned)

        if isinstance(stmt, ast.If):
            self._compile_expr(stmt.test, assigned)
            else_l = self._label()
            self._emit(M.JUMP_IF_FALSE, else_l)
            then_assigned = self._compile_block(stmt.body, assigned)
            if stmt.orelse:
                end_l = self._label()
                self._emit(M.JUMP, end_l)
                self._mark(else_l)
                else_assigned = self._compile_block(stmt.orelse, assigned)
                self._mark(end_l)
                return then_assigned & else_assigned
            self._mark(else_l)
            return set(assigned)

        if isinstance(stmt, ast.While):
            if stmt.orelse:
                raise SyntaxError("while-else is not in the P3 subset")
            loop_l = self._label()
            end_l = self._label()
            self._mark(loop_l)
            self._compile_expr(stmt.test, assigned)
            self._emit(M.JUMP_IF_FALSE, end_l)
            self._compile_block(stmt.body, assigned)
            self._emit(M.JUMP, loop_l)
            self._mark(end_l)
            return set(assigned)

        if isinstance(stmt, ast.Pass):
            return set(assigned)

        raise SyntaxError("not in the P3 subset: %s" % type(stmt).__name__)

    def _compile_print(self, node, assigned: set) -> None:
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            raise SyntaxError("only print(...) statements are accepted")
        if node.func.id != "print":
            raise SyntaxError("only print(...) statements are accepted")
        if node.keywords or len(node.args) != 1:
            raise SyntaxError("print() takes exactly one argument")
        self._compile_expr(node.args[0], assigned)
        self._emit(M.OUT_BYTE, None)

    def _compile_expr(self, node, assigned: set) -> None:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, int):
                raise SyntaxError("only integer literals 0..255 are accepted")
            if not 0 <= node.value <= 255:
                raise SyntaxError("integer must be 0..255, got %s" % node.value)
            self._emit(M.PUSH_CONST, node.value)
            return

        if isinstance(node, ast.Name):
            if node.id not in assigned:
                raise SyntaxError("name %s is not assigned on this path" % node.id)
            self._emit(M.LOAD_LOCAL, self._slots[node.id])
            return

        if isinstance(node, ast.BinOp):
            opcode = _BINOPS.get(type(node.op))
            if opcode is None:
                raise SyntaxError("operator is not in the P3 subset: %s" % type(node.op).__name__)
            self._compile_expr(node.left, assigned)
            self._compile_expr(node.right, assigned)
            self._emit(opcode, None)
            return

        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise SyntaxError("only a single comparison is accepted")
            opcode = _CMPOPS.get(type(node.ops[0]))
            if opcode is None:
                raise SyntaxError("comparison is not in the P3 subset: %s" % type(node.ops[0]).__name__)
            self._compile_expr(node.left, assigned)
            self._compile_expr(node.comparators[0], assigned)
            self._emit(opcode, None)
            return

        raise SyntaxError("expression is not in the P3 subset: %s" % type(node).__name__)

    def _encode(self) -> bytes:
        labels = {}
        pos = 0
        for kind, a, _b in self._instrs:
            if kind == "label":
                labels[a] = pos
                continue
            pos += 1 + M.operand_width(M.OPERANDS[a])
        built = []
        for kind, opcode, operand in self._instrs:
            if kind == "label":
                continue
            if opcode in (M.JUMP, M.JUMP_IF_FALSE):
                built.append((opcode, labels[operand]))
            elif M.OPERANDS[opcode] is None:
                built.append((opcode, None))
            else:
                built.append((opcode, operand))
        return M.encode(built)


def run_mbir(blob: bytes) -> dict:
    vm = MBIRRefVM()
    vm.load(blob)
    return vm.run()


CASES = [
    ("print(2 + 3)", b"\x05", "add literals"),
    ("x = 5\nprint(x + 2)", b"\x07", "assign and load"),
    ("x = 1\nx = x + 4\nprint(x)", b"\x05", "reassign"),
    ("x = 10\ny = 20\nprint(x + y)", b"\x1e", "two locals"),
    ("print(200 + 100)", b"\x2c", "add wraps mod 256"),
    ("print(1 - 2)", b"\xff", "sub wraps mod 256"),
    ("print(3 * 4)", b"\x0c", "multiply"),
    ("if 5 > 3:\n    print(7)\nelse:\n    print(9)", b"\x07", "if taken"),
    ("if 1 > 2:\n    print(7)\nelse:\n    print(9)", b"\x09", "else taken"),
    ("x = 0\nif x > 0:\n    print(7)\nelse:\n    print(9)", b"\x09", "branch on a local"),
    ("x = 1\nif x > 0:\n    print(7)\nelse:\n    print(9)", b"\x07", "other branch on a local"),
    ("if 0 > 1:\n    print(1)\nelif 2 > 1:\n    print(2)\nelse:\n    print(3)", b"\x02", "elif"),
    ("x = 3\nwhile x > 0:\n    print(x)\n    x = x - 1", b"\x03\x02\x01", "while decrements"),
    ("x = 2\nwhile x > 0:\n    if x > 1:\n        print(9)\n    else:\n        print(8)\n    x = x - 1", b"\x09\x08", "while and if"),
    ("if 1 > 2:\n    y = 7\nelse:\n    y = 9\nprint(y)", b"\x09", "assign on both arms"),
]


def _record(compiler: P3Compiler, source: str, expected: bytes, desc: str) -> dict:
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
    compiler = P3Compiler()
    results = []
    for source, expected, desc in CASES:
        try:
            record = _record(compiler, source, expected, desc)
        except Exception as exc:
            record = {"source": source, "description": desc, "error": str(exc), "verdict": "ERROR"}
        results.append(record)
        print("%s [%s]" % (desc, record["verdict"]))

    source_bytes = Path(__file__).read_bytes()
    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "milestone": "P3",
        "evidence_kind": "FRONTEND",
        "host_language": "Python",
        "mbir_version": M.MBIR_VERSION,
        "description": "Python subset -> MBIR_VERSION 0 -> MBIR reference VM",
        "compiler": "P3Compiler (ast.parse, no eval/exec, no constant fold)",
        "oracle": "mbir.mbir_ref.MBIRRefVM",
        "compiler_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "host_eval_exec": False,
        "constant_fold": False,
        "tests": results,
        "summary": {
            "all_pass": all(item["verdict"] == "PASS" for item in results),
            "lowers_to_mbir": True,
            "execution_on_malbolge_hosted_runtime": "NOT_DEMONSTRATED",
            "functions": "NOT_STARTED",
            "python_mb_interpreter": "NOT_DEMONSTRATED",
        },
    }
    path = Path(__file__).resolve().parents[1] / "evidence" / "P3" / "run_p3_compiler.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("evidence %s" % path)
    if not evidence["summary"]["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
