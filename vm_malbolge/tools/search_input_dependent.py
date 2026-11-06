#!/usr/bin/env python3
"""Búsqueda vectorizada del comparador de DOS operandos variables.

Ataque al hueco que la prueba de no-existencia deja abierto
(`vm_malbolge/evidence/cmp2_two_operand_blocker.json`): esa prueba cubre
cadenas de ROT + CRAZY-con-constante, que son funciones separables de los
trits de entrada. Queda fuera el caso en que el operando del CRAZY es una
celda cuyo contenido depende de la entrada.

Mecanismo (op 62, CRAZY): `mem[d] = crazy(a, mem[d])`. Una receta puede:

    IN A          a = A
    p @celda(C)   a = crazy(A, C);  mem[celda] = crazy(A, C)   <- almacena A
    IN B          a = B
    p @celda      a = crazy(B, crazy(A, C))   <- depende de AMBOS
    ...cadena...  rot / crazy(constante) sobre el acumulador
    OUT           a & 255

CRAZY es trit a trit, así que se descompone en 10 trits y se vectoriza sobre
una matriz (N estados x 100 pares): eso es lo que hace el barrido viable en
Python en lugar de un estado por vez.

Uso (desde la raíz del repo):
    python3 vm_malbolge/tools/search_input_dependent.py [--max-depth D]
"""
import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "native_classic"))

PAIRS = [(48 + a, 48 + b) for a in range(10) for b in range(10)]
CLS1 = np.array([a < b for a in range(10) for b in range(10)])   # 45 pares
CLS0 = ~CLS1                                                      # 55 pares
CONSTS = np.arange(33, 127, dtype=np.int64)

POW3 = np.array([3 ** i for i in range(10)], dtype=np.int64)
# TBL[cell_trit][ctrl_trit], de native_classic/constants.py (_CRAZY_TRITS)
TBL = np.array([[1, 0, 0], [1, 0, 2], [2, 2, 1]], dtype=np.int64)

A_VEC = np.array([p[0] for p in PAIRS], dtype=np.int64)
B_VEC = np.array([p[1] for p in PAIRS], dtype=np.int64)


def crazy_const(x, c):
    """crazy(x, c) vectorizado; x es un array (cualquier forma), c escalar."""
    out = np.zeros_like(x)
    for i in range(10):
        out += TBL[(c // POW3[i]) % 3, (x // POW3[i]) % 3] * POW3[i]
    return out


def rot_rows(mat):
    return mat // 3 + (mat % 3) * (3 ** 9)


def separated(mat):
    """Filas cuyo byte bajo separa las dos clases (un valor por clase)."""
    low = mat & 255
    v1, v0 = low[:, CLS1], low[:, CLS0]
    return (np.all(v1 == v1[:, :1], axis=1)
            & np.all(v0 == v0[:, :1], axis=1)
            & (v1[:, 0] != v0[:, 0]))


def class_spread(mat):
    """Por fila: valores distintos dentro de cada clase (menor = más cerca)."""
    low = mat & 255
    out = np.zeros(len(mat), dtype=np.int64)
    for i in range(len(mat)):
        out[i] = len(set(low[i][CLS1].tolist())) + len(set(low[i][CLS0].tolist()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=10)
    ap.add_argument("--beam", type=int, default=4000)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    print("=== búsqueda vectorizada (beam): comparador de dos operandos ===")
    print("modelo: crazy(B, crazy(A, C)) + cadena rot/crazy(const)")
    print(f"constantes candidatas: {len(CONSTS)}; profundidad máx: {args.max_depth}; "
          f"beam: {args.beam}")
    print(f"pares: {int(CLS1.sum())} clase 1 (a<b), {int(CLS0.sum())} clase 0\n")

    best = None
    hits = []
    for C in CONSTS:
        stored = crazy_const(A_VEC, int(C))
        state = crazy_const(B_VEC, stored)
        if separated(state.reshape(1, -1))[0]:
            hits.append({"C": int(C), "chain_length": 0})
            print(f"*** C={C}: separa SIN cadena adicional")
            continue
        frontier = state.reshape(1, -1).copy()
        for depth in range(args.max_depth):
            cand = [rot_rows(frontier)]
            for c in CONSTS:
                cand.append(crazy_const(frontier, int(c)))
            allc = np.vstack(cand)
            mask = separated(allc)
            if mask.any():
                hit = allc[mask][0]
                hits.append({"C": int(C), "chain_length": depth + 1,
                             "class1_byte": int(hit[CLS1][0] & 255),
                             "class0_byte": int(hit[CLS0][0] & 255)})
                print(f"*** C={C}: separa con cadena de longitud {depth + 1} "
                      f"-> clase1={int(hit[CLS1][0] & 255)}, "
                      f"clase0={int(hit[CLS0][0] & 255)}")
                break
            spread = class_spread(allc)
            # Callejon sin salida: la fila entera colapsa a un solo valor.
            # Una vez ahi, cualquier operacion punto a punto da otro valor
            # unico: nunca podra separar. Fuera del beam.
            low_all = allc & 255
            constant_row = np.all(low_all == low_all[:, :1], axis=1)
            alive = ~(constant_row & ~mask)
            keep_pool = allc[alive]
            keep_spread = class_spread(keep_pool) if len(keep_pool) else np.array([999])
            keep = np.argsort(keep_spread)[: args.beam]
            frontier = keep_pool[keep]
            if keep_spread[keep[0]] == 2 and separated(keep_pool[keep[:1]])[0]:
                print(f"    C={C} d{depth}: spread 2 con valores distintos en el beam")
        if hits:
            break
        score = len(set((state & 255).tolist()))
        if best is None or score > best[1]:
            best = (int(C), score)

    print()
    if hits:
        print(f"RESULTADO: {len(hits)} solución(es). El comparador de dos operandos "
              f"SÍ existe en esta clase de funciones.")
    else:
        print("RESULTADO: ninguna solución hasta la profundidad dada.")
        if best:
            print(f"  mejor constante C={best[0]} con {best[1]} pares distintos "
                  f"(hacen falta 100 para separar)")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(__import__("json").dumps({
            "schema": "input-dependent-cmp-search/1",
            "claim": ("Whether a two-operand comparator exists when the CRAZY operand is "
                      "an input-dependent stored cell (the gap the separability proof leaves open)."),
            "model": "state = crazy(B, crazy(A, C)); then a chain of rot/crazy(const)",
            "max_depth": args.max_depth,
            "constants_tried": len(CONSTS),
            "solutions": hits,
            "best_constant": {"C": best[0], "distinct_pairs": best[1]} if best else None,
        }, indent=2), encoding="utf-8")
        print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
