"""Differential bridge between a HeLL MBIR probe and the Zig MBIR oracle.

The same MBIR byte stream is:
1. handed to Zig as a native MBIR program, and
2. streamed as stdin into a HeLL-built Malbolge probe.

The probe is then compared byte-for-byte against the Zig oracle, the Classic
Python oracle and the real Classic runner. A mismatch is a module boundary for
the next Malbolge milestone, never a fabricated PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import oracle_classic  # noqa: E402

LMAO = ROOT / "third_party" / "lmao" / "bin" / "lmao.exe"
RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge.exe"
ZIG = ROOT / "mbir" / "zig" / "zig-out" / "bin" / "mbir-zig.exe"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_hell(source: Path, output: Path) -> None:
    # Normal layout is the evidence-supported path; -f is runner-flaky (A04).
    proc = subprocess.run(
        [str(LMAO), "-o", str(output), str(source)],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not output.exists():
        raise RuntimeError(
            "LMAO compile failed rc=%s stdout=%r stderr=%r"
            % (proc.returncode, proc.stdout, proc.stderr)
        )


def run_classic_oracle(binary: Path, mbir_bytes: bytes, max_steps: int):
    source = binary.read_text(encoding="latin-1")
    text, steps, status = oracle_classic.run(
        source, max_steps=max_steps, stdin_data=mbir_bytes.decode("latin-1")
    )
    return text.encode("latin-1"), steps, status


def run_runner(binary: Path, mbir_bytes: bytes, max_steps: int):
    fd, input_path = tempfile.mkstemp(prefix="mbir-malbolge-input-", suffix=".bin")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(mbir_bytes)
        with open(input_path, "rb") as stdin:
            proc = subprocess.run(
                [str(RUNNER), str(binary), str(max_steps)],
                stdin=stdin,
                capture_output=True,
                check=False,
            )
        output = proc.stdout
        if output.endswith(b"\r\n"):
            output = output[:-2]
        return output, proc.returncode, proc.stderr.decode("latin-1")
    finally:
        os.unlink(input_path)


def run_zig(program: bytes, max_steps: int):
    with tempfile.TemporaryDirectory(prefix="mbir-zig-oracle-") as tmp:
        program_path = Path(tmp) / "program.mbir"
        program_path.write_bytes(program)
        proc = subprocess.run(
            [str(ZIG), str(program_path), "--max-steps", str(max_steps)],
            capture_output=True,
            check=False,
        )
    result = json.loads(proc.stdout.decode("utf-8"))
    result["exit_code"] = proc.returncode
    result["stderr"] = proc.stderr.decode("utf-8")
    return result


def run_case(source: Path, program: bytes, max_steps: int):
    with tempfile.TemporaryDirectory(prefix="mbir-malbolge-", suffix=".mb") as tmp_name:
        compiled = Path(tmp_name)
    try:
        compile_hell(source, compiled)
        oracle_output, oracle_steps, oracle_status = run_classic_oracle(compiled, program, max_steps)
        runner_output, runner_code, runner_stderr = run_runner(compiled, program, max_steps)
        zig = run_zig(program, max_steps)
        zig_output = bytes(zig["output"])
        return {
            "hell_source": str(source),
            "mbir_hex": program.hex(),
            "zig": zig,
            "malbolge_oracle": {
                "output": list(oracle_output),
                "steps": oracle_steps,
                "status": oracle_status,
            },
            "malbolge_runner": {
                "output": list(runner_output),
                "exit_code": runner_code,
                "stderr": runner_stderr,
            },
            "match": (
                zig["status"] == "HALTED"
                and zig_output == oracle_output == runner_output
            ),
            "sources": {
                "hell_sha256": sha256_file(source),
                "compiled_sha256": sha256_file(compiled),
                "zig_runner_sha256": sha256_file(ZIG),
                "malbolge_runner_sha256": sha256_file(RUNNER),
                "lmao_sha256": sha256_file(LMAO),
                "oracle_tool_sha256": sha256_file(Path(__file__).resolve()),
            },
        }
    finally:
        if compiled.exists():
            compiled.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hell", required=True, help="HeLL probe source")
    parser.add_argument("--mbir-hex", required=True, help="MBIR stream fed to Zig and Malbolge")
    parser.add_argument("--max-steps", type=int, default=600000)
    parser.add_argument("--expect-match", action="store_true", help="exit 1 when outputs differ")
    parser.add_argument("--manifest", help="write differential evidence JSON")
    options = parser.parse_args()

    source = (ROOT / options.hell).resolve() if not Path(options.hell).is_absolute() else Path(options.hell).resolve()
    program = bytes.fromhex(options.mbir_hex)
    if len(program) == 0 or len(program) > 65536:
        raise ValueError("MBIR stream must contain 1..65536 bytes")

    result = run_case(source, program, options.max_steps)
    zig_output = bytes(result["zig"]["output"])
    oracle_output = bytes(result["malbolge_oracle"]["output"])
    runner_output = bytes(result["malbolge_runner"]["output"])
    verdict = "MATCH" if result["match"] else "MISMATCH"
    print("zig   : status=%s error=%r steps=%s out=%s" % (
        result["zig"]["status"], result["zig"]["error"], result["zig"]["steps"], zig_output.hex()))
    print("oracle: status=%s steps=%s out=%s" % (
        result["malbolge_oracle"]["status"], result["malbolge_oracle"]["steps"], oracle_output.hex()))
    print("runner: rc=%s out=%s" % (result["malbolge_runner"]["exit_code"], runner_output.hex()))
    print("verdict: %s" % verdict)

    if options.manifest:
        manifest_path = (ROOT / options.manifest).resolve() if not Path(options.manifest).is_absolute() else Path(options.manifest).resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": "mbir-zig-malbolge-oracle/1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "verdict": verdict,
            "note": "MATCH proves the probe implements this MBIR stream; MISMATCH records the next Malbolge boundary.",
            "result": result,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print("manifest: %s" % manifest_path)

    if options.expect_match and not result["match"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
