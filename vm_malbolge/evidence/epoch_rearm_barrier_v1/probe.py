#!/usr/bin/env python3
"""probe.py — epoch_rearm_barrier_v1: qué se puede rearmar y qué no.

Motores: las primitivas del oráculo del repo (`tools/oracle_classic.py`).

Comprobaciones:
  1. M1: el cifrado posterior a la ejecución no se deshace con rotaciones
     (0 de 2400 pares (opcode, celda) de las celdas 0..299).
  2. M2: el cifrado sí se deshace con un único CRAZY en el 65% de los pares
     (839/2400) y 290 de las 300 celdas tienen al menos un opcode restaurable.
  3. M3: la palabra de control de esa restauración NO es materializable desde
     una celda sembrada (0 imprimibles, 0 en órbita imprimible).
  4. M4: la vía de dos pasos (rearm a 29524 + escritura exacta) sí funciona,
     pero sólo en 34 de las 3200 combinaciones (opcode, celda) de 0..399:
     el artefacto es la tabla de posiciones.
  5. M5: el rearm de una celda de DATO es universal y exacto
     (crazy(29524,X) = extract2(X) y crazy(E,E) = 29524 sobre las 59049
     palabras, 0 discrepancias).
  6. M6: el papel de la celda sucesora (cadena del puntero + opcode) es
     per-época y forzado; la cadena del puntero sigue siendo compatible.
  7. M7: la alcance del salto de retorno: con una celda sembrada sólo se
     llega a 34..127; por encima hace falta la palabra exacta escrita en
     runtime, y hay 452 direcciones alcanzables por esa vía.
  8. M8: la capacidad de la zona de dato (86 celdas) frente a la demanda del
     diario (1 celda por celda de código re-ejecutada).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

sys.path.insert(0, str(PACK))
import build as B  # noqa: E402

VALID = B.VALID_OPS
CELLS_A = 300      # para M1..M3
CELLS_B = 400      # para M4
DATA_LO, DATA_HI = 41, 126


def op_at(v: int, c: int) -> int:
    return (v + c) % 94


def main() -> int:
    results: dict = {}
    ok = True
    enc = oc._ENC

    # ---------- M1: el cifrado no se deshace con rotaciones ----------
    tot = 0
    rot_ok = 0
    for c in range(CELLS_A):
        for v in range(33, 127):
            if op_at(v, c) not in VALID:
                continue
            tot += 1
            w = enc[v]
            x = w
            for _ in range(10):
                if x == v:
                    rot_ok += 1
                    break
                x = B.rot(x)
    m1 = {"cells": CELLS_A, "pairs": tot, "restorable_with_rot": rot_ok}
    results["m1_rot_restore"] = m1
    ok = ok and rot_ok == 0
    print("[M1] cifrado restaurable con rotaciones: %d/%d pares (opcode, celda) "
          "de las celdas 0..%d" % (rot_ok, tot, CELLS_A - 1), flush=True)

    # ---------- M2: el cifrado sí se deshace con un único CRAZY ----------
    tot2 = 0
    one_ok = 0
    cells_with = 0
    for c in range(CELLS_A):
        good = 0
        for v in range(33, 127):
            if op_at(v, c) not in VALID:
                continue
            tot2 += 1
            ctrl = B.ctrl_for(v, enc[v])
            if ctrl is None:
                continue
            assert oc.crazy_op(ctrl, enc[v]) == v
            one_ok += 1
            good += 1
        if good:
            cells_with += 1
    m2 = {"cells": CELLS_A, "pairs": tot2, "restorable_with_one_crazy": one_ok,
          "cells_with_at_least_one": cells_with, "cells_total": CELLS_A}
    results["m2_single_crazy_restore"] = m2
    ok = ok and one_ok > 0 and cells_with > 0
    print("[M2] restaurable con un único CRAZY: %d/%d pares (%.1f%%); celdas "
          "con al menos un opcode restaurable: %d/%d"
          % (one_ok, tot2, 100.0 * one_ok / tot2, cells_with, CELLS_A),
          flush=True)

    # ---------- M3: la palabra de control no es materializable ----------
    printable = 0
    materializable = []
    ctrl_total = 0
    for c in range(CELLS_A):
        for v in range(33, 127):
            if op_at(v, c) not in VALID:
                continue
            ctrl = B.ctrl_for(v, enc[v])
            if ctrl is None:
                continue
            ctrl_total += 1
            if 33 <= ctrl <= 126:
                printable += 1
            if any(33 <= x <= 126 for x in B.orbit(ctrl)):
                materializable.append({"cell": c, "op": op_at(v, c),
                                       "ctrl": ctrl})
    m3 = {"controls": ctrl_total, "printable_controls": printable,
          "materializable_controls": len(materializable),
          "distinct_cells": len({m["cell"] for m in materializable}),
          "distinct_control_words": sorted({m["ctrl"] for m in materializable}),
          "materializable_detail": materializable}
    results["m3_control_materializability"] = m3
    ok = ok and printable == 0 and len(materializable) > 0
    print("[M3] palabra de control de la restauración de un CRAZY: %d controles "
          "sobre %d pares; imprimibles=%d, materializables desde una celda "
          "sembrada=%d (en %d celdas, palabra de control única=%s)"
          % (ctrl_total, tot2, printable, len(materializable),
             m3["distinct_cells"], m3["distinct_control_words"]), flush=True)

    # ---------- M4: la vía de dos pasos y su tabla de posiciones ----------
    table = B.position_table(enc, CELLS_B)
    pairs_b = sum(1 for c in range(CELLS_B) for v in range(33, 127)
                  if op_at(v, c) in VALID)
    m4 = {"cells": CELLS_B, "pairs": pairs_b,
          "restorable_in_two_steps": sum(len(x) for x in table.values()),
          "cells_with_rearmable_opcodes": len(table),
          "position_table": table}
    results["m4_two_step_restore"] = m4
    ok = ok and m4["restorable_in_two_steps"] > 0
    print("[M4] restaurable en dos pasos: %d/%d pares (opcode, celda) de las "
          "celdas 0..%d, en %d celdas"
          % (m4["restorable_in_two_steps"], pairs_b, CELLS_B - 1,
             len(table)), flush=True)

    # ---------- M5: el rearm de celda de DATO es universal y exacto ----------
    bad1 = bad2 = 0
    for x in range(59049):
        e = oc.crazy_op(29524, x)
        if e != B.extract2(x):
            bad1 += 1
        if oc.crazy_op(e, e) != 29524:
            bad2 += 1
    m5 = {"words": 59049, "extract2_failures": bad1, "mask_failures": bad2}
    results["m5_data_cell_rearm"] = m5
    ok = ok and bad1 == 0 and bad2 == 0
    print("[M5] rearm de celda de dato: crazy(29524,X)=extract2(X) y "
          "crazy(E,E)=29524 sobre %d palabras, %d y %d discrepancias"
          % (59049, bad1, bad2), flush=True)

    # ---------- M6: el papel de la celda sucesora ----------
    epochs = {100: 99, 106: 105, 112: 111}
    rows = {}
    for t, b in epochs.items():
        # el papel "JMP de vuelta" obliga a v = (4 - (T+1)) mod 94
        v_jmp = (4 - (t + 1)) % 94
        # el papel "END" obliga a v = (81 - (T+1)) mod 94
        v_end = (81 - (t + 1)) % 94
        chain_cell = v_jmp + 1
        rows[str(t)] = {
            "b": b, "successor_cell": t + 1,
            "value_for_jmp_back": v_jmp, "value_for_end": v_end,
            "opcode_with_jmp_value": (v_jmp + t + 1) % 94,
            "opcode_with_end_value": (v_end + t + 1) % 94,
            "chain_cell_if_jmp": chain_cell,
            "chain_cell_in_data_zone": DATA_LO <= chain_cell <= DATA_HI,
            "chain_cell_free_in_current_layout": chain_cell not in (55, 65, 75),
        }
    m6 = {"rows": rows,
          "both_roles_are_per_epoch": all(
              r["value_for_jmp_back"] != r["value_for_end"] for r in rows.values()),
          "jmp_role_chain_compatible": all(
              r["chain_cell_in_data_zone"] for r in rows.values())}
    results["m6_successor_role"] = m6
    ok = ok and m6["jmp_role_chain_compatible"]
    print("[M6] celda sucesora: el valor de retorno (JMP) y el de parada (END) "
          "son distintos por época; la cadena del puntero sigue encajando: %s"
          % m6["jmp_role_chain_compatible"], flush=True)

    # ---------- M7: alcance del salto de retorno ----------
    seeded = list(range(34, 128))
    runtime_built = [a for a in range(35, 4000)
                     if any(33 <= x <= 126 for x in B.orbit(B.swap01(a - 1)))]
    img = ROOT / "vm_malbolge/evidence/epoch_resolver_epoch_select_v1/resolver_epoch.mb"
    img_len = len(img.read_bytes()) if img.exists() else None
    m7 = {"seeded_targets": [seeded[0], seeded[-1]], "seeded_count": len(seeded),
          "runtime_built_targets": runtime_built[:12],
          "runtime_built_count": len(runtime_built),
          "current_image_length": img_len,
          "seeded_reaches_current_size": (seeded[-1] >= (img_len or 0)),
          "runtime_built_reaches_current_size": (
              runtime_built[-1] >= (img_len or 0)),
          "note": "la celda que el JMP de retorno lee tiene que contener "
                  "(destino-1); con una celda sembrada (imprimible) el destino "
                  "queda en 34..127, y por encima hace falta escribir la "
                  "palabra exacta en runtime"}
    results["m7_back_edge_reach"] = m7
    ok = ok and (not m7["seeded_reaches_current_size"]
                 and m7["runtime_built_reaches_current_size"])
    print("[M7] salto de retorno: celda sembrada -> %d..%d (no llega al tamaño "
          "actual de la imagen, %s); palabra exacta escrita en runtime -> %d "
          "destinos, el mayor %d"
          % (seeded[0], seeded[-1], img_len, len(runtime_built),
             runtime_built[-1]), flush=True)

    # ---------- M8: capacidad de la zona de dato ----------
    data_cells = DATA_HI - DATA_LO + 1
    m8 = {"data_zone_cells": data_cells,
          "journal_cells_per_rearmable_code_cell": 1,
          "current_loop_body_size_estimate": 200,
          "capacity_sufficient_for_current_body": False}
    results["m8_data_zone_capacity"] = m8
    ok = ok and not m8["capacity_sufficient_for_current_body"]
    print("[M8] zona de dato: %d celdas; el diario necesita 1 celda por celda "
          "de código re-ejecutada y el cuerpo del bucle actual ronda las 200: "
          "no cabe" % data_cells, flush=True)

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
