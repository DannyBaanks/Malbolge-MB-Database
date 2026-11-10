#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_rearm_primitive_v1 (schema isyco-evidence-pack-v1)."""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]

ARTIFACTS = ["VERDICT.md", "plan.py", "build.py", "probe.py", "manifest.py",
             "rearm_primitive.mb", "mutant_no_rearm.mb",
             "mutant_reload_wrong.mb", "mutant_boot_trit2.mb",
             "mutant_write_wrong_cell.mb",
             "labels.json", "build_index.json", "results.json",
             "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge": ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/evidence/torus_reach_v1/tr_spec.py":
        ROOT / "vm_malbolge/evidence/torus_reach_v1/tr_spec.py",
    "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb":
        ROOT / "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb",
}

CLAIMS = [
    {"text": "two EXACT byte writes in ONE execution (payloads 242 and 255 from "
             "stdin, OUT = f2 ff) with the mask cells restored in between",
     "status": "DEMONSTRATED"},
    {"text": "the rearm works: extract2 then crazy(E,E) brings a consumed mask "
             "cell back to 29524 (B = 29524 immediately before the second write)",
     "status": "DEMONSTRATED"},
    {"text": "the reload does not consume the source: 29524 is all 1s and therefore "
             "ROT-invariant, so one ROT on S leaves a = 29524 and S intact",
     "status": "DEMONSTRATED"},
    {"text": "bootstrap needs no zero cell and no printable involutive mask: "
             "a starts at 0 and crazy(0, 36) = 29524 (36 = 1100_3 has no trit 2)",
     "status": "DEMONSTRATED"},
    {"text": "three-engine agreement (traced repo oracle, repo oracle, original "
             "C runner) byte-for-byte on all five instances",
     "status": "DEMONSTRATED"},
    {"text": "four negative controls rejected (no rearm, reload from the wrong "
             "cell, boot cell with trit 2, write landing on the wrong cell)",
     "status": "DEMONSTRATED"},
    {"text": "d-routing planner (plan.py) raises on any hop cell that would need "
             "two different values; zone split code/data with a JMP",
     "status": "DEMONSTRATED"},
    {"text": "the swapped-hop mutant that pushed d out of the data zone was "
             "dropped: the C runner and the oracle diverge out of contract "
             "(unwrapped d), replaced by an in-contract mutant",
     "status": "DEMONSTRATED"},
    {"text": "full 10-trit payloads selected by epoch (v3 architecture with the "
             "29524 mask) and a conditional loop instead of unrolled phases",
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
        "command": "python3 vm_malbolge/evidence/epoch_rearm_primitive_v1/probe.py",
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
