#!/usr/bin/env python3
"""build.py — epoch_rearm_barrier_v1: tabla de posiciones para el rearm de código.

Este pack NO construye una imagen: es una caracterización. Su artefacto es la
**tabla de posiciones** que dice en qué celdas del programa puede vivir una
instrucción que haya que re-ejecutar, y con qué palabra de control.

## Las tres Mediciones que deciden

M1. El cifrado posterior a la ejecución (`_ENC`, la tabla XLAT2) **no** se
    deshace con rotaciones: `rot^10 = identidad`, luego `rot^k(_ENC[v]) = v`
    no tiene solución para ninguna de las 2400 combinaciones (opcode, celda)
    válidas de las celdas 0..299.

M2. El cifrado **sí** se puede deshacer con un único `CRAZY` cuando la palabra
    de control existe por trit: `TBL[w_d][a_d] = v_d` tiene solución salvo que
    `w_d = 0` y `v_d = 2`. Eso ocurre en el 65% de los pares (opcode, celda):
    839 de 2400, y 290 de las 300 celdas tienen al menos un opcode restaurable.

M3. Pero esa palabra de control **no se puede materializar**: para que el
    acumulador reciba una palabra concreta hace falta una celda sembrada
    (imprimible) de la que cargarla con un `ROT`, y el `ROT` sólo barre la
    órbita de rotación de la palabra sembrada (10 elementos). Medido: **0** de
    las 839 palabras de control son imprimibles y **0** están en una órbita con
    alguna palabra imprimible.

## La vía de dos pasos (y su tabla)

Hay una segunda vía, la que usa `epoch_rearm_primitive_v1`:

    paso 1 (rearm):  celda <- crazy(29524, celda) = extract2(celda)
    paso 2 (cifrado): celda <- crazy(E, E) = 29524        (E = extract2(celda))
    paso 3 (escritura exacta): celda <- crazy(swap01(v), 29524) = v

El paso 3 necesita `a = swap01(v)`, y `v` es el valor original de la celda de
código (imprimible ✓, sembrable ✓). Para cargarlo en `a` con un `ROT` hace
falta que `swap01(v)` esté en la misma órbita de rotación que `v`: **34 de los
3200** pares (opcode, celda) de las celdas 0..399 cumplen esa condición, en 34
celdas distintas.

Ése es el artefacto de este pack: la **tabla de posiciones** (qué celdas admiten
qué opcode re-ejecutable) que un planificador tendría que respetar para que
un bucle pueda re-ejecutar su propio cuerpo.

## Lo que este pack NO mide

No construye el bucle. Mide las condiciones que el bucle tendría que cumplir.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACK = Path(__file__).resolve().parent

VALID_OPS = {4: "JMP", 5: "OUT", 23: "IN", 39: "ROT", 40: "DLOAD",
             62: "CRAZY", 68: "NOP", 81: "END"}
TBL = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
ENCODING = None  # se rellena desde el oráculo del repo en probe.py


def rot(v: int) -> int:
    return v // 3 + (v % 3) * 19683


def orbit(v: int, k: int = 10) -> set[int]:
    s, x = set(), v
    for _ in range(k):
        s.add(x)
        x = rot(x)
    return s


def trits(v: int) -> list[int]:
    return [(v // 3 ** i) % 3 for i in range(10)]


def swap01(v: int) -> int:
    r = 0
    for i, d in enumerate(trits(v)):
        r += (1 if d == 0 else 0 if d == 1 else 2) * 3 ** i
    return r


def extract2(v: int) -> int:
    r = 0
    for i, d in enumerate(trits(v)):
        r += (2 if d == 2 else 0) * 3 ** i
    return r


def ctrl_for(v: int, w: int) -> int | None:
    """Palabra de control `a` con crazy(a, w) = v, o None si no existe."""
    ctrl = 0
    for i in range(10):
        vd, wd = trits(v)[i], trits(w)[i]
        cand = [a for a in range(3) if TBL[wd][a] == vd]
        if not cand:
            return None
        ctrl += cand[0] * 3 ** i
    return ctrl


def position_table(enc: dict[int, int], cells: int = 400) -> dict:
    """Mapa celda -> opcodes re-ejecutables por la vía de dos pasos."""
    table: dict[str, dict] = {}
    for c in range(cells):
        ok = {}
        for v in range(33, 127):
            op = (v + c) % 94
            if op not in VALID_OPS:
                continue
            w = enc[v]
            if swap01(v) in orbit(v):
                ok[str(op)] = {"value": v, "ctrl_needed": swap01(v),
                               "orbit_size": len(orbit(v))}
        if ok:
            table[str(c)] = ok
    return table


def main() -> int:
    import argparse
    sys_path = PACK.parents[2] / "tools"
    import sys
    sys.path.insert(0, str(sys_path))
    import oracle_classic as oc  # noqa: E402

    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    table = position_table(oc._ENC)
    # celdas con las que un bucle podría trabalhar: un opcode re-ejecutable por
    # celda, y el conjunto de direcciones de continuación alcanzables por la
    # vía runtime-built (swap01(A-1) en una órbita imprimible).
    printable = set(range(33, 127))
    continuation = []
    for a in range(35, 400):
        if any(33 <= x <= 126 for x in orbit(swap01(a - 1))):
            continuation.append(a)
    plan = {
        "schema": "isyco-rearm-position-table-v1",
        "cells_with_rearmable_opcodes": len(table),
        "position_table": table,
        "continuation_addresses_runtime_built": continuation,
        "continuation_addresses_seeded": list(range(34, 128)),
        "note": "las direcciones de continuación sembradas sólo llegan a 127; "
                "por encima hace falta la palabra exacta escrita en runtime",
    }
    path = out / "position_table.json"
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf8")
    print("celdas con opcodes re-ejecutables (dos pasos): %d" % len(table))
    print("direcciones de continuación alcanzables por vía sembrada: 34..127")
    print("direcciones de continuación alcanzables por vía runtime-built: %d "
          "(%s..%s)" % (len(continuation), continuation[0], continuation[-1]))
    print("sha256=%s" % hashlib.sha256(path.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
