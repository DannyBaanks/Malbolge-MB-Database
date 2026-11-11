#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_dload_reset_v1 (isyco-evidence-pack-v1)."""
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
             "dload_reset.mb", "ctrl_k_off.mb", "ctrl_no_dload.mb",
             "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "vm_malbolge/evidence/epoch_xlat2_block_v1/probe.py (edge de código)":
        ROOT / "vm_malbolge/evidence/epoch_xlat2_block_v1/probe.py",
    "vm_malbolge/evidence/epoch_xlat2_block_v1/scratch_engine.py":
        ROOT / "vm_malbolge/evidence/epoch_xlat2_block_v1/scratch_engine.py",
    "vm_malbolge/evidence/epoch_xlat2_block_v1/dload_block.mb (control histórico)":
        ROOT / "vm_malbolge/evidence/epoch_xlat2_block_v1/dload_block.mb",
    "tools/oracle_classic.py": ROOT / "tools" / "oracle_classic.py",
    "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py":
        ROOT / "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py",
    "runners/malbolge-original/malbolge":
        ROOT / "runners" / "malbolge-original" / "malbolge",
    "Malbolge-PureEpoch/build/olmstead (externo)": OLMSTEAD,
}

CLAIMS = [
    {"text": "C1: las cuatro celdas de dato del punto fijo se calculan en el probe "
             "desde parámetros medidos y coinciden con la predicción en papel de "
             "GATES.md (99<-59, 100<-100, 105<-59, 110<-98)",
     "status": "DEMONSTRATED"},
    {"text": "C2: la tabla de destinos tiene tamaño constante: la imagen mide 111 "
             "celdas para cualquier R (block_v1 necesitaba 525 para R = 60)",
     "status": "DEMONSTRATED"},
    {"text": "C3: dload_reset.mb cierra 10 000 vueltas con exactamente un DLOAD por "
             "vuelta, sólo los opcodes 40 y 4 en el cuerpo, todos los JMP en el "
             "trampolín 59 y d al empezar cada vuelta en {100, 106}",
     "status": "DEMONSTRATED"},
    {"text": "C4: en esas 60 060 instrucciones, trazador, scratch e intérprete "
             "independiente coinciden en la memoria final (sha256 de las 59 049 "
             "celdas); trazador y scratch en destinos de JMP y en d por vuelta; "
             "oráculo y runner C sólo en no parar antes del tope",
     "status": "DEMONSTRATED"},
    {"text": "C5: el estado completo (memoria, a, c, d) al empezar la vuelta se "
             "repite con periodo 1020 = mcm(2, 5, 6, 68), el predicho; en este "
             "dialecto y con esta semántica el bucle se repite para siempre",
     "status": "DEMONSTRATED"},
    {"text": "C6: los tres controles rompen el criterio: K desplazado (JMP malo en "
             "la vuelta 1), sin DLOAD (JMP malo en la vuelta 1, luego HALT) y la "
             "imagen histórica de block_v1 (0 vueltas cerradas)",
     "status": "DEMONSTRATED"},
    {"text": "C7: el bloque de DLOAD (C8 de epoch_xlat2_block_v1) se construye y "
             "ejecuta una vez por vuelta con esta colocación de datos",
     "status": "DEMONSTRATED"},
    {"text": "C8: una variante que pase el cargador de Olmstead 1998",
     "status": "NOT_DEMONSTRATED"},
    {"text": "C9: componer DLOAD con OUT/ROT/CRAZY en el mismo bucle ilimitado",
     "status": "NOT_DEMONSTRATED"},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    artifacts = []
    for name in ARTIFACTS:
        p = PACK / name
        if not p.exists():
            print("FALTA %s" % name, file=sys.stderr)
            return 1
        artifacts.append({"file": name, "sha256": sha256(p)})
    deps = {}
    for label, p in DEPENDENCIES.items():
        if not p.exists():
            print("FALTA dependencia %s" % label, file=sys.stderr)
            return 1
        deps[label] = sha256(p)
    manifest = {
        "schema": "isyco-evidence-pack-v1",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": "python3 -I vm_malbolge/evidence/epoch_dload_reset_v1/probe.py </dev/null",
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
