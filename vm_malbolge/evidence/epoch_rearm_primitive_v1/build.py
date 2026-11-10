#!/usr/bin/env python3
"""build.py — epoch_rearm_primitive_v1: dos escrituras exactas en UNA ejecución,
restaurando la máscara entre ambas.

Programa (ver plan.py para el planificador y las zonas):

    S  = 41    celda con 29524, nunca consumida (fuente de recarga por ROT)
    X  = 44    Scratch de fábrica
    A  = 45    máscara de escritura 1 (recibe el payload)
    B  = 46    destino de la escritura exacta (se rearma igual)

  fase 0  bootstrap:  a = 0 (valor inicial) y CRAZY sobre 41 (sembrada 36,
           sin trit 2) → S = 29524, a = 29524
  fase 1  fábrica:    44 → 0 (a=29524), 45 → 29524 (a=0), 46 → 0 (a=29524),
           hop 47→45, 46 → 29524 (a=0)      [A y B con 29524, a = 29524]
  fase 2  escritura 1: IN (a = V), hop → 45, CRAZY 45 (→ swap(V), a = swap(V)),
           CRAZY 46 (→ V EXACTO, a = V), OUT (emite V)
  fase 3  recarga:     ROT sobre S.  29524 es todo 1s, así que es invariante
           bajo ROT: a = 29524 y S intacto
  fase 4  rearmado B:  hop → 46, CRAZY 46 (a=29524 → extract2(V) = E2, a = E2),
           hop → 46, CRAZY 46 (a=E2 → 29524, a = 29524)
  fase 5  rearmado A:  igual sobre 45
  fase 6  escritura 2: IN (a = V2), hop → 45, CRAZY 45 (→ swap(V2)), CRAZY 46
           (→ V2 EXACTO), OUT (emite V2)
           END

Identidades usadas (verificadas en torus_reach_v1):
    crazy(0, v)        = 29524                si v no tiene ningún trit 2
    crazy(V, 29524)    = swap(V)              (0↔1, 2 fijo)
    crazy(swap(V),29524)= V                   ← la escritura exacta
    crazy(29524, X)    = extract2(X)          (2 donde X tiene 2, 0 fuera)
    crazy(E, E)        = 29524                si E sólo tiene trits 0 y 2
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from plan import (DATA_HI, OPS, Planner, PlanError, enc)

S = 41            # fuente de recarga (29524 permanente)
X = 44            # scratch de fábrica
A = 45            # máscara de escritura 1
B = 46            # destino de la escritura
NO_TRIT2 = 36     # 1100_3: sin ningún trit 2
ROTS = 1          # una rotación basta: 29524 es invariante bajo ROT
PAYLOAD1 = 242    # 22222_3: cinco trits 2
PAYLOAD2 = 255    # 100110_3

MUTANTS = ("", "mutant_no_rearm", "mutant_reload_wrong",
           "mutant_boot_trit2", "mutant_write_wrong_cell")


def build(mutant: str = "", payload1: int = 242, payload2: int = 255) -> dict:
    p = Planner()
    # siembras de partida
    boot_seed = 62 if mutant == "mutant_boot_trit2" else NO_TRIT2
    p.seed_free(S, boot_seed)          # 2022_3 en el mutante: el bootstrap falla
    for addr in (X, A, B):
        p.seed_free(addr, NO_TRIT2)

    # ---------- fase 0: bootstrap de S ----------
    # pc0 = DLOAD con mem[0] = 40 (40 decodifica DLOAD en 0) → d = 41
    if p.pc == 0:
        p.seed_free(0, 40)
        p._emit("DLOAD", S)
        p.d = S
        p.log[-1]["arg"] = S
    p.crazy(S)                     # a = 0 → S = 29524, a = 29524

    # ---------- fase 1: fábrica de A y B ----------
    p.ensure_d(X)
    p.crazy(X)                     # a=29524 → X = 0, a = 0
    p.crazy(A)                     # a=0     → A = 29524, a = 29524
    p.crazy(B)                     # a=29524 → B = 0, a = 0
    p.ensure_d(B)                  # hop desde X+3 → B
    p.crazy(B)                     # a=0     → B = 29524, a = 29524

    # ---------- fase 2: escritura 1 ----------
    p.park()
    p.zone_jump()                  # sale de la zona A con d en celda libre
    p.inn()                        # a = V
    p.ensure_d(A)
    p.crazy(A)                     # A = swap(V), a = swap(V)
    p.crazy(B)                     # B = V  (exacto), a = V
    p.out()                        # emite V

    # ---------- fase 3: recarga de a = 29524 ----------
    # 29524 es todo 1s, así que es INVARIANTE bajo ROT: una sola rotación de S
    # deja a = 29524 y la celda S intacta (no se consume).
    rots = 1
    if mutant == "mutant_reload_wrong":
        rots = 0
    if rots:
        p.ensure_d(S)
        p.rot(S)                     # a = rot(29524) = 29524 ; S sigue = 29524
        p.nop(1)                     # no volver a leer la celda de salto
    if mutant == "mutant_reload_wrong":
        # recarga desde A (que guarda swap(V)) en lugar de S: el rearmado falla
        p.ensure_d(A)
        p.rot(A)

    # ---------- fase 4/5: rearmado de B y A ----------
    rearm = mutant != "mutant_no_rearm"
    if rearm:
        p.ensure_d(B)
        p.crazy(B)                 # B = extract2(V) = E2, a = E2
        p.ensure_d(B)
        p.crazy(B)                 # B = 29524, a = 29524
        p.nop(1)
        p.ensure_d(A)
        p.crazy(A)                 # A = extract2(swap(V)) = E1, a = E1
        p.nop(2)
        p.ensure_d(A)
        p.crazy(A)                 # A = 29524, a = 29524

    # ---------- fase 6: escritura 2 ----------
    p.inn()                        # a = V2
    p.nop(1)
    p.ensure_d(A)
    p.crazy(A)                     # A = swap(V2), a = swap(V2)
    p.crazy(B)                     # B = V2 (exacto), a = V2
    p.out()                        # emite V2
    p.end()

    if mutant == "mutant_write_wrong_cell":
        # la escritura aterriza en el scratch X en lugar de la máscara A
        # (celda de salto de la fase 2 redirigida a X-1): sigue en contrato,
        # pero el payload no se escribe donde debe.
        for addr, tgt in sorted(p.hop_used.items()):
            if tgt == A:
                p.mem[addr] = X - 1
                break

    data = p.to_bytes()
    meta = {
        "mutant": mutant or None,
        "payload1": payload1, "payload2": payload2,
        "rots": rots, "rearm": rearm,
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "printable": all(33 <= b <= 126 for b in data),
        "cells": {"S": S, "X": X, "A": A, "B": B},
        "plan": p.summary(),
        "final_a": p.a, "final_d": p.d,
    }
    return {"data": data, "meta": meta, "plan": p}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for m in MUTANTS:
        name = m or "rearm_primitive"
        r = build(m)
        (out / (name + ".mb")).write_bytes(r["data"])
        index[name] = r["meta"]
        print(f"{name:24s} len={r['meta']['length']} instr={r['meta']['plan']['instructions']} "
              f"sha256={r['meta']['sha256'][:16]} imprimible={r['meta']['printable']}")
    (out / "labels.json").write_text(json.dumps(
        {"S": S, "X": X, "A": A, "B": B, "no_trit2_seed": NO_TRIT2,
         "rots": ROTS, "payloads": [242, 255]}, indent=2) + "\n", encoding="utf8")
    (out / "build_index.json").write_text(json.dumps(index, indent=2) + "\n",
                                          encoding="utf8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
