#!/usr/bin/env python3
"""Pila LIFO de profundidad 2 dentro de un bucle real (fase por ciclo XLAT2).

CONTINUIDAD DE `stack_loop_phase_gen.py`

Alli se demostro que una celda de trabajo NO restaurada avanza por su ciclo de
XLAT2 y por tanto cambia de opcode en cada iteracion: la fase la elige el
estado de cifrado, y la misma celda puede hacer `CRAZY` (escritura) en una
iteracion y `ROT` (lectura) en otra. Eso refuto el bloqueante medido en
`stack2_oneshot.md` (una celda no puede escribirse y leerse en el mismo
ciclo, porque `CRAZY` y `ROT` comparten las celdas-puntero `(S+1, S+2)`).

Aqui se lleva el mecanismo a una PILA LIFO DE PROFUNDIDAD 2: dos celdas de
pila, dos celdas de trabajo, cuatro fases útiles por ciclo.

LAS DOS CELDAS DE TRABAJO (misma clase de ciclo de XLAT2, longitud 9)

Clase de ciclo C = [73, 50, 80, 66, 62, 76, 79, 67, 85].

  W1 @ 71, valor inicial 85 -> op0 = CRAZY (62), y el ciclo da:
      fase 0 -> CRAZY (escribe S1)     fase 5 -> ROT (lee S1)
  W2 @ 83, valor inicial 79 -> op0 = NOP  (68), y el ciclo da:
      fase 3 -> CRAZY (escribe S2)     fase 4 -> ROT (lee S2)

Las dos celdas arrancan en un opcode VALIDO (loader estricto completo): W1
como CRAZY, W2 como NOP. Las dos estan en la misma clase de ciclo, asi que sus
fases no derivan: ambas avanzan un paso por iteracion.

ORDEN LIFO POR CICLO (9 iteraciones = 9 bytes de entrada)

    fase 0 : W1 CRAZY -> push en S1
    fase 1 : (inerte)
    fase 2 : (inerte)
    fase 3 : W2 CRAZY -> push en S2
    fase 4 : W2 ROT    -> pop de S2, emite
    fase 5 : W1 ROT    -> pop de S1, emite
    fases 6..8 : (inertes)

Es LIFO: el valor apilado mas tarde (fase 3) sale primero (fase 4) y el
apilado antes (fase 0) sale despues (fase 5).

CADENA DEL BUCLE (una vuelta = 19 pasos)

    IN        a = byte
    J_IN      restaura IN; despacha a MOVD1
    M1 MOVD   d = mem[S2+8] = S1-3
    J_M1      restaura M1; despacha a W1 con d = S1
    W1        CRAZY (fase 0) / NOP / ROT (fase 5) sobre mem[S1]
    J_W1      UN solo salto (no restaura W1): despacha a MOVD2
    M2 MOVD   d = mem[S1+2] = S2-3
    J_M2      restaura M2; despacha a W2 con d = S2
    W2        CRAZY (fase 3) / NOP / ROT (fase 4) sobre mem[S2]
    J_W2      UN solo salto: despacha a OUT
    O  OUT    emite a & 255
    J_O       restaura OUT; despacha de vuelta a IN

Las celdas W no se restauran (por eso sus fases avanzan); IN, M1, M2 y OUT si,
con el par JMP de siempre y valores en 2-ciclo de XLAT2.

NOTAS HONESTAS

- El pop es un `ROT`: lee la celda, la rota y la deja rotada. No es una
  extraccion que vacie la ranura. Un pop exacto (10 ROT = rot^10 = identidad)
  es IMPOSIBLE en bucle: varios ROT sobre la misma celda dejan todos `d` en la
  misma direccion y compartirian las celdas-puntero `(S+1, S+2)`.
- Las fases inertes (1, 2, 6, 7, 8) no tocan la pila, pero `IN` y `OUT` siguen
  ejecutandose: `OUT` emite el byte de entrada en esas fases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "native_classic"))
from constants import XLAT1, XLAT2, char_for_op, crazy_op, rot_op  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import oracle_classic  # noqa: E402

RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"
VALID = frozenset("ji*p</vo")
OPNUM = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "MOVD": 40,
         "CRAZY": 62, "NOP": 68, "HALT": 81}
LEN = 256
CYCLE9 = (73, 50, 80, 66, 62, 76, 79, 67, 85)
A_W1, A_W2 = 71, 83
W1_VALUE, W2_VALUE = 85, 79          # CRAZY@0/ROT@5  y  NOP@0/CRAZY@3/ROT@4


def enc(v: int) -> int:
    return ord(XLAT2[v - 33])


def two_cycle(v: int) -> bool:
    e = enc(v)
    return e != v and enc(e) == v


def valid_cell(addr: int, value: int) -> bool:
    return (33 <= value <= 126
            and XLAT1[(value - 33 + addr) % 94] in VALID)


def cell(opname: str, addr: int) -> int:
    return ord(char_for_op(OPNUM[opname], addr))


def phase_ops(addr: int, value0: int, n=9):
    """(opcode, valor) por iteracion de una celda con valor inicial `value0`."""
    rows = []
    v = value0
    for _ in range(n):
        rows.append(((v + addr) % 94, v))
        v = enc(v)
    return rows


def layout(S1, S2, A_IN, A_M1, A_M2, A_OUT):
    """Celdas de codigo, landings y punteros deducidos del flujo de d.

    El flujo (medido con el traza del oraculo) es:

      IN en d=D_IN=S2+5
      J_IN: lee (D_IN+1) y (D_IN+2) -> restaura IN, despacha a MOVD1
      MOVD1 en d=S2+8, lee mem[S2+8]=S1-3 -> d=S1-3 (post S1-2)
      J_M1: lee (S1-2) y (S1-1) -> restaura MOVD1, despacha a W1 con d=S1
      W1 en d=S1 (post S1+1)
      J_W1 (unico): lee (S1+1) -> despacha a MOVD2
      MOVD2 en d=S1+2, lee mem[S1+2]=S2-3 -> d=S2-3 (post S2-2)
      J_M2: lee (S2-2) y (S2-1) -> restaura MOVD2, despacha a W2 con d=S2
      W2 en d=S2 (post S2+1)
      J_W2 (unico): lee (S2+1) -> despacha a OUT
      OUT en d=S2+2 (post S2+3)
      J_OUT: lee (S2+3) y (S2+4) -> restaura OUT, despacha a IN
    """
    code = {0: cell("MOVD", 0), 1: cell("MOVD", 1), 2: cell("JMP", 2)}
    roles = {0: "boot_movd0", 1: "boot_movd1", 2: "boot_jmp"}
    for name, addr in (("IN", A_IN), ("MOVD", A_M1), ("CRAZY", A_W1),
                       ("MOVD", A_M2), ("NOP", A_W2), ("OUT", A_OUT)):
        code[addr] = cell(name, addr)
        code[addr + 1] = cell("JMP", addr + 1)
        roles[addr] = name
        roles[addr + 1] = "jmp_" + name
    code[A_W1] = W1_VALUE
    code[A_W2] = W2_VALUE
    land = {A_IN - 1: "L_IN", A_M1 - 1: "L_M1", A_W1 - 1: "L_W1",
            A_M2 - 1: "L_M2", A_W2 - 1: "L_W2", A_OUT - 1: "L_OUT"}
    ptr_items = [
        (41, S2 + 3, "boot_d"),      # bootstrap: MOVD de la celda 1
        (S2 + 6, A_IN, "J_IN_restaura"),
        (S2 + 7, A_M1 - 1, "J_IN_despacha"),
        (S2 + 8, S1 - 3, "MOVD1_lee"),
        (S1 - 2, A_M1, "J_M1_restaura"),
        (S1 - 1, A_W1 - 1, "J_M1_despacha"),
        (S1 + 1, A_M2 - 1, "J_W1_despacha"),
        (S1 + 2, S2 - 3, "MOVD2_lee"),
        (S2 - 2, A_M2, "J_M2_restaura"),
        (S2 - 1, A_W2 - 1, "J_M2_despacha"),
        (S2 + 1, A_OUT - 1, "J_W2_despacha"),
        (S2 + 3, A_OUT, "J_OUT_restaura"),
        (S2 + 4, A_IN - 1, "J_OUT_despacha"),
    ]
    seen = {}
    dup = []
    for a, v, role in ptr_items:
        if a in seen:
            dup.append((a, seen[a], role))
        seen[a] = role
    if dup:
        return None, f"direccion de puntero duplicada {dup[:3]}"
    ptr = {a: v for a, v, _ in ptr_items}
    roles_ptr = {a: r for a, _, r in ptr_items}
    return code, roles, land, ptr, roles_ptr


def check_layout(S1, S2, A_IN, A_M1, A_M2, A_OUT, v1=33, v2=33):
    res = layout(S1, S2, A_IN, A_M1, A_M2, A_OUT)
    if res[0] is None:
        return res
    code, roles, land, ptr, roles_ptr = res
    occupied = {}
    for a in code:
        occupied.setdefault(a, []).append("code")
    for a in land:
        occupied.setdefault(a, []).append("land")
    for a in ptr:
        occupied.setdefault(a, []).append("ptr")
    col = {a: r for a, r in occupied.items() if len(r) > 1}
    if col:
        return None, f"colision {sorted(col.items())[:3]}"
    if S1 in occupied or S2 in occupied:
        return None, "la celda de pila pisa otro rol"
    if S1 == S2:
        return None, "S1 == S2"
    if any(not (0 <= a < LEN) for a in occupied):
        return None, "direccion fuera de imagen"
    bad = [(a, v, roles[a]) for a, v in code.items() if not valid_cell(a, v)]
    if bad:
        return None, f"codigo no valido {bad[:3]}"
    for a, v in ptr.items():
        if not (33 <= v <= 126):
            return None, f"puntero {a}={v} no imprimible"
    for name, addr in (("IN", A_IN), ("MOVD", A_M1), ("MOVD", A_M2),
                       ("OUT", A_OUT)):
        if not two_cycle(code[addr]):
            return None, f"{name}@{addr} no esta en 2-ciclo ({code[addr]})"
    # fases de W1 y W2
    f1 = phase_ops(A_W1, W1_VALUE)
    f2 = phase_ops(A_W2, W2_VALUE)
    if [o for o, _ in f1].count(OPNUM["CRAZY"]) != 1 or \
       [o for o, _ in f1].count(OPNUM["ROT"]) != 1:
        return None, f"W1 fases {[o for o, _ in f1]}"
    if [o for o, _ in f2].count(OPNUM["CRAZY"]) != 1 or \
       [o for o, _ in f2].count(OPNUM["ROT"]) != 1:
        return None, f"W2 fases {[o for o, _ in f2]}"
    p1 = [o for o, _ in f1].index(OPNUM["CRAZY"])
    q1 = [o for o, _ in f1].index(OPNUM["ROT"])
    p2 = [o for o, _ in f2].index(OPNUM["CRAZY"])
    q2 = [o for o, _ in f2].index(OPNUM["ROT"])
    if not (p1 < p2 < q2 < q1):
        return None, f"orden no LIFO: {p1},{p2},{q2},{q1}"
    if not (33 <= v1 <= 126 and 33 <= v2 <= 126):
        return None, "valores de pila no imprimibles"
    return (code, roles, land, ptr, roles_ptr, f1, f2,
            (p1, p2, q2, q1)), "OK"


def search_layout():
    """Primer layout valido, en orden determinista."""
    for S1 in range(40, 121):
        for S2 in range(40, 121):
            for A_IN in (43, 47):
                for A_M1, A_M2 in ((60, 64), (64, 60)):
                    for A_OUT in (119, 123):
                        r, msg = check_layout(S1, S2, A_IN, A_M1, A_M2, A_OUT)
                        if r:
                            return (S1, S2, A_IN, A_M1, A_M2, A_OUT, r)
    raise RuntimeError("no se encontro layout valido")


def build(params, control=False, v1=33, v2=33, w_inerte=42):
    S1, S2, A_IN, A_M1, A_M2, A_OUT, (code, roles, land, ptr, roles_ptr,
                                      f1, f2, phases) = params
    mem = [cell("NOP", a) for a in range(LEN)]
    for a, v in code.items():
        mem[a] = v
    for a in land:
        mem[a] = cell("NOP", a)
    for a, v in ptr.items():
        mem[a] = v
    mem[S1] = v1
    mem[S2] = v2
    assert all(33 <= v <= 126 for v in mem)
    for a, v in code.items():
        assert valid_cell(a, v), f"codigo {a} ({roles[a]}) no valido"
    if control:
        # control: W1 y W2 quedan INERTES en todas las fases. El valor 42
        # tiene un ciclo de 4 cuyos opcodes en 71 y en 83 son todos invalidos
        # (19,87,8,82 y 31,9,20,0): nunca CRAZY, nunca ROT.
        for addr in (A_W1, A_W2):
            ops = [o for o, _ in phase_ops(addr, w_inerte, 4)]
            assert OPNUM["CRAZY"] not in ops and OPNUM["ROT"] not in ops, \
                f"control no inerte en {addr}: {ops}"
            mem[addr] = w_inerte
    return bytes(mem)


def model(data: bytes, v1=33, v2=33, control=False):
    """Maquina de 9 fases con dos ranuras de pila."""
    s1, s2 = v1, v2
    out = []
    for i, b in enumerate(data):
        p = i % 9
        a = b
        if not control:
            if p == 0:
                s1 = crazy_op(b, s1)
                a = s1
            elif p == 5:
                s1 = rot_op(s1)
                a = s1
            if p == 3:
                s2 = crazy_op(b, s2)
                a = s2
            elif p == 4:
                s2 = rot_op(s2)
                a = s2
        out.append(a & 255)
    return bytes(out)


def run_oracle(memory: bytes, sb: bytes, max_steps=800000):
    src = memory.decode("latin-1")
    return oracle_classic.run(src, max_steps=max_steps,
                              stdin_data=sb.decode("latin-1"),
                              stop_on_eof=True)


def run_runner(memory: bytes, sb: bytes, max_steps=800000):
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
        return r.stdout, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(n)
        os.unlink(mbn)


def runner_agrees(raw: bytes, expected: bytes) -> bool:
    return raw == expected or (raw.endswith(b"\n") and raw[:-1] == expected)


def trace_w(memory: bytes, data: bytes, w_addrs, s_addrs, n=20):
    """Traza las ejecuciones de las celdas de trabajo: opcode, d y valor.

    Instrumenta la semántica del oraculo (no la reimplementa).
    """
    mem = oracle_classic.load_memory(memory.decode("latin-1"))
    a = c = d = 0
    out = []
    it = iter(data)
    steps = 0
    rows = []
    watch = set(w_addrs)
    while steps < 4000 and len(rows) < n:
        steps += 1
        cell = mem[c]
        op = (cell + c) % 94
        jumped = False
        if op == 4:
            tgt = mem[d]
            jumped = True
        elif op == 5:
            out.append(a % 256)
        elif op == 23:
            ch = next(it, None)
            if ch is None:
                break
            a = ch
        elif op == 39:
            v = mem[d]
            mem[d] = (v // 3) + (v % 3) * (3 ** 9)
            a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = oracle_classic.crazy_op(a, mem[d])
            a = mem[d]
        elif op == 81:
            break
        d_exec = d
        if jumped:
            c = tgt
        if 33 <= mem[c] <= 126:
            mem[c] = oracle_classic._ENC[mem[c]]
        executed = c
        c = (c + 1) % oracle_classic.MEM_SIZE
        d = (d + 1) % oracle_classic.MEM_SIZE
        if not jumped and executed in watch:
            rows.append({
                "celda": executed, "paso": steps, "opcode": op,
                "nombre": next((k for k, v in OPNUM.items() if v == op),
                               "invalido"),
                "d": d_exec,
                "valor_celda": mem[executed],
                "mem_S1": mem[s_addrs[0]], "mem_S2": mem[s_addrs[1]],
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_stack_loop_lifo2.mb")
    ap.add_argument("--ctrl", type=Path,
                    default=ROOT /
                    "vm_malbolge/src/mbir_stack_loop_lifo2_ctrl.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT /
                    "vm_malbolge/evidence/stack_loop_lifo2.json")
    args = ap.parse_args()

    params = search_layout()
    (S1, S2, A_IN, A_M1, A_M2, A_OUT,
     (code, roles, land, ptr, roles_ptr, f1, f2, phases)) = params
    pos = build(params)
    ctl = build(params, control=True)
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(pos)
    args.ctrl.write_bytes(ctl)

    print(f"layout: S1={S1} S2={S2} IN={A_IN} MOVD1={A_M1} MOVD2={A_M2} "
          f"OUT={A_OUT} W1={A_W1} W2={A_W2}")
    print(f"  fases: push S1@{phases[0]}, push S2@{phases[1]}, "
          f"pop S2@{phases[2]}, pop S1@{phases[3]}")
    print(f"  punteros: {sorted(ptr.items())}")
    print(f"imagen: {args.mb} ({len(pos)} bytes)")
    print(f"control: {args.ctrl} ({len(ctl)} bytes)")

    # 9 bytes por ciclo: el byte 0 se apila en S1 y el byte 3 en S2
    blk = bytearray(b"." * 9)
    blk[0] = ord("A")
    blk[3] = ord("B")
    blk2 = bytearray(b"." * 9)
    blk2[0] = ord("B")
    blk2[3] = ord("A")
    cases = [b"", b"A", bytes(blk), bytes(blk2),
             bytes(blk) + bytes(blk2),
             bytes(range(1, 10)), bytes(range(1, 28))]
    rnd = random.Random(4411)
    cases.append(bytes(rnd.randrange(256) for _ in range(2048)))

    rows, ok_pos, ok_ctl, total = [], 0, 0, 0
    for sb in cases:
        exp_pos = model(sb)
        exp_ctl = model(sb, control=True)
        o_pos, st_pos, status_pos = run_oracle(pos, sb)
        r_pos_raw, err_pos = run_runner(pos, sb)
        o_ctl, st_ctl, status_ctl = run_oracle(ctl, sb)
        r_ctl_raw, err_ctl = run_runner(ctl, sb)
        o_pos_b = o_pos.encode("latin-1")
        o_ctl_b = o_ctl.encode("latin-1")
        agree_pos = o_pos_b == exp_pos and runner_agrees(r_pos_raw, exp_pos)
        agree_ctl = o_ctl_b == exp_ctl and runner_agrees(r_ctl_raw, exp_ctl)
        ok_pos += agree_pos
        ok_ctl += agree_ctl
        total += 1
        print(f"  in={sb.hex()[:30]:30s} l={len(sb):5d} "
              f"pos={'OK' if agree_pos else 'FALLO'} "
              f"ctl={'OK' if agree_ctl else 'FALLO'} "
              f"({st_pos}p {status_pos})")
        rows.append({
            "stdin": sb.hex(), "bytes": len(sb),
            "esperado_pos": exp_pos.hex(), "oraculo_pos": o_pos_b.hex(),
            "runner_pos_crudo": r_pos_raw.hex(),
            "pasos_pos": st_pos, "status_pos": status_pos,
            "stderr_runner_pos": err_pos,
            "esperado_ctl": exp_ctl.hex(), "oraculo_ctl": o_ctl_b.hex(),
            "runner_ctl_crudo": r_ctl_raw.hex(),
            "pasos_ctl": st_ctl, "status_ctl": status_ctl,
            "stderr_runner_ctl": err_ctl,
            "acuerdo_pos": agree_pos, "acuerdo_ctl": agree_ctl,
        })

    # evidencia LIFO: el pop de S2 (fase 4) va antes que el de S1 (fase 5)
    o_blk, _, _ = run_oracle(pos, bytes(blk))
    o_swap, _, _ = run_oracle(pos, bytes(blk2))
    bl = o_blk.encode("latin-1")
    sw = o_swap.encode("latin-1")
    lifo = (len(bl) == 9 and len(sw) == 9
            and bl[4] == sw[5] and bl[5] == sw[4]
            and bl[4] != bl[5])
    print(f"\nLIFO: pop S2 (pos 4) y pop S1 (pos 5) intercambian al "
          f"intercambiar A y B -> {'OK' if lifo else 'FALLO'}")
    print(f"  bloque A..B: {bl.hex()}   bloque B..A: {sw.hex()}")

    trace = trace_w(pos, bytes(blk) * 3, (A_W1, A_W2), (S1, S2), n=20)
    w1 = [r for r in trace if r["celda"] == A_W1]
    w2 = [r for r in trace if r["celda"] == A_W2]
    trace_ok = (all(r["d"] == S1 for r in w1)
                and all(r["d"] == S2 for r in w2)
                and [r["nombre"] for r in w1[:6]]
                == ["CRAZY", "invalido", "invalido", "invalido", "invalido",
                    "ROT"]
                and [r["nombre"] for r in w2[:6]]
                == ["NOP", "invalido", "invalido", "CRAZY", "ROT", "invalido"])
    print(f"\ntraza: W1 ops={[r['nombre'] for r in w1[:6]]} "
          f"d={ {r['d'] for r in w1} } | "
          f"W2 ops={[r['nombre'] for r in w2[:6]]} d={ {r['d'] for r in w2} }"
          f" -> {'OK' if trace_ok else 'FALLO'}")

    verdict = ("PILA_LIFO_PROFUNDIDAD_2_EN_BUCLE_DEMOSTRADA"
               if ok_pos == total and ok_ctl == total and lifo and trace_ok
               else "FALLO")
    print(f"\npositivo {ok_pos}/{total} | control {ok_ctl}/{total}")
    print(f"veredicto: {verdict}")

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "control": str(args.ctrl.relative_to(ROOT)),
        "bytes": len(pos),
        "sha256": hashlib.sha256(pos).hexdigest(),
        "sha256_control": hashlib.sha256(ctl).hexdigest(),
        "layout": {
            "S1": S1, "S2": S2, "A_IN": A_IN, "A_MOVD1": A_M1,
            "A_MOVD2": A_M2, "A_OUT": A_OUT, "A_W1": A_W1, "A_W2": A_W2,
            "v1": 33, "v2": 33,
            "punteros": {str(a): v for a, v in sorted(ptr.items())},
            "landings": {str(a): n for a, n in sorted(land.items())},
            "roles_codigo": {str(a): n for a, n in sorted(roles.items())},
            "roles_puntero": {str(a): n for a, n in sorted(roles_ptr.items())},
        },
        "fases": {
            "W1": [{"fase": i, "opcode": o, "valor": v}
                   for i, (o, v) in enumerate(f1)],
            "W2": [{"fase": i, "opcode": o, "valor": v}
                   for i, (o, v) in enumerate(f2)],
            "orden_lifo": {"push_S1": phases[0], "push_S2": phases[1],
                           "pop_S2": phases[2], "pop_S1": phases[3]},
        },
        "modelo": {
            "ciclo": "9 iteraciones = 9 bytes de entrada",
            "0": "S1 = crazy(byte, S1)  (push S1)",
            "3": "S2 = crazy(byte, S2)  (push S2)",
            "4": "S2 = rot(S2)           (pop S2, emite)",
            "5": "S1 = rot(S1)           (pop S1, emite)",
            "1,2,6,7,8": "inerte: emite el byte de entrada",
        },
        "casos": rows,
        "trazado": {
            "descripcion": ("ejecuciones de W1 (71) y W2 (83): opcode, d con "
                            "el que se ejecutan y valor de las dos ranuras"),
            "coincide": trace_ok,
            "filas": trace,
        },
        "lifo": {
            "bloque_A_en_0_B_en_3": bl.hex(),
            "bloque_B_en_0_A_en_3": sw.hex(),
            "pop_S2_posicion": 4,
            "pop_S1_posicion": 5,
            "intercambian": lifo,
        },
        "veredicto": verdict,
        "alcance": {
            "demostrado": ("dos ranuras de pila en un bucle real con orden "
                           "LIFO: push S1 (fase 0), push S2 (fase 3), pop S2 "
                           "(fase 4), pop S1 (fase 5); las fases las elige el "
                           "ciclo de XLAT2 de cada celda de trabajo"),
            "no_demostrado": [
                "pop exacto: el pop es un ROT y deja la ranura rotada; 10 "
                "ROT (rot^10 = identidad) es imposible en bucle porque varios "
                "ROT sobre la misma celda comparten las celdas-puntero",
                "supresion de las fases inertes 1,2,6,7,8 (IN/OUT siguen "
                "ejecutandose y emiten el byte)",
                "profundidad 3 o mayor",
                "que la clase de ciclo de 9 sea la unica que permita este "
                "calendario de fases",
            ],
        },
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"evidencia: {args.json}")
    return 0 if (ok_pos == total and ok_ctl == total and lifo) else 1


if __name__ == "__main__":
    sys.exit(main())
