"""Reproducible differential probe for A04's explicit second sequential IN.

Builds ``cell_stack_second_read.hell`` with normal-layout LMAO, feeds two-byte
inputs to both the independent Python Classic oracle and the real Classic C
runner, and requires byte 2 to be emitted while byte 1 is discarded.

The probe also includes truncated/empty-input controls. Those controls require
matching HALT/output behavior, but intentionally do not require equal step
counts because EOF accounting differs between the two Classic engines on this
artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


CASES = [
    ("first-00_second-41", bytes.fromhex("0041")),
    ("first-ff_second-41", bytes.fromhex("ff41")),
    ("first-01_second-7a", bytes.fromhex("017a")),
    ("first-00_second-7a", bytes.fromhex("007a")),
    ("second-00", bytes.fromhex("ff00")),
    ("second-ff", bytes.fromhex("12ff")),
    ("second-01", bytes.fromhex("4101")),
    ("second-42", bytes.fromhex("7a42")),
    ("second-55", bytes.fromhex("aa55")),
    ("second-aa", bytes.fromhex("55aa")),
    ("truncated-after-first", bytes.fromhex("41")),
    ("empty-input", b""),
]

RUNNER_RE = re.compile(r"steps:\s*(\d+)\s*\|\s*status:\s*(\S+)")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exe_command(path: Path) -> list[str]:
    if os.name == "nt":
        return [str(path)]
    wine = shutil.which("wine")
    if wine is None:
        raise RuntimeError("Wine is required on non-Windows hosts for the checked-in .exe tools")
    return [wine, str(path)]


def compile_hell(lmao: Path, source: Path, output: Path) -> None:
    proc = subprocess.run(
        [*exe_command(lmao), "-o", str(output), str(source)],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not output.exists():
        raise RuntimeError(
            "LMAO compile failed rc=%s stdout=%r stderr=%r"
            % (proc.returncode, proc.stdout, proc.stderr)
        )


def run_runner(runner: Path, binary: Path, stdin_data: bytes, max_steps: int) -> dict:
    proc = subprocess.run(
        [*exe_command(runner), str(binary), str(max_steps)],
        input=stdin_data,
        capture_output=True,
        check=False,
    )
    output = proc.stdout[:-2] if proc.stdout.endswith(b"\r\n") else proc.stdout
    stderr = proc.stderr.decode("latin-1").strip()
    match = RUNNER_RE.search(stderr)
    return {
        "output_hex": output.hex(),
        "exit_code": proc.returncode,
        "steps": int(match.group(1)) if match else None,
        "status": match.group(2) if match else None,
        "stderr": stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", help="repository root; inferred when installed in vm_malbolge/tools")
    parser.add_argument("--max-steps", type=int, default=600000)
    parser.add_argument("--manifest", help="write evidence JSON to this path")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    source = root / "vm_malbolge" / "src" / "cell_stack_second_read.hell"
    lmao = root / "third_party" / "lmao" / "bin" / "lmao.exe"
    runner = root / "runners" / "malbolge-original" / "malbolge.exe"
    oracle_tool = root / "tools" / "oracle_classic.py"

    sys.path.insert(0, str(root / "tools"))
    import oracle_classic  # noqa: E402

    for required in (source, lmao, runner, oracle_tool):
        if not required.is_file():
            raise FileNotFoundError(required)

    records = []
    with tempfile.TemporaryDirectory(prefix="cell-second-read-") as tmp:
        binary = Path(tmp) / "cell_stack_second_read.mb"
        compile_hell(lmao, source, binary)
        compiled_sha = sha256_file(binary)
        program_text = binary.read_text(encoding="latin-1")

        for name, stdin_data in CASES:
            expected = stdin_data[1:2] if len(stdin_data) >= 2 else b""
            oracle_text, oracle_steps, oracle_status = oracle_classic.run(
                program_text,
                max_steps=args.max_steps,
                stdin_data=stdin_data.decode("latin-1"),
            )
            oracle_output = oracle_text.encode("latin-1")
            real = run_runner(runner, binary, stdin_data, args.max_steps)
            runner_output = bytes.fromhex(real["output_hex"])
            full_pair = len(stdin_data) >= 2
            output_match = oracle_output == runner_output == expected
            halt_match = oracle_status == "HALTED" and real["status"] == "HALTED" and real["exit_code"] == 0
            step_match = real["steps"] == oracle_steps
            ok = output_match and halt_match and (step_match if full_pair else True)
            records.append(
                {
                    "name": name,
                    "input_hex": stdin_data.hex(),
                    "expected_hex": expected.hex(),
                    "full_two_byte_case": full_pair,
                    "oracle": {
                        "output_hex": oracle_output.hex(),
                        "steps": oracle_steps,
                        "status": oracle_status,
                    },
                    "runner": real,
                    "output_match": output_match,
                    "step_match": step_match,
                    "ok": ok,
                }
            )

        hashes = {
            "hell_sha256": sha256_file(source),
            "compiled_sha256": compiled_sha,
            "lmao_sha256": sha256_file(lmao),
            "malbolge_runner_sha256": sha256_file(runner),
            "oracle_tool_sha256": sha256_file(oracle_tool),
            "probe_tool_sha256": sha256_file(Path(__file__).resolve()),
        }

    all_ok = all(record["ok"] for record in records)
    full_cases = [record for record in records if record["full_two_byte_case"]]
    eof_controls = [record for record in records if not record["full_two_byte_case"]]
    manifest = {
        "schema": "malbolge-cell-second-read/1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "DEMONSTRATED" if all_ok else "NOT_DEMONSTRATED",
        "experiment": "explicit MOVED return structure around two sequential IN operations",
        "source": "vm_malbolge/src/cell_stack_second_read.hell",
        "build": "LMAO v0.6.0 normal layout (no -f)",
        "oracle": "tools/oracle_classic.py",
        "runner": "runners/malbolge-original/malbolge.exe",
        "claim": (
            "For a complete two-byte input, the first byte is discarded and the second byte is read, "
            "stored through the dedicated stack_scratch/stack_top route, recovered, and emitted."
        ),
        "summary": {
            "cases_total": len(records),
            "cases_ok": sum(1 for record in records if record["ok"]),
            "full_two_byte_cases": len(full_cases),
            "full_two_byte_cases_ok": sum(1 for record in full_cases if record["ok"]),
            "eof_controls": len(eof_controls),
            "eof_controls_ok": sum(1 for record in eof_controls if record["ok"]),
            "full_case_step_parity": all(record["step_match"] for record in full_cases),
            "eof_step_parity_required": False,
        },
        "cases": records,
        "hashes": hashes,
        "scope_limits": [
            "Demonstrates exactly two sequential input reads for this straight-line artifact; no third read or fetch loop.",
            "The first byte is intentionally discarded; this is not yet MBIR opcode/operand dispatch.",
            "Does not demonstrate per-iteration state reset, arbitrary-length stdin loading, or a multi-value stack.",
            "EOF controls require output/status agreement only; oracle and C runner step accounting differs on EOF for this artifact.",
        ],
    }

    print(
        "second-read: %s %d/%d; full=%d/%d eof=%d/%d"
        % (
            manifest["status"],
            manifest["summary"]["cases_ok"],
            manifest["summary"]["cases_total"],
            manifest["summary"]["full_two_byte_cases_ok"],
            manifest["summary"]["full_two_byte_cases"],
            manifest["summary"]["eof_controls_ok"],
            manifest["summary"]["eof_controls"],
        )
    )
    for record in records:
        print(
            "%s in=%s expect=%s oracle=%s runner=%s steps=%s/%s ok=%s"
            % (
                record["name"],
                record["input_hex"] or "<empty>",
                record["expected_hex"] or "<empty>",
                record["oracle"]["output_hex"] or "<empty>",
                record["runner"]["output_hex"] or "<empty>",
                record["oracle"]["steps"],
                record["runner"]["steps"],
                record["ok"],
            )
        )

    if args.manifest:
        manifest_path = Path(args.manifest).resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print("manifest:", manifest_path)

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
