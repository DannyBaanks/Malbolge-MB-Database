#!/usr/bin/env python3
"""Genera manifest.json del pack v3 (schema isyco-evidence-pack-v1)."""
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
             "mask_upgrade_probe.py", "mask_upgrade.raw.txt", "mask_upgrade.json",
             "resolver.mb", "mutant_residue.mb", "mutant_journal.mb",
             "mutant_pointer.mb", "mutant_mask.mb", "mutant_target.mb",
             "labels.json", "build_index.json", "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge": ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/tools/native_classic/constants.py":
        ROOT / "vm_malbolge/tools/native_classic/constants.py",
}

CLAIMS = [
    {"text": "runtime epoch selection by pointer (T = request+1) over aligned cells "
             "36/130/224", "status": "PASS"},
    {"text": "exact byte write into the selected epoch cell without value branches "
             "(256 payloads x 3 epochs, 0 mismatches)", "status": "PASS"},
    {"text": "jump to the written cell and execute it (OUT at pc=36/130/224)",
     "status": "PASS"},
    {"text": "three-engine agreement (traced oracle, repo oracle, original C runner)",
     "status": "PASS"},
    {"text": "negative controls (residue, journal, pointer, mask, target)",
     "status": "PASS"},
    {"text": "rearm of the epoch cell for a second request in the same run",
     "status": "NOT_DEMONSTRATED"},
    {"text": "10-trit word extension via runtime C1 manufacturing "
             "(121 -> 29523 -> C1 identities measured; not integrated in the "
             "resolver image)", "status": "NOT_DEMONSTRATED"},
    {"text": "general transition search / synthesis with dynamic discovered address",
     "status": "NOT_DEMONSTRATED"},
    {"text": "live streaming output before stdin close (batch model only)",
     "status": "NOT_DEMONSTRATED"},
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
        "command": "python3 vm_malbolge/evidence/epoch_algebra_v3/probe.py",
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
