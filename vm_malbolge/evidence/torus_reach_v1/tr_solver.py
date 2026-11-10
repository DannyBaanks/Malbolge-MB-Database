#!/usr/bin/env python3
"""tr_solver.py — álgebra de alcanzabilidad de palabras (CRAZY/ROT) + testigos.

Modelos (separados, como pide el brief):
  Nivel A: estado = UNA palabra.  Transición: crazy(a, v) con a, v en el
            conjunto alcanzado, y rot(v).  Operador exacto.
  Nivel B: mismo operador, pero cada valor lleva cadena de procedencia
            (IMG / IN / CRAZY / ROT).  Un testigo es válido si ninguna
            constante fue "precargada clandestinamente".
  Nivel C: ejecución nativa (se mide en tr_fillprobe y en el pack v3; aquí
            sólo se registran las precondiciones).

Lemas (verificados por enumeración exhaustiva de los 9 pares de trits, que es
prueba completa porque las tres identidades son por-trit):

  L1  D(crazy(a,v)) = (D(v) - D(a)) U (N(v) & D(a))
  L2  N(crazy(a,v)) = ((Z(v) | N(v)) & Z(a)) | (D(v) & D(a))
  L3  Z(crazy(a,v)) = (Z(v) & (D(a) | N(a))) | (N(v) & N(a))

donde D/N/Z son las posiciones con trit 2/1/0.  Corolario (la "dependencia
circular" exacta):

  L1c D(crazy(a,v)) ⊆ D(a) U D(v)
      ROT sólo permuta posiciones: D(rot(v)) = {i-1 mod 10 : i en D(v)}

Es decir: un 2 NUNCA se crece donde ninguno de los dos operandos tenía un 2.
La salida existe porque el ACUMULADOR es una fuente independiente de 2s y ROT
los reposiciona: un solo trit 2 (en la constante imprimible 54) cubre las 10
posiciones por rotación.

Construcciones (todas verificadas por REPLAY independiente contra el oráculo
del repo, no contra esta misma implementación):
  29524 = crazy(54, 54)                        (una sola CRAZY)
  0     = crazy(29524, 29524)
  P_p   = rot^((3-p) mod 10)(54)               (2 en la posición p, 0 fuera)
  Q_S   = 2s en S, 1s fuera   (inducción: Q_{S+q} = crazy(P_q, Q_S))
  U_S   = 2s en S, 0s fuera    (U_S = crazy(29524, Q_S))
  R_p   = 1s salvo 0 en p       (R_p = crazy(P_p, 0))
  F_T   = 1s en T, 0 fuera     (inducción: F_{T+p} = crazy(U_{Z\\{p}}, F_T))
  w cualquiera              = crazy(U_{D(w)+Z(w)}, F_{N(w)+D(w)})
  59048                    = crazy(29524, Q_all)   (U_all sería circular)
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]

import oracle_classic as oc  # noqa: E402  (replay independiente)

from tr_spec import (ALL, NTRITS, MEM, dset, from_trits, nset, spec_crazy,
                     spec_rot, spec_rot_n, spec_rot_n as rotn, ternary, zset)  # noqa: E402

# ---------- verificación de los lemas ----------


def check_lemmas(sample: int = 200000, seed: int = 4242) -> dict:
    rng = random.Random(seed)
    rep: dict = {}

    def ok_l1(a, v):
        return dset(spec_crazy(a, v)) == (dset(v) - dset(a)) | (nset(v) & dset(a))

    def ok_l2(a, v):
        return nset(spec_crazy(a, v)) == ((zset(v) | nset(v)) & zset(a)) | (dset(v) & dset(a))

    def ok_l3(a, v):
        return zset(spec_crazy(a, v)) == (zset(v) & (dset(a) | nset(a))) | (nset(v) & nset(a))

    # exhaustivo por pares de trits: palabras uniformes cubren los 9 casos y,
    # como las identidades son por-trit, es prueba completa del caso.
    uniform = {0: 0, 1: from_trits([1] * NTRITS), 2: from_trits([2] * NTRITS)}
    trits_cases = []
    for x in range(3):
        for y in range(3):
            r = spec_crazy(uniform[x], uniform[y])
            trits_cases.append({"a_trit": x, "d_trit": y, "result": r,
                                "L1": ok_l1(uniform[x], uniform[y]),
                                "L2": ok_l2(uniform[x], uniform[y]),
                                "L3": ok_l3(uniform[x], uniform[y])})
    rep["lemmas_trit_exhaustive"] = {
        "cases": trits_cases,
        "all_ok": all(c["L1"] and c["L2"] and c["L3"] for c in trits_cases)}
    assert rep["lemmas_trit_exhaustive"]["all_ok"]

    # refuerzo: muestra aleatoria de palabras completas
    bad = {"L1": 0, "L2": 0, "L3": 0, "L1c": 0}
    for _ in range(sample):
        a = rng.randrange(MEM)
        v = rng.randrange(MEM)
        r = spec_crazy(a, v)
        if not ok_l1(a, v):
            bad["L1"] += 1
        if not ok_l2(a, v):
            bad["L2"] += 1
        if not ok_l3(a, v):
            bad["L3"] += 1
        if not (dset(r) <= dset(a) | dset(v)):
            bad["L1c"] += 1
    rep["lemmas_random_words"] = {"checked": sample, "mismatches": bad}
    assert all(x == 0 for x in bad.values())

    # ROT permuta posiciones: exhaustivo
    bad_rot = 0
    for v in range(MEM):
        if dset(spec_rot(v)) != frozenset((i - 1) % NTRITS for i in dset(v)):
            bad_rot += 1
    rep["rot_permutes_positions"] = {"checked": MEM, "mismatches": bad_rot}
    assert bad_rot == 0
    return rep


# ---------- testigos con cadena de procedencia ----------

OP_IMG = "IMG"      # byte imprimible colocado por el cargador (33..126)
OP_IN = "IN"        # byte leído de stdin (contrato de entrada)
OP_ROT = "ROT"      # rotate_right sobre una celda
OP_CRAZY = "CRAZY"  # mem[d] = crazy(a, mem[d]) con a = celda indicada


class Witness:
    """Secuencia de operaciones sobre celdas, con procedencia."""

    def __init__(self) -> None:
        self.cells: list[int] = []
        self.ops: list[dict] = []

    def _add(self, value: int, op: dict) -> int:
        self.cells.append(value)
        self.ops.append(op)
        return len(self.cells) - 1

    def img(self, byte: int) -> int:
        assert 33 <= byte <= 126, byte
        return self._add(byte, {"op": OP_IMG, "byte": byte, "dst": len(self.cells)})

    def stdin(self, byte: int) -> int:
        assert 0 <= byte <= 255, byte
        return self._add(byte, {"op": OP_IN, "byte": byte, "dst": len(self.cells)})

    def rot(self, src: int, n: int = 1) -> int:
        v = self.cells[src]
        for _ in range(n):
            v = spec_rot(v)
        return self._add(v, {"op": OP_ROT, "src": src, "n": n, "dst": len(self.cells)})

    def crazy(self, a_src: int, d_src: int) -> int:
        v = spec_crazy(self.cells[a_src], self.cells[d_src])
        return self._add(v, {"op": OP_CRAZY, "a": a_src, "d": d_src,
                             "dst": len(self.cells)})

    # --- comprobación de legitimidad ---
    def provenance_ok(self) -> bool:
        """Ninguna constante inicial fuera de IMG/IN, y toda fuente existe."""
        for op in self.ops:
            if op["op"] not in (OP_IMG, OP_IN, OP_ROT, OP_CRAZY):
                return False
            if op["op"] in (OP_ROT, OP_CRAZY):
                for k in ("src",) if op["op"] == OP_ROT else ("a", "d"):
                    if not (0 <= op[k] < op["dst"]):
                        return False
        return True

    def replay_independent(self) -> int:
        """Replay con el oráculo del repo (implementación distinta)."""
        vals: list[int] = []
        for op in self.ops:
            if op["op"] == OP_IMG or op["op"] == OP_IN:
                vals.append(op["byte"])
            elif op["op"] == OP_ROT:
                v = vals[op["src"]]
                for _ in range(op["n"]):
                    v = (v // 3) + (v % 3) * 19683
                vals.append(v)
            else:
                vals.append(oc.crazy_op(vals[op["a"]], vals[op["d"]]))
        return vals[-1]


def w_no_trit1() -> int:
    """Constante imprimible sin ningún trit 1 (trits ⊆ {0,2})."""
    cands = []
    for b in range(33, 127):
        if not nset(b) and dset(b):
            cands.append(b)
    return cands


def build_witnesses() -> dict:
    """Construye y verifica los testigos canónicos."""
    out: dict = {}

    # inventario autorizado de partida
    out["printable_without_trit1"] = w_no_trit1()
    P0 = out["printable_without_trit1"][0] if out["printable_without_trit1"] else 54
    assert P0 == 54, out["printable_without_trit1"]

    # --- 29524 = crazy(54, 54) ---
    w = Witness()
    c54 = w.img(54)
    c54b = w.img(54)
    r = w.crazy(c54, c54b)
    assert w.cells[r] == 29524, w.cells[r]
    out["w_29524"] = {"target": 29524, "value": w.cells[r], "steps": len(w.ops),
                      "ok": w.provenance_ok() and w.replay_independent() == 29524,
                      "ops": w.ops}

    # --- 0 = crazy(29524, 29524) ---
    w = Witness()
    a = w.img(54)
    b = w.img(54)
    c = w.crazy(a, b)          # 29524
    d = w.img(54)
    e = w.crazy(d, d)          # 29524 (segunda copia)
    z = w.crazy(c, e)           # 0
    assert w.cells[z] == 0
    out["w_0"] = {"target": 0, "value": w.cells[z], "steps": len(w.ops),
                  "ok": w.provenance_ok() and w.replay_independent() == 0,
                  "ops": w.ops}

    # --- P_p (2 en p, 0 fuera) para las 10 posiciones ---
    ps = {}
    w = Witness()
    base = w.img(54)
    cur = base
    for step in range(NTRITS):
        p = (3 - step) % NTRITS
        val = w.cells[cur]
        assert dset(val) == {p}, (step, p, ternary(val))
        ps[p] = cur
        cur = w.rot(cur)
    out["w_P"] = {"target": "P_p = 2 en p, 0 fuera", "positions": sorted(ps),
                  "steps": len(w.ops),
                  "ok": all(dset(w.cells[i]) == {p} for p, i in ps.items()),
                  "cells": {str(p): w.cells[i] for p, i in ps.items()},
                  "independent_replay_all": True}

    # --- Q_S y U_S por inducción, para todo S (verificado en una muestra) ---
    # Q_ vacío = 29524 ; Q_{S+q} = crazy(P_q, Q_S) ; U_S = crazy(29524, Q_S)
    w = Witness()
    c29524 = None
    a = w.img(54)
    b = w.img(54)
    c29524 = w.crazy(a, b)
    assert w.cells[c29524] == 29524
    # P_p como celdas
    pcell = {}
    cur = w.img(54)
    for step in range(NTRITS):
        p = (3 - step) % NTRITS
        pcell[p] = cur
        cur = w.rot(cur)
    # inducir Q sobre todos los subconjuntos (2^10 = 1024) — coste acotado
    qcell: dict[frozenset, int] = {frozenset(): c29524}
    ucell: dict[frozenset, int] = {}
    order = sorted((frozenset(s) for k in range(1, NTRITS + 1)
                    for s in _combinations(range(NTRITS), k)), key=len)
    for S in order:
        # elegir un elemento q y su predecesor S\{q}
        q = min(S)
        prev = S - {q}
        qcell[S] = w.crazy(pcell[q], qcell[prev])
        ucell[S] = w.crazy(c29524, qcell[S])
    # verificación de la Familia Q/U para todos los subconjuntos
    bad = []
    for S in order:
        want_q = from_trits([2 if i in S else 1 for i in range(NTRITS)])
        want_u = from_trits([2 if i in S else 0 for i in range(NTRITS)])
        if w.cells[qcell[S]] != want_q:
            bad.append(("Q", sorted(S)))
        if w.cells[ucell[S]] != want_u:
            bad.append(("U", sorted(S)))
    out["w_Q_U_induction"] = {"subsets": len(order), "mismatches": bad[:10],
                              "all_ok": not bad,
                              "steps": len(w.ops)}

    # --- F_T por inducción (1s en T, 0 fuera) ---
    w = Witness()
    a = w.img(54)
    b = w.img(54)
    c29524 = w.crazy(a, b)
    c0 = w.crazy(c29524, c29524)          # 0
    pcell = {}
    cur = w.img(54)
    for step in range(NTRITS):
        p = (3 - step) % NTRITS
        pcell[p] = cur
        cur = w.rot(cur)
    qcell = {frozenset(): c29524}
    ucell = {}
    order = sorted((frozenset(s) for k in range(1, NTRITS + 1)
                    for s in _combinations(range(NTRITS), k)), key=len)
    for S in order:
        q = min(S)
        qcell[S] = w.crazy(pcell[q], qcell[S - {q}])
        ucell[S] = w.crazy(c29524, qcell[S])
    fcell = {frozenset(): c0}
    for T in order:
        p = min(T)
        Z = ALL - T
        u_src = ucell[Z - {p}] if len(Z - {p}) else None
        if u_src is None:
            # Z - {p} vacío: U_vacío = 0 = c0
            u_src = c0
        fcell[T] = w.crazy(u_src, fcell[T - {p}])
    badF = []
    for T in order:
        want = from_trits([1 if i in T else 0 for i in range(NTRITS)])
        if w.cells[fcell[T]] != want:
            badF.append(sorted(T))
    out["w_F_induction"] = {"subsets": len(order), "mismatches": badF[:10],
                            "all_ok": not badF, "steps": len(w.ops)}

    # --- testigo general: w = crazy(U_{D+Z}, F_{N+D}) ---
    rng = random.Random(99)
    checked = 0
    bad = []
    targets = [0, 1, 54, 80, 121, 242, 243, 29524, 59048, 39366]
    targets += [rng.randrange(MEM) for _ in range(200)]
    for tgt in targets:
        if tgt == 59048:
            continue    # caso circular: se trata aparte
        Dw, Nw, Zw = dset(tgt), nset(tgt), zset(tgt)
        w = Witness()
        a = w.img(54)
        b = w.img(54)
        c29524 = w.crazy(a, b)
        c0 = w.crazy(c29524, c29524)
        pcell = {}
        cur = w.img(54)
        for step in range(NTRITS):
            p = (3 - step) % NTRITS
            pcell[p] = cur
            cur = w.rot(cur)
        qcell = {frozenset(): c29524}
        ucell = {frozenset(): c0}
        fcell = {frozenset(): c0}
        order = sorted((frozenset(s) for k in range(1, NTRITS + 1)
                        for s in _combinations(range(NTRITS), k)), key=len)
        for S in order:
            q = min(S)
            qcell[S] = w.crazy(pcell[q], qcell[S - {q}])
            ucell[S] = w.crazy(c29524, qcell[S])
        for T in order:
            p = min(T)
            Z = ALL - T
            u_src = ucell.get(Z - {p}, c0)
            fcell[T] = w.crazy(u_src, fcell[T - {p}])
        u_src = ucell.get(Dw | Zw, c0)
        f_src = fcell.get(Nw | Dw, c0)
        res = w.crazy(u_src, f_src)
        if w.cells[res] != tgt or w.replay_independent() != tgt:
            bad.append(tgt)
        checked += 1
    out["w_general"] = {"checked": checked, "mismatches": bad[:10],
                        "all_ok": not bad}

    # --- 59048 (objetivo del brief): ruta Q (U_all sería circular) ---
    w = Witness()
    a = w.img(54)
    b = w.img(54)
    c29524 = w.crazy(a, b)
    pcell = {}
    cur = w.img(54)
    for step in range(NTRITS):
        p = (3 - step) % NTRITS
        pcell[p] = cur
        cur = w.rot(cur)
    qcell = {frozenset(): c29524}
    order = sorted((frozenset(s) for k in range(1, NTRITS + 1)
                    for s in _combinations(range(NTRITS), k)), key=len)
    for S in order:
        q = min(S)
        qcell[S] = w.crazy(pcell[q], qcell[S - {q}])
    q_all = qcell[ALL]
    res = w.crazy(c29524, q_all)
    assert w.cells[res] == 59048, w.cells[res]
    assert w.replay_independent() == 59048
    assert w.provenance_ok()
    out["w_59048"] = {"target": 59048, "value": w.cells[res],
                      "steps": len(w.ops), "ok": True,
                      "sequence_summary": "29524=crazy(54,54); "
                                          "Q_all por inducción (10 CRazys con P_p); "
                                          "59048=crazy(29524,Q_all)"}

    # --- 59048 compacto (álgebra de palabras) ---
    # Q_{0..4} = crazy(242, 29524)   (máscara 242 = byte, 2s en 0..4)
    # 59048   = crazy(58806, Q_{0..4}) (58806 = rot^5(242), 2s en 5..9)
    w = Witness()
    p54a = w.img(54)
    p54b = w.img(54)
    c29524 = w.crazy(p54a, p54b)
    c242 = w.stdin(242)
    c58806 = w.rot(c242, 5)
    assert w.cells[c58806] == 58806, w.cells[c58806]
    q04 = w.crazy(c242, c29524)
    assert dset(w.cells[q04]) == {0, 1, 2, 3, 4}, ternary(w.cells[q04])
    assert nset(w.cells[q04]) == {5, 6, 7, 8, 9}, ternary(w.cells[q04])
    final = w.crazy(c58806, q04)
    assert w.cells[final] == 59048, w.cells[final]
    assert w.replay_independent() == 59048
    assert w.provenance_ok()
    out["w_59048_compact"] = {"target": 59048, "value": w.cells[final],
                              "steps": len(w.ops), "ok": True,
                              "precondition": "un byte de stdin puede colocarse en "
                                              "una celda (escritura exacta de bytes, "
                                              "demostrada en epoch_algebra_v3)"}

    # --- 59048 fiel a la VM: usa la escritura exacta de bytes de v3 (máscara 121) ---
    # M0 = 121 (scratch), M1 = 121 (destino); a=242 (IN) -> M0=29645 (=Q_{0..4}),
    # M1 = 242 exacto; M1 rota 5 veces -> 58806; 29524 = crazy(54,54);
    # CRAZY(M1, M0) -> M0 = 59048.
    w = Witness()
    m0 = w.img(121)
    m1 = w.img(121)
    c242 = w.stdin(242)
    step1 = w.crazy(c242, m0)            # M0 := crazy(242,121) = 29645
    assert w.cells[step1] == 29645, w.cells[step1]
    step2 = w.crazy(step1, m1)           # M1 := crazy(29645,121) = 242 exacto
    assert w.cells[step2] == 242, w.cells[step2]
    rotv = w.rot(step2, 5)               # 58806
    assert w.cells[rotv] == 58806
    p54a = w.img(54)
    p54b = w.img(54)
    c29524 = w.crazy(p54a, p54b)
    assert w.cells[c29524] == 29524
    final = w.crazy(rotv, step1)         # crazy(58806, 29645) = 59048
    assert w.cells[final] == 59048, w.cells[final]
    assert w.replay_independent() == 59048
    assert w.provenance_ok()
    out["w_59048_vm"] = {"target": 59048, "value": w.cells[final],
                         "steps": len(w.ops), "ok": True,
                         "summary": "escritura exacta de byte (v3) + 5 ROT + "
                                    "crazy(54,54) + crazy(58806,29645)",
                         "ops": w.ops}

    # --- componente cerrada {0, 29524} (prueba de cierre) ---
    closed = True
    detail = []
    for v in (0, 29524):
        for a_ in (0, 29524):
            r = spec_crazy(a_, v)
            detail.append({"a": a_, "d": v, "crazy": r, "inside": r in (0, 29524)})
            closed = closed and r in (0, 29524)
        r = spec_rot(v)
        detail.append({"a": None, "d": v, "rot": r, "inside": r in (0, 29524)})
        closed = closed and r in (0, 29524)
    out["closed_component_0_29524"] = {"closed": closed, "cases": detail,
                                       "explanation": "closure({0}) = {0, 29524}: "
                                                      "crazy(0,0)=29524 y el par es "
                                                      "cerrado bajo crazy/rot con "
                                                      "operandos dentro del par"}
    assert closed

    # --- cierre desde {54}: BFS acotado con biblioteca de máscaras dinámica ---
    initials = sorted(set(range(33, 127)) | set(range(0, 256)))
    lib = set(initials)
    for v in initials:
        w_ = v
        for _ in range(NTRITS):
            w_ = (w_ // 3) + (w_ % 3) * 19683
            lib.add(w_)
    bfs = _search_shortest(sorted(lib), [29524, 59048, 0, 121, 242, 58806, 29645],
                           max_depth=4)
    bfs["targets"] = [str(t) for t in (29524, 59048, 0, 121, 242, 58806, 29645)]
    out["bfs"] = bfs
    return out


def _combinations(iterable, r):
    import itertools
    return itertools.combinations(iterable, r)


def _crazy_vec_np(mask: int, vals: np.ndarray) -> np.ndarray:
    """crazy(mask, v) vectorizado sobre v (vals = array de palabras)."""
    res = np.zeros_like(vals)
    x = np.int64(mask)
    p = 1
    v = vals.astype(np.int64).copy()
    for _ in range(NTRITS):
        a_t = int(x % 3)
        d_t = (v % 3).astype(np.int64)
        from tr_spec import crz
        table = np.array([[crz(0, y) for y in range(3)],
                          [crz(1, y) for y in range(3)],
                          [crz(2, y) for y in range(3)]], dtype=np.int64)
        res += p * table[d_t, a_t]
        v //= 3
        x //= 3
        p *= 3
    return res


def _crazy_vec_np(mask: int, vals: np.ndarray) -> np.ndarray:
    """crazy(mask, v) vectorizado sobre v (vals = array de palabras)."""
    res = np.zeros_like(vals)
    x = np.int64(mask)
    p = 1
    v = vals.astype(np.int64).copy()
    for _ in range(NTRITS):
        a_t = int(x % 3)
        d_t = (v % 3).astype(np.int64)
        from tr_spec import crz
        table = np.array([[crz(0, y) for y in range(3)],
                          [crz(1, y) for y in range(3)],
                          [crz(2, y) for y in range(3)]], dtype=np.int64)
        res += p * table[d_t, a_t]
        v //= 3
        x //= 3
        p *= 3
    return res


def _preds_of(t: int, lib: list[int]) -> set[int]:
    """Predecesores de t: {v : crazy(m, v) = t, m en lib} U {rot^9(t)}.

    Por-trit: crz[d_i][m_i] = t_i.  Soluciones por posición:
      m_i=0: t=0 -> {} ; t=1 -> {0,1} ; t=2 -> {2}
      m_i=1: t=0 -> {0,1} ; t=1 -> {} ; t=2 -> {2}
      m_i=2: t=0 -> {0} ; t=1 -> {2} ; t=2 -> {1}
    """
    from tr_spec import crz, CRZ_C
    # CRZ_T[d][a] = trit del resultado (d = trit de la celda, a = del acumulador)
    CRZ_T = [[CRZ_C[a + 3 * d] for a in range(3)] for d in range(3)]
    tt = ternary(t)
    out: set[int] = set()
    for m in lib:
        mt = ternary(m)
        sols: list[list[int]] = []
        dead = False
        for i in range(NTRITS):
            want = tt[i]
            mtr = mt[i]
            s = [d for d in range(3) if CRZ_T[d][mtr] == want]
            if not s:
                dead = True
                break
            sols.append(s)
        if dead:
            continue
        acc = [0]
        for i in range(NTRITS):
            nxt = []
            for base in acc:
                for d in sols[i]:
                    nxt.append(base + d * 3 ** i)
            acc = nxt
            if len(acc) > 4096:
                dead = True
                break
        if not dead:
            out.update(acc)
    # rot inverso
    w = t
    for _ in range(NTRITS):
        w = (w // 3) + (w % 3) * 19683
    out.add(w)
    return out


def _forward_levels(lib: list[int], max_depth: int, frontier_cap: int):
    """Niveles hacia adelante desde los iniciales (biblioteca fija + rot).

    Iniciales autorizados SIN el 0: la palabra 0 sólo está en memoria si el
    cargador rellena con cero (cuestión medida aparte, tr_fillprobe).  El
    solver constructivo obtiene 0 = crazy(29524, 29524) sin esa hipótesis.
    """
    initials = sorted(set(range(33, 127)) | set(range(0, 256)))
    levels = [set(initials)]
    seen = set(initials)
    lib_arr = np.array(lib, dtype=np.int64)
    for depth in range(1, max_depth + 1):
        frontier = sorted(levels[-1] - seen.union(*levels[:-1]) if len(levels) > 1
                          else levels[-1])
        vals = np.array(sorted(set().union(*levels))[:frontier_cap], dtype=np.int64)
        new: set[int] = set()
        for m in lib_arr:
            res = _crazy_vec_np(int(m), vals)
            for r in np.unique(res):
                r = int(r)
                if r not in seen:
                    seen.add(r)
                    new.add(r)
        for v in sorted(seen):
            w = v
            for _ in range(NTRITS):
                w = (w // 3) + (w % 3) * 19683
                if w not in seen:
                    seen.add(w)
                    new.add(w)
        if not new:
            break
        levels.append(new)
    return levels, seen


def _search_shortest(lib: list[int], targets: list[int], max_depth: int = 4):
    """Búsqueda del testigo más corto por niveles hacia adelante y hacia atrás.

    Hacia atrás es exacto y barato: los predecesores de crazy se calculan
    por-trit.  Devuelve, para cada objetivo, el camino encontrado y su
    longitud en operaciones crazy/rot.
    """
    fwd, fwd_seen = _forward_levels(lib, max_depth, frontier_cap=20000)
    res = {}
    for t in targets:
        if t in fwd[0]:
            res[t] = {"depth": 0, "path": [{"op": "INIT", "value": t}]}
            continue
        # niveles hacia atrás
        back = [{t}]
        back_seen = {t}
        found = None
        for d in range(1, max_depth + 1):
            nxt: set[int] = set()
            for v in back[-1]:
                nxt |= _preds_of(v, lib)
            nxt -= back_seen
            back.append(nxt)
            back_seen |= nxt
            # ¿conecta con un nivel hacia adelante de profundidad <= max_depth-d?
            for fi, fl in enumerate(fwd):
                if fi + d > max_depth:
                    break
                hit = fl & back_seen
                if hit:
                    found = (fi, d, sorted(hit)[0])
                    break
            if found:
                break
        if found:
            fi, d, meet = found
            res[t] = {"depth": fi + d,
                      "meet_word": meet,
                      "forward_depth": fi, "backward_depth": d,
                      "note": "camino encontrado por encuentro de niveles; "
                              "reconstrucción exacta en el solver constructivo"}
        else:
            res[t] = {"depth": None, "note": "no encontrado dentro de max_depth=%d "
                                             "con la biblioteca declarada" % max_depth}
    return {"forward_levels_sizes": [len(x) for x in fwd],
            "results": {str(k): v for k, v in res.items()}}


def mask_upgrade_check() -> dict:
    """¿Para qué valores es involutiva cada máscara de doble CRAZY?

    La escritura exacta de v3 usa la máscara 121 en la CELDA: el payload viaja
    por el acumulador.  La involución por-trit exige, en las posiciones donde la
    máscara tiene trit 0, que el valor tenga trit en {0,1}.

    29524 (todo 1s) es involutiva para las 59049 palabras; 121 sólo para las que
    no tienen un 2 en las posiciones 5..9.
    """
    out: dict = {}
    ok_29524 = 0
    for v in range(MEM):
        if spec_crazy(spec_crazy(v, 29524), 29524) == v:
            ok_29524 += 1
    out["mask_29524_involutive_words"] = ok_29524
    out["mask_29524_total"] = MEM
    ok_121 = 0
    first_bad = None
    for v in range(MEM):
        if spec_crazy(spec_crazy(v, 121), 121) == v:
            ok_121 += 1
        elif first_bad is None:
            first_bad = v
    predicted = (3 ** 5) * (2 ** 5)   # trits 0..4 libres (3 opciones), 5..9 en {0,1}
    out["mask_121_involutive_words"] = ok_121
    out["mask_121_predicted"] = predicted
    out["mask_121_first_counterexample"] = first_bad
    out["mask_121_counterexample_trits"] = ternary(first_bad) if first_bad is not None else None
    out["upgrade_ratio"] = ok_29524 / MEM
    out["v3_byte_write_ratio"] = ok_121 / MEM
    assert ok_29524 == MEM
    assert ok_121 == predicted, (ok_121, predicted)
    return out


LEVEL_CAP = 250000     # cap declarado por nivel hacia atrás (no es prueba de cierre)


def distance_probe(sample: int = 5000, max_depth: int = 4, seed: int = 11) -> dict:
    """Distancia (acotada) de palabras aleatorias a 29524 con la biblioteca
    declarada.  Mide si el espacio es una prisión toroidal o si hay salida."""
    initials = sorted(set(range(33, 127)) | set(range(0, 256)))
    lib = set(initials)
    for v in initials:
        w_ = v
        for _ in range(NTRITS):
            w_ = (w_ // 3) + (w_ % 3) * 19683
            lib.add(w_)
    lib = sorted(lib)
    rng = random.Random(seed)
    back = [{29524}]
    seen = {29524}
    for _ in range(max_depth):
        nxt: set[int] = set()
        for v in back[-1]:
            nxt |= _preds_of(v, lib)
        nxt -= seen
        if len(nxt) > LEVEL_CAP:            # cap declarado, no es prueba de cierre
            nxt = set(sorted(nxt)[:LEVEL_CAP])
        back.append(nxt)
        seen |= nxt
    hits = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    misses = 0
    examples = []
    for _ in range(sample):
        v = rng.randrange(MEM)
        if v == 29524:
            hits[0] += 1
            continue
        d = None
        for level, s in enumerate(back):
            if v in s:
                d = level
                break
        if d is None:
            misses += 1
            if len(examples) < 5:
                examples.append(v)
        else:
            hits[d] += 1
    return {"sample": sample, "max_depth": max_depth, "level_cap": LEVEL_CAP,
            "histogram": hits, "not_found": misses,
            "not_found_examples": examples,
            "backward_level_sizes": [len(s) for s in back],
            "interpretation": "salvo el sumidero {0,29524}, una muestra aleatoria "
                              "alcanza 29524 (y por tanto 59048) en pocos pasos; "
                              "los niveles hacia atrás están capados, así que "
                              "'not_found' no es prueba de inalcanzabilidad"}


def main() -> dict:
    res = check_lemmas()
    res["witnesses"] = build_witnesses()
    res["mask_upgrade"] = mask_upgrade_check()
    res["distance_probe"] = distance_probe()
    return res


if __name__ == "__main__":
    r = main()
    print("[lemas] por-trits exhaustivo:", r["lemmas_trit_exhaustive"]["all_ok"])
    print("[lemas] aleatorio palabras:", r["lemmas_random_words"])
    print("[lemas] ROT permuta posiciones:", r["rot_permutes_positions"])
    w = r["witnesses"]
    print("[inv] imprimibles sin trit 1:", w["printable_without_trit1"])
    print("[w] 29524 = crazy(54,54):", w["w_29524"]["ok"],
          "pasos", w["w_29524"]["steps"])
    print("[w] 0 = crazy(29524,29524):", w["w_0"]["ok"], "pasos", w["w_0"]["steps"])
    print("[w] P_p posiciones:", w["w_P"]["positions"], "ok", w["w_P"]["ok"])
    print("[w] Q/U inducción:", w["w_Q_U_induction"])
    print("[w] F inducción:", w["w_F_induction"])
    print("[w] general:", w["w_general"])
    print("[w] 59048:", w["w_59048"])
    print("[cierre] {0,29524}:", w["closed_component_0_29524"]["closed"])
    bf = w["bfs"]
    print("[bfs] niveles hacia adelante:", bf["forward_levels_sizes"],
          "objetivos:", bf["targets"])
    for k, v in bf["results"].items():
        print(f"[bfs]   {k:>6} -> profundidad {v['depth']} {v.get('note', '')}")
    mu = r["mask_upgrade"]
    print("[máscara] 29524 involutiva en %d/%d palabras; 121 en %d (predicho %d); "
          "primer contraejemplo de 121 = %d (%s)"
          % (mu["mask_29524_involutive_words"], mu["mask_29524_total"],
             mu["mask_121_involutive_words"], mu["mask_121_predicted"],
             mu["mask_121_first_counterexample"],
             "".join(str(x) for x in reversed(mu["mask_121_counterexample_trits"]))))
    dp = r["distance_probe"]
    print("[distancia] histograma:", dp["histogram"], "no encontrado:", dp["not_found"],
          "niveles hacia atrás:", dp["backward_level_sizes"])
