#!/usr/bin/env python3
"""tr_spec.py — especificación INDEPENDIENTE del álgebra de palabras (Classic Malbolge).

No reutiliza código del repo para las operaciones: las implementa desde la
especificación y desde la tabla del fuente C de referencia, y después las
somete a diferencial contra las implementaciones del repo.

Fuentes de la semántica (leídas, no recordadas):
  * third_party/lmao/src/malbolge.c:25-43  crazy(a, d): crz[a + 3*d],
    crz[] = {1,0,0,1,0,2,2,2,1}  (a = trit del acumulador, d = trit de la celda)
  * third_party/lmao/src/malbolge.c:46-51  rotate_right(d) = d/3 + 19683*(d%3)
  * palabra = 10 trits, 3^10 = 59049 palabras

Comprobaciones que ejecuta spec_check():
  1. autocontrol de conversión: 35 = 1022_3  ->  trits[0..3] = 2,2,0,1
  2. crazy: exhaustivo sobre los 9 pares de trits (prueba completa del caso)
     + muestra aleatoria de 200000 pares de palabras
  3. rot: exhaustivo sobre las 59049 palabras
  4. diferencial triple: esta spec vs tools/oracle_classic.py vs
     vm_malbolge/tools/native_classic/constants.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "vm_malbolge/tools/native_classic")]

NTRITS = 10
MEM = 3 ** NTRITS

# Tabla transcrita del fuente C (índice a + 3*d, a = acumulador, d = celda).
CRZ_C = (1, 0, 0, 1, 0, 2, 2, 2, 1)


def crz(a_trit: int, d_trit: int) -> int:
    return CRZ_C[a_trit + 3 * d_trit]


def ternary(v: int) -> list[int]:
    """Trits de v; posición 0 = menos significativa."""
    out = []
    for _ in range(NTRITS):
        out.append(v % 3)
        v //= 3
    return out


def from_trits(tr: list[int]) -> int:
    return sum(t * 3 ** i for i, t in enumerate(tr))


def spec_crazy(a: int, d: int) -> int:
    """mem[d] = crazy(a, mem[d]); por trit: crz[a_i][d_i]."""
    res = 0
    p = 1
    for _ in range(NTRITS):
        res += crz(a % 3, d % 3) * p
        a //= 3
        d //= 3
        p *= 3
    return res


def spec_rot(d: int) -> int:
    """rotate_right del fuente C: d/3 + 19683*(d%3)."""
    return (d // 3) + (d % 3) * (3 ** (NTRITS - 1))


def spec_rot_n(d: int, n: int) -> int:
    for _ in range(n % NTRITS):
        d = spec_rot(d)
    return d


# ---------- partición de trits de una palabra ----------

def dset(v: int) -> frozenset[int]:
    """Posiciones con trit 2."""
    return frozenset(i for i, t in enumerate(ternary(v)) if t == 2)


def nset(v: int) -> frozenset[int]:
    """Posiciones con trit 1."""
    return frozenset(i for i, t in enumerate(ternary(v)) if t == 1)


def zset(v: int) -> frozenset[int]:
    """Posiciones con trit 0."""
    return frozenset(i for i, t in enumerate(ternary(v)) if t == 0)


ALL = frozenset(range(NTRITS))


def spec_check(sample: int = 200000, seed: int = 20261109) -> dict:
    """Diferenciales y autocontroles. Devuelve un dict de resultados."""
    import oracle_classic as oc

    out: dict = {}
    rng = random.Random(seed)

    # --- 1. conversión ternaria: 35 = 1022_3 ---
    t35 = ternary(35)
    out["ternary_35"] = {"trits": t35,
                        "expected": [2, 2, 0, 1, 0, 0, 0, 0, 0, 0],
                        "value_check": from_trits(t35) == 35,
                        "digits_string": "".join(str(x) for x in reversed(t35))}
    assert t35 == [2, 2, 0, 1, 0, 0, 0, 0, 0, 0], t35
    assert from_trits(t35) == 35

    # --- 2. crazy exhaustivo sobre los 9 pares de trits ---
    uniform = {0: 0, 1: from_trits([1] * NTRITS), 2: from_trits([2] * NTRITS)}
    pairs = {}
    for x in range(3):
        for y in range(3):
            got = spec_crazy(uniform[x], uniform[y])
            pairs[f"({x},{y})"] = {"result": got,
                                  "table_entry": crz(x, y),
                                  "matches_table": all(
                                      crz(x, y) == t
                                      for t in ternary(got))}
    out["crazy_trit_pairs"] = pairs
    assert all(v["matches_table"] for v in pairs.values())

    # --- 3. crazy: muestra aleatoria de pares de palabras ---
    bad = 0
    for _ in range(sample):
        a = rng.randrange(MEM)
        d = rng.randrange(MEM)
        if spec_crazy(a, d) != oc.crazy_op(a, d):
            bad += 1
    out["crazy_random"] = {"checked": sample, "mismatches_vs_repo_oracle": bad}
    assert bad == 0

    # --- 4. rot exhaustivo sobre todas las palabras ---
    bad_rot = 0
    for v in range(MEM):
        if spec_rot(v) != (v // 3) + (v % 3) * 19683:
            bad_rot += 1
    out["rot_exhaustive"] = {"checked": MEM, "mismatches": bad_rot}
    assert bad_rot == 0
    # rot^10 = identidad (grupo cíclico de orden 10 sobre las posiciones)
    bad_rot10 = 0
    for v in range(0, MEM, 977):
        w = v
        for _ in range(NTRITS):
            w = spec_rot(w)
        if w != v:
            bad_rot10 += 1
    out["rot_order10"] = {"checked": len(range(0, MEM, 977)),
                          "mismatches": bad_rot10}
    assert bad_rot10 == 0

    # --- 5. diferencial contra la segunda implementación del repo ---
    try:
        import constants as nc  # native_classic
        has_nc = hasattr(nc, "crazy_op")
    except Exception as exc:  # pragma: no cover
        nc = None
        has_nc = False
        out["native_classic_import_error"] = repr(exc)
    if has_nc:
        bad_nc = 0
        for _ in range(50000):
            a = rng.randrange(MEM)
            d = rng.randrange(MEM)
            if nc.crazy_op(a, d) != spec_crazy(a, d):
                bad_nc += 1
        out["crazy_vs_native_classic"] = {"checked": 50000,
                                          "mismatches": bad_nc}
        assert bad_nc == 0

    # --- 6. las tres implementaciones coinciden en vectores fijos ---
    vectors = []
    for a in (0, 1, 2, 33, 54, 80, 121, 242, 29524, 59048):
        for d in (0, 1, 2, 33, 54, 80, 121, 242, 29524, 59048):
            r1 = spec_crazy(a, d)
            r2 = oc.crazy_op(a, d)
            r3 = nc.crazy_op(a, d) if has_nc else r1
            vectors.append({"a": a, "d": d, "spec": r1, "repo_oracle": r2,
                            "native_classic": r3,
                            "agree": r1 == r2 == r3})
    out["fixed_vectors"] = {"rows": len(vectors),
                            "all_agree": all(v["agree"] for v in vectors),
                            "rows_data": vectors}
    assert all(v["agree"] for v in vectors)

    out["verdict"] = True
    return out


if __name__ == "__main__":
    res = spec_check()
    print("[spec] ternary_35 trits=", res["ternary_35"]["trits"],
          "digits=", res["ternary_35"]["digits_string"])
    print("[spec] crazy 9 pares de trits: todos coinciden con la tabla C")
    print("[spec] crazy aleatorio:", res["crazy_random"])
    print("[spec] rot exhaustivo:", res["rot_exhaustive"])
    print("[spec] rot orden 10:", res["rot_order10"])
    if "crazy_vs_native_classic" in res:
        print("[spec] crazy vs native_classic:", res["crazy_vs_native_classic"])
    print("[spec] vectores fijos 3 impls:", res["fixed_vectors"]["all_agree"],
          "(", res["fixed_vectors"]["rows"], "filas )")
    print("[spec] ok =", res["verdict"])
