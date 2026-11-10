#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_mask_native_v1 (schema isyco-evidence-pack-v1)."""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]

ARTIFACTS = ["VERDICT.md", "build.py", "probe.py", "manifest.py",
             "mask_native.mb", "bootstrap_only.mb",
             "mutant_boot_has_trit2.mb", "mutant_rot_src.mb",
             "mutant_forward.mb", "mutant_nine_blocks.mb",
             "labels.json", "build_index.json", "results.json",
             "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge": ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/evidence/torus_reach_v1/tr_spec.py":
        ROOT / "vm_malbolge/evidence/torus_reach_v1/tr_spec.py",
}

CLAIMS = [
    {"text": "autonomous (no stdin) Classic Malbolge image that writes 29524 "
             "(ten trits = 1) into cell 41 with the first CRAZY (a = 0 at start, "
             "cell holds printable 36 with no trit 2): mem[41] = 29524, OUT = 0x54",
     "status": "DEMONSTRATED"},
    {"text": "the same image extends to 59048 (ten trits = 2): ten unrolled "
             "blocks [DLOAD, ROT, CRAZY] add one trit 2 per ROT of the 54 cell; "
             "mem[41] = 59048 = 29524 + (3^0+...+3^9), OUT = 0xa8, 34 steps, HALTED",
     "status": "DEMONSTRATED"},
    {"text": "three-engine agreement (traced repo oracle, repo oracle, original "
             "C runner) on both legitimate instances", "status": "DEMONSTRATED"},
    {"text": "four negative controls rejected (boot cell with trit 2, rotation "
             "source without trit 2, clobbered forward cell, nine blocks)",
     "status": "DEMONSTRATED"},
    {"text": "the 29524 cell is left in memory as a usable mask (bootstrap_only "
             "instance halts with mem[41] = 29524)", "status": "DEMONSTRATED"},
    {"text": "rearm of the mask cell for a second construction in the same run "
             "and an epoch resolver with a full 10-trit payload driven by stdin",
     "status": "NOT_DEMONSTRATED"},
    {"text": "a closed loop (the ten blocks are unrolled; no conditional exit "
             "was needed)", "status": "NOT_DEMONSTRATED"},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    artifacts = []
    for name in ARTIFACTS:
        p = PACK / name
        if not p.exists():
            print(f"FALTA {name}", file=sys.stderr)
            return 1
        artifacts.append({"file": name, "sha256": sha256(p)})
    deps = {}
    for label, p in DEPENDENCIES.items():
        if not p.exists():
            print(f"FALTA dependencia {label}", file=sys.stderr)
            return 1
        deps[label] = sha256(p)
    manifest = {
        "schema": "isyco-evidence-pack-v1",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": "python3 vm_malbolge/evidence/epoch_mask_native_v1/probe.py",
        "exit_code": 0,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "artifacts": artifacts,
        "dependencies": deps,
        "claims": CLAIMS,
    }
    (PACK / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(json.dumps({"artifacts": len(artifacts), "dependencies": len(deps),
                      "claims": len(CLAIMS)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
