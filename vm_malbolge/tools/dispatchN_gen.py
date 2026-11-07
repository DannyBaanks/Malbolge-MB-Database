#!/usr/bin/env python3
"""Frente 3: maquina de bytecode de N instrucciones con despacho computado.

Generaliza dispatch2_gen.py de 2 instrucciones a N: cada instruccion del flujo
(enrutada por opcode) se ejecuta y la maquina encadena con el despacho siguiente,
as que el programa vive en el flujo de entrada, no en la imagen.

EL DESPACHO COMPUTADO

En un programa one-shot cada celda se escribe una sola vez, as que
mem[P] = crazy(a, mem[P]) es una FUNCION PURA del byte ledo (mem[P] vale V,
fijo). Eligiendo V de forma que

    crazy(op_push, V) = landing_push - 1
    crazy(op_pop , V) = landing_pop  - 1

un JMP que lea mem[P] salta al manejador correcto: salto computado por el dato,
sin cadena de comparaciones ni contador.

PROTOCOLO: PUSH = 0x01, POP = 0xF4 (244). Los dos opcodes difieren en un trit
ALTO (trit 5): con opcodes de un solo trit bajo, los destinos computados caen en
una banda de ~215 celdas y no se pueden separar N parejas de manejadores.

PROGRAMA (N instrucciones)

    D_0 (dir 0):  bootstrap (NOP + MOVD que lee su propia celda), IN op0,
                 MOVD->P_0, CRAZY mem[P_0]=crazy(op0,V_0), MOVD->P_0, JMP mem[P_0]
    D_k (dir 40+20(k-1)): entra con el d que dejo la instruccion anterior; igual
                 con P_k,V_k
    Cada despacho enruta a:
       push_k: IN operando, MOVD->slotA, CRAZY store, JMP al despacho siguiente
       pop_k : MOVD->slotA, 10x(MOVD,ROT) lectura exacta, OUT, JMP al siguiente
    Tras la instruccion N, los manejadores saltan al HALT.

Semantica verificable (modelo): N instrucciones de longitud variable sobre una
unica celda de pila; slot = crazy(operando, slot) en cada PUSH, y cada POP emite
slot & 255.
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

OP_PUSH = 53           # 0x35
OP_POP = 65            # 0x41
# PROTOCOLO MEDIDO, no elegido a ojo: con V imprimible (< 243) los trits altos
# de crazy(opcode, V) quedan fijos, asi que TODOS los destinos caen en una
# ventana de ~284 celdas. La busqueda sobre las 255x255 parejas de opcodes con
# el constraint de emparejado (cada V da un destino push y uno pop) dio un
# maximo de N=3 instrucciones, y solo con el manejador de POP reducido a una
# rotacion. Ver dispatchN.md.
DSTRIDE = 30           # huecos libres para las celdas P
MINSEP = 14            # separacion minima entre destinos (manejador <= 11 celdas)
N_INST = 3


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
    """Despachador. boot_nops > 0: arranca en lockstep con bootstrap propio.
    boot_nops == 0: entra con un d externo y arranca con el IN.
    Devuelve (d tras el salto, destino push, destino pop)."""
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
    """POP con lectura de UNA rotacion: emite rot(slot) & 255 y rota la celda.

    La lectura exacta (10 rotaciones) ocupa 20 celdas mas y obligaria a separar
    los destinos 32 celdas, lo que mide N=2 como maximo. Con una rotacion el
    manejador cabe en ~10 celdas y caben N=3 instrucciones encadenadas. El
    modelo de referencia aplica el mismo rot, así que la semantica es exacta
    aunque el valor emitido sea el rotado."""
    code.append((addr, "NOP"))
    code.append((addr + 1, "MOVD"))
    put(data, d0 + 1, slotA - 1)          # d = slotA-1 -> post: slotA
    code.append((addr + 2, "ROT"))         # mem[slotA] = rot(mem[slotA])
    code.append((addr + 3, "OUT"))         # emite rot(slot) & 255
    for i in range(tail):
        code.append((addr + 4 + i, "NOP"))
    j = addr + 4 + tail
    code.append((j, "JMP"))
    put(data, slotA + 2 + tail, exit_landing)
    return slotA + 3 + tail


def tails_for(n):
    """Rellenos de cola crecientes: cada pareja usa su propia celda de salida."""
    return [3 * k + 1 for k in range(n)]


def plan(Vs, Ps, slotA, n, tails=None, stride=None):
    """Devuelve (code, data, destinos); ValueError si la coreografia no cierra.

    `tails` permite fijar las colas medidas por el empaquetado exacto
    (dispatch_pack_gen.py); por defecto se usa la convencion 3k+1 de N=3.
    `stride` separa los despachos; con N=4 hay que bajarlo de 30 para que
    el HALT y el ultimo exit_landing sigan siendo imprimibles."""
    code, data = [], {}
    if tails is None:
        tails = tails_for(n)
    if len(tails) != n:
        raise ValueError(f"se esperaban {n} colas, hay {len(tails)}")
    if stride is None:
        stride = DSTRIDE
    put(data, slotA, 33)                     # valor inicial de la pila
    d_prev, Tp_prev, Tq_prev = 0, None, None
    targets = []
    for k in range(n):
        if k == 0:
            d_after, Tp, Tq = emit_dispatch(0, 0, Ps[0], Vs[0], 1, code, data)
            nxt = 45              # evita la celda 41 (puntero del bootstrap)
        else:
            landing = nxt - 1
            ex_p = emit_push(Tp_prev + 1, d_prev, slotA, landing,
                             tails[k - 1], code, data)
            ex_q = emit_pop(Tq_prev + 1, d_prev, slotA, landing,
                            tails[k - 1] - 1, code, data)
            if ex_p != ex_q:
                raise ValueError(
                    f"caminos de D{k} con distinto d: {ex_p} vs {ex_q}")
            d_after, Tp, Tq = emit_dispatch(nxt, ex_p, Ps[k], Vs[k],
                                            0, code, data)
            nxt = nxt + stride
        targets.append((Tp, Tq))
        Tp_prev, Tq_prev, d_prev = Tp, Tq, d_after
    # ultima pareja: salida al HALT
    halt = nxt + 20
    ex_p = emit_push(Tp_prev + 1, d_prev, slotA, halt - 1, tails[n - 1],
                     code, data)
    ex_q = emit_pop(Tq_prev + 1, d_prev, slotA, halt - 1, tails[n - 1] - 1,
                    code, data)
    if ex_p != ex_q:
        raise ValueError(f"caminos del ultimo despacho con distinto d")
    code.append((halt, "HALT"))
    # validacion final: dato y codigo disjointos, valores imprimibles
    codeset = {a for a, _ in code}
    for a, v in data.items():
        if a in codeset:
            raise ValueError(f"celda de dato {a} pisa codigo")
        if not (33 <= v <= 126):
            raise ValueError(f"celda de dato {a} no imprimible: {v}")
    return code, data, targets


def build(Vs, Ps, slotA, n, tails=None, stride=None):
    code, data, targets = plan(Vs, Ps, slotA, n, tails, stride)
    flat = [t for pair in targets for t in pair]
    top = max([a for a, _ in code] + list(data) + flat) + 2
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
    return bytes(mem), code, data, targets, nbad


def search_params(n):
    """N valores de V con los 2N destinos separados, N celdas P distintas y
    una celda de pila; valida cada candidato con plan()."""
    crz = oracle_classic.crazy_op
    pool = [Vv for Vv in range(33, 127)
            if crz(OP_PUSH, Vv) > 600 and crz(OP_POP, Vv) > 200
            and abs(crz(OP_PUSH, Vv) - crz(OP_POP, Vv)) >= MINSEP]
    tgt = {Vv: (crz(OP_PUSH, Vv), crz(OP_POP, Vv)) for Vv in pool}

    def sep_ok(chosen, cand):
        ts = []
        for Vv in list(chosen) + [cand]:
            ts.extend(tgt[Vv])
        if len(set(ts)) != len(ts):
            return False
        return all(abs(a - b) >= MINSEP for x, a in enumerate(ts)
                   for b in ts[x + 1:])

    vsets = []

    def grow(chosen):
        if len(chosen) == n:
            vsets.append(list(chosen))
            return True                     # con el primer conjunto basta
        for Vv in pool:
            if Vv in chosen or not sep_ok(chosen, Vv):
                continue
            chosen.append(Vv)
            if grow(chosen):
                return True
            chosen.pop()
        return False

    if not grow([]):
        raise RuntimeError(f"no hay {n} valores de V con destinos separados")
    # regiones disjuntas: P en [50,74] (hueco entre D1=[45,49] y D2=[75,79]),
    # la pila y sus punteros por encima del ultimo despacho
    for slotA in range(82, 117):
        for Vs in vsets:
            for P0 in range(50, 56):
                # P_k espaciadas 5: los manejadores leen P_k+2 y P_k+3
                Ps = [P0 + 5 * k for k in range(n)]
                if any(p > 126 or p + 1 > 126 for p in Ps):
                    continue
                if len(set(Ps) | {p + 1 for p in Ps}) != 2 * n:
                    continue
                try:
                    plan(Vs, Ps, slotA, n)
                except ValueError:
                    continue
                return Vs, Ps, slotA
    raise RuntimeError("no se encontro layout valido")


def model(data: bytes, v0a: int, n: int) -> bytes:
    """Modelo de referencia: N instrucciones de longitud variable."""
    crz = oracle_classic.crazy_op
    slot = v0a
    i = 0
    out = []
    for _ in range(n):
        if i >= len(data):
            break
        op = data[i]
        if op == OP_PUSH:
            if i + 1 >= len(data):
                break
            slot = crz(data[i + 1], slot)
            i += 2
        elif op == OP_POP:
            slot = (slot // 3) + (slot % 3) * (3 ** 9)   # rot(slot)
            out.append(slot & 255)
            i += 1
        else:
            break
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
                    default=ROOT / "vm_malbolge/src/mbir_dispatchN.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/dispatchN.json")
    ap.add_argument("-n", type=int, default=N_INST)
    args = ap.parse_args()
    n = args.n

    Vs, Ps, slotA = search_params(n)
    memory, code, data, targets, nbad = build(Vs, Ps, slotA, n)
    v0a = data[slotA]
    print(f"N={n} instrucciones | V={Vs} P={Ps} slotA={slotA} (V0={v0a})")
    for k, (tp, tq) in enumerate(targets):
        print(f"  D{k}: push@{tp} pop@{tq}")
    print(f"imagen: {args.mb} ({len(memory)} bytes, {len(code)} celdas de "
          f"codigo, {len(data)} de dato, {nbad} sin opcode valido)")
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)

    cases = [
        bytes([OP_PUSH, 0x41, OP_POP, OP_PUSH, 0x42, OP_POP]),
        bytes([OP_PUSH, 0x41, OP_PUSH, 0x42, OP_POP, OP_POP]),
        bytes([OP_POP, OP_PUSH, 0x41, OP_POP, OP_PUSH, 0x42]),
        bytes([OP_PUSH, 0x41, OP_PUSH, 0x42, OP_PUSH, 0x43, OP_POP]),
        bytes([OP_PUSH, 0x41, OP_POP, OP_POP]),
        bytes([OP_PUSH, 0x41]),
        bytes([OP_POP]),
        b"",
        bytes([OP_PUSH, 0x00, OP_POP, OP_PUSH, 0xFF, OP_POP]),
    ]
    rows, ok = [], 0
    for sb in cases:
        exp = model(sb, v0a, n)
        oout, osteps, ostatus = run_oracle(memory, sb)
        oout_b = oout.encode("latin-1")
        rout, rerr = run_runner(memory, sb)
        agree = (oout_b == exp) and (rout == exp)
        ok += agree
        rows.append({"stdin": sb.hex(), "esperado": exp.hex(),
                     "oraculo": oout_b.hex(), "runner_c": rout.hex(),
                     "pasos_oraculo": osteps, "status": ostatus,
                     "stderr_runner": rerr, "acuerdo": agree})
        print(f"  {sb.hex()[:32]:32s} esperado={exp.hex():10s} "
              f"oraculo={oout_b.hex():10s} runner={rout.hex():10s} "
              f"{osteps:6d}p {ostatus:8s} {'OK' if agree else 'FALLO'}")
    print(f"\n{ok}/{len(cases)} casos de acuerdo")

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "bytes": len(memory),
        "sha256": hashlib.sha256(memory).hexdigest(),
        "n_instrucciones": n,
        "parametros": {"Vs": Vs, "Ps": Ps, "slotA": slotA, "v0a": v0a,
                       "destinos": [list(t) for t in targets],
                       "colas": tails_for(n)},
        "codigo_celdas": len(code),
        "dato_celdas": len(data),
        "dato_no_valido": nbad,
        "casos": rows,
        "veredicto": ("DESPACHO_N_INSTRUCCIONES_DEMOSTRADO"
                      if ok == len(cases) else "FALLO"),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"evidencia: {args.json}")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
