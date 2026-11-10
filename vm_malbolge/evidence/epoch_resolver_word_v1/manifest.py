#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_resolver_word_v1 (schema isyco-evidence-pack-v1)."""
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
             "resolver_word.mb", "resolver_word_dynamic.mb",
             "mutant_mask_121.mb", "mutant_wrong_payload.mb",
             "labels.json", "build_index.json", "results.json",
             "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge": ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/tools/native_classic/constants.py":
        ROOT / "vm_malbolge/tools/native_classic/constants.py",
    "vm_malbolge/evidence/torus_reach_v1/tr_spec.py":
        ROOT / "vm_malbolge/evidence/torus_reach_v1/tr_spec.py",
    "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb":
        ROOT / "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb",
}

CLAIMS = [
    {"text": "the epoch cell ends up holding the EXACT 10-trit payload 29797 "
             "(2s at trit positions 1, 3 and 5) and the payload is executed: "
             "OUT = 0x65 emitted at pc = T = 100, END at T+1",
     "status": "DEMONSTRATED"},
    {"text": "the request pointer is written exactly (W = 99 from the stdin byte)",
     "status": "DEMONSTRATED"},
    {"text": "three Python engines agree: traced repo oracle, traced "
             "native_classic, repo oracle_run", "status": "DEMONSTRATED"},
    {"text": "negative controls: with the printable 121 mask the write of this "
             "payload FAILS (T = 29311); a payload without the position-5 trit 2 "
             "gives another opcode at T", "status": "DEMONSTRATED"},
    {"text": "two legitimate instances (static jump and the v3 dynamic-pointer "
             "jump) both verify", "status": "DEMONSTRATED"},
    {"text": "the 29524 mask makes exact writes cover all 59049 words instead of "
             "the 7776 covered by 121", "status": "DEMONSTRATED"},
    {"text": "the ORIGINAL C RUNNER diverges in the final phase of the two "
             "legitimate instances: it lands at T (step count matches the OUT) "
             "but emits nothing and halts one step earlier; all previous phases "
             "agree, and a runtime-written JMP target works in that runner "
             "(control program, 29429 steps, both engines agree)",
     "status": "DEMONSTRATED"},
    {"text": "the C runner divergence root cause", "status": "NOT_DEMONSTRATED"},
    {"text": "a payload chosen by the request (today the payload is fixed and "
             "only the epoch is chosen by the stdin byte) and the rearm of the "
             "epoch cell for a second request in the same run",
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
        "command": "python3 vm_malbolge/evidence/epoch_resolver_word_v1/probe.py",
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
