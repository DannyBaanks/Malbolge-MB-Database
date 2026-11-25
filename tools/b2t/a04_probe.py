#!/usr/bin/env python3
"""Regenerate vm_malbolge/evidence/mbir_a04_backend_bridge.json.

The bridge evidence record for the `a04-malbolge` dispatcher backend.  Runs
the full pipeline (.b2t container -> dispatch -> profile route -> real
Malbolge machine -> oracle parity) over every machine-evidenced vector, the
extension vectors of a04_vectors.py and the refusal vectors; records every
observation plus artifact hashes into an append-only evidence JSON.

Refuses to write the record unless every expectation holds; any failure
exits non-zero and leaves the previous record untouched.

Usage:
    python3 tools/b2t/a04_probe.py
    A04_MALBOLGE_RUNNER=/path/to/malbolge python3 tools/b2t/a04_probe.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
for _path in (_HERE, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import a04_backend
import a04_vectors
import b2t
import dispatch

EVIDENCE_PATH = _REPO_ROOT / "vm_malbolge/evidence/mbir_a04_backend_bridge.json"

# oracle_classic hash recorded by the machine evidence, for the drift note.
_MACHINE_EVIDENCE_ORACLE_SHA = "5dae8f31"


def _sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _dispatch_record(input_hex: str) -> dict:
    program = bytes.fromhex(input_hex)
    container = b2t.encode_bytes(program).container
    envelope = dispatch.dispatch_container(
        container, backend_id=a04_backend.BACKEND_ID
    )
    meta = envelope.get("backend_meta") or {}
    return {
        "input_hex": input_hex,
        "machine": meta.get("machine"),
        "status": envelope["status"],
        "exit_code": envelope["exit_code"],
        "output_hex": envelope["stdout_hex"],
        "steps": envelope["steps"],
        "runner_status": meta.get("runner_status"),
        "malbolge_budget": meta.get("malbolge_budget"),
        "parity": meta.get("parity"),
    }


def _refusal_record(input_hex: str, expected_reason: str) -> dict:
    backend = dispatch.CATALOG.get(a04_backend.BACKEND_ID)
    run = backend.run_full(bytes.fromhex(input_hex))
    assert run["error"]["reason"] == expected_reason, (input_hex, run)
    return {"input_hex": input_hex, "reason": expected_reason, "status": run["status"]}


def main() -> int:
    backend = dispatch.CATALOG.get(a04_backend.BACKEND_ID)
    try:
        runner = backend.resolve_runner()
    except a04_backend._Refusal as refusal:
        print("refusing to probe: %s" % refusal, file=sys.stderr)
        return 2

    routed_cases = []
    for machine in ("lifo", "multicycle"):
        for case in a04_vectors.machine_cases(machine):
            program = bytes.fromhex(case["input_hex"])
            routed = a04_backend.route_machine(program)
            expected = a04_vectors.case_by_input(routed, case["input_hex"])
            record = _dispatch_record(case["input_hex"])
            assert record["status"] == "HALTED", record
            assert record["machine"] == routed, (record, routed)
            assert record["output_hex"] == expected["runner_hex"], (record, expected)
            assert record["steps"] == expected["runner_steps"], (record, expected)
            record["source_machine"] = machine
            record["recorded_verdict"] = case["verdict"]
            routed_cases.append(record)

    extension_cases = []
    for machine, input_hex, expected_hex, expected_steps, note in (
        a04_vectors.EXTENSION_VECTORS
    ):
        record = _dispatch_record(input_hex)
        assert record["machine"] == machine, record
        assert record["status"] == "HALTED", record
        assert record["output_hex"] == expected_hex, (record, expected_hex)
        assert record["steps"] == expected_steps, (record, expected_steps)
        record["note"] = note
        extension_cases.append(record)

    refusals = [
        _refusal_record(input_hex, reason)
        for input_hex, reason, _note in a04_vectors.REFUSAL_VECTORS
    ]

    instance_checks = {}
    for machine in ("lifo", "multicycle"):
        rows = []
        for case in a04_vectors.machine_cases(machine):
            result = backend.run_machine(machine, bytes.fromhex(case["input_hex"]))
            assert result["status"] == "HALTED", (machine, case, result)
            assert result["output"].hex() == case["runner_hex"], (machine, case, result)
            assert result["steps"] == case["runner_steps"], (machine, case, result)
            rows.append(
                {
                    "input_hex": case["input_hex"],
                    "verdict": case["verdict"],
                    "output_hex": result["output"].hex(),
                    "steps": result["steps"],
                    "parity": result["meta"]["parity"],
                }
            )
        instance_checks[machine] = rows

    document = {
        "schema": "malbolge-mb-database/bridge-evidence",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "evidence_kind": "BACKEND_BRIDGE",
        "claim": (
            "the dispatcher backend a04-malbolge executes the demonstrated MBIR "
            "subset on the committed Malbolge-hosted machines via the recorded C "
            "runner, with byte-and-step dual-engine parity (oracle_classic) "
            "asserted on every execution, and refuses every out-of-profile "
            "program with an explicit UNSUPPORTED_* envelope"
        ),
        "claim_status": "DEMONSTRATED",
        "source": {
            "backend": "tools/b2t/a04_backend.py",
            "backend_sha256": _sha256_file("tools/b2t/a04_backend.py"),
            "dispatcher": "tools/b2t/dispatch.py",
            "dispatcher_sha256": _sha256_file("tools/b2t/dispatch.py"),
            "codec": "tools/b2t/b2t.py",
            "codec_sha256": _sha256_file("tools/b2t/b2t.py"),
            "vectors": "tools/b2t/a04_vectors.py",
            "vectors_sha256": _sha256_file("tools/b2t/a04_vectors.py"),
            "tests": "tools/b2t/test_a04_backend.py",
            "tests_sha256": _sha256_file("tools/b2t/test_a04_backend.py"),
            "oracle": "tools/oracle_classic.py",
            "oracle_sha256": _sha256_file("tools/oracle_classic.py"),
            "oracle_drift_note": (
                "oracle_classic.py drifted from the hash recorded by the machine "
                "evidence (prefix %s...) through unrelated master work; behavior "
                "parity on every vector was re-verified by this record"
                % _MACHINE_EVIDENCE_ORACLE_SHA
            ),
            "runner": str(runner),
            "runner_sha256": _sha256_file(runner),
            "runner_reproducibility_note": (
                "byte-identical rebuild of the recorded runner binary from "
                "Malbolge-Engine master (404de20) with the host gcc; CI builds "
                "its own instance and asserts behavioral equality instead"
            ),
        },
        "artifact": {
            "lifo_image": "vm_malbolge/src/mbir_a05_lifo.mb",
            "lifo_image_file_sha256": _sha256_file("vm_malbolge/src/mbir_a05_lifo.mb"),
            "multicycle_image": "vm_malbolge/src/mbir_a05_multicycle.mb",
            "multicycle_image_file_sha256": _sha256_file(
                "vm_malbolge/src/mbir_a05_multicycle.mb"
            ),
            "machine_images_normalized_sha256": {
                name: a04_backend._sha256(a04_backend.load_machine(name))
                for name in ("lifo", "multicycle")
            },
            "normalization_note": (
                "worktree .mb files are autocrlf variants of the committed LF "
                "blobs; the normalized sha256 is the runtime identity both "
                "engines consume"
            ),
            "multicycle_instance_note": (
                "fresh LMAO 0.6.0 assembly (file sha 9e8eb271...) of the "
                "canonical .hell blob (26bf541b..., identical to the machine "
                "evidence source); behavior-identical to the recorded A05b "
                "instance despite the differing artifact hash (Finding 62)"
            ),
        },
        "runner_contract": {
            "invocation": "malbolge <image.mb> <step_budget>",
            "stdin": "the MBIR program as RAW bytes (never an ASCII hex string)",
            "stdout": "emitted bytes plus ONE trailing newline (stripped once)",
            "stderr": "steps: <N> | status: HALTED|TIMEOUT",
            "exit_code": "0 for HALTED and TIMEOUT alike",
            "ascii_hex_trap": (
                "feeding ASCII hex feeds the machines' unknown-opcode guard: "
                "constant 0x54 emitted per byte, HALTED with wrong output"
            ),
            "step_budget_cap": (
                "the limit is parsed with strtoul into uint32; the backend "
                "caps below 2^32"
            ),
        },
        "routed_cases": routed_cases,
        "extension_cases": extension_cases,
        "instance_checks": instance_checks,
        "refusals": refusals,
        "scope_limits": [
            "opcodes: {HALT 0x00, PUSH_CONST 0x01, OUT_BYTE 0x10} only; anything else is UNSUPPORTED_OPCODE",
            "trailing HALT required; nothing after it; a missing HALT is UNSUPPORTED_PROFILE",
            "stdin must be empty: the machines consume the program itself from stdin; IN_BYTE is out of profile",
            "shapes: the six LIFO bodies, or strictly alternating (PUSH,OUT)^k with k >= 1 on multicycle",
            "routing is lifo-first: k <= 2 alternations and single pushes run on the committed LIFO image",
            "the multicycle push-push limitation (LIMITATION_CONFIRMED control) is unreachable through this backend: that shape routes to the LIFO machine, which implements it correctly",
            "max_steps is MBIR-denominated; translated to a Malbolge budget (150000 floor + 6500/instruction, capped at 4e9); runner TIMEOUT maps to MAX_STEPS (exit 2)",
            "trace is not supported by this substrate (trace_supported=False); mbir-ref-python provides it",
            "a full MBIR-on-Malbolge VM remains NOT_DEMONSTRATED (mbir_vm.hell stub; M2/P* stored programs are not composed with the fetch loop)",
        ],
    }

    EVIDENCE_PATH.write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "wrote %s: %d routed, %d extensions, %d refusals, %d+%d instance checks"
        % (
            EVIDENCE_PATH,
            len(routed_cases),
            len(extension_cases),
            len(refusals),
            len(instance_checks["lifo"]),
            len(instance_checks["multicycle"]),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
