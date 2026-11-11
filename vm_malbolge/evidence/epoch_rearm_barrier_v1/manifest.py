#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_rearm_barrier_v1 (schema isyco-evidence-pack-v1)."""
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
             "position_table.json", "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "vm_malbolge/evidence/epoch_rearm_primitive_v1/VERDICT.md":
        ROOT / "vm_malbolge/evidence/epoch_rearm_primitive_v1/VERDICT.md",
    "vm_malbolge/evidence/epoch_resolver_epoch_select_v1/resolver_epoch.mb":
        ROOT / "vm_malbolge/evidence/epoch_resolver_epoch_select_v1/resolver_epoch.mb",
    "vm_malbolge/evidence/epoch_resolver_epoch_select_v1/VERDICT.md":
        ROOT / "vm_malbolge/evidence/epoch_resolver_epoch_select_v1/VERDICT.md",
}

CLAIMS = [
    {"text": "the post-execution encryption (XLAT2) cannot be undone with "
             "rotations: rot^10 = identity, and none of the 2400 valid "
             "(opcode, cell) pairs of cells 0..299 satisfies rot^k(_ENC[v]) = v",
     "status": "DEMONSTRATED"},
    {"text": "the post-execution encryption CAN be undone with a single CRAZY "
             "when a per-trit control word exists (TBL[w_d][a_d] = v_d has no "
             "solution only when w_d = 0 and v_d = 2): 839 of 2400 pairs (35%), "
             "and 290 of the 300 cells have at least one restorable opcode",
     "status": "DEMONSTRATED"},
    {"text": "that control word is materializable from a seeded (printable) "
             "cell only through a rotation orbit: 0 of the 839 control words "
             "are printable, but 26 of them lie in an orbit containing a "
             "printable word, and those 26 are the SAME word (29403) in 26 "
             "distinct cells",
     "status": "DEMONSTRATED"},
    {"text": "the two-step restore (rearm to 29524 via extract2, then the exact "
             "write crazy(swap01(v), 29524)) requires swap01(v) to lie in the "
             "rotation orbit of v: measured on the 3200 valid (opcode, cell) "
             "pairs of cells 0..399, that holds for 34 pairs in 34 distinct "
             "cells. The pack ships that position table as its artifact",
     "status": "DEMONSTRATED"},
    {"text": "the rearm of a DATA cell is universal and exact: crazy(29524, X) "
             "= extract2(X) and crazy(E, E) = 29524 hold for ALL 59049 words "
             "(0 mismatches), so an epoch cell that consumed a payload can be "
             "returned to its mask exactly, always",
     "status": "DEMONSTRATED"},
    {"text": "the successor cell can take the back-edge role without breaking "
             "the pointer chain: its value is forced per epoch "
             "(v = (4-(T+1)) mod 94, i.e. 91, 85, 79 for T = 100, 106, 112) "
             "and the chain cell v+1 (92, 86, 80) stays inside the data zone "
             "and free",
     "status": "DEMONSTRATED"},
    {"text": "the back-edge target is out of reach with a seeded cell: a "
             "seeded (printable) cell can only carry 33..126, so the "
             "continuation address stays in 34..127 while the current image is "
             "340 bytes. Above that the exact word must be written at runtime: "
             "the condition swap01(dest-1) in a printable orbit holds for 36 "
             "destinations between 35 and 3999 (largest 3767), at a density of "
             "about 1 per 100 addresses",
     "status": "DEMONSTRATED"},
    {"text": "NEGATIVE / CAPACITY: the data zone has 86 cells and the two-step "
             "route needs one journal cell per re-executed code cell; the "
             "current loop body is around 200 cells, so it does not fit",
     "status": "DEMONSTRATED"},
    {"text": "a loop that serves a SECOND request in the same execution is "
             "still NOT demonstrated: this pack measures the three conditions "
             "such a loop would have to meet (position table, runtime-written "
             "back-edge target, journal capacity) but does not build it",
     "status": "NOT_DEMONSTRATED"},
    {"text": "the composition of the data-cell rearm (measured here) with the "
             "runtime pointer (measured in epoch_resolver_epoch_select_v1) "
             "inside one complete program is NOT demonstrated",
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
        "command": "python3 vm_malbolge/evidence/epoch_rearm_barrier_v1/probe.py",
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
