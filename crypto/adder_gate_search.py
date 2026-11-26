#!/usr/bin/env python3
"""M2 — derivacion empirica (nivel TRIT) de los gadgets del sumador completo.

BFS por waves sobre composiciones crazy (TBL[b][a] por trit) con hojas
{x, y, 0, 1, 2}; dedupe por tabla y salida temprana al encontrar objetivos.
Espacio acotado: 3^9 = 19683 tablas binarias distintas.
"""
from __future__ import annotations

import json
import pathlib
import sys

TBL = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy_trit(a, b):
    return TBL[b][a]


def t_const(c):
    return tuple(tuple(c for _ in range(3)) for _ in range(3))


def compose(fa, fb):
    return tuple(
        tuple(crazy_trit(fa[x][y], fb[x][y]) for y in range(3)) for x in range(3)
    )


LEAVES = (
    ("x", ((0, 0, 0), (1, 1, 1), (2, 2, 2))),
    ("y", ((0, 1, 2), (0, 1, 2), (0, 1, 2))),
    ("0", t_const(0)),
    ("ONE", t_const(1)),
    ("TWO", t_const(2)),
)

TARGETS = {
    "D_mod3": ((0, 1, 2), (1, 2, 0), (2, 0, 1)),
    "G_ge3": ((0, 0, 0), (0, 0, 1), (0, 1, 1)),
    "P_eq2": ((0, 0, 1), (0, 1, 0), (1, 0, 0)),
}


def main():
    by_table = {t: (s, 0) for s, t in LEAVES}
    wave = list(LEAVES)
    found = {}
    depth = 0
    while wave and len(found) < len(TARGETS) and depth < 6:
        depth += 1
        nxt = []
        pairs_done = 0
        for expr_a, ta in wave:
            for tb, (expr_b, _d) in list(by_table.items()):
                for new in (compose(ta, tb), compose(tb, ta)):
                    if new in by_table:
                        continue
                    e = f"crazy({expr_a},{expr_b})"
                    by_table[new] = (e, depth)
                    nxt.append((e, new))
                    for name, tgt in TARGETS.items():
                        if name not in found and new == tgt:
                            found[name] = (e, depth)
                            print(f"{name}: ENCONTRADO depth={depth} {e}", flush=True)
                pairs_done += 1
        wave = nxt
        print(f"depth={depth} tablas_nuevas={len(nxt)} total={len(by_table)}", flush=True)
    out = {n: {"found": n in found, "expr": found[n][0] if n in found else None,
               "depth": found[n][1] if n in found else None} for n in TARGETS}
    out["tables_reached"] = len(by_table)
    print("objetivos encontrados:", list(found), "| tablas totales:", len(by_table))
    ev = pathlib.Path(__file__).resolve().parent / "evidence"
    ev.mkdir(exist_ok=True)
    (ev / "adder_gadgets.json").write_text(json.dumps(out, indent=2))
    print("evidencia:", ev / "adder_gadgets.json")
    if len(found) < len(TARGETS):
        sys.exit(3)


if __name__ == "__main__":
    main()