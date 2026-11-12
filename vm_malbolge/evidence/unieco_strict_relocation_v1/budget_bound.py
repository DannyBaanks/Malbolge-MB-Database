#!/usr/bin/env python3
"""Presupuesto de la variante relocalizada: cuantas celdas destino caben.

El planificador (BolgeForge/tools/resynthesize.py) escribe el estado destino
desde la propia imagen fuente: cada celda destino cuesta una cantidad de ops
medida, y el plan vive en una region de la fuente. Este script acota, con los
numeros medidos en synthesis.results.json, cuantas celdas destino caben y
compara ese techo con el tamano de las referencias con deteccion de EOF que si
existen y funcionan (PureEpoch cat_real y ejemplo LMAO con halt en EOF).

No modifica nada: solo lee numeros ya medidos y calcula el limite.
"""
import hashlib, json, pathlib

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
syn = json.loads((P / "synthesis.results.json").read_text())

shift = syn["shift"]
source_len = syn["source_len"]
plan_length = syn["plan_length"]
target_cells = syn["target_cells"]
plan_region_now = 94 * 200                      # parametro del planificador
template_len = source_len - plan_region_now     # longitud de cat.mal de BolgeForge
header = 99                                    # ops empiezan en la posicion 99
tail = 2
max_source_len = shift + 42 - 1                # la fuente no puede invadir el destino
max_plan_ops = max_source_len - template_len - header - tail
ops_per_cell = plan_length / target_cells
cells_now = int(plan_region_now // ops_per_cell)
cells_max = int(max_plan_ops // ops_per_cell)

refs = {
    "pureepoch_cat_real": {
        "_abs": ROOT.parent / "Malbolge-PureEpoch/candidates/cat_real.mal",
        "path": "Malbolge-PureEpoch/candidates/cat_real.mal (repo hermano PureEpoch)",
        "cells": 7972,
        "note": "eco binario + halt limpio en EOF; el loader estricto lo acepta",
    },
    "lmao_example_cat_halt_on_eof": {
        "_abs": ROOT / "third_party/lmao/example_cat_halt_on_eof.hell",
        "path": "third_party/lmao/example_cat_halt_on_eof.hell (este repo)",
        "cells": 20776,
        "note": "fuente HeLL; compilada a 20776 celdas; halt limpio en EOF",
    },
}
for name, r in refs.items():
    p = r.pop("_abs")
    r["exists"] = p.exists()
    r["file_bytes"] = p.stat().st_size if p.exists() else None
    r["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None

dispatch = {
    "option": "tabla de despacho de 256 entradas indexada por el byte exacto",
    "cells": 256,
    "ops": int(256 * ops_per_cell),
    "fits_current_region": 256 * ops_per_cell <= plan_region_now,
    "remaining_ops_in_current_region": plan_region_now - int(256 * ops_per_cell),
    "remaining_cells_in_current_region": int(
        (plan_region_now - 256 * ops_per_cell) // ops_per_cell),
    "note": ("el indice exige el byte EXACTO en una celda, que en un bucle exige "
             "la mascara C1 y su rearme por vuelta (coste medido en las "
             "referencias de la tabla superior)"),
}

report = {
    "measured": {
        "shift": shift,
        "source_len": source_len,
        "plan_length": plan_length,
        "target_cells": target_cells,
        "ops_per_target_cell": round(ops_per_cell, 4),
        "plan_region_now": plan_region_now,
        "template_len": template_len,
        "max_source_len": max_source_len,
        "max_plan_ops": max_plan_ops,
    },
    "bounds": {
        "max_target_cells_current_region": cells_now,
        "max_target_cells_max_region": cells_max,
        "formula": "max_plan_ops / ops_per_target_cell",
    },
    "eof_capable_references": refs,
    "comparison": {
        name: {
            "reference_cells": r["cells"],
            "over_current_region": round(r["cells"] / cells_now, 2),
            "over_max_region": round(r["cells"] / cells_max, 2),
            "fits_current_region": r["cells"] <= cells_now,
            "fits_max_region": r["cells"] <= cells_max,
        } for name, r in refs.items()
    },
    "dispatch_option": dispatch,
    "conclusion": (
        "El techo medido es de %d celdas destino con la region de plan actual y "
        "%d con la region maxima admisible antes de invadir el destino. Las dos "
        "referencias con deteccion de EOF que existen y funcionan necesitan "
        "%d y %d celdas: un factor de reduccion de %.1fx y %.1fx. Una variante "
        "relocalizada con halt en EOF exige por tanto un cuerpo nuevo de como "
        "maximo %d celdas, que no es ninguno de los dos artefactos medidos."
        % (cells_now, cells_max, refs["pureepoch_cat_real"]["cells"],
           refs["lmao_example_cat_halt_on_eof"]["cells"],
           refs["pureepoch_cat_real"]["cells"] / cells_max,
           refs["lmao_example_cat_halt_on_eof"]["cells"] / cells_max,
           cells_max)),
    "not_demonstrated": [
        "el minimo celdas de un cuerpo con deteccion de EOF: solo hay dos "
        "mediciones (7972 y 20776 celdas), ambas por encima del techo",
        "que exista un cuerpo con deteccion de EOF por debajo de %d celdas" % cells_max,
        "que la tabla de despacho de 256 entradas sea viable con rearme por vuelta",
    ],
}

out = json.dumps(report, indent=2, sort_keys=True) + "\n"
(P / "budget_bound.results.json").write_text(out)
print(json.dumps(report, indent=2, sort_keys=True))
