#!/usr/bin/env python3
"""M1 — host oracle de la carry chain suma/resta sobre dominio ternario 3^6=729.

El circuito que emitira M2 opera sobre palabras ternarias de 10 trits con
primitivas crazy/rot. Aqui se verifica el ALGORITMO de carry chain sobre los
mismos trits (extraidos por rotacion + mascara, que es lo que luego baja a
gates): add(x,y) = (x+y) mod 729 y sub(x,y) = (x-y) mod 729.

Dominio 3^6 = 729: alineado a trits (el wrap es mascara sobre 6 trits, natural
en crazy/ROT), cubre los 256 valores de byte. El transporte del criptograma
(ASCII 33..126, 2 chars por palabra) es codigo, no cripto.

Exhaustivo: 729x729 pares para add y para sub + identidades.
"""
import json, hashlib, pathlib

def trit(x, k):
    return (x // (3 ** k)) % 3

def left(x, n):
    """rotar n trits (rot de Malbolge: x/3 + (x%3)*3^9)."""
    for _ in range(n):
        x = x // 3 + (x % 3) * 19683
    return x

def add(x, y, width=6):
    out, carry = 0, 0
    for k in range(width):
        s = trit(x, k) + trit(y, k) + carry
        out += (s % 3) * (3 ** k)
        carry = s // 3
    return out, carry

def sub(x, y, width=6):
    out, borrow = 0, 0
    for k in range(width):
        s = trit(x, k) - trit(y, k) - borrow
        if s < 0:
            s += 3
            borrow = 1
        else:
            borrow = 0
        out += s * (3 ** k)
    return out, borrow

def wrap(v):  # wrap mod 3^6: mantiene los 6 trits bajos
    return v % 729

rows_add, rows_sub = [], []
bad = 0
for x in range(729):
    for y in range(729):
        got_add, _ = add(x, y)
        got_sub, _ = sub(x, y)
        ea, es = wrap(x + y), wrap(x - y)
        if wrap(got_add) != ea or wrap(got_sub) != es:
            bad += 1
        if x % 53 == 0 and y % 61 == 0:
            rows_add.append({"x": x, "y": y, "got": wrap(got_add), "exp": ea})
            rows_sub.append({"x": x, "y": y, "got": wrap(got_sub), "exp": es})

# identidades clave
assert add(0, 0)[0] == 0 and sub(0, 0)[0] == 0
assert wrap(add(728, 1)[0]) == 0, "wrap de carry alto"
assert wrap(sub(0, 1)[0]) == 728, "wrap de borrow"
assert wrap(add(0x41, 0x41)[0]) == 0x82 and wrap(sub(0x82, 0x41)[0]) == 0x41
assert wrap(add(255, 1)[0]) == 256 and wrap(sub(256, 1)[0]) == 255, "bytes completos sin wrap"
print(f"pares verificados: {729 * 729} add + {729 * 729} sub ({729*729*2} casos) | fallos: {bad}")
