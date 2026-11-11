#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_xlat2_phase_census_v1 (isyco-evidence-pack-v1)."""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
OLMSTEAD = PACK.parents[3] / "Malbolge-PureEpoch" / "build" / "olmstead"

ARTIFACTS = ["GATES.md", "VERDICT.md", "probe.py", "manifest.py",
             "jmp_control.mb", "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools" / "oracle_classic.py",
    "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py":
        ROOT / "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py",
    "vm_malbolge/evidence/epoch_rearm_budget_v1/results.json":
        ROOT / "vm_malbolge/evidence/epoch_rearm_budget_v1/results.json",
    "Malbolge-PureEpoch/build/olmstead (externo)": OLMSTEAD,
}

CLAIMS = [
    {"text": "C1: XLAT2 tiene exactamente un ciclo de cada longitud 2,4,5,6,9,68 "
             "(censo 2,4,5,6,9,68) y coincide con epoch_rearm_budget_v1 q6",
     "status": "DEMONSTRATED"},
    {"text": "C2: para OUT, IN, ROT, DLOAD y CRAZY no existe ventana desfasada "
             "en ningún ciclo: 0 posiciones sobre 94x6x5",
     "status": "DEMONSTRATED"},
    {"text": "C3: la causa es estructural — el ciclo de 68 no tiene ningún "
             "desplazamiento bueno (todo desplazamiento tiene >=2 opcodes "
             "válidos) y en los ciclos cortos la racha máxima de desplazamientos "
             "buenos es menor que L",
     "status": "DEMONSTRATED"},
    {"text": "C4: la versión válida al cargar también es 0, por ser subconjunto "
             "de las ventanas",
     "status": "DEMONSTRATED"},
    {"text": "C5: una celda JMP ejecutada conserva su valor (98->98) y el JMP "
             "cifra la celda destino (64->81), medido en oráculo, trazador e "
             "intérprete independiente",
     "status": "DEMONSTRATED"},
    {"text": "C6: Olmstead 1998 carga la imagen de control (todas las celdas "
             "válidas al cargar) y termina con rc 0 y stdout vacío",
     "status": "DEMONSTRATED"},
    {"text": "C7: el censo de JMP como control también es NO_WINDOW",
     "status": "DEMONSTRATED"},
    {"text": "C8: el cuerpo 'ventana + JMP de vuelta' se ejecutó 2L vueltas "
             "para cada (X,L) con ventana",
     "status": "NOT_DEMONSTRATED"},
    {"text": "C9: el resolvedor rediseñado sobre ciclos XLAT2 cortos queda "
             "construido y verificado",
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
        "command": "python3 -I vm_malbolge/evidence/epoch_xlat2_phase_census_v1/probe.py </dev/null",
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
