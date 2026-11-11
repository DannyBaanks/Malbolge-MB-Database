#!/usr/bin/env python3
"""build.py — construye las tres imágenes de `epoch_rearm_cost_v1`.

  restore.mb     : OUT(X) -> cifrado -> CRAZY de restauración -> OUT(X) -> END
  no_restore.mb  : el mismo programa sin el CRAZY (control negativo)
  rearm.mb       : el programa con restauración y, después, el rearm ejecutado
                   de la celda auxiliar 103 (ctrl -> v2)

El planificador simula en vivo: cada `put` ejecuta la instrucción y el build
falla si una aserción de estado no se cumple. Después se comprueba la imagen
volcada contra el oráculo del repo (no contra valores escritos a mano: contra la
semántica de referencia).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
sys.path.insert(0, str(PACK))
import plan  # noqa: E402

EXPECT = {
    "restore": {"output": bytes([42, 55]), "steps": 21, "status": "HALTED"},
    "no_restore": {"output": bytes([42]), "steps": 21, "status": "HALTED"},
    "rearm": {"output": bytes([42]), "steps": 28, "status": "HALTED"},
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    index = {"schema": "isyco-build-index-v1", "pack": PACK.name,
             "dialect": "classic-permissive-3^10", "images": {}}
    for name, p, info in plan.images():
        data = p.dump()
        (PACK / (name + ".mb")).write_bytes(data)
        got = plan.oc.oracle_run(str(PACK / (name + ".mb")), 500)
        out = got["output"].encode("latin-1")
        want = EXPECT[name]
        if (out, got["steps"], got["status"]) != (want["output"],
                                                  want["steps"],
                                                  want["status"]):
            print(f"FALLA {name}: oráculo {out.hex()} {got['steps']} "
                  f"{got['status']} != {want['output'].hex()} "
                  f"{want['steps']} {want['status']}", file=sys.stderr)
            return 1
        if not all(33 <= b <= 126 for b in data):
            print(f"FALLA {name}: byte no imprimible", file=sys.stderr)
            return 1
        index["images"][name] = {
            "sha256": sha256(data),
            "length": len(data),
            "info": info,
            "seeds": {str(k): v for k, v in sorted(p.seeds.items())},
            "code": {str(k): v for k, v in sorted(p.code.items())},
            "plan_log": p.log,
            "plan_final": {"a": p.a, "c": p.c, "d": p.d,
                           "out": p.out, "status": p.status},
            "oracle": {"output_hex": out.hex(), "steps": got["steps"],
                       "status": got["status"]},
        }
        print("%-10s len=%3d sha256=%s out=%s steps=%d %s ctrl=%d"
              % (name, len(data), sha256(data)[:16], out.hex(),
                 got["steps"], got["status"], info["ctrl"]))
    path = PACK / "build_index.json"
    path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf8")
    print("build_index.json sha256=%s" % sha256(path.read_bytes()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
