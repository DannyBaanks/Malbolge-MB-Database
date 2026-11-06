#!/usr/bin/env python3
"""Frente 3 (vía nativa): bucle de fetch real con estado entre bytes.

LA PRIMITIVA DE BUCLE (medida sobre example_simple_cat.mb, traza paso a paso)

En este dialecto, cada celda ejecutada se cifra tras la instruccion. El cifrado
(XLAT2) NO es una involucion global: es una permutacion con ciclos mezclados, y
solo DOS valores imprimibles forman un 2-ciclo: 70 ('F') y 74 ('J'). Ademas,
cuando la instruccion es un salto, `c` se reasigna al destino ANTES del cifrado,
asi que la celda del salto nunca se cifra.

De ahi la recipe real de LMAO, verificada en la traza de simple_cat:

    celda A   : instruccion, con un valor en 2-ciclo (74/70)
                -> al ejecutarse se cifra una vez
    celda A+1 : JMP con destino A
                -> la cifra otra vez: 70 -> 74, QUEDA RESTAURADA

La misma celda JMP se ejecuta dos veces por vuelta: primero restaura, luego
salta al siguiente landing. Un JMP es estable para siempre. La vuelta se cierra
con un MOVD final que rebobina `d` al primer par de punteros.

LO QUE EMITE ESTE GENERADOR

Una imagen Classic SIN LMAO. Layout (las direcciones de las celdas de trabajo
son las unicas donde su valor cae en 2-ciclo, modulo 94):

    IN 43 | MOVD 60 | CRAZY 82 | OUT 119 | MOVD 64
    JMPs en 44, 61, 83, 120, 65 (nunca se cifran)
    landings en 42, 45, 62, 84, 121, 66 (sacrificiales, solo se cifran)

    bucle:
        IN          a = byte de stdin
        MOVD        d = X2          (apunta a la celda de estado)
        CRAZY       mem[X2+3] = crazy(a, mem[X2+3]); a = mem[X2+3]
        OUT         emite a & 255   (el estado acumulado)
        MOVD        d = D0-3        (rebobina d y cierra la vuelta)

Es un bucle de fetch REAL (vuelve al mismo punto de despacho, celda 43) con una
celda de estado que sobrevive a todos los bytes leidos. Termina en EOF: lo para
el runner C (terminated=1) y el oraculo con stop_on_eof=True.

Semantica esperada (precalculable): estado = crazy(byte, estado) por byte.

NOTA DE ESTANDAR: las celdas de codigo decodifican a opcode valido en su propia
direccion (loader estricto). Las celdas de PUNTERO son imprimibles pero su
decodificacion no siempre es un opcode valido; nunca se ejecutan como
instruccion (c no las visita), solo las leen MOVD/JMP como datos. Ver
native_fold_loop.json, campo punteros_no_validos.
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
from constants import CHAR_OP_MAP, XLAT1, XLAT2, char_for_op, crazy_op  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import oracle_classic  # noqa: E402

RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"
VALID = frozenset("ji*p</vo")

OP_FOR = {"MOVD": "j", "IN": "/", "CRAZY": "p", "OUT": "<"}
OPNUM = {"MOVD": 40, "IN": 23, "CRAZY": 62, "OUT": 5}

# direcciones de trabajo (mod 94) cuyo char_for_op cae en 2-ciclo de XLAT2
A_IN, A_MOVD1, A_CRAZY, A_OUT, A_MOVD2 = 43, 60, 82, 119, 64
BOOTSTRAP = (0, 1, 2)          # MOVD, MOVD, JMP
D0, X2 = 70, 90                # valor de d en el IN, y base del grupo de estado
ZB = D0 - 2                    # celda leida por el MOVD del bootstrap
SLOT = X2 + 3
V0 = 33                        # valor inicial de la celda de estado

WORK = [(A_IN, "IN"), (A_MOVD1, "MOVD"), (A_CRAZY, "CRAZY"),
        (A_OUT, "OUT"), (A_MOVD2, "MOVD")]
CODE_CELLS = ({a for a, _ in WORK} | {a + 1 for a, _ in WORK}
              | {a + 2 for a, _ in WORK} | set(BOOTSTRAP))

POINTERS = {
    ZB: A_MOVD2,          # 68 -> 64   (d rebobinado por el MOVD de 64)
    ZB + 1: A_IN - 1,     # 69 -> 42   (landing antes del IN)
    D0 + 1: A_IN,         # 71 -> 43   (restaura el IN)
    D0 + 2: A_MOVD1 - 1,  # 72 -> 59   (landing antes del MOVD de 60)
    D0 + 3: X2,           # 73 -> 90   (el MOVD de 60 lee esto -> d = 90)
    X2 + 1: A_MOVD1,      # 91 -> 60   (restaura el MOVD de 60)
    X2 + 2: A_CRAZY - 1,  # 92 -> 81   (landing antes del CRAZY)
    X2 + 3: V0,           # 93 -> SLOT (celda de estado)
    X2 + 4: A_CRAZY,      # 94 -> 82   (restaura el CRAZY)
    X2 + 5: A_OUT - 1,    # 95 -> 118  (landing antes del OUT)
    X2 + 7: A_OUT,        # 97 -> 119  (restaura el OUT)
    X2 + 8: A_MOVD2 - 1,  # 98 -> 63   (landing antes del MOVD de 64)
    X2 + 9: D0 - 3,       # 99 -> 67   (el MOVD de 64 lee esto -> d = 67)
    41: ZB,               # 41 -> 68   (leida por el MOVD del bootstrap)
}
LEN = 130


def two_cycle(v: int) -> bool:
    e = ord(XLAT2[v - 33])
    return e != v and ord(XLAT2[e - 33]) == v


def valid_cell(addr: int, value: int) -> bool:
    return 33 <= value <= 126 and XLAT1[(value - 33 + addr) % 94] in VALID


def build() -> bytes:
    mem = [ord(char_for_op(CHAR_OP_MAP["j"], a)) for a in range(LEN)]
    # bootstrap explicito
    mem[0] = ord(char_for_op(CHAR_OP_MAP["j"], 0))   # d = 40
    mem[1] = ord(char_for_op(CHAR_OP_MAP["j"], 1))   # d = mem[41]
    mem[2] = ord(char_for_op(CHAR_OP_MAP["i"], 2))   # c = mem[69]
    # celdas de trabajo + sus JMP
    for addr, opname in WORK:
        v = ord(char_for_op(OPNUM[opname], addr))
        assert two_cycle(v), f"{opname}@{addr}: valor {v} no esta en 2-ciclo"
        mem[addr] = v
        mem[addr + 1] = ord(char_for_op(CHAR_OP_MAP["i"], addr + 1))
    # punteros
    for addr, value in POINTERS.items():
        mem[addr] = value
    # comprobaciones
    for addr, value in enumerate(mem):
        assert 33 <= value <= 126, f"celda {addr} no imprimible: {value}"
    for addr, opname in WORK:
        assert valid_cell(addr, mem[addr]), f"trabajo {addr} no valida"
        assert valid_cell(addr + 1, mem[addr + 1]), f"jmp {addr+1} no valido"
    ptrs = set(POINTERS)
    assert not (ptrs & CODE_CELLS), f"punteros pisan codigo: {ptrs & CODE_CELLS}"
    for a in ptrs:
        assert a + 1 < LEN, f"puntero fuera de imagen: {a}"
    bad = sorted(a for a, v in POINTERS.items() if not valid_cell(a, v))
    return bytes(mem), bad


def fold(data: bytes, v0: int) -> bytes:
    st = v0
    out = []
    for b in data:
        st = crazy_op(b, st)
        out.append(st & 255)
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
                    default=ROOT / "vm_malbolge/src/mbir_native_fold_loop.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/native_fold_loop.json")
    args = ap.parse_args()

    memory, bad = build()
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)
    print(f"imagen: {args.mb} ({len(memory)} bytes)")
    print(f"vuelta: IN@{A_IN} MOVD@{A_MOVD1} CRAZY@{A_CRAZY} "
          f"OUT@{A_OUT} MOVD@{A_MOVD2}")
    print(f"celda de estado: {SLOT} (valor inicial {V0})")
    print(f"punteros: {len(POINTERS)} celdas, {len(bad)} sin opcode valido "
          f"(nunca ejecutadas): {bad}")

    cases = [b"A", b"AB", b"ABC", b"HELLO", b"12345", b"", b"\x00\x01\x02",
             bytes(range(1, 33))]
    rows, ok = [], 0
    for sb in cases:
        exp = fold(sb, V0)
        oout, osteps, ostatus = run_oracle(memory, sb)
        oout_b = oout.encode("latin-1")
        rout, rerr = run_runner(memory, sb)
        agree = (oout_b == exp) and (rout == exp)
        ok += agree
        rows.append({"stdin": sb.hex(), "esperado": exp.hex(),
                     "oraculo": oout_b.hex(), "runner_c": rout.hex(),
                     "pasos_oraculo": osteps, "status": ostatus,
                     "stderr_runner": rerr, "acuerdo": agree})
        print(f"  {sb.hex()[:26]:26s} esperado={exp.hex()[:22]:22s} "
              f"oraculo={oout_b.hex()[:22]:22s} runner={rout.hex()[:22]:22s} "
              f"{osteps:6d}p {ostatus:8s} {'OK' if agree else 'FALLO'}")

    import random
    rnd = random.Random(1234)
    big = bytes(rnd.randrange(256) for _ in range(4096))
    rout, rerr = run_runner(memory, big, max_steps=60000000)
    exp = fold(big, V0)
    agree_big = rout == exp
    ok += agree_big
    print(f"  4096 bytes aleatorios: {'OK' if agree_big else 'FALLO'} ({rerr})")
    print(f"\n{ok}/{len(cases) + 1} casos de acuerdo")

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "bytes": len(memory),
        "sha256": hashlib.sha256(memory).hexdigest(),
        "slot_celda": SLOT, "slot_valor_inicial": V0,
        "layout": {
            "trabajo": {name: addr for addr, name in WORK},
            "jmp": sorted(addr + 1 for addr, _ in WORK),
            "bootstrap": list(BOOTSTRAP),
            "punteros": {str(a): v for a, v in sorted(POINTERS.items())},
            "punteros_no_validos": bad,
        },
        "casos": rows,
        "volumen_4096": {"acuerdo": agree_big,
                         "sha_esperado": hashlib.sha256(exp).hexdigest()},
        "veredicto": ("BUCLE_DE_FETCH_CON_ESTADO_DEMOSTRADO"
                      if ok == len(cases) + 1 else "FALLO"),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"evidencia: {args.json}")
    return 0 if ok == len(cases) + 1 else 1


if __name__ == "__main__":
    sys.exit(main())
