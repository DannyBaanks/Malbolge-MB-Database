#!/usr/bin/env python3
"""Frente: celda-puntero escrita en runtime (one-shot, sin LMAO).

BLOQUEANTE QUE ATACA

El bucle de pila (stack2_oneshot.md, lineas 68-78) no puede escribir y leer la
misma celda en el mismo ciclo: CRAZY y ROT dejan `d` en la misma celda y
compartirian las celdas-puntero (S+1, S+2), que necesitan valores distintos.
La salida documentada es escribir la celda-puntero en runtime.

PRIMITIVA

Una celda P se siembra con v0. s bloques [MOVD, ROT, MOVD, CRAZY] rotan una
celda semilla K y aplican

    mem[P] = crazy(rot^i(vK), mem[P])

en la i-esima vuelta. Al final, un MOVD ejecutado con d=P lee mem[P] = T, el
valor escrito en runtime; el incremento automatico deja d=T+1, y un ROT sobre
esa celda emite un byte que solo puede salir si la escritura ocurrio.

PROGRAMA (k NOPs; s bloques; lectura final)

    k:              MOVD   d = V(k) = P
    (bloque x s)    MOVD   d = mem[P+1] = K-1
                    ROT    mem[K] = rot(mem[K]); a = mem[K]
                    MOVD   d = mem[K+1] = P-1
                    CRAZY  mem[P] = crazy(a, mem[P])
    final:          MOVD   d = mem[P+1] = K-1
                    ROT    mem[K] = rot(mem[K])
                    MOVD   d = mem[K+1] = P-1
                    MOVD   d = mem[P] = T        <- celda escrita en runtime
                    ROT    a = rot(mem[T+1])
                    OUT    emite a & 255
                    HALT

Semantica verificable: T = f_s(...f_1(v0)), f_i(x) = crazy(rot^i(vK), x).
La salida positiva es rot(w) & 255, con w = mem[T+1].
El control negativo sustituye CRAZY por NOP: mem[P] sigue siendo v0 y el MOVD
lee la celda v0+1, luego la salida es rot(u) & 255 con u = mem[v0+1].

El emisor busca (s, vK, v0, k, K, w, u) con loader estricto: TODAS las celdas
de codigo y de dato decodifican a opcode valido en su propia direccion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "native_classic"))
from constants import (CHAR_OP_MAP, XLAT1, char_for_op, crazy_op,  # noqa: E402
                       rot_op)

sys.path.insert(0, str(ROOT / "tools"))
import oracle_classic  # noqa: E402

RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"
VALID = frozenset("ji*p</vo")
OPCH = {"MOVD": "j", "IN": "/", "ROT": "*", "CRAZY": "p", "OUT": "<",
        "HALT": "v", "NOP": "o"}
LEN = 256


def V(k: int) -> int:
    """Valor propio de la celda k (lo que lee el MOVD en lockstep)."""
    return ((7 - k) % 94) + 33


def valid_cell(addr: int, value: int) -> bool:
    return 33 <= value <= 126 and XLAT1[(value - 33 + addr) % 94] in VALID


def chain(vK: int, v0: int, s: int) -> int:
    """T = f_s(...f_1(v0)); f_i(x) = crazy(rot^i(vK), x)."""
    mK, x = vK, v0
    for _ in range(s):
        mK = rot_op(mK)
        x = crazy_op(mK, x)
    return x


def layout(p):
    """Simula (c, d) y devuelve (code, ncode, ptrs).

    code: [(direccion, opcode)]. ptrs: celdas-puntero que lee cada MOVD.
    """
    c = d = 0
    code, ptrs = [], {}

    def nop(n):
        nonlocal c, d
        for _ in range(n):
            code.append((c, "NOP"))
            c += 1
            d += 1

    nop(p["k"])
    ptrs["boot"] = d
    d = V(p["k"])
    code.append((c, "MOVD"))
    c += 1
    d += 1
    if d != p["P"] + 1:
        raise AssertionError((d, p["P"] + 1))

    def ciclo():
        nonlocal c, d
        ptrs.setdefault("pf_K", d)
        d = p["K"] - 1
        code.append((c, "MOVD"))
        c += 1
        d += 1
        code.append((c, "ROT"))
        c += 1
        d += 1
        ptrs.setdefault("pf_P", d)
        d = p["P"] - 1
        code.append((c, "MOVD"))
        c += 1
        d += 1
        code.append((c, "CRAZY"))
        c += 1
        d += 1

    for _ in range(p["s"]):
        ciclo()

    # lectura final: MOVD, ROT, MOVD, MOVD(por P), ROT(M), OUT, HALT
    ptrs.setdefault("pf_K", d)
    d = p["K"] - 1
    code.append((c, "MOVD"))
    c += 1
    d += 1
    code.append((c, "ROT"))
    c += 1
    d += 1
    ptrs.setdefault("pf_P", d)
    d = p["P"] - 1
    code.append((c, "MOVD"))
    c += 1
    d += 1
    if d != p["P"]:
        raise AssertionError((d, p["P"]))
    d = p["T"]
    code.append((c, "MOVD"))
    c += 1
    d += 1
    if d != p["M"]:
        raise AssertionError((d, p["M"]))
    code.append((c, "ROT"))
    c += 1
    d += 1
    code.append((c, "OUT"))
    c += 1
    d += 1
    code.append((c, "HALT"))
    c += 1
    d += 1
    return code, c, ptrs


def data_cells(p, ptrs):
    if ptrs["pf_K"] != p["P"] + 1:
        raise AssertionError(("pf_K", ptrs["pf_K"], p["P"] + 1))
    if ptrs["pf_P"] != p["K"] + 1:
        raise AssertionError(("pf_P", ptrs["pf_P"], p["K"] + 1))
    dc = {
        p["P"]: p["v0"],
        p["P"] + 1: p["K"] - 1,
        p["K"]: p["vK"],
        p["K"] + 1: p["P"] - 1,
        p["M"]: p["w"],
        p["N"]: p["u"],
    }
    if len(dc) != 6:
        raise AssertionError(("celdas de dato repetidas", dc))
    return dc


def build(p, control=False):
    code, ncode, ptrs = layout(p)
    if ncode != p["ncode"]:
        raise AssertionError(("ncode", ncode, p["ncode"]))
    dc = data_cells(p, ptrs)
    mem = [ord(char_for_op(CHAR_OP_MAP["j"], a)) for a in range(LEN)]
    for idx, op in code:
        real = "NOP" if (control and op == "CRAZY") else op
        mem[idx] = ord(char_for_op(CHAR_OP_MAP[OPCH[real]], idx))
    for addr, value in dc.items():
        mem[addr] = value
    for addr, value in enumerate(mem):
        if not (33 <= value <= 126):
            raise AssertionError(("celda no imprimible", addr, value))
    for idx, op in code:
        real = "NOP" if (control and op == "CRAZY") else op
        if not valid_cell(idx, mem[idx]):
            raise AssertionError(("codigo no valido", idx, real))
        if (mem[idx] + idx) % 94 != CHAR_OP_MAP[OPCH[real]]:
            raise AssertionError(("op equivocada", idx, real))
    for addr, value in dc.items():
        if addr <= ncode:
            raise AssertionError(("dato dentro del codigo", addr, ncode))
        if not valid_cell(addr, value):
            raise AssertionError(("dato no valido", addr, value))
    return bytes(mem)


def marker_pair(M, N):
    """Primer par (w, u) valido en M y N con salidas distintas."""
    ws = [(w, rot_op(w) & 255) for w in range(33, 127)
          if valid_cell(M, w)]
    us = [(u, rot_op(u) & 255) for u in range(33, 127)
          if valid_cell(N, u)]
    for w, ow in ws:
        for u, ou in us:
            if ow != ou:
                return w, u, ow, ou
    return None


def find_layout(s, vK, v0, T, M, N, pair):
    done = {
        "s": s, "vK": vK, "v0": v0, "T": T, "M": M, "N": N,
        "w": pair[0], "u": pair[1], "out_pos": pair[2], "out_ctl": pair[3],
    }
    for k in range(0, 94):
        P = V(k)
        ncode = k + 4 * s + 8
        if min(P, P + 1, M, N) <= ncode:
            continue
        for K in range(ncode + 1, 127):
            six = (P, P + 1, K, K + 1, M, N)
            if len(set(six)) != 6:
                continue
            if not valid_cell(P, v0) or not valid_cell(P + 1, K - 1):
                continue
            if not valid_cell(K, vK) or not valid_cell(K + 1, P - 1):
                continue
            done.update({"k": k, "P": P, "K": K, "ncode": ncode})
            return done
    return None


def search_variants():
    sols = []
    for s in range(1, 9):
        for vK in range(33, 127):
            for v0 in range(33, 127):
                T = chain(vK, v0, s)
                M, N = T + 1, v0 + 1
                if not (33 <= M < LEN) or not (33 <= N < 128):
                    continue
                pair = marker_pair(M, N)
                if pair is None:
                    continue
                r = find_layout(s, vK, v0, T, M, N, pair)
                if r is not None:
                    sols.append(r)
    return sols


def select_variants(sols, count=9):
    key = {"s": 5, "vK": 121, "v0": 53, "k": 12, "K": 71}
    primary = None
    for x in sols:
        if all(x[k] == v for k, v in key.items()):
            primary = x
            break
    if primary is None:
        raise RuntimeError("no se encontro la variante primaria")
    chosen = [primary]
    used = {primary["out_pos"]}
    for out in sorted({x["out_pos"] for x in sols}):
        if out in used:
            continue
        for x in sols:
            if x["out_pos"] == out:
                chosen.append(x)
                used.add(out)
                break
        if len(chosen) == count:
            break
    for x in sols:
        if len(chosen) == count:
            break
        if x not in chosen:
            chosen.append(x)
    if len(chosen) != count:
        raise RuntimeError("solo %d variantes" % len(chosen))
    return chosen


def expected(p):
    return bytes([p["out_pos"]]), bytes([p["out_ctl"]])


def run_oracle(memory, max_steps=200000):
    return oracle_classic.run(memory.decode("latin-1"), max_steps=max_steps,
                              stdin_data="", stop_on_eof=True)


def run_runner(memory, max_steps=200000):
    """Devuelve (stdout CRUDO, stderr).

    TRAMPA MEDIDA: el runner C anade UN 0x0a al final. Normalizar con
    `endswith(b"\\r\\n")` es incorrecto: si el programa emite 0x0d, la salida
    real es `0d 0a` y el recorte CRLF se come el byte emitido. Aqui se compara
    el crudo contra `esperado` o `esperado + b"\\n"` (ver runner_agrees).
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mal") as f:
        f.write(memory)
        name = f.name
    try:
        r = subprocess.run([str(RUNNER), name, str(max_steps)],
                           input=b"", capture_output=True)
        return r.stdout, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(name)


