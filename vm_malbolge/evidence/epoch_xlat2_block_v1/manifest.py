#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_xlat2_block_v1 (isyco-evidence-pack-v1)."""
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

ARTIFACTS = ["GATES.md", "VERDICT.md", "probe.py", "scratch_engine.py",
             "manifest.py", "out_block.mb", "out_block_ctrl_phase.mb",
             "out_block_ctrl_filler.mb", "rot_block.mb", "crazy_block.mb",
             "dload_block.mb", "results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "tools/oracle_classic.py": ROOT / "tools" / "oracle_classic.py",
    "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py":
        ROOT / "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py",
    "runners/malbolge-original/malbolge":
        ROOT / "runners" / "malbolge-original" / "malbolge",
    "tools/fixtures/hello_world_40.mb":
        ROOT / "tools" / "fixtures" / "hello_world_40.mb",
    "Malbolge-PureEpoch/build/olmstead (externo)": OLMSTEAD,
}

CLAIMS = [
    {"text": "C1: el cálculo del bloque (posiciones, valores, relleno, trampolín, "
             "JMP, tabla) se deriva en el probe de los ciclos de XLAT2, y la "
             "puerta G0 (tercera pasada) lo comprueba leyendo los bytes de la "
             "imagen con código propio y las tablas del motor scratch; cinco "
             "imágenes rotas a propósito la fallan",
     "status": "DEMONSTRATED"},
    {"text": "C2: out_block.mb hace la operación exactamente una vez por vuelta "
             "durante 60 vueltas, con PCs alternantes 119/123 y sin ningún "
             "opcode perjudicial en el cuerpo",
     "status": "DEMONSTRATED"},
    {"text": "C3: oráculo, intérprete independiente, trazador (que registra "
             "bytes), runner C y motor scratch (escrito desde la especificación "
             "de 1998, validado con el vector 'Hello World!' a 40 pasos) "
             "coinciden byte a byte y en el paso exacto de cada uno de los 60 OUT "
             "(tope s-1 / s); la memoria final coincide en trazador, scratch e "
             "intérprete independiente",
     "status": "DEMONSTRATED"},
    {"text": "C4: el control de desfase produce 2 y 0 operaciones por vuelta "
             "alternadas",
     "status": "DEMONSTRATED"},
    {"text": "C5: el control de relleno no inocuo decodifica el opcode "
             "perjudicial 39 en el cuerpo del bucle",
     "status": "DEMONSTRATED"},
    {"text": "C6: el bloque de ROT se construye y ejecuta exactamente una vez "
             "por vuelta durante 60 vueltas, con el d medido por paridad",
     "status": "DEMONSTRATED"},
    {"text": "C7: el bloque de CRAZY se construye y ejecuta exactamente una vez "
             "por vuelta durante 60 vueltas, con el d medido por paridad",
     "status": "DEMONSTRATED"},
    {"text": "C8: el bloque de DLOAD se construye y ejecuta con esta colocación",
     "status": "NOT_DEMONSTRATED"},
    {"text": "C9: una variante del bloque que pase el cargador de Olmstead 1998",
     "status": "NOT_DEMONSTRATED"},
    {"text": "C10: los 60 JMP de out_block.mb, rot_block.mb y crazy_block.mb "
             "caen todos en el trampolín, comprobado dentro del probe",
     "status": "DEMONSTRATED"},
    {"text": "C11: las puertas G0..G4 están computadas en el probe (G0 recalcula "
             "la construcción con controles negativos, G1 compara cinco motores en "
             "bytes y en el paso de cada OUT, G3 exige el opcode 39 concreto y G4 "
             "es un check de regresión contra lo publicado en 3bbdfb5, no un "
             "pre-registro)",
     "status": "DEMONSTRATED"},
    {"text": "C12: el bloque de IN se construye pero no se ejecuta (no medido)",
     "status": "NOT_DEMONSTRATED"},
    {"text": "C13: en rot/crazy/dload_block, oráculo, scratch, runner C e "
             "intérprete independiente coinciden en pasos y HALT, y la memoria "
             "final coincide en trazador, scratch e indep (fuera de G0..G4; la "
             "memoria del oráculo y del runner C no se compara)",
     "status": "DEMONSTRATED"},
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
        "command": "python3 -I vm_malbolge/evidence/epoch_xlat2_block_v1/probe.py </dev/null",
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
