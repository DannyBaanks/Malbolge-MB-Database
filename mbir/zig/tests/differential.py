"""M3 differential runner: Python MBIR reference VM vs the Zig backend."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from mbir import mbir as M  # noqa: E402
from mbir import MBIRError, MBIRRefVM  # noqa: E402
from mbir import (  # noqa: E402
    ADD,
    CALL,
    CMP_EQ,
    CMP_GT,
    CMP_LT,
    DUP,
    HALT,
    IN_BYTE,
    JUMP,
    JUMP_IF_FALSE,
    LOAD_LOCAL,
    MUL,
    OUT_BYTE,
    POP,
    PUSH_CONST,
    RETURN,
    STORE_LOCAL,
    SUB,
)


def asm(program):
    offsets = {}
    raw = []
    pc = 0
    for item in program:
        if isinstance(item, str):
            offsets[item] = pc
            continue
        op, operands = item
        raw.append((pc, op, operands))
        pc += 1 + M.operand_width(M.OPERANDS[op])

    def resolve(operands):
        if isinstance(operands, str):
            return offsets[operands]
        if isinstance(operands, tuple):
            return tuple(resolve(op) if isinstance(op, str) else op for op in operands)
        return operands

    return M.encode([(op, resolve(operands)) for _, op, operands in raw])


BRANCH_TRUE = [
    (PUSH_CONST, 5), (PUSH_CONST, 3), (CMP_GT, ()),
    (JUMP_IF_FALSE, "false"), (PUSH_CONST, 7), (OUT_BYTE, ()),
    (JUMP, "end"), "false", (PUSH_CONST, 9), (OUT_BYTE, ()),
    "end", (HALT, ()),
]

LOOP = [
    (PUSH_CONST, 0), (STORE_LOCAL, 0),
    "loop", (LOAD_LOCAL, 0), (OUT_BYTE, ()),
    (LOAD_LOCAL, 0), (PUSH_CONST, 1), (ADD, ()), (STORE_LOCAL, 0),
    (LOAD_LOCAL, 0), (PUSH_CONST, 5), (CMP_LT, ()),
    (JUMP_IF_FALSE, "end"), (JUMP, "loop"), "end", (HALT, ()),
]

CALL_ADD = [
    (PUSH_CONST, 2), (PUSH_CONST, 3), (CALL, ("add", 2)),
    (OUT_BYTE, ()), (HALT, ()), "add",
    (LOAD_LOCAL, 0), (LOAD_LOCAL, 1), (ADD, ()), (RETURN, ()),
]

FIB = [
    (PUSH_CONST, 6), (CALL, ("fib", 1)), (OUT_BYTE, ()), (HALT, ()),
    "fib", (LOAD_LOCAL, 0), (PUSH_CONST, 2), (CMP_LT, ()),
    (JUMP_IF_FALSE, "recurse"), (LOAD_LOCAL, 0), (RETURN, ()),
    "recurse", (LOAD_LOCAL, 0), (PUSH_CONST, 1), (SUB, ()),
    (CALL, ("fib", 1)),
    (LOAD_LOCAL, 0), (PUSH_CONST, 2), (SUB, ()),
    (CALL, ("fib", 1)), (ADD, ()), (RETURN, ()),
]

IO_LOOP = [
    "loop", (IN_BYTE, ()), (DUP, ()), (PUSH_CONST, 0xFF), (CMP_EQ, ()),
    (JUMP_IF_FALSE, "keep"), (POP, ()), (JUMP, "end"),
    "keep", (OUT_BYTE, ()), (JUMP, "loop"), "end", (HALT, ()),
]

FIXTURES = [
    ("add-wrap", [(PUSH_CONST, 200), (PUSH_CONST, 100), (ADD, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("sub-wrap", [(PUSH_CONST, 5), (PUSH_CONST, 10), (SUB, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("mul", [(PUSH_CONST, 16), (PUSH_CONST, 3), (MUL, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("cmp-eq", [(PUSH_CONST, 9), (PUSH_CONST, 9), (CMP_EQ, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("cmp-lt", [(PUSH_CONST, 3), (PUSH_CONST, 5), (CMP_LT, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("cmp-gt", [(PUSH_CONST, 7), (PUSH_CONST, 2), (CMP_GT, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("locals-dup", [(PUSH_CONST, 9), (STORE_LOCAL, 0), (LOAD_LOCAL, 0), (DUP, ()), (ADD, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("pop-leaves", [(PUSH_CONST, 1), (PUSH_CONST, 2), (POP, ()), (OUT_BYTE, ()), (HALT, ())]),
    ("branch-true", BRANCH_TRUE),
    ("loop-0-4", LOOP),
    ("call-add", CALL_ADD),
    ("fib6", FIB),
    ("io-echo", IO_LOOP, b"Hi"),
    ("eof-repeat", [(IN_BYTE, ()), (IN_BYTE, ()), (OUT_BYTE, ()), (OUT_BYTE, ()), (HALT, ())], b"A"),
    ("underflow-out", [(OUT_BYTE, ()), (HALT, ())]),
    ("underflow-add", [(PUSH_CONST, 1), (ADD, ()), (HALT, ())]),
    ("bad-opcode", bytes([0x99, HALT])),
    ("bad-target", M.encode([(PUSH_CONST, 5), (JUMP, 1), (HALT, ())])),
    ("bad-slot", [(LOAD_LOCAL, 5), (HALT, ())]),
    ("return-no-frame", [(RETURN, ()), (HALT, ())]),
    ("truncated-push", bytes([PUSH_CONST])),
    ("max-steps", [(JUMP, 0)], b"", 3),
]


def fixture_blob(program):
    return program if isinstance(program, bytes) else asm(program)


def run_python(program, input_bytes, max_steps):
    vm = MBIRRefVM(max_steps=max_steps)
    try:
        result = vm.load(program, input_bytes).run()
        return {
            "status": result["status"],
            "error": None,
            "steps": result["steps"],
            "output": result["output_bytes"],
        }
    except MBIRError as exc:
        return {
            "status": "ERROR",
            "error": exc.reason,
            "steps": vm.steps,
            "output": list(vm.output),
        }


def run_zig(exe, program, input_bytes, max_steps):
    with tempfile.TemporaryDirectory(prefix="mbir-zig-") as tmp:
        work = Path(tmp)
        program_path = work / "program.mbir"
        input_path = work / "input.bin"
        program_path.write_bytes(program)
        input_path.write_bytes(input_bytes)
        proc = subprocess.run(
            [str(exe), str(program_path), str(input_path), "--max-steps", str(max_steps)],
            capture_output=True,
            check=False,
        )
    if not proc.stdout:
        raise RuntimeError("zig produced empty stdout: %r" % proc.stderr)
    result = json.loads(proc.stdout.decode("utf-8"))
    expected_code = 0 if result["error"] is None else 1
    if proc.returncode != expected_code:
        raise RuntimeError("bad exit code %s for %r" % (proc.returncode, result))
    return {key: result[key] for key in ("status", "error", "steps", "output")}


def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", help="write a hashed differential manifest")
    options = parser.parse_args()

    exe = Path(__file__).resolve().parents[1] / "zig-out" / "bin" / "mbir-zig.exe"
    failures = 0
    records = []
    for entry in FIXTURES:
        name, program = entry[0], entry[1]
        input_bytes = entry[2] if len(entry) > 2 else b""
        max_steps = entry[3] if len(entry) > 3 else 1_000_000
        blob = fixture_blob(program)
        expected = run_python(blob, input_bytes, max_steps)
        actual = run_zig(exe, blob, input_bytes, max_steps)
        record = {
            "name": name,
            "program_sha256": sha256_bytes(blob),
            "input_sha256": sha256_bytes(input_bytes),
            "max_steps": max_steps,
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
        }
        records.append(record)
        if record["match"]:
            print("PASS %s steps=%s output_len=%d" % (name, actual["steps"], len(actual["output"])))
        else:
            failures += 1
            print("FAIL %s expected=%r actual=%r" % (name, expected, actual))

    print("differential: %d/%d PASS" % (len(FIXTURES) - failures, len(FIXTURES)))
    if options.manifest:
        manifest_path = Path(options.manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        schema_dir = Path(__file__).resolve().parents[1]
        manifest = {
            "schema": "mbir-zig-differential/1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "verdict": "PASS" if failures == 0 else "FAIL",
            "fixtures": len(FIXTURES),
            "passed": len(FIXTURES) - failures,
            "failed": failures,
            "hashes": {
                "runner_exe": sha256_file(exe),
                "runner_main": sha256_file(schema_dir / "src" / "main.zig"),
                "vm_zig": sha256_file(schema_dir / "src" / "mbir.zig"),
                "differential_script": sha256_file(Path(__file__).resolve()),
                "python_contract": sha256_file(REPO / "mbir" / "mbir.py"),
                "python_ref_vm": sha256_file(REPO / "mbir" / "mbir_ref.py"),
            },
            "records": records,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print("manifest: %s" % manifest_path)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
