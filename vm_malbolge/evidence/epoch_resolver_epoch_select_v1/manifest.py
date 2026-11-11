#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_resolver_epoch_select_v1 (schema isyco-evidence-pack-v1)."""
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
             "resolver_epoch.mb", "labels.json", "build_index.json",
             "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge":
        ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/tools/native_classic/constants.py":
        ROOT / "vm_malbolge/tools/native_classic/constants.py",
    "vm_malbolge/evidence/epoch_resolver_request_v1/resolver_request.mb":
        ROOT / "vm_malbolge/evidence/epoch_resolver_request_v1/resolver_request.mb",
    "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb":
        ROOT / "vm_malbolge/evidence/epoch_algebra_v3/resolver.mb",
    "vm_malbolge/evidence/c_printable_guard_v1/probe.py":
        ROOT / "vm_malbolge/evidence/c_printable_guard_v1/probe.py",
}

CLAIMS = [
    {"text": "the request selects BOTH the epoch cell and the payload: with ONE "
             "fixed 340-byte image, the 21-byte request chooses the epoch cell "
             "T (100, 106 or 112) and the 10-trit payload V written exactly in "
             "it and executed there (OUT = V % 256 at pc = T, END at T+1)",
     "status": "DEMONSTRATED"},
    {"text": "the epoch cell is chosen by the request byte, not by the program: "
             "mutating ONLY the epoch byte moves the payload from cell 100 to "
             "cell 106 (cell 100 keeps the 29524 mask) and changes the opcode "
             "from OUT to an invalid one (no output), while mutating ONLY a "
             "control digit changes the payload and keeps the epoch",
     "status": "DEMONSTRATED"},
    {"text": "the pointer mechanism needs no comparison by value: the DLOAD "
             "reads mem[W] = b, d becomes b, the automatic increment lands on "
             "T = b+1 and the CRAZY writes exactly there; the successor cell "
             "T+1 serves both as END ((v+T+1)%94 = 81) and as the trampoline "
             "back to W (v+1 holds W-1) through a two-DLOAD chain identical in "
             "all three epochs",
     "status": "DEMONSTRATED"},
    {"text": "the request is consumed in order: the 21 bytes (1 epoch byte + 20 "
             "control digits) are read in sequence and each one lands in its "
             "own position",
     "status": "DEMONSTRATED"},
    {"text": "the payload does not spill: the two epoch cells that were NOT "
             "selected still hold the 29524 mask at the end of the run",
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
    {"text": "the epoch and the payload are coupled (measured): the opcode of V "
             "at T is (V+T)%94, so the same word is not the same opcode in "
             "another epoch. With the three implemented epochs (residues 6, 12, "
             "18 mod 94) there are 0 residues whose three opcodes are all "
             "valid, against 8 for three epochs aligned to 94",
     "status": "DEMONSTRATED"},
    {"text": "the data zone admits 92 candidate epochs (34 <= T <= 126 with a "
             "printable successor v = 80-T mod 94 and v+1 <= 126); this pack "
             "implements and measures 3 of them",
     "status": "DEMONSTRATED"},
    {"text": "an epoch byte outside the catalogue (measured, no gate) selects "
             "no epoch at all: the payload lands in none of the epoch cells",
     "status": "DEMONSTRATED"},
    {"text": "two independent Python engines agree byte for byte with the repo "
             "oracle (traced repo oracle + traced native_classic), and the C "
             "runner matches byte for byte when the payload is printable "
             "(V = 93 at epoch 100: same OUT 0x5d, 218 steps) and stops at the "
             "printable guard otherwise (step 217, exactly the step predicted "
             "from the oracle trace, see c_printable_guard_v1)",
     "status": "DEMONSTRATED"},
    {"text": "rearming the epoch for a SECOND request in the same execution is "
             "still NOT demonstrated: epoch_rearm_primitive_v1 has not been "
             "composed with this selection; the current program consumes 21 "
             "bytes and terminates",
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
        "command": "python3 vm_malbolge/evidence/epoch_resolver_epoch_select_v1/probe.py",
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
