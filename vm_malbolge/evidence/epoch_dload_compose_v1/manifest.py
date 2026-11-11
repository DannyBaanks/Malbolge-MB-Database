#!/usr/bin/env python3
"""Genera manifest.json del pack epoch_dload_compose_v1 (isyco-evidence-pack-v1)."""
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
             "compose_out.mb", "compose_rot.mb", "compose_crazy.mb"]
for _t in ("out", "rot", "crazy"):
    for _c in ("k_off", "no_dload", "op_phase", "dload_phase"):
        ARTIFACTS.append("ctrl_%s_%s.mb" % (_t, _c))
ARTIFACTS += ["results.json", "stdout.raw.txt"]

DEPENDENCIES = {
    "vm_malbolge/evidence/epoch_xlat2_block_v1/probe.py (edge de código)":
        ROOT / "vm_malbolge/evidence/epoch_xlat2_block_v1/probe.py",
    "vm_malbolge/evidence/epoch_xlat2_block_v1/scratch_engine.py":
        ROOT / "vm_malbolge/evidence/epoch_xlat2_block_v1/scratch_engine.py",
    "vm_malbolge/evidence/epoch_dload_reset_v1/probe.py (punto fijo)":
        ROOT / "vm_malbolge/evidence/epoch_dload_reset_v1/probe.py",
    "tools/oracle_classic.py": ROOT / "tools" / "oracle_classic.py",
    "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py":
        ROOT / "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py",
    "runners/malbolge-original/malbolge":
        ROOT / "runners" / "malbolge-original" / "malbolge",
    "Malbolge-PureEpoch/build/olmstead (externo)": OLMSTEAD,
}

CLAIMS = [
    {"text": "C1: para X = OUT, ROT y CRAZY el probe deriva la construcción desde "
             "los ciclos de XLAT2 y los parámetros medidos (no de la tabla de papel) "
             "y los 15 campos coinciden con la predicción de GATES.md",
     "status": "DEMONSTRATED"},
    {"text": "C2: las cuatro ecuaciones del punto fijo, leídas de los bytes de la "
             "imagen, se cumplen; las tres imágenes son imprimibles y sus pares, "
             "trampolín, tabla y semillas llevan los valores calculados",
     "status": "DEMONSTRATED"},
    {"text": "C3: cada composición cierra 10 000 vueltas con exactamente una X y un "
             "DLOAD por vuelta, los únicos opcodes válidos del cuerpo son {4, 40, op}, "
             "todos los JMP caen en 59 y d al empezar la vuelta toma 2 valores",
     "status": "DEMONSTRATED"},
    {"text": "C4: en esa ejecución acotada oráculo, intérprete independiente, motor "
             "scratch y runner C llegan al tope sin parar; en OUT los cuatro emiten "
             "los mismos 10 000 bytes (0x00); trazador, scratch e intérprete "
             "independiente coinciden en el sha256 de la memoria final, y trazador y "
             "scratch en destinos de JMP y d por vuelta",
     "status": "DEMONSTRATED"},
    {"text": "C5: el estado completo (memoria, a, c, d) al empezar la vuelta se "
             "repite con periodo 3060 = mcm(2, 4, 5, 6, 9, 68), el predicho, en los "
             "tres objetivos, y d tiene periodo 2",
     "status": "DEMONSTRATED"},
    {"text": "C6: los doce controles rompen el criterio: k_off (JMP malo en la vuelta "
             "1, destino 60), no_dload (0 DLOAD por vuelta, luego HALT), op_phase "
             "(X por vuelta 2, 0, 2, 0) y dload_phase (algún round cerrado con 2 "
             "DLOADs, enmienda fechada ebaf700)",
     "status": "DEMONSTRATED"},
    {"text": "C7: el bloque de DLOAD que reinicia d de epoch_dload_reset_v1 se "
             "compone con OUT, ROT y CRAZY en un bucle de tabla constante (cierra C9 "
             "de epoch_dload_reset_v1)",
     "status": "DEMONSTRATED"},
    {"text": "C8: componer IN en el mismo bucle",
     "status": "NOT_DEMONSTRATED"},
    {"text": "C9: una variante que pase el cargador de Olmstead 1998 (las tres "
             "imágenes son Classic permisivo 3^10; olmstead rc 1)",
     "status": "NOT_DEMONSTRATED"},
    {"text": "C10: usar la composición dentro de un programa que calcule algo elegido "
             "por la petición",
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
        "command": "python3 -I vm_malbolge/evidence/epoch_dload_compose_v1/probe.py </dev/null",
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
