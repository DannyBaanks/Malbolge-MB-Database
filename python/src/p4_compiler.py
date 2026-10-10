"""
P4: Python functions → MBIR_VERSION 0.

Adds top-level `def`, calls, and `return` on top of the P3 subset.
A function body is a fresh frame: parameters are locals 0..n-1, and the
return value is whatever the body leaves on the stack. RETURN does not
pop it. CALL's address is a u8, so bodies are emitted before the module
and a direct self-call is rejected (recursion is P5).

print still emits the raw byte. The compiler does not constant-fold and
does not call eval or exec.

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
from p3_compiler import P3Compiler, run_mbir


class P4Compiler(P3Compiler):
    """Lower the P3 subset plus top-level functions to MBIR."""

    def compile(self, source: str) -> bytes:
        tree = ast.parse(source)
        if not isinstance(tree, ast.Module):
            raise SyntaxError("expected a module")
        self._funcs = {}
        self._order = []
        for stmt in tree.body:
            if isinstance(stmt, ast.FunctionDef):
                self._check_func(stmt)
                self._order.append(stmt.name)
                self._funcs[stmt.name] = stmt
        self._instrs = []
        self._lab = 0
        self._slots = {}
        self._current = None
        self._defined = set()
        if self._order:
            main = self._label()
            self._emit(M.JUMP, main)
            for name in self._order:
                self._compile_func(self._funcs[name])
            self._mark(main)
        module_assigned = set()
        for stmt in tree.body:
            if isinstance(stmt, ast.FunctionDef):
                self._defined.add(stmt.name)
                continue
            if isinstance(stmt, (ast.AsyncFunctionDef, ast.ClassDef)):
                raise SyntaxError("not in the P4 subset: %s" % type(stmt).__name__)
            module_assigned = self._compile_stmt(stmt, module_assigned)
        self._emit(M.HALT, None)
        return self._encode()

    def _check_func(self, stmt: ast.FunctionDef) -> None:
        if stmt.decorator_list:
            raise SyntaxError("decorators are not in the P4 subset")
        if stmt.name == "print":
            raise SyntaxError("print is reserved")
        if stmt.name in self._funcs:
            raise SyntaxError("function %s is already defined" % stmt.name)
        if stmt.returns is not None:
            raise SyntaxError("annotations are not in the P4 subset")
        args = stmt.args
        if (
            args.posonlyargs
            or args.vararg
            or args.kwonlyargs
            or args.kwarg
            or args.defaults
            or any(item is not None for item in args.kw_defaults)
        ):
            raise SyntaxError("only plain parameters are accepted")
        seen = []
        for arg in args.args:
            if arg.annotation is not None:
                raise SyntaxError("annotations are not in the P4 subset")
            if arg.arg == "print" or arg.arg in seen or arg.arg in self._funcs:
                raise SyntaxError("parameter %s is not accepted" % arg.arg)
            seen.append(arg.arg)

    def _compile_func(self, stmt: ast.FunctionDef) -> None:
        self._mark("fn_%s" % stmt.name)
        self._current = stmt.name
        params = [arg.arg for arg in stmt.args.args]
        self._slots = {name: index for index, name in enumerate(params)}
        if not self._always_returns(stmt.body):
            raise SyntaxError("function %s does not return on every path" % stmt.name)
        self._compile_block(stmt.body, set(params))
        self._current = None
        self._slots = {}

    def _always_returns(self, stmts) -> bool:
        for stmt in stmts:
            if isinstance(stmt, ast.Return):
                return True
            if isinstance(stmt, ast.If) and stmt.orelse:
                if self._always_returns(stmt.body) and self._always_returns(stmt.orelse):
                    return True
        return False

    def _compile_stmt(self, stmt, assigned: set) -> set:
        if isinstance(stmt, ast.FunctionDef):
            raise SyntaxError("nested functions are not in the P4 subset")
        if isinstance(stmt, ast.Return):
            if self._current is None:
                raise SyntaxError("return outside a function")
            if stmt.value is None:
                raise SyntaxError("return needs a value")
            self._compile_expr(stmt.value, assigned)
            self._emit(M.RETURN, None)
            return set(assigned)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            func = stmt.value.func
            if isinstance(func, ast.Name) and func.id != "print":
                self._compile_call(stmt.value, assigned)
                self._emit(M.POP, None)
                return set(assigned)
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id in self._funcs
        ):
            raise SyntaxError("name %s is a function" % stmt.targets[0].id)
        return super()._compile_stmt(stmt, assigned)

    def _compile_expr(self, node, assigned: set) -> None:
        if isinstance(node, ast.Call):
            self._compile_call(node, assigned)
            return
        super()._compile_expr(node, assigned)

    def _compile_call(self, node, assigned: set) -> None:
        if node.keywords or not isinstance(node.func, ast.Name):
            raise SyntaxError("only a direct function call is accepted")
        name = node.func.id
        if name == "print":
            raise SyntaxError("print is a statement")
        if name not in self._funcs:
            raise SyntaxError("unknown function %s" % name)
        if name == self._current:
            raise SyntaxError("direct recursion is P5")
        if self._current is None and name not in self._defined:
            raise SyntaxError("function %s is not defined yet" % name)
        params = self._funcs[name].args.args
        if len(node.args) != len(params):
            raise SyntaxError("wrong number of arguments for %s" % name)
        for arg in node.args:
            self._compile_expr(arg, assigned)
        self._emit(M.CALL, ("fn_%s" % name, len(params)))

    def _encode(self) -> bytes:
        labels = {}
        pos = 0
        for kind, opcode, _operand in self._instrs:
            if kind == "label":
                labels[opcode] = pos
                continue
            pos += 1 + M.operand_width(M.OPERANDS[opcode])
        built = []
        for kind, opcode, operand in self._instrs:
            if kind == "label":
                continue
            if opcode in (M.JUMP, M.JUMP_IF_FALSE):
                built.append((opcode, labels[operand]))
            elif opcode == M.CALL:
                label, nargs = operand
                addr = labels[label]
                if addr > 0xFF:
                    raise SyntaxError("function address %s does not fit in CALL's u8" % addr)
                built.append((opcode, (addr, nargs)))
            elif M.OPERANDS[opcode] is None:
                built.append((opcode, None))
            else:
                built.append((opcode, operand))
        return M.encode(built)


CASES = [
    (
        "def add(a, b):\n    return a + b\nprint(add(2, 3))",
        b"\x05",
        "spec add",
    ),
    (
        "def add(a, b):\n    return a + b\nprint(add(2, 3))\nprint(add(10, 20))",
        b"\x05\x1e",
        "one body, two calls",
    ),
    (
        "def add(a, b):\n    c = a + b\n    return c\nprint(add(4, 1))",
        b"\x05",
        "local in the frame",
    ),
    (
        "def pick(x):\n    if x > 0:\n        return 7\n    else:\n        return 9\nprint(pick(1))\nprint(pick(0))",
        b"\x07\x09",
        "return from both arms",
    ),
    (
        "def one():\n    return 1\nprint(one())",
        b"\x01",
        "no parameters",
    ),
    (
        "def inc(x):\n    return x + 1\ndef twice(x):\n    return inc(inc(x))\nprint(twice(3))",
        b"\x05",
        "one function calls another",
    ),
    (
        "def emit(x):\n    print(x)\n    return x + 1\nprint(emit(4))",
        b"\x04\x05",
        "print inside the function",
    ),
    (
        "def sum3():\n    x = 1\n    s = 0\n    while x < 4:\n        s = s + x\n        x = x + 1\n    return s\nprint(sum3())",
        b"\x06",
        "while inside the function",
    ),
    (
        "def add(a, b):\n    return a + b\nx = 4\nprint(add(x, 1))",
        b"\x05",
        "module local is a different frame",
    ),
    (
        "def add(a, b):\n    return a + b\nprint(add(200, 100))",
        b"\x2c",
        "add inside the function wraps",
    ),
    (
        "def add(a, b):\n    return a + b\nprint(add(add(1, 2), 3))",
        b"\x06",
        "nested call",
    ),
    ("print(2 + 3)", b"\x05", "no function, same bytes as P3"),
]


def _record(compiler: P4Compiler, source: str, expected: bytes, desc: str) -> dict:
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
    compiler = P4Compiler()
    results = []
    for source, expected, desc in CASES:
        try:
            record = _record(compiler, source, expected, desc)
        except Exception as exc:
            record = {"source": source, "description": desc, "error": str(exc), "verdict": "ERROR"}
        results.append(record)
        print("%s [%s]" % (desc, record["verdict"]))
    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "milestone": "P4",
        "evidence_kind": "FRONTEND",
        "host_language": "Python",
        "mbir_version": M.MBIR_VERSION,
        "description": "Python functions -> MBIR CALL/RETURN -> MBIR reference VM",
        "compiler": "P4Compiler (ast.parse, no eval/exec, no constant fold, no direct recursion)",
        "oracle": "mbir.mbir_ref.MBIRRefVM",
        "compiler_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "host_eval_exec": False,
        "constant_fold": False,
        "direct_recursion": "REJECTED (P5)",
        "tests": results,
        "summary": {
            "all_pass": all(item["verdict"] == "PASS" for item in results),
            "lowers_to_mbir": True,
            "execution_on_malbolge_hosted_runtime": "NOT_DEMONSTRATED",
            "recursion": "NOT_STARTED",
            "python_mb_interpreter": "NOT_DEMONSTRATED",
        },
    }
    path = Path(__file__).resolve().parents[1] / "evidence" / "P4" / "run_p4_compiler.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("evidence %s" % path)
    if not evidence["summary"]["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
