#!/usr/bin/env python3
"""Sonda del upgrade de máscara: identidades medidas que acotan el alcance de v3.

Objetivo: medir por qué la máscara del resolvedor v3 es `121` (byte) y qué
identidades permitirían extender la escritura exacta a palabras de 10 trits.
NO integra el upgrade en la imagen del resolvedor: solo mide y documenta.

Salida por stdout: tabla de identidades y su alcance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

C1 = 29524
MASK = 121


def trits(v: int, n: int = 10) -> list[int]:
    out = []
    for _ in range(n):
        out.append(v % 3)
        v //= 3
    return out


def main() -> int:
    res: dict = {}

    # 1. identidades de fabricacion de mascara
    res["crazy(0,0)"] = {"value": oc.crazy_op(0, 0), "is_C1": oc.crazy_op(0, 0) == C1}
    res["crazy(0,C1)"] = {"value": oc.crazy_op(0, C1), "is_C1": oc.crazy_op(0, C1) == C1}
    res["crazy(1,MASK)"] = {"value": oc.crazy_op(1, MASK), "is_zero": oc.crazy_op(1, MASK) == 0}

    # 2. la doble aplicacion con cada mascara, sobre el rango de byte y sobre
    #    el rango completo de 10 trits
    for name, m in (("MASK_121", MASK), ("C1", C1)):
        byte_ok = all(oc.crazy_op(oc.crazy_op(v, m), m) == v for v in range(256))
        word_ok = all(oc.crazy_op(oc.crazy_op(v, m), m) == v
                      for v in range(0, 59049, 7))
        res[f"involucion_{name}"] = {
            "byte_range_0_255_exacto": byte_ok,
            "muestra_10_trits_0_59048_paso_7_exacto": word_ok,
            "muestras_10_trits": len(range(0, 59049, 7)),
        }

    # 3. por que 121 y no C1 en una celda fuente: printabilidad
    res["printabilidad"] = {
        "MASK_121": 33 <= MASK <= 126,
        "C1": 33 <= C1 <= 126,
        "nota": "el loader Classic exige celdas fuente imprimibles (33..126)",
    }

    # 4. celdas con valor 0 en el relleno de la imagen v3 (origen de C1)
    src = (PACK / "resolver.mb").read_text(encoding="latin-1")
    mem = oc.load_memory(src)
    n_src = len([ch for ch in src if not ch.isspace()])
    zeros = [i for i in range(n_src, oc.MEM_SIZE) if mem[i] == 0]
    res["celdas_cero_en_el_relleno"] = {
        "celdas_rellenadas": oc.MEM_SIZE - n_src,
        "con_valor_cero": len(zeros),
        "primera": zeros[:5],
    }

    # 5.Upgrade medible: 121 -> 0 -> C1 en dos CRAZY (a = 1 y luego a = 0)
    a, m = 1, MASK
    m1 = oc.crazy_op(a, m)
    a1 = m1
    m2 = oc.crazy_op(0, m1)
    res["upgrade_121_a_C1"] = {
        "paso1_crazy(a=1, m=121)": m1,
        "paso2_crazy(a=0, m=paso1)": m2,
        "resultado_es_C1": m2 == C1,
    }

    print(json.dumps(res, indent=2, ensure_ascii=False))
    (PACK / "mask_upgrade.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
