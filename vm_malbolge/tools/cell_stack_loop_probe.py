"""Differential probe for A04's reusable dedicated-cell input loop.

Builds ``cell_stack_loop_echo.hell`` with normal-layout LMAO and requires the
independent Classic Python oracle plus the real Classic C runner to echo every
input byte, including binary 0x00/0xff, before halting on EOF.
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
    ("empty", b""),
    ("one", bytes.fromhex("41")),
    ("two-binary", bytes.fromhex("00ff")),
    ("three", bytes.fromhex("017aff")),
    ("five-mixed", bytes.fromhex("00ff017a42")),
    ("eight-low", bytes.fromhex("0001020304050607")),
    ("eight-high", bytes.fromhex("f8f9fafbfcfdfeff")),
    ("sixteen-no-newline", bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 255])),
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
    parser.add_argument("--max-steps", type=int, default=2_000_000)
    parser.add_argument("--manifest", help="write evidence JSON to this path")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    source = root / "vm_malbolge" / "src" / "cell_stack_loop_echo.hell"
    lmao = root / "third_party" / "lmao" / "bin" / "lmao.exe"
    runner = root / "runners" / "malbolge-original" / "malbolge.exe"
    oracle_tool = root / "tools" / "oracle_classic.py"

    sys.path.insert(0, str(root / "tools"))
    import oracle_classic  # noqa: E402

    for required in (source, lmao, runner, oracle_tool):
        if not required.is_file():
            raise FileNotFoundError(required)

    records = []
    with tempfile.TemporaryDirectory(prefix="cell-stack-loop-") as tmp:
        binary = Path(tmp) / "cell_stack_loop_echo.mb"
        compile_hell(lmao, source, binary)
        program_text = binary.read_text(encoding="latin-1")
        compiled_sha = sha256_file(binary)

        for name, stdin_data in CASES:
            oracle_text, oracle_steps, oracle_status = oracle_classic.run(
                program_text,
                max_steps=args.max_steps,
                stdin_data=stdin_data.decode("latin-1"),
            )
            oracle_output = oracle_text.encode("latin-1")
            real = run_runner(runner, binary, stdin_data, args.max_steps)
            runner_output = bytes.fromhex(real["output_hex"])
            output_match = oracle_output == runner_output == stdin_data
            halt_match = (
                oracle_status == "HALTED"
                and real["status"] == "HALTED"
                and real["exit_code"] == 0
            )
            records.append(
                {
                    "name": name,
                    "input_hex": stdin_data.hex(),
                    "expected_hex": stdin_data.hex(),
                    "oracle": {
                        "output_hex": oracle_output.hex(),
                        "steps": oracle_steps,
                        "status": oracle_status,
                    },
                    "runner": real,
                    "output_match": output_match,
                    "step_match": real["steps"] == oracle_steps,
                    "ok": output_match and halt_match,
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
    manifest = {
        "schema": "malbolge-cell-stack-loop/1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "DEMONSTRATED" if all_ok else "NOT_DEMONSTRATED",
        "experiment": "dedicated stack_scratch/stack_top store-recover path reused across an EOF-terminated input loop",
        "source": "vm_malbolge/src/cell_stack_loop_echo.hell",
        "build": "LMAO v0.6.0 normal layout (no -f)",
        "oracle": "tools/oracle_classic.py",
        "runner": "runners/malbolge-original/malbolge.exe",
        "claim": (
            "The dedicated stack_scratch/stack_top pair can be reinitialized and reused across "
            "multiple sequential input iterations, recovering and emitting every byte exactly until EOF."
        ),
        "summary": {
            "cases_total": len(records),
            "cases_ok": sum(1 for record in records if record["ok"]),
            "max_input_bytes": max(len(data) for _, data in CASES),
            "all_outputs_exact": all(record["output_match"] for record in records),
            "step_parity_required": False,
        },
        "cases": records,
        "hashes": hashes,
        "runner_text_mode_observation": {
            "input_hex": "000102030405060708090a0b0c0d0e0f",
            "oracle_output_hex": "000102030405060708090a0b0c0d0e0f",
            "runner_output_hex": "000102030405060708090d0a0b0c0d0e0f",
            "oracle_steps": 55888,
            "runner_steps": 54286,
            "interpretation": (
                "The checked-in Classic C runner under Wine emitted LF as CRLF on stdout. "
                "This is a host text-mode output translation, so exact binary loop cases avoid 0x0a."
            ),
        },
        "scope_limits": [
            "This is a reusable byte loop through the dedicated cell pair, not MBIR opcode dispatch.",
            "It demonstrates per-iteration reset and reads beyond byte 2, but does not store a whole program into consecutive cells.",
            "It uses one logical stack value per iteration; persistence across a later independent opcode dispatch is not demonstrated.",
            "Oracle and C runner EOF step accounting differs; output/HALT agreement is the required cross-engine invariant.",
            "Exact-output cases omit LF (0x0a) because the C runner under Wine translates LF to CRLF on stdout; the observed control is preserved above.",
        ],
    }

    print(
        "stack-loop: %s %d/%d max_bytes=%d"
        % (
            manifest["status"],
            manifest["summary"]["cases_ok"],
            manifest["summary"]["cases_total"],
            manifest["summary"]["max_input_bytes"],
        )
    )
    for record in records:
        print(
            "%s bytes=%d oracle=%s runner=%s steps=%s/%s ok=%s"
            % (
                record["name"],
                len(bytes.fromhex(record["input_hex"])),
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