def runner_agrees(raw: bytes, expected: bytes) -> bool:
    """El runner anade 0x0a; acepta crudo o crudo sin ese unico sufijo."""
    if raw == expected:
        return True
    return raw.endswith(b"\n") and raw[:-1] == expected


def runner_display(raw: bytes, expected: bytes) -> bytes:
    if raw != expected and raw.endswith(b"\n") and raw[:-1] == expected:
        return raw[:-1]
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_pointer_cell_rt.mb")
    ap.add_argument("--mb-ctrl", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_pointer_cell_rt_ctrl.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/pointer_cell_rt.json")
    ap.add_argument("--variants-dir", type=Path, default=None,
                    help="si se indica, escribe las 9 variantes y sus controles")
    args = ap.parse_args()

    sols = search_variants()
    print("soluciones con loader estricto: %d" % len(sols))
    variants = select_variants(sols)
    primary = variants[0]
    mem = build(primary)
    ctrl = build(primary, control=True)
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(mem)
    args.mb_ctrl.write_bytes(ctrl)
    print("imagen: %s (%d bytes)" % (args.mb, len(mem)))
    print("control: %s (%d bytes)" % (args.mb_ctrl, len(ctrl)))

    rows, ok = [], 0
    for i, p in enumerate(variants):
        pos = build(p)
        ctl = build(p, control=True)
        if args.variants_dir:
            args.variants_dir.mkdir(parents=True, exist_ok=True)
            (args.variants_dir / ("v%d.mb" % i)).write_bytes(pos)
            (args.variants_dir / ("v%d_ctrl.mb" % i)).write_bytes(ctl)
        exp_pos, exp_ctl = expected(p)
        o_pos, o_steps, o_status = run_oracle(pos)
        o_pos_b = o_pos.encode("latin-1")
        r_pos_raw, r_err = run_runner(pos)
        o_ctl, o_steps2, o_status2 = run_oracle(ctl)
        o_ctl_b = o_ctl.encode("latin-1")
        r_ctl_raw, r_err2 = run_runner(ctl)
        r_pos = runner_display(r_pos_raw, exp_pos)
        r_ctl = runner_display(r_ctl_raw, exp_ctl)
        agree = (o_pos_b == exp_pos and runner_agrees(r_pos_raw, exp_pos)
                 and o_ctl_b == exp_ctl and runner_agrees(r_ctl_raw, exp_ctl))
        ok += agree
        rows.append({
            "variante": i,
            "parametros": {kk: p[kk] for kk in
                           ("s", "k", "K", "vK", "v0", "P", "T", "M", "N",
                            "ncode", "w", "u")},
            "sha256_pos": hashlib.sha256(pos).hexdigest(),
            "sha256_ctl": hashlib.sha256(ctl).hexdigest(),
            "esperado_pos": exp_pos.hex(),
            "oraculo_pos": o_pos_b.hex(),
            "runner_pos": r_pos.hex(),
            "runner_pos_crudo": r_pos_raw.hex(),
            "esperado_ctl": exp_ctl.hex(),
            "oraculo_ctl": o_ctl_b.hex(),
            "runner_ctl": r_ctl.hex(),
            "runner_ctl_crudo": r_ctl_raw.hex(),
            "pasos_pos": o_steps,
            "status_pos": o_status,
            "pasos_ctl": o_steps2,
            "status_ctl": o_status2,
            "stderr_runner_pos": r_err,
            "stderr_runner_ctl": r_err2,
            "acuerdo": agree,
        })
        print("  v%d: s=%d k=%d K=%d vK=%d v0=%d T=%d M=%d N=%d "
              "pos=%s ctl=%s %s"
              % (i, p["s"], p["k"], p["K"], p["vK"], p["v0"], p["T"],
                 p["M"], p["N"], exp_pos.hex(), exp_ctl.hex(),
                 "OK" if agree else "FALLO"))
    print("\n%d/%d variantes (positivo y control, dos motores)"
          % (ok, len(variants)))

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "imagen_control": str(args.mb_ctrl.relative_to(ROOT)),
        "bytes": len(mem),
        "sha256": hashlib.sha256(mem).hexdigest(),
        "sha256_control": hashlib.sha256(ctrl).hexdigest(),
        "busqueda": {
            "soluciones_loader_estricto": len(sols),
            "por_s": {str(s): sum(1 for x in sols if x["s"] == s)
                      for s in sorted({x["s"] for x in sols})},
            "salidas_positivas_distintas": len({x["out_pos"] for x in sols}),
            "rango_M": [min(x["M"] for x in sols), max(x["M"] for x in sols)],
            "nota": ("T cae en rango de imagen solo con s=5 para semillas "
                     "imprimibles (barrido s=1..8, M<256); no es un sesgo de "
                     "busqueda"),
        },
        "layout_primario": {kk: primary[kk] for kk in
                            ("s", "k", "K", "vK", "v0", "P", "T", "M", "N",
                             "ncode", "w", "u")},
        "variantes": rows,
        "veredicto": ("CELDA_PUNTERO_RUNTIME_DEMOSTRADA"
                      if ok == len(variants) else "FALLO"),
        "nota": ("one-shot sin LMAO: mem[P] se escribe con CRAZY y luego "
                 "gobierna d mediante MOVD; el control con CRAZY->NOP lee "
                 "otra celda. La integracion de la primitiva en el bucle de "
                 "pila queda abierta."),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("evidencia: %s" % args.json)
    return 0 if ok == len(variants) else 1


if __name__ == "__main__":
    sys.exit(main())
