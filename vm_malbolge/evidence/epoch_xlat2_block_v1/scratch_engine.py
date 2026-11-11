#!/usr/bin/env python3
"""scratch_engine.py — motor de Malbolge escrito desde la especificación de 1998.

Sin importar nada del repo: las tres tablas se teclean desde la especificación
clásica (Olmstead 1998) y la semántica se implementa sobre los opcodes canónicos
`(mem[c] + c) % 94` = {4 jmp, 5 out, 23 rot, 39 crazy, 40 dload, 62 in, 68 nop,
81 end}. Sirve como cuarto motor independiente para `epoch_xlat2_block_v1`:
se valida contra el vector conocido `tools/fixtures/hello_world_40.mb`
("Hello World!", 40 pasos) y contra las imágenes del pack.

Uso:  python3 scratch_engine.py <imagen.mb> [max_steps]
"""
from __future__ import annotations

MEM = 3 ** 10

# Tabla de cifrado posterior a la ejecución (XLAT2), especificación de 1998.
XLAT2 = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TV"
         "ac`uY*MK'X~xDl}REokN:#?G\"i@")
assert len(XLAT2) == 94

# Tabla de la operación "crazy" (filas = trit de memoria, columnas = trit de A).
CRZ = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

# Opcode canónico 1998: número = (mem[c] + c) % 94. Nombres según el oráculo del
# repo (validado con "Hello World!" en 40 pasos): 23 es la lectura de stdin y 62
# es la operación crazy.
OP_NAMES = {4: "jmp", 5: "out", 23: "in", 39: "rot", 40: "dload",
            62: "crazy", 68: "nop", 81: "end"}


def crazy(x: int, y: int) -> int:
    res = 0
    p = 1
    for _ in range(10):
        res += CRZ[y % 3][x % 3] * p
        x //= 3
        y //= 3
        p *= 3
    return res


def encrypt(v: int) -> int:
    return ord(XLAT2[v - 33])


def rot(v: int) -> int:
    return v // 3 + (v % 3) * 19683


def run(image: bytes, max_steps: int = 10000, stdin: bytes = b"",
        collect: bool = False) -> dict:
    mem = list(image) + [0] * (MEM - len(image))
    for i in range(len(image), MEM):
        mem[i] = crazy(mem[i - 1], mem[i - 2])
    a = c = d = 0
    ip = 0
    out = bytearray()
    events = []
    for step in range(1, max_steps + 1):
        cell = mem[c]
        o = (cell + c) % 94
        dest = None
        if collect:
            events.append({"step": step, "pc": c, "op": o, "d": d,
                           "value": cell, "dest": None})
        if o == 4:
            dest = mem[d]
            c = dest                     # el salto canónico
        elif o == 5:
            out.append(a % 256)
        elif o == 23:
            a = 59048 if ip >= len(stdin) else stdin[ip]
            ip += 1
        elif o == 39:
            mem[d] = rot(mem[d])
            a = mem[d]
        elif o == 40:
            d = mem[d]
        elif o == 62:
            mem[d] = crazy(a, mem[d])
            a = mem[d]
        elif o == 81:
            if collect:
                events[-1]["dest"] = dest
            return {"out": bytes(out), "steps": step, "status": "HALTED",
                    "events": events}
        if collect:
            events[-1]["dest"] = dest
        if 33 <= mem[c] <= 126:
            mem[c] = encrypt(mem[c])
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {"out": bytes(out), "steps": max_steps, "status": "MAX",
            "events": events}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("usage: scratch_engine.py <imagen.mb> [max_steps]")
    path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    data = open(path, "rb").read()
    r = run(data, max_steps=limit, stdin=b"")
    print("steps=%d status=%s out=%s" % (r["steps"], r["status"], r["out"].hex()))
