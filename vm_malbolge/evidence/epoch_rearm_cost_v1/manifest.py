#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_rearm_cost_v1 (schema isyco-evidence-pack-v1)."""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]

ARTIFACTS = ["GATES.md", "VERDICT.md", "plan.py", "build.py", "probe.py",
             "manifest.py", "restore.mb", "no_restore.mb", "rearm.mb",
             "build_index.json", "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools/oracle_classic.py",
    "runners/malbolge-original/malbolge":
        ROOT / "runners/malbolge-original/malbolge",
    "vm_malbolge/evidence/epoch_rearm_barrier_v1/position_table.json":
        ROOT / "vm_malbolge/evidence/epoch_rearm_barrier_v1/position_table.json",
    "vm_malbolge/evidence/epoch_audit_v1/AUDIT.md":
        ROOT / "vm_malbolge/evidence/epoch_audit_v1/AUDIT.md",
}

CLAIMS = [
    {"text": "C1: la palabra de control (29552) se carga con 5 instrucciones "
             "(DLOAD,DLOAD,ROT,DLOAD,CRAZY), 3 hops de d y 4 celdas auxiliares "
             "(89,100,101,103), 2 de ellas consumidas (100,103)",
     "status": "DEMONSTRATED"},
    {"text": "C1: la tabla de 34 posiciones de la barrera no contiene la celda "
             "44; swap01(55)=29550 no está en la órbita de 55, así que la vía "
             "de un ROT no puede expresar este restore",
     "status": "DEMONSTRATED"},
    {"text": "C2: una celda de código ya ejecutada (44, OUT) se cifra a 110, se "
             "restaura exactamente a 55 con un CRAZY y se re-ejecuta en la "
             "misma ejecución: salida 2a37, 21 pasos, HALTED",
     "status": "DEMONSTRATED"},
    {"text": "C2 negativo: sin el CRAZY de restauración la segunda visita a 44 "
             "decodifica el opcode 60 (no OUT), no hay CRAZY a 44 y la salida "
             "es 2a",
     "status": "DEMONSTRATED"},
    {"text": "C3: M8 = 12 celdas de código del cuerpo (44,45,46..55), contadas "
             "desde la traza, con 2 re-ejecutadas (44,45); no se usa el "
             "literal 200",
     "status": "DEMONSTRATED"},
    {"text": "C4: el rearm ejecutado de la celda auxiliar 103 (29552 -> 74) "
             "cuesta 7 instrucciones y consume 2 celdas nuevas (90,92)",
     "status": "DEMONSTRATED"},
    {"text": "C4: el ciclo cerrado de rearm no se construyó; cada carga de "
             "palabra de control consume una celda ROT y no hay punto fijo ROT "
             "imprimible",
     "status": "NOT_DEMONSTRATED"},
    {"text": "el cuerpo del bucle de la época tiene 200 celdas",
     "status": "NOT_DEMONSTRATED"},
    {"text": "tres motores (oráculo del repo, trazador, runner C) coinciden en "
             "bytes, pasos y estado en las tres imágenes",
     "status": "DEMONSTRATED"},
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
        "command": "python3 vm_malbolge/evidence/epoch_rearm_cost_v1/probe.py",
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
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf8")
    print(json.dumps({"artifacts": len(artifacts), "dependencies": len(deps),
                      "claims": len(CLAIMS)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
