#!/usr/bin/env python3
"""Genera manifest.json del pack torus_reach_v1 (schema isyco-evidence-pack-v1)."""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]

ARTIFACTS = ["VERDICT.md", "tr_spec.py", "tr_solver.py", "tr_fillprobe.py",
             "tr_mutants.py", "probe.py", "manifest.py",
             "mutant_m1_crazy33.mb", "mutant_m2_rot33.mb",
             "fillprobe_1200.mb", "fillprobe_1300.mb", "fillprobe_1294.mb",
             "fillprobe_58000.mb", "fillprobe_58900.mb",
             "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge": ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/tools/native_classic/constants.py":
        ROOT / "vm_malbolge/tools/native_classic/constants.py",
    "third_party/lmao/src/malbolge.c": ROOT / "third_party/lmao/src/malbolge.c",
    "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb":
        ROOT / "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb",
    "vm_malbolge/evidence/epoch_algebra_v3/mutant_residue.mb":
        ROOT / "vm_malbolge/evidence/epoch_algebra_v3/mutant_residue.mb",
}

CLAIMS = [
    {"text": "independent spec of crazy/rot agrees with the repo oracle, "
             "native_classic and the original C runner (35 = 1022_3)",
     "status": "DEMONSTRATED"},
    {"text": "2-creation lemma D(crazy(a,v)) subset D(a) U D(v) (exhaustive over "
             "the 9 trit pairs + 200k words): the real circular dependency, and "
             "it is satisfiable", "status": "DEMONSTRATED"},
    {"text": "ROT permutes trit positions (Z_10) and rot^10 = identity "
             "(exhaustive over 59049 words)", "status": "DEMONSTRATED"},
    {"text": "{0, 29524} is a closed component under the restricted operator",
     "status": "DEMONSTRATED"},
    {"text": "29524 = crazy(54, 54) with printable 54; 8 printable constants "
             "carry no trit 1", "status": "DEMONSTRATED"},
    {"text": "0 = crazy(29524, 29524)", "status": "DEMONSTRATED"},
    {"text": "every 10-trit word is reachable from authorized initials "
             "(constructive witness: Q/U induction on 1023 subsets, F induction, "
             "general formula verified on 209 words; backward closure of 29524 "
             "= 59049 words)", "status": "DEMONSTRATED"},
    {"text": "59048 = ten 2s is reachable: constructive (1038 ops), compact "
             "(7 ops) and VM-faithful (11 ops, using the v3 byte-write) "
             "witnesses, all replayed with the repo oracle",
     "status": "DEMONSTRATED"},
    {"text": "shortest search (level meet) finds 59048 in 2 operations with the "
             "declared mask library", "status": "DEMONSTRATED"},
    {"text": "memory beyond the program is crazy-filled in the original C "
             "runner (5 targets, 3 engines): no free zero cells",
     "status": "DEMONSTRATED"},
    {"text": "mask 121 (v3) is involutive on 7776/59049 words; 29524 is "
             "involutive on all 59049 (upgrade path for a full-word resolver)",
     "status": "DEMONSTRATED"},
    {"text": "v3 exact byte-write primitive is reused as a precondition of the "
             "VM-faithful witness", "status": "DEMONSTRATED"},
    {"text": "blind spot: 6 mutants (altered crz table, wrong rotation, ternary "
             "error on 35, clandestine 59048 preload, position-blind decoder, "
             "write-only verifier) are all rejected or detected",
     "status": "DEMONSTRATED"},
    {"text": "impossibility of synthesizing 10-trit constants",
     "status": "DESTROYED"},
    {"text": "toroidal topology that blocks reaching patterns (distance to "
             "29524 <= 2 over a 5000-word sample)",
     "status": "DESTROYED"},
    {"text": "autonomous Classic Malbolge program (no stdin) that builds 59048",
     "status": "NOT_DEMONSTRATED"},
    {"text": "epoch resolver with full 10-trit payload (mask 29524) executing "
             "on the native VM", "status": "NOT_DEMONSTRATED"},
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
        "command": "python3 vm_malbolge/evidence/torus_reach_v1/probe.py",
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
