#!/usr/bin/env python3
"""Bucle de pila por fases: CRAZY y ROT sobre la MISMA celda, en iteraciones
distintas, dentro de un bucle real.

EL BLOQUEANTE QUE ATACA

`stack2_oneshot.md` (lineas 68-78) demostro que con la primitiva de
restauracion por 2-ciclo una celda no puede escribirse y leerse en el mismo
ciclo: `CRAZY` y `ROT` dejan ambos `d = S`, comparten las celdas-puntero
`(S+1, S+2)` y los valores que necesitan (sus propias direcciones, para
restaurar) no pueden coincidir. La salida documentada era una celda-puntero
escrita en runtime (cerrada en `pointer_cell_rt.md`, one-shot).

LA SALIDA: EL CICLO DE CIFRADO COMO SELECTOR DE FASE

En este dialecto cada celda ejecutada se cifra con XLAT2. Si una celda de
trabajo NO se restaura, su valor avanza por su ciclo de XLAT2 y el opcode que
decodifica cambia en cada iteracion. Ese es el selector de fase, y es runtime
puro: el estado de cifrado de la propia celda.

Medido: en la direccion A_W = 83 (mod 94) la celda arranca como `CRAZY`, y su
ciclo de XLAT2 tiene longitud 9:

    iteracion : 0     1     2   3   4   5   6    7   8
    valor     : 73    50    80  66  62  76  79   67  85
    opcode    : CRAZY ROT   inv inv inv inv NOP  inv inv

Es decir: **iteracion 0 escribe** (`CRAZY`), **iteracion 1 lee** (`ROT`), las
otras siete no tocan la celda, y a la novena vuelve a empezar. La misma celda
de instruccion hace las dos cosas: no hay dos direcciones que colisionen en
`(S+1, S+2)`; hay una sola, y su pareja de punteros es unica.

CADENA DEL BUCLE (una vuelta = 14 pasos)

    IN        a = byte
    J_IN      primer salto restaura IN; segundo despacha a M
    M  MOVD   d = S-6  (post d = S-5)
    J_M       restaura M; despacha a P
    P  NOP    consume d (post S-2)
    J_P       restaura P; despacha a W con d = S
    W         CRAZY/ROT/NOP sobre mem[S] segun la fase
    J_W       UN solo salto: despacha a O (no restaura W: queremos que siga
              avanzando por su ciclo)
    O  OUT    emite a & 255
    J_O       restaura O; despacha de vuelta a IN

Los punteros viven en S-6..S+8 y NINGUNO cae en S: la celda de pila no se usa
como puntero. Las celdas IN/M/P/O y sus JMP usan valores en 2-ciclo de XLAT2
(74/70) y se restauran cada vuelta; W es la unica que no se restaura.

SALIDA ESPERADA (modelo, no supuesta)

    fase 0: S = crazy(byte, S); sale S & 255   (push)
    fase 1: S = rot(S);         sale S & 255   (lectura)
    fases 2..8: sale el byte tal cual          (paso)

Las fases 2..8 son transito (IN y OUT siguen ejecutandose); el documento de
evidencia lo dice sin adornos. El control negativo cambia SOLO el valor de W
por 42 (ciclo de 4, todos opcodes invalidos): W nunca escribe ni lee, y la
salida debe ser el flujo de entrada sin tocar.

ESTANDAR DE CELDAS

Como en `native_fold_loop_gen.py`: las celdas de CODIGO decodifican a opcode
valido en su propia direccion; las celdas-PUNTERO son imprimibles pero pueden
decodificar a un opcode invalido porque nunca se ejecutan (solo las leen
MOVD/JMP como datos). El control, a proposito, arranca W en un opcode
invalido: es una celda inerte y asi se documenta.
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
from constants import (  # noqa: E402
    XLAT1, XLAT2, char_for_op, crazy_op, rot_op,
)

sys.path.insert(0, str(ROOT / "tools"))
import oracle_classic  # noqa: E402

RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"
VALID = frozenset("ji*p</vo")
OPNUM = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "MOVD": 40,
         "CRAZY": 62, "NOP": 68, "HALT": 81}
VALID_OPS = frozenset(OPNUM.values())

LEN = 256


def enc(v: int) -> int:
    return ord(XLAT2[v - 33])


def two_cycle(v: int) -> bool:
    e = enc(v)
    return e != v and enc(e) == v


def valid_cell(addr: int, value: int) -> bool:
    return (33 <= value <= 126
            and XLAT1[(value - 33 + addr) % 94] in VALID)


def op_at(addr: int, value: int) -> int:
    return (value + addr) % 94


def cell(opname: str, addr: int) -> int:
    return ord(char_for_op(OPNUM[opname], addr))


def cycle_from(addr: int, v0: int):
    """Valores y opcodes de una celda al ejecutarse una vez por iteracion."""
    vals, ops = [], []
    v = v0
    while True:
        vals.append(v)
        ops.append(op_at(addr, v))
        v = enc(v)
        if v == v0:
            break
        if len(vals) > 100:
            raise RuntimeError("ciclo XLAT2 no cerro")
    return vals, ops


def w_cycle(addr: int, start_op: str = "CRAZY"):
    """Ciclo de W arrancando en el opcode valido `start_op`."""
    return cycle_from(addr, cell(start_op, addr))


def layout(S, A_IN, A_MOVD, A_NOP, A_OUT, A_W):
    """Simula el flujo de d y devuelve celdas de codigo, landings y punteros."""
    code = {0: cell("MOVD", 0), 1: cell("MOVD", 1), 2: cell("JMP", 2)}
    roles = {0: "boot_movd0", 1: "boot_movd1", 2: "boot_jmp"}
    work = (("IN", A_IN), ("MOVD", A_MOVD), ("NOP", A_NOP),
            ("OUT", A_OUT), ("CRAZY", A_W))
    for name, addr in work:
        code[addr] = cell(name, addr)
        code[addr + 1] = cell("JMP", addr + 1)
        roles[addr] = name
        roles[addr + 1] = "jmp_" + name
    land = {A_IN - 1: "L_IN", A_MOVD - 1: "L_MOVD", A_NOP - 1: "L_NOP",
            A_OUT - 1: "L_OUT", A_W - 1: "L_W"}
    ptr = {
        41: S + 3,            # bootstrap: MOVD de la celda 1
        S + 6: A_IN,          # J_IN primer salto (restaura IN)
        S + 7: A_MOVD - 1,    # J_IN segundo salto (despacha a MOVD)
        S + 8: S - 6,         # MOVD lee esto -> d = S-6
        S - 5: A_MOVD,        # J_MOVD primer salto (restaura MOVD)
        S - 4: A_NOP - 1,     # J_MOVD segundo salto (despacha a NOP)
        S - 2: A_NOP,         # J_NOP primer salto (restaura NOP)
        S - 1: A_W - 1,       # J_NOP segundo salto (despacha a W, d=S)
        S + 1: A_OUT - 1,     # J_W unico salto (despacha a OUT)
        S + 3: A_OUT,         # J_OUT primer salto (restaura OUT)
        S + 4: A_IN - 1,      # J_OUT segundo salto (vuelve a IN)
    }
    return code, roles, land, ptr


def check_layout(S, A_IN, A_MOVD, A_NOP, A_OUT, A_W, len_=LEN):
    code, roles, land, ptr = layout(S, A_IN, A_MOVD, A_NOP, A_OUT, A_W)
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
    if any(not (0 <= a < len_) for a in occupied):
        return None, "direccion fuera de imagen"
    bad = [(a, v, roles[a]) for a, v in code.items() if not valid_cell(a, v)]
    if bad:
        return None, f"codigo no valido {bad[:3]}"
    for a, v in ptr.items():
        if not (33 <= v <= 126):
            return None, f"puntero {a}={v} no imprimible"
    for name, addr in (("IN", A_IN), ("MOVD", A_MOVD),
                       ("NOP", A_NOP), ("OUT", A_OUT)):
        if not two_cycle(code[addr]):
            return None, f"{name}@{addr} no esta en 2-ciclo ({code[addr]})"
    vals, ops = w_cycle(A_W)
    if len(vals) != 9 or ops[0] != OPNUM["CRAZY"] or ops[1] != OPNUM["ROT"]:
        return None, f"W ciclo/ops inesperado: {ops[:3]}"
    return (code, roles, land, ptr, vals, ops), "OK"


def search_layout():
    """Primer layout valido en orden determinista (S creciente, luego A_*)."""
    for S in range(39, 127):
        for A_IN in (43, 47):
            for A_MOVD in (60, 64):
                for A_NOP in (88, 92):
                    for A_OUT in (119, 123):
                        A_W = 83
                        r, msg = check_layout(S, A_IN, A_MOVD, A_NOP,
                                              A_OUT, A_W)
                        if r:
                            return (S, A_IN, A_MOVD, A_NOP, A_OUT, A_W, r)
    raise RuntimeError("no se encontro layout valido")


def build(params, control=False, v_stack=33, w_control=42):
    S, A_IN, A_MOVD, A_NOP, A_OUT, A_W, (code, roles, land, ptr,
                                          vals, ops) = params
    mem = [cell("NOP", a) for a in range(LEN)]
    for a, v in code.items():
        mem[a] = v
    for a in land:
        mem[a] = cell("NOP", a)      # sacrificial, nunca se ejecuta
    for a, v in ptr.items():
        mem[a] = v
    mem[S] = v_stack
    if control:
        mem[A_W] = w_control          # ciclo inerte: nunca CRAZY/ROT
    assert all(33 <= v <= 126 for v in mem)
    for a, v in code.items():
        assert valid_cell(a, v), f"codigo {a} ({roles[a]}) no valido"
    return bytes(mem)


def model(data: bytes, v_stack=33, control=False):
    """Modelo de la maquina de 9 fases (la fase es i mod 9)."""
    st = v_stack
    out = []
    for i, b in enumerate(data):
        if control:
            out.append(b & 255)
            continue
        phase = i % 9
        if phase == 0:
            st = crazy_op(b, st)
            out.append(st & 255)
        elif phase == 1:
            st = rot_op(st)
            out.append(st & 255)
        else:
            out.append(b & 255)
    return bytes(out)


def run_oracle(memory: bytes, sb: bytes, max_steps=400000):
    src = memory.decode("latin-1")
    return oracle_classic.run(src, max_steps=max_steps,
                              stdin_data=sb.decode("latin-1"),
                              stop_on_eof=True)


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
        return r.stdout, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(n)
        os.unlink(mbn)


def runner_agrees(raw: bytes, expected: bytes) -> bool:
    """El runner C anade UN 0x0a; trampa CRLF: comparar contra el crudo."""
    return raw == expected or (raw.endswith(b"\n") and raw[:-1] == expected)


def trace_w(memory: bytes, data: bytes, w_addr: int, s_addr: int, n=10):
    """Traza las primeras n ejecuciones de la celda W: opcode, d y mem[S].

    Instrumenta la semántica del oráculo (no la reimplementa): replica el
    bucle de `oracle_classic.run` registrando la celda de trabajo.
    """
    mem = oracle_classic.load_memory(memory.decode("latin-1"))
    a = c = d = 0
    out = []
    it = iter(data)
    steps = 0
    rows = []
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
        if not jumped and executed == w_addr:
            rows.append({
                "paso": steps, "opcode": op,
                "nombre": next((k for k, v in OPNUM.items() if v == op),
                               "invalido"),
                "d": d_exec, "valor_celda_W": mem[w_addr],
                "mem_S": mem[s_addr],
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_stack_loop_phase.mb")
    ap.add_argument("--ctrl", type=Path,
                    default=ROOT /
                    "vm_malbolge/src/mbir_stack_loop_phase_ctrl.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT /
                    "vm_malbolge/evidence/stack_loop_phase.json")
    args = ap.parse_args()

    params = search_layout()
    S, A_IN, A_MOVD, A_NOP, A_OUT, A_W, (code, roles, land, ptr,
                                          vals, ops) = params
    pos = build(params)
    ctl = build(params, control=True)
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(pos)
    args.ctrl.write_bytes(ctl)

    print(f"layout: S={S} IN={A_IN} MOVD={A_MOVD} NOP={A_NOP} "
          f"OUT={A_OUT} W={A_W}")
    print(f"  punteros: {sorted(ptr.items())}")
    print(f"  landings: {sorted(land.items())}")
    print(f"  W ciclo ({len(vals)}): {vals}")
    print(f"  W ops: {[next((k for k, v in OPNUM.items() if v == o), o) for o in ops]}")
    print(f"imagen: {args.mb} ({len(pos)} bytes)")
    print(f"control: {args.ctrl} ({len(ctl)} bytes)")

    cases = [b"", b"A", b"AB", b"ABCDEFGHI", b"ABCDEFGHIJKLMNOPQR",
             bytes(range(1, 33)), b"AB" + bytes(range(0x30, 0x37))]
    rnd = random.Random(2026)
    big = bytes(rnd.randrange(256) for _ in range(4096))
    cases.append(big)

    rows, ok_pos, ok_ctl = [], 0, 0
    total = 0
    for sb in cases:
        exp_pos = model(sb)
        exp_ctl = model(sb, control=True)
        o_pos, st_pos, status_pos = run_oracle(pos, sb)
        r_pos_raw, err_pos = run_runner(pos, sb)
        o_ctl, st_ctl, status_ctl = run_oracle(ctl, sb)
        r_ctl_raw, err_ctl = run_runner(ctl, sb)
        o_pos_b = o_pos.encode("latin-1")
        o_ctl_b = o_ctl.encode("latin-1")
        agree_pos = (o_pos_b == exp_pos
                     and runner_agrees(r_pos_raw, exp_pos))
        agree_ctl = (o_ctl_b == exp_ctl
                     and runner_agrees(r_ctl_raw, exp_ctl))
        ok_pos += agree_pos
        ok_ctl += agree_ctl
        total += 1
        label = sb.hex()
        print(f"  in={label[:34]:34s} l={len(sb):5d} "
              f"pos={'OK' if agree_pos else 'FALLO'} "
              f"ctl={'OK' if agree_ctl else 'FALLO'} "
              f"({st_pos}p {status_pos})")
        rows.append({
            "stdin": sb.hex(), "bytes": len(sb),
            "esperado_pos": exp_pos.hex(),
            "oraculo_pos": o_pos_b.hex(),
            "runner_pos_crudo": r_pos_raw.hex(),
            "pasos_pos": st_pos, "status_pos": status_pos,
            "stderr_runner_pos": err_pos,
            "esperado_ctl": exp_ctl.hex(),
            "oraculo_ctl": o_ctl_b.hex(),
            "runner_ctl_crudo": r_ctl_raw.hex(),
            "pasos_ctl": st_ctl, "status_ctl": status_ctl,
            "stderr_runner_ctl": err_ctl,
            "acuerdo_pos": agree_pos, "acuerdo_ctl": agree_ctl,
        })

    trace = trace_w(pos, b"ABCDEFGHIJKLMNOPQR", A_W, S, n=10)
    ops_seq = [r["nombre"] for r in trace]
    ds = {r["d"] for r in trace}
    trace_ok = (ops_seq[0] == "CRAZY" and ops_seq[1] == "ROT"
                and ops_seq[9] == "CRAZY" and ds == {S})
    print(f"\ntraza de W: ops={ops_seq} d={ds} -> {'OK' if trace_ok else 'FALLO'}")

    verdict = ("BUCLE_DE_FASES_ESCRITURA_Y_LECTURA_MISMA_CELDA_DEMOSTRADO"
               if ok_pos == total and ok_ctl == total and trace_ok else "FALLO")
    print(f"\npositivo {ok_pos}/{total} | control {ok_ctl}/{total}")
    print(f"veredicto: {verdict}")

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "control": str(args.ctrl.relative_to(ROOT)),
        "bytes": len(pos),
        "sha256": hashlib.sha256(pos).hexdigest(),
        "sha256_control": hashlib.sha256(ctl).hexdigest(),
        "layout": {
            "S": S, "A_IN": A_IN, "A_MOVD": A_MOVD, "A_NOP": A_NOP,
            "A_OUT": A_OUT, "A_W": A_W, "v_stack": 33,
            "punteros": {str(a): v for a, v in sorted(ptr.items())},
            "landings": {str(a): n for a, n in sorted(land.items())},
            "roles_codigo": {str(a): n for a, n in sorted(roles.items())},
            "w_control": 42,
            "w_control_ciclo": {
                "valores": cycle_from(A_W, 42)[0],
                "opcodes": cycle_from(A_W, 42)[1],
                "nota": "ciclo inerte: ningun opcode es CRAZY ni ROT",
            },
        },
        "w_ciclo": {
            "valores": vals,
            "opcodes": ops,
            "nombres": [next((k for k, v in OPNUM.items() if v == o), "invalido")
                        for o in ops],
            "nota": ("W no se restaura: avanza por su ciclo XLAT2. "
                     "Iteracion 0 CRAZY (escritura), 1 ROT (lectura), "
                     "2..8 NOP/invalido."),
        },
        "modelo": {
            "fase": "i mod 9",
            "0": "S = crazy(byte, S); emite S & 255",
            "1": "S = rot(S); emite S & 255",
            "2..8": "emite el byte de entrada",
            "control": "W=42 en la celda W: ciclo inerte; emite la entrada",
        },
        "casos": rows,
        "trazado_w": {
            "descripcion": ("primeras 10 ejecuciones de la celda W: opcode, "
                            "d con el que se ejecuta y valor de mem[S]"),
            "todas_con_d_igual_S": trace_ok,
            "filas": trace,
        },
        "veredicto": verdict,
        "alcance": {
            "demostrado": ("CRAZY y ROT sobre la misma celda S en iteraciones "
                           "distintas dentro de un bucle real; la fase la "
                           "selecciona el ciclo de cifrado de W, sin celda-"
                           "puntero de fase y sin colision de pares"),
            "no_demostrado": [
                "pila LIFO de profundidad 2 o mayor en bucle",
                "supresion de las fases de transito 2..8 (IN/OUT siguen "
                "ejecutandose y emiten el byte)",
                "que el ciclo de 9 sea el unico posible; se eligio por "
                "CRAZY@0 y ROT@1 medidos",
            ],
        },
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"evidencia: {args.json}")
    return 0 if (ok_pos == total and ok_ctl == total) else 1


if __name__ == "__main__":
    sys.exit(main())
