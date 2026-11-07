#!/usr/bin/env python3
"""Frente 3: maquina de bytecode con DESPACHO COMPUTADO sobre flujo (one-shot).

La pila de stack2_oneshot tiene horario fijo (push, push, pop, pop). Esta
maquina lee parejas (opcode, operando) y ENRUTA segun el opcode: el flujo decide
el orden.

EL DESPACHO COMPUTADO

En un programa one-shot cada celda se escribe una sola vez, as que
mem[P] = crazy(a, mem[P]) es una FUNCION PURA del byte ledo (mem[P] vale V,
fijo). Eligiendo V de forma que

    crazy(op_push, V) = landing_push - 1
    crazy(op_pop , V) = landing_pop  - 1

un JMP que lea mem[P] salta al manejador correcto: salto computado por el dato,
sin cadena de comparaciones.

Cada despacho lleva su bootstrap (k NOPs + un MOVD en lockstep que lee su propio
valor V(k) = ((7-k) mod 94) + 33) porque el primer MOVD de un flujo en lockstep
solo puede leer su propia celda.

PROGRAMA (dos parejas: la primera enruta, la segunda ejecuta y para)

    D1 (dir 0):  bootstrap, IN op1, MOVD->P1, CRAZY mem[P1]=crazy(op1,V1),
                 MOVD->P1, JMP mem[P1]
       -> push1: IN operando, MOVD->slotA, CRAZY store, JMP a D2
       -> pop1 : MOVD->slotA, 10x(MOVD,ROT) lectura exacta, OUT, JMP a D2
    D2 (dir 40): igual con P2,V2 (objetivos distintos)
       -> push2: ... , JMP a HALT
       -> pop2 : ... , OUT, JMP a HALT
    HALT (dir 60)

Protocolo: 0x01 = PUSH, 0xF2 = POP. Semantica verificable: el pop emite
crazy(operando, V0A) & 255, lo que el push guardo.

Coreografia: cada fase se emite con un simulador de (c, d); las celdas-puntero se
colocan donde el flujo de d las lee, y los rellenos de cola se ajustan para que
los dos caminos de cada despacho dejen el MISMO d (si no, la celda-puntero del
despacho siguiente necesitaria dos valores distintos).
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
        "HALT": "v", "NOP": "o", "JMP": "i"}

OP_PUSH = 0x01
OP_POP = 0xF2
D2, HALT = 34, 45


def V(k: int) -> int:
    """Valor propio de la celda k (lo que lee el MOVD en lockstep)."""
    return ((7 - k) % 94) + 33


def put(data, addr, value):
    """Asigna una celda de dato; falla si dos fases piden valores distintos."""
    if addr in data and data[addr] != value:
        raise ValueError(f"celda {addr}: pide {data[addr]} y {value}")
    data[addr] = value


def valid_cell(addr: int, value: int) -> bool:
    return 33 <= value <= 126 and XLAT1[(value - 33 + addr) % 94] in VALID


# ---------------------------------------------------------------- fases ----
def emit_dispatch(addr, d0, P, Vv, boot_nops, code, data):
    """Despachador. boot_nops > 0: arranca en lockstep con bootstrap propio
    (k NOPs + un MOVD que lee su propia celda). boot_nops == 0: entra con un d
    externo y arranca directamente con el IN. Devuelve (d tras el salto,
    destinos push/pop)."""
    crz = oracle_classic.crazy_op
    if boot_nops:
        for _ in range(boot_nops):
            code.append((addr, "NOP"))
            addr += 1
            d0 += 1
        code.append((addr, "MOVD"))          # bootstrap: lee su propia celda
        d = V(addr) + 1                      # su post-incremento
        addr += 1
    else:
        d = d0
    code.append((addr, "IN"))                # a = opcode
    addr += 1
    d += 1
    put(data, d, P - 1)                      # puntero de store
    code.append((addr, "MOVD"))              # d = P-1 -> P
    d = P
    addr += 1
    put(data, P, Vv)                         # celda de despacho
    code.append((addr, "CRAZY"))             # mem[P] = crazy(a, mem[P])
    addr += 1
    d = P + 1
    put(data, d, P - 1)                      # puntero de lectura
    code.append((addr, "MOVD"))              # d = P-1 -> P
    d = P
    addr += 1
    code.append((addr, "JMP"))               # c = mem[P] = destino
    return P + 1, crz(OP_PUSH, Vv), crz(OP_POP, Vv)


def emit_push(addr, d0, slotA, exit_landing, tail, code, data):
    code += [(addr, "IN"), (addr + 1, "NOP"), (addr + 2, "MOVD"),
             (addr + 3, "CRAZY")]
    put(data, d0 + 2, slotA - 1)
    for i in range(tail):
        code.append((addr + 4 + i, "NOP"))
    j = addr + 4 + tail
    code.append((j, "JMP"))
    put(data, slotA + 1 + tail, exit_landing)
    return slotA + 2 + tail


def emit_pop(addr, d0, slotA, exit_landing, tail, code, data):
    code.append((addr, "NOP"))
    code.append((addr + 1, "MOVD"))
    put(data, d0 + 1, slotA)
    put(data, slotA + 1, slotA - 1)                # compartido por los 10
    for i in range(10):
        code.append((addr + 2 + 2 * i, "MOVD"))
        code.append((addr + 3 + 2 * i, "ROT"))
    o = addr + 22
    code.append((o, "OUT"))
    for i in range(tail):
        code.append((o + 1 + i, "NOP"))
    j = o + 1 + tail
    code.append((j, "JMP"))
    put(data, slotA + 2 + tail, exit_landing)
    return slotA + 3 + tail


def plan(V1, V2, slotA, P1, P2, tail1, tail2):
    """Devuelve (code, data, destinos); ValueError si la coreografia no cierra."""
    code, data = [], {}
    put(data, slotA, 33)                           # valor inicial de la pila
    # D1 en 0 con 1 NOP de bootstrap (d0 = 1 -> el MOVD de 1 lee mem[1] propio)
    d_after, T1p, T1q = emit_dispatch(0, 0, P1, V1, 1, code, data)
    ex_push = emit_push(T1p + 1, d_after, slotA, D2 - 1, tail1, code, data)
    ex_pop = emit_pop(T1q + 1, d_after, slotA, D2 - 1, tail1 - 1, code, data)
    if ex_push != ex_pop:
        raise ValueError(f"caminos de D1 con distinto d: {ex_push} vs {ex_pop}")
    # D2 entra con d = ex_push
    d_after2, T2p, T2q = emit_dispatch(D2, ex_push, P2, V2, 0, code, data)
    ex_push2 = emit_push(T2p + 1, d_after2, slotA, HALT - 1, tail2, code, data)
    ex_pop2 = emit_pop(T2q + 1, d_after2, slotA, HALT - 1, tail2 - 1, code, data)
    if ex_push2 != ex_pop2:
        raise ValueError(f"caminos de D2 con distinto d: {ex_push2} vs {ex_pop2}")
    code.append((HALT, "HALT"))
    # validacion final: dato y codigo disjointos, valores imprimibles
    codeset = {a for a, _ in code}
    for a, v in data.items():
        if a in codeset:
            raise ValueError(f"celda de dato {a} pisa codigo")
        if not (33 <= v <= 126):
            raise ValueError(f"celda de dato {a} no imprimible: {v}")
    return code, data, (T1p, T1q, T2p, T2q)


def build(params):
    (V1, V2, slotA, P1, P2, tail1, tail2) = params
    code, data, T = plan(V1, V2, slotA, P1, P2, tail1, tail2)
    top = max([a for a, _ in code] + list(data) + list(T)) + 2
    mem = [ord(char_for_op(CHAR_OP_MAP["j"], a)) for a in range(top)]
    codelist = [a for a, _ in code]
    for addr, value in data.items():
        assert 33 <= value <= 126, f"dato {addr} no imprimible: {value}"
        assert addr not in codelist, f"dato {addr} pisa codigo"
        mem[addr] = value
    for addr, op in code:
        assert addr not in data, f"codigo {addr} pisa dato"
        mem[addr] = ord(char_for_op(CHAR_OP_MAP[OPCH[op]], addr))
    for addr, op in code:
        assert valid_cell(addr, mem[addr]), f"codigo {addr} ({op}) no valido"
        assert (mem[addr] + addr) % 94 == CHAR_OP_MAP[OPCH[op]], f"op {addr}"
    nbad = sum(0 if valid_cell(a, v) else 1 for a, v in data.items())
    return bytes(mem), code, data, T, nbad


def search_params():
    """Busca (V1, V2, slotA, P1, P2): tripletas de celdas fuera, parejas de V
    dentro, para que el primer acierto salga en el primer barrido."""
    crz = oracle_classic.crazy_op
    codepos = set(range(0, 7)) | set(range(D2, D2 + 5)) | {HALT}

    def cells(slotA, P1, P2):
        """Las 14 celdas de dato que la coreografia necesita."""
        return [41, P1, P1 + 1, P1 + 2, P1 + 3,
                slotA, slotA + 1, slotA + 2, slotA + 3, slotA + 4,
                P2, P2 + 1, P2 + 2, P2 + 3]

    triples = []
    for slotA in range(34, 120):
        for P1 in range(34, 120):
            for P2 in range(34, 120):
                cs = cells(slotA, P1, P2)
                if len(set(cs)) != len(cs):
                    continue
                if any(c in codepos for c in cs):
                    continue
                triples.append((slotA, P1, P2))
    if not triples:
        raise RuntimeError("ninguna tripleta de celdas valida")

    valid_V = [V for V in range(33, 127)
               if crz(OP_PUSH, V) > 600 and crz(OP_POP, V) > 600
               and abs(crz(OP_PUSH, V) - crz(OP_POP, V)) >= 30]
    if len(valid_V) < 2:
        raise RuntimeError("pocos V validos")
    targets = {V: (crz(OP_PUSH, V), crz(OP_POP, V)) for V in valid_V}
    pairs = []
    for i, V1 in enumerate(valid_V):
        t1 = targets[V1]
        for V2 in valid_V[i + 1:]:
            t2 = targets[V2]
            ts = list(t1) + list(t2)
            ps = [(a, b) for x, a in enumerate(ts) for b in ts[x + 1:]]
            if min(abs(a - b) for a, b in ps) < 30:
                continue
            pairs.append((V1, V2))
    if not pairs:
        raise RuntimeError("ninguna pareja de V con destinos separados")

    for slotA, P1, P2 in triples:
        for V1, V2 in pairs:
            try:
                plan(V1, V2, slotA, P1, P2, 1, 2)
            except ValueError:
                continue
            return (V1, V2, slotA, P1, P2, 1, 2)
    raise RuntimeError("no se encontraron parametros de despacho")


def model(data: bytes, v0a: int):
    """Modelo de referencia: dos instrucciones de longitud variable
    (PUSH consume 2 bytes, POP consume 1; los bytes sobrantes se ignoran)."""
    crz = oracle_classic.crazy_op
    slot = v0a
    i = 0
    out = []
    for _ in range(2):
        if i >= len(data):
            break
        op = data[i]
        if op == OP_PUSH:
            if i + 1 >= len(data):
                break                       # operando ausente: EOF
            slot = crz(data[i + 1], slot)
            i += 2
        elif op == OP_POP:
            out.append(slot & 255)
            i += 1
        else:
            break                           # opcode fuera de contrato
    return bytes(out)


def run_oracle(memory: bytes, sb: bytes, max_steps=400000):
    src = memory.decode("latin-1")
    return oracle_classic.run(src, max_steps=max_steps,
                              stdin_data=sb.decode("latin-1"), stop_on_eof=True)


def run_runner(memory: bytes, sb: bytes, max_steps=400000):
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
                    default=ROOT / "vm_malbolge/src/mbir_dispatch2.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/dispatch2.json")
    args = ap.parse_args()

    params = search_params()
    (V1, V2, slotA, P1, P2, tail1, tail2) = params
    memory, code, data, T, nbad = build(params)
    v0a = data[slotA]
    print(f"parametros: V1={V1} V2={V2} slotA={slotA} (V0={v0a}) "
          f"P1={P1} P2={P2} colas=({tail1},{tail2})")
    print(f"destinos: push1@{T[0]} pop1@{T[1]} push2@{T[2]} pop2@{T[3]}")
    print(f"imagen: {args.mb} ({len(memory)} bytes, {len(code)} celdas de "
          f"codigo, {len(data)} de dato, {nbad} sin opcode valido)")
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)

    cases = [bytes([OP_PUSH, 0x41, OP_POP]),
             bytes([OP_PUSH, 0x42, OP_POP]),
             bytes([OP_POP, OP_PUSH, 0x43]),
             bytes([OP_PUSH, 0x41, OP_PUSH, 0x42]),
             bytes([OP_PUSH, 0x41]),
             bytes([OP_POP]),
             b"",
             bytes([OP_PUSH, 0x41, OP_POP, OP_POP])]
    rows, ok = [], 0
    for sb in cases:
        exp = model(sb, v0a)
        oout, osteps, ostatus = run_oracle(memory, sb)
        oout_b = oout.encode("latin-1")
        rout, rerr = run_runner(memory, sb)
        agree = (oout_b == exp) and (rout == exp)
        ok += agree
        rows.append({"stdin": sb.hex(), "esperado": exp.hex(),
                     "oraculo": oout_b.hex(), "runner_c": rout.hex(),
                     "pasos_oraculo": osteps, "status": ostatus,
                     "stderr_runner": rerr, "acuerdo": agree})
        print(f"  {sb.hex()[:30]:30s} esperado={exp.hex():8s} "
              f"oraculo={oout_b.hex():8s} runner={rout.hex():8s} "
              f"{osteps:6d}p {ostatus:8s} {'OK' if agree else 'FALLO'}")
    print(f"\n{ok}/{len(cases)} casos de acuerdo")

    # barrido: push(operando k) + pop  y  pop + push(operando k)
    sweep, sok = [], 0
    for k in list(range(0, 32)) + [0x7F, 0x80, 0xC3, 0xFE, 0xFF]:
        for seq in (bytes([OP_PUSH, k, OP_POP]),
                    bytes([OP_POP, OP_PUSH, k]),
                    bytes([OP_PUSH, k, OP_PUSH, k & 0x0F])):
            exp = model(seq, v0a)
            oout, osteps, ostatus = run_oracle(memory, seq)
            rout, _ = run_runner(memory, seq)
            good = (oout.encode("latin-1") == exp) and (rout == exp)
            sok += good
            sweep.append({"stdin": seq.hex(), "esperado": exp.hex(),
                          "oraculo": oout.encode("latin-1").hex(),
                          "runner_c": rout.hex(), "acuerdo": good})
    print(f"barrido: {sok}/{len(sweep)} combinaciones de acuerdo")

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "bytes": len(memory),
        "sha256": hashlib.sha256(memory).hexdigest(),
        "parametros": {"V1": V1, "V2": V2, "slotA": slotA, "v0a": v0a,
                       "P1": P1, "P2": P2, "tail1": tail1, "tail2": tail2,
                       "D2": D2, "HALT": HALT, "destinos": list(T)},
        "codigo_celdas": len(code),
        "dato_celdas": len(data),
        "dato_no_valido": nbad,
        "casos": rows,
        "barrido": {"combinaciones": len(sweep), "acuerdo": sok,
                    "detalle": sweep},
        "veredicto": ("DESPACHO_COMPUTADO_DEMOSTRADO"
                      if ok == len(cases) else "FALLO"),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"evidencia: {args.json}")
    return 0 if ok == len(cases) and sok == len(sweep) else 1


if __name__ == "__main__":
    sys.exit(main())
