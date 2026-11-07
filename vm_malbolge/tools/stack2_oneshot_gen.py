#!/usr/bin/env python3
"""Frente 3: pila de profundidad 2 (LIFO) sobre flujo de bytes, via one-shot.

ARQUITECTURA (distinta a la del bucle, y por eso cabe)

Un programa ONE-SHOT no necesita la primitiva de restauracion: cada celda se
ejecuta una sola vez, asi que (a) su valor no tiene por que caer en un 2-ciclo
de XLAT2 (puede estar en CUALQUIER direccion) y (b) no hay pares de punteros que
colisionen. El flujo es una linea recta de celdas consecutivas y el puntero de
datos se gobierna con celdas-puntero imprimibles colocadas en el camino de `d`:

  - k NOP iniciales mantienen c y d en lockstep;
  - el MOVD de la direccion k lee su PROPIO valor V(k) = ((7-k) mod 94) + 33 y
    fija el desfase d = V(k);
  - cada MOVD posterior lee la celda-puntero que hay en su `d` actual; ese valor
    (imprimible, elegido) es el `d` con el que ejecuta la instruccion siguiente,
    que es CONSECUTIVA. Con puntero = destino - 1, la instruccion siguiente toca
    exactamente la celda de pila deseada.

Las direcciones de las celdas-puntero se obtienen SIMULANDO el flujo de d
(layout()), no derivandolas a mano: es la unica forma fiable de que la
coreografia cierre.

PROGRAMA (k, pad1, pad2, pad3 = NOPs de relleno, elegidos por la busqueda)

    k:              MOVD   d = V(k)
    k+1:            IN     a = byte1
    k+2+pad1:       MOVD   d = mem[pf1] = slotA-1
    k+3+pad1:       CRAZY  mem[slotA] = crazy(a, mem[slotA])       (PUSH 1)
    k+4+pad1:       IN     a = byte2
    k+5+pad1+pad2:  MOVD   d = mem[pf2] = slotB-1
    k+6+...:        CRAZY  mem[slotB] = crazy(a, mem[slotB])       (PUSH 2)
    k+7+...:        OUT    emite a & 256 = mem[slotB]              (POP: cima)
    k+8+pad3:       MOVD   d = mem[pf3] = slotA
    k+9+pad3 .. k+28+pad3: 10 x (MOVD, ROT)
                            a = rot^10(mem[slotA]) = mem[slotA]     (POP: fondo)
    k+29+pad3:      OUT    emite a & 256 = mem[slotA]
    k+30+pad3:      HALT

Las 10 rotaciones hacen falta porque ROT rota un trit: rot^10 es la identidad, y
cada ROT va precedido de un MOVD que devuelve `d` a la celda de pila (la
celda-puntero en slotA+1 contiene slotA-1 y sirve para las 10 vueltas).

Semantica verificable: salida = [crazy(byte2, V0B) & 255, crazy(byte1, V0A) & 255].
Los dos bytes almacenados se emiten EN ORDEN INVERSO (LIFO), con una
transformacion fija precalculable. El orden se demuestra comparando "AB" y "BA".
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
from constants import CHAR_OP_MAP, XLAT1, char_for_op  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import oracle_classic  # noqa: E402

RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"
VALID = frozenset("ji*p</vo")
OPCH = {"MOVD": "j", "IN": "/", "ROT": "*", "CRAZY": "p", "OUT": "<",
        "HALT": "v", "NOP": "o"}
LEN = 160


def V(k: int) -> int:
    """Valor propio de la celda k (lo que lee el MOVD en lockstep)."""
    return ((7 - k) % 94) + 33


def valid_cell(addr: int, value: int) -> bool:
    return 33 <= value <= 126 and XLAT1[(value - 33 + addr) % 94] in VALID


def layout(k, pad1, pad2, pad3, slotA, slotB):
    """Simula el flujo de (c, d) y devuelve (code, ncode, punteros).

    code: lista de (direccion, opcode). punteros: {nombre: direccion de celda}.
    """
    c = 0
    d = 0
    code = []
    ptrs = {}

    def nop(n):
        nonlocal c, d
        for _ in range(n):
            code.append((c, "NOP"))
            c += 1
            d += 1

    def step(op, reads_d=False, sets_d=None):
        nonlocal c, d
        if reads_d:
            ptrs.setdefault("next", d)
        if sets_d is not None:
            d = sets_d
        code.append((c, op))
        c += 1
        d += 1

    nop(k)
    ptrs["boot"] = d              # el MOVD inicial lee su propia celda
    d = V(k)                      # d = mem[k]
    code.append((c, "MOVD"))
    c += 1
    d += 1
    step("IN")                                   # d = V(k)+2
    nop(pad1)
    ptrs["pf1"] = d                              # celda-puntero de storeA
    d = slotA - 1
    code.append((c, "MOVD"))
    c += 1
    d += 1
    step("CRAZY")                                # ejecuta con d = slotA
    step("IN")                                   # d = slotA+2
    nop(pad2)
    ptrs["pf2"] = d                              # celda-puntero de storeB
    d = slotB - 1
    code.append((c, "MOVD"))
    c += 1
    d += 1
    step("CRAZY")                                # ejecuta con d = slotB
    step("OUT")                                  # emite a = mem[slotB]
    nop(pad3)
    ptrs["pf3"] = d                              # salto al puntero de slotA
    d = slotA
    code.append((c, "MOVD"))
    c += 1
    d += 1
    for _ in range(10):
        ptrs["pf_readA"] = d                     # debe ser slotA+1 siempre
        d = slotA - 1
        code.append((c, "MOVD"))
        c += 1
        d += 1
        step("ROT")                              # ejecuta con d = slotA
    step("OUT")                                  # emite rot^10(mem[slotA])
    step("HALT")
    ncode = c
    return code, ncode, ptrs


def data_cells(ptrs, slotA, slotB, v0a, v0b):
    return {
        ptrs["pf1"]: slotA - 1,
        slotA: v0a,
        slotA + 1: slotA - 1,      # pf_readA: puntero de lectura de slotA
        ptrs["pf2"]: slotB - 1,
        slotB: v0b,
        ptrs["pf3"]: slotA,
    }


def search_layout():
    """Busca (k, pads, slots, V0) con loader estricto: TODAS las celdas de codigo
    y de dato decodifican a opcode valido en su propia direccion."""
    for k in range(0, 53):
        for pad1 in range(0, 41):
            for pad2 in range(0, 11):
                for pad3 in range(0, 11):
                    for slotA in range(60, 127):
                        if not valid_cell(slotA + 1, slotA - 1):
                            continue
                        for slotB in range(60, 127):
                            if abs(slotA - slotB) < 2:
                                continue
                            code, ncode, ptrs = layout(
                                k, pad1, pad2, pad3, slotA, slotB)
                            dc = data_cells(ptrs, slotA, slotB, 33, 33)
                            if any(a <= ncode for a in dc):
                                continue
                            if len(set(dc)) != len(dc):
                                continue
                            if not all(valid_cell(a, v) for a, v in dc.items()
                                       if a not in (slotA, slotB)):
                                continue
                            for v0a in range(33, 127):
                                if not valid_cell(slotA, v0a):
                                    continue
                                for v0b in range(33, 127):
                                    if not valid_cell(slotB, v0b):
                                        continue
                                    return (k, pad1, pad2, pad3,
                                            slotA, slotB, v0a, v0b)
    raise RuntimeError("no se encontro layout con loader estricto completo")


def build(params):
    k, pad1, pad2, pad3, slotA, slotB, v0a, v0b = params
    code, ncode, ptrs = layout(k, pad1, pad2, pad3, slotA, slotB)
    dc = data_cells(ptrs, slotA, slotB, v0a, v0b)
    mem = [ord(char_for_op(CHAR_OP_MAP["j"], a)) for a in range(LEN)]
    for idx, op in code:
        mem[idx] = ord(char_for_op(CHAR_OP_MAP[OPCH[op]], idx))
    for addr, value in dc.items():
        mem[addr] = value
    for addr, value in enumerate(mem):
        assert 33 <= value <= 126, f"celda {addr} no imprimible: {value}"
    for idx, op in code:
        assert valid_cell(idx, mem[idx]), f"codigo {idx} ({op}) no valido"
        assert (mem[idx] + idx) % 94 == CHAR_OP_MAP[OPCH[op]], f"op {idx}"
    for a, v in dc.items():
        assert valid_cell(a, v), f"dato {a} no valido"
        assert a > ncode, f"dato {a} dentro del codigo"
    assert ptrs["pf_readA"] == slotA + 1, "el puntero de lectura no cerro"
    return bytes(mem)


def expect(data: bytes, v0a: int, v0b: int) -> bytes:
    """Salida esperada: crazy(byte, V0) por celda, en orden LIFO."""
    if len(data) < 2:
        return b""
    crz = oracle_classic.crazy_op
    return bytes([crz(data[1], v0b) & 255, crz(data[0], v0a) & 255])


def run_oracle(memory: bytes, sb: bytes, max_steps=200000):
    src = memory.decode("latin-1")
    return oracle_classic.run(src, max_steps=max_steps,
                              stdin_data=sb.decode("latin-1"), stop_on_eof=True)


def run_runner(memory: bytes, sb: bytes, max_steps=200000):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(sb)
        n = f.name
    mbn = n + ".mal"
    with open(mbn, "wb") as f:
        f.write(memory)
    try:
        with open(n, "rb") as fin:
            r = subprocess.run([str(RUNNER), mbn, str(max_steps)],
                               stdin=fin, capture_output=True)
        out = r.stdout
        if out.endswith(b"\r\n"):
            out = out[:-2]
        elif out.endswith(b"\n"):
            out = out[:-1]
        return out, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(n)
        os.unlink(mbn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_stack2_oneshot.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/stack2_oneshot.json")
    args = ap.parse_args()

    params = search_layout()
    (k, pad1, pad2, pad3, slotA, slotB, v0a, v0b) = params
    code, ncode, ptrs = layout(k, pad1, pad2, pad3, slotA, slotB)
    print(f"layout: k={k} pads=({pad1},{pad2},{pad3}) codigo={ncode} celdas")
    print(f"  punteros: pf1={ptrs['pf1']} pf2={ptrs['pf2']} pf3={ptrs['pf3']} "
          f"pf_readA={ptrs['pf_readA']}")
    print(f"  slotA={slotA} (V0={v0a})  slotB={slotB} (V0={v0b})")
    memory = build(params)
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)
    print(f"imagen: {args.mb} ({len(memory)} bytes)")

    cases = [b"AB", b"BA", b"AZ", b"\x01\x02", b"xy", b"A", b"", b"ABC"]
    rows, ok = [], 0
    for sb in cases:
        exp = expect(sb, v0a, v0b)
        oout, osteps, ostatus = run_oracle(memory, sb)
        oout_b = oout.encode("latin-1")
        rout, rerr = run_runner(memory, sb)
        agree = (oout_b == exp) and (rout == exp)
        ok += agree
        rows.append({"stdin": sb.hex(), "esperado": exp.hex(),
                     "oraculo": oout_b.hex(), "runner_c": rout.hex(),
                     "pasos_oraculo": osteps, "status": ostatus,
                     "stderr_runner": rerr, "acuerdo": agree})
        print(f"  {sb.hex()[:16]:16s} esperado={exp.hex():8s} "
              f"oraculo={oout_b.hex():8s} runner={rout.hex():8s} "
              f"{osteps:5d}p {ostatus:7s} {'OK' if agree else 'FALLO'}")
    print(f"\n{ok}/{len(cases)} casos de acuerdo")

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "bytes": len(memory),
        "sha256": hashlib.sha256(memory).hexdigest(),
        "layout": {"k": k, "pad1": pad1, "pad2": pad2, "pad3": pad3,
                   "codigo_celdas": ncode,
                   "punteros": {kk: vv for kk, vv in ptrs.items()},
                   "slotA": {"celda": slotA, "valor_inicial": v0a},
                   "slotB": {"celda": slotB, "valor_inicial": v0b}},
        "casos": rows,
        "veredicto": ("PILA_PROFUNDIDAD_2_LIFO_DEMONSTRADA"
                      if ok == len(cases) else "FALLO"),
        "nota": ("one-shot sin bucle ni restauracion; el bucle con escritura y "
                 "lectura de la misma celda queda bloqueado por colision de "
                 "pares de punteros (CRAZY y ROT dejan d en la misma celda)"),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"evidencia: {args.json}")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
