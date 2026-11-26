#!/usr/bin/env python3
"""crypto/gadget_min.py — expresiones MINIMAS de crazy para las tablas del kit.

Busqueda por conteo de crazy (Dijkstra sobre el closure completo de tablas
por-trit: 19.683 tablas binarias). Para cada tabla guarda la expresion con
el minimo numero de gates. Luego verifica el ripple Kogge-Stone (3 pasos
con duplicado de P) y el kit completo, exhaustivo.
"""
from __future__ import annotations

import hashlib
import heapq
import json
import pathlib

ONE = 29524
TWO = 59048
TBL = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy(x, y):
    out, p = 0, 1
    for _ in range(10):
        out += TBL[(y // p) % 3][(x // p) % 3] * p
        p *= 3
    return out % 59049


def rot(x):
    return x // 3 + (x % 3) * 19683


def left(x, n):
    for _ in range((10 - n) % 10):
        x = rot(x)
    return x


# ---------- busqueda minima por conteo de crazy ----------
def t_const(c):
    return tuple(tuple(c for _ in range(3)) for _ in range(3))


def compose(fa, fb):
    return tuple(tuple(TBL[fb[x][y]][fa[x][y]] for y in range(3)) for x in range(3))


LEAVES = (
    ("x", ((0, 0, 0), (1, 1, 1), (2, 2, 2)), 0),
    ("y", ((0, 1, 2), (0, 1, 2), (0, 1, 2)), 0),
    ("0", t_const(0), 0),
    ("ONE", t_const(1), 0),
    ("TWO", t_const(2), 0),
)

TARGETS = {
    "D": ((0, 1, 2), (1, 2, 0), (2, 0, 1)),
    "G": ((0, 0, 0), (0, 0, 1), (0, 1, 1)),
    "P": ((0, 0, 1), (0, 1, 0), (1, 0, 0)),
    "DS": ((0, 2, 1), (1, 0, 2), (2, 1, 0)),
    "B": ((0, 1, 1), (0, 0, 1), (0, 0, 0)),
    "Q": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
}


def search_min():
    # Dijkstra: (count, table) -> expr minima
    best = {t: (s, c) for s, t, c in LEAVES}
    heap = [(c, i, t, s) for i, (s, t, c) in enumerate(LEAVES)]
    seen_pairs = set()
    found = {}
    while heap and len(found) < len(TARGETS):
        cnt, _, ta, ea = heapq.heappop(heap)
        for tb, (eb, cntb) in list(best.items()):
            for t_new, e_new in ((compose(ta, tb), f"crazy({ea},{eb})"), (compose(tb, ta), f"crazy({eb},{ea})")):
                nc = cnt + cntb + 1
                cur = best.get(t_new)
                if cur is None or nc < cur[1]:
                    if cur is not None:
                        heapq.heappush(heap, (nc, len(heap), t_new, e_new))
                    best[t_new] = (e_new, nc)
                    for name, tgt in TARGETS.items():
                        if name not in found and t_new == tgt:
                            found[name] = (e_new, nc)
                            print(f"{name}: {nc} gates -> {e_new[:80]}")
                    # empujar para expandir
                    heapq.heappush(heap, (nc, len(heap), t_new, e_new))
    return found


def expr_fn(expr):
    def run(x, y):
        return eval(expr, {"__builtins__": {}}, {"x": x, "y": y, "ONE": ONE, "TWO": TWO, "crazy": crazy})
    return run


def bool_and(x, y):
    g1 = crazy(TWO, x)
    g2 = crazy(y, y)
    g3 = crazy(g1, g2)
    return crazy(g3, y)


def bool_or(x, y):
    g1 = crazy(TWO, y)
    g2 = crazy(x, g1)
    return crazy(g2, g1)


def ripple_ks(g, p, steps=(1, 2, 4)):
    """Kogge-Stone: duplica (c,P); cout(k)=Cin(k+1); carry-in = left(c,1)."""
    c = g
    P = p
    for s in steps:
        c = bool_or(c, bool_and(P, left(c, s)))
        P = bool_and(P, left(P, s))
    return left(c, 1)


def main():
    found = search_min()
    missing = [n for n in TARGETS if n not in found]
    if missing:
        raise SystemExit(f"faltan gadgets: {missing}")
    fns = {n: expr_fn(e) for n, (e, _c) in found.items()}
    D, G, P, DS, B, Q = (fns[n] for n in ("D", "G", "P", "DS", "B", "Q"))

    def add(x, y):
        return D(D(x, y), ripple_ks(G(x, y), P(x, y)))

    def sub(x, y):
        return DS(DS(x, y), ripple_ks(B(x, y), Q(x, y)))

    def sub256(x, y):
        return sub(add(x, 256), y)

    bad = bads = 0
    for x in range(256):
        for y in range(256):
            if add(x, y) % 256 != (x + y) % 256:
                bad += 1
            if sub256(x, y) % 256 != (x - y) % 256:
                bads += 1
    print(f"Kogge-Stone add 65.536 casos: fallos={bad} | sub256: fallos={bads}")
    gates = {n: c for n, (e, c) in found.items()}
    print("gates por gadget:", gates, "| adder:", gates["D"] + gates["G"] + gates["P"] + 3 * 6 + gates["D"])
    doc = {
        "claim_status": "DEMONSTRATED" if bad == 0 and bads == 0 else "FAILED",
        "gadgets_min": {n: {"expr": e, "gates": c} for n, (e, c) in found.items()},
        "ripple": "Kogge-Stone shifts (1,2,4) with P-doubling, 3 steps",
        "cases": {"add256": 65536, "sub256": 65536, "failures": bad + bads},
        "adder_gate_estimate": gates["D"] + gates["G"] + gates["P"] + 3 * 6 + gates["D"],
    }
    ev = pathlib.Path(__file__).resolve().parent / "evidence"
    ev.mkdir(exist_ok=True)
    (ev / "gadget_min.json").write_text(json.dumps(doc, indent=2))
    if bad or bads:
        raise SystemExit(3)


if __name__ == "__main__":
    main()