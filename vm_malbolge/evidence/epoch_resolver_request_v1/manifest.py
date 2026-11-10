#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_resolver_request_v1 (schema isyco-evidence-pack-v1)."""
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
             "resolver_request.mb", "labels.json", "build_index.json",
             "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge":
        ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/tools/native_classic/constants.py":
        ROOT / "vm_malbolge/tools/native_classic/constants.py",
    "vm_malbolge/evidence/epoch_resolver_word_v1/resolver_word.mb":
        ROOT / "vm_malbolge/evidence/epoch_resolver_word_v1/resolver_word.mb",
    "vm_malbolge/evidence/c_printable_guard_v1/probe.py":
        ROOT / "vm_malbolge/evidence/c_printable_guard_v1/probe.py",
}

CLAIMS = [
    {"text": "the 10-trit payload is chosen by the request: with ONE fixed "
             "293-byte image, four different requests produce four different "
             "exact payloads (93, 187, 281, 29797), each written exactly in "
             "the epoch cell and executed there (OUT = V % 256 at pc = T = 100)",
     "status": "DEMONSTRATED"},
    {"text": "the request is consumed in order: the 20 control bytes are read "
             "in sequence and each one lands in its own position",
     "status": "DEMONSTRATED"},
    {"text": "the payload is not fixed in the program: mutating a single "
             "request byte changes the written payload (29797 -> 29798)",
     "status": "DEMONSTRATED"},
    {"text": "the decomposition V = crazy(M, P) with P = 29524 + sum(3^p for "
             "trit_p(V)=1) and M = 29524 + sum(3^p for trit_p(V)!=0), both in "
             "{1,2}^10, holds for ALL 59049 words (exhaustive, 0 mismatches)",
     "status": "DEMONSTRATED"},
    {"text": "NEGATIVE: the trit -> control-digit map that would let the "
             "request carry the 10 trits directly ((0,2,0) or (0,2,2)) is NOT "
             "reachable by any composition of crazy: the semigroup over one "
             "trit has exactly 15 maps and neither is among them ((0,0,2) is "
             "reachable). The interface therefore carries control digits",
     "status": "DEMONSTRATED"},
    {"text": "two independent Python engines agree byte for byte with the "
             "repo oracle (traced repo oracle + traced native_classic)",
     "status": "DEMONSTRATED"},
    {"text": "the C runner executes the whole program when the payload is "
             "printable (V = 93: same OUT 0x5d, 171 steps) and stops at the "
             "printable guard otherwise (step 170, exactly the step predicted "
             "from the oracle trace, see c_printable_guard_v1)",
     "status": "DEMONSTRATED"},
    {"text": "the epoch cell is still chosen by the program (T = 100 fixed); "
             "combining the request-driven epoch selection of "
             "epoch_algebra_v3 with this request-driven payload, and rearming "
             "the epoch for a second request in the same run, is NOT yet done",
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
        "command": "python3 vm_malbolge/evidence/epoch_resolver_request_v1/probe.py",
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
