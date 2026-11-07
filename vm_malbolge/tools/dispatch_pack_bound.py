#!/usr/bin/env python3
"""Cota medida del empaquetado exacto: N=5 es el maximo con coste cero.

Fase 1 (barrido): protocolos mixtos `(a in [243,255], b in [0,242])` — la clase
que gano para N=5 (bandas adyacentes). Para cada uno se comprueba la condicion
NECESARIA de N=6: 6 parejas con los 12 destinos a >= 6 celdas entre si (el
bloque mas corto mide 7 push / 6 pop). Los que pasan se ordenan por capacidad
de empaquetado (cota superior: clusters separados por huecos > 16, que es el
alcance maximo de un bloque con cola 10).

Fase 2 (exacta): en los candidatos de mayor capacidad, busqueda EXHAUSTIVA de
6 parejas con asignacion de colas. Cada hoja se comprueba con un DP sobre los
12 destinos ordenados (posicion, parejas asignadas, colas usadas, fin del
ultimo bloque).

**Por que basta el conjunto de colas (1,2,5,6,9,10).** Una cola valida no puede
diferir en 2 de otra (choque celda JMP / celda de entrada). Ese conjunto es el
minimo componente a componente de todos los conjuntos validos de 6 colas:
cualquier otro conjunto ordenado cumple `t_i >= m_i`. Reasignar por rango al
minimo solo acorta bloques, y acortar intervalos no crea solapes. Si el minimo
no empaqueta, ningun conjunto valido empaqueta.

Controles positivos: el mismo DP debe aceptar las soluciones ya demostradas de
N=4 (`dispatch4_pack.json`) y N=5 (`dispatch5.json`).

Evidencia: vm_malbolge/evidence/dispatch_pack_bound.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import oracle_classic as oc  # noqa: E402

TAILS6 = (1, 2, 5, 6, 9, 10)
# Protocolos de control negativos ademas de los mejores por capacidad:
# (53,65) es el de N=4 (banda unica) y (255,53) el de N=5.
EXTRA = [(53, 65), (255, 53)]


def pairs_for(a: int, b: int):
    d = {}
    for v in range(33, 127):
        p = (oc.crazy_op(a, v), oc.crazy_op(b, v))
        if p not in d:
            d[p] = v
    return sorted(d)


def capacity(land, max_span=16):
    """Cota superior: suma de spans de clusters separados por huecos > 16."""
    if not land:
        return 0
    total = 0
    start = prev = land[0]
    for x in land[1:]:
        if x - prev > max_span:
            total += (prev - start) + max_span
            start = x
        prev = x
    return total + (prev - start)


def spread(n, pairs):
    """Condicion NECESARIA: n parejas con los 2n destinos a >= 6 celdas."""
    found = []

    def rec(i, chosen, used):
        if len(chosen) == n:
            found.append(list(chosen))
            return True
        if len(chosen) + (len(pairs) - i) < n:
            return False
        for j in range(i, len(pairs)):
            p = pairs[j]
            if any(abs(x - u) < 6 for x in p for u in used):
                continue
            chosen.append(p)
            if rec(j + 1, chosen, used + list(p)):
                return True
            chosen.pop()
        return False

    rec(0, [], [])
    return found[0] if found else None


def leaf_ok(sel, tails):
    """DP exacto: asignacion de colas sin solape de bloques."""
    blocks = []
    for i, (p, q) in enumerate(sel):
        blocks.append((p, i, 0))
        blocks.append((q, i, 1))
    blocks.sort()
    n = len(sel)

    @lru_cache(maxsize=None)
    def dp(pos, pm, tm, end):
        if pos == len(blocks):
            return True
        landing, pair, kind = blocks[pos]
        if landing <= end - 1:
            return False
        if pm >> pair & 1:
            return dp(pos + 1, pm, tm, end)
        for k in range(n):
            if tm >> k & 1:
                continue
            t = tails[k]
            length = 6 + t if kind == 0 else 5 + t
            if dp(pos + 1, pm | (1 << pair), tm | (1 << k), landing + length):
                return True
        return False

    return dp(0, 0, 0, -10**9)


def exhaustive(a, b, n, tails, deadline):
    pairs = pairs_for(a, b)
    nodes = leaves = 0
    hit = []

    def rec(i, chosen, used):
        nonlocal nodes, leaves
        nodes += 1
        if time.time() > deadline:
            raise TimeoutError
        if len(chosen) == n:
            leaves += 1
            if leaf_ok(chosen, tails):
                hit.append(list(chosen))
                return True
            return False
        if len(chosen) + (len(pairs) - i) < n:
            return False
        for j in range(i, len(pairs)):
            p = pairs[j]
            if any(abs(x - u) < 6 for x in p for u in used):
                continue
            chosen.append(p)
            stop = rec(j + 1, chosen, used + list(p))
            chosen.pop()
            if stop:
                return True
        return False

    t0 = time.time()
    try:
        rec(0, [], [])
    except TimeoutError:
        return "TIMEOUT", nodes, leaves, time.time() - t0, None
    verdict = "ENCONTRADO" if hit else "NO"
    return verdict, nodes, leaves, time.time() - t0, (hit[0] if hit else None)


def controls():
    out = []
    for name, path in (("n4", "vm_malbolge/evidence/dispatch4_pack.json"),
                       ("n5", "vm_malbolge/evidence/dispatch5.json")):
        d = json.loads((ROOT / path).read_text(encoding="utf-8"))
        p = d["parametros"]
        sel = [tuple(x) for x in p["destinos"]]
        out.append({"caso": name, "imagen": d["imagen"],
                    "sha256": d["sha256"],
                    "dp_acepta": leaf_ok(sel, p["colas"])})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--budget", type=float, default=220.0)
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/dispatch_pack_bound.json")
    args = ap.parse_args()
    args.json = args.json.resolve()

    t_start = time.time()
    ctrl = controls()
    out = {"colas_minimas": list(TAILS6),
           "wlog": "minimo componente a componente; acortar bloques no crea solapes",
           "controles_positivos": ctrl,
           "espacio_barrido": "a in [243,255], b in [0,242]",
           "protocolos_barridos": 13 * 243,
           "protocolos_que_pasan_filtro": 0,
           "candidatos": [],
           "protocolos": []}
    if not all(c["dp_acepta"] for c in ctrl):
        out["veredicto"] = "CONTROL_FALLA"
    else:
        cands = []
        for a in range(243, 256):
            for b in range(0, 243):
                pairs = pairs_for(a, b)
                if not spread(6, pairs):
                    continue
                land = sorted({x for p in pairs for x in p})
                cands.append({"opcodes": [a, b], "parejas": len(pairs),
                              "capacidad": capacity(land)})
        out["protocolos_que_pasan_filtro"] = len(cands)
        cands.sort(key=lambda d: -d["capacidad"])
        chosen = cands[:args.top]
        have = {tuple(c["opcodes"]) for c in chosen}
        for ab in EXTRA:
            if ab not in have:
                pairs = pairs_for(*ab)
                land = sorted({x for p in pairs for x in p})
                chosen.append({"opcodes": list(ab), "parejas": len(pairs),
                               "capacidad": capacity(land), "extra": True})
        out["candidatos"] = chosen

        verdicts = []
        for cand in chosen:
            a, b = cand["opcodes"]
            v, nodes, leaves, secs, sel = exhaustive(
                a, b, 6, TAILS6, time.time() + args.budget)
            row = {"opcodes": [a, b], "capacidad": cand["capacidad"],
                   "veredicto": v, "nodos": nodes, "hojas": leaves,
                   "segundos": round(secs, 1)}
            if sel:
                row["destinos"] = [list(t) for t in sel]
            out["protocolos"].append(row)
            verdicts.append(v)
            print(f"({a},{b}): {v:11s} cap={cand['capacidad']:3d} "
                  f"nodos={nodes:7d} hojas={leaves:7d} {secs:5.1f}s")
            sys.stdout.flush()

        if any(v == "ENCONTRADO" for v in verdicts):
            out["veredicto"] = "N6_ENCONTRADO"
        elif all(v == "NO" for v in verdicts):
            out["veredicto"] = "N6_EXCLUIDO_EN_PROTOCOLOS_MEDIDOS"
        else:
            out["veredicto"] = "N6_NO_DEMOSTRADO"

    out["tiempo_total_s"] = round(time.time() - t_start, 1)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(out, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print("\nveredicto:", out["veredicto"])
    print("filtro: %d/%d protocolos" % (out["protocolos_que_pasan_filtro"],
                                        out["protocolos_barridos"]))
    print("evidencia:", args.json.relative_to(ROOT))
    print("sha256:", hashlib.sha256(args.json.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
