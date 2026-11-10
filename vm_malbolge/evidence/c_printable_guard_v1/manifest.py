#!/usr/bin/env python3
"""Genera manifest.json del pack c_printable_guard_v1 (schema isyco-evidence-pack-v1)."""
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
             "guard_high.mb", "guard_low.mb",
             "control_seed_33.mb", "control_seed_126.mb",
             "build_index.json", "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge":
        ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/tools/native_classic/constants.py":
        ROOT / "vm_malbolge/tools/native_classic/constants.py",
    "vm_malbolge/evidence/epoch_resolver_word_v1/resolver_word.mb":
        ROOT / "vm_malbolge/evidence/epoch_resolver_word_v1/resolver_word.mb",
    "vm_malbolge/evidence/epoch_resolver_word_v1/resolver_word_dynamic.mb":
        ROOT / "vm_malbolge/evidence/epoch_resolver_word_v1/resolver_word_dynamic.mb",
    "vm_malbolge/evidence/epoch_resolver_word_v1/mutant_mask_121.mb":
        ROOT / "vm_malbolge/evidence/epoch_resolver_word_v1/mutant_mask_121.mb",
    "vm_malbolge/evidence/epoch_resolver_word_v1/mutant_wrong_payload.mb":
        ROOT / "vm_malbolge/evidence/epoch_resolver_word_v1/mutant_wrong_payload.mb",
}

CLAIMS = [
    {"text": "the C runner's vm_run halts BEFORE decoding when mem[pc] is "
             "outside 33..126 (vm_run 1cd4-1cda: `lea edx,[rax-0x21]` / "
             "`cmp edx,0x5d` / `ja 1e5e`), i.e. it refuses to execute cells "
             "that are not printable ASCII",
     "status": "DEMONSTRATED"},
    {"text": "that guard is the root cause of the epoch_resolver_word_v1 "
             "divergence: the step at which the oracle first enters a "
             "non-printable cell predicts the C runner's step count exactly in "
             "all four instances (276, 273, 272, 176)",
     "status": "DEMONSTRATED"},
    {"text": "the guarded interval is exactly the printable range: landing on "
             "a data cell with 33 and with 126 runs the full program to END in "
             "the C runner, while 0 and 29524 halt it at the landing step",
     "status": "DEMONSTRATED"},
    {"text": "canonical semantics are unaffected: the repo oracle and "
             "native_classic execute the non-printable cells, decode "
             "(mem[c] + c) % 94 and only condition the post-execution "
             "encryption on printability",
     "status": "DEMONSTRATED"},
    {"text": "the C runner is therefore a RESTRICTED variant, not a divergent "
             "Malbolge engine: it cannot run programs whose executed cells "
             "hold non-printable values, which is exactly what executing a "
             "10-trit payload in the epoch cell requires",
     "status": "DEMONSTRATED"},
    {"text": "the C runner agrees with the canonical engines on all phases "
             "that stay inside printable cells (measured in "
             "epoch_resolver_word_v1)", "status": "DEMONSTRATED"},
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
        "command": "python3 vm_malbolge/evidence/c_printable_guard_v1/probe.py",
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
