#!/usr/bin/env python3
"""M2 — netlist host de la suma general add(x, y) sobre 3^6 = 729.

Composicion verificable compuesta SOLO de primitivas demostradas:
  - el circuito de incremento (+1 con carry paralelo) de
    vm_malbolge/tools/increment_bf/circuit.py (verificado all-256 en
    increment_circuit_loop_v1), portado aqui con nota de procedencia;
  - rotaciones de trits (rot de Malbolge).

Idea: sumar y = sumar sus trits uno a uno en su posicion. Sumar 3^k a una
palabra = rotar para llevar el trit k a la posicion 0, aplicar +1 (el carry
se propaga hacia arriba, que es exactamente sumar 3^k), y rotar de vuelta.
Un trit de valor t aplica el incremento posicional t veces (t<=2).

El netlist resultante (lista de gates/rotaciones) es lo que M2-imagen baja
a HeLL con la tuberia de build_hell.py.

Verificacion exhaustiva: 729 x 729 pares para add; sub se deriva como
add(x, (729 - y) % 729) y se verifica con el mismo barrido.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

# ---- primitivas Malbolge (portadas de increment_bf/circuit.py, MIT repo) ----
ONE = 29524          # C1: todos los trits = 1
TWO = 59048          # C2: todos los trits = 2
LOW = sum(3 ** i for i in range(6))   # trits 0..5 (dominio 729)
HIGH = ONE - LOW


def crazy(x, y):
    """TBL[cell][acc] trit a trit (constants.py: crazy_op)."""
    TBL = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
    out, p = 0, 1
    for _ in range(10):
        xt = (x // p) % 3
        yt = (y // p) % 3
        out += TBL[yt][xt] * p
        p *= 3
    return out % 59049


def rot(x):
    return x // 3 + (x % 3) * 19683


def left(x, n):
    for _ in range((10 - n) % 10):
        x = rot(x)
    return x


# ---- circuito de incremento (+1 con carry), tal cual circuit.py ----
def eq2_or(x, mask):
    g = crazy(mask, x)
    return crazy(g, x)


def and_or(x, y, mask):
    g1 = crazy(TWO, x)
    g2 = crazy(g1, y)
    g3 = crazy(mask, g2)
    return crazy(g3, g3)


def bool_and(x, y):
    g1 = crazy(TWO, x)
    g2 = crazy(y, y)
    g3 = crazy(g1, g2)
    return crazy(g3, y)


def add_bit(x, y):
    g1 = crazy(TWO, y)
    g2 = crazy(x, 0)
    g3 = crazy(g2, g1)
    g4 = crazy(g3, x)
    return crazy(g4, ONE)


def increment(x):
    p = eq2_or(x, HIGH)
    for k in (1, 2, 4):
        p = and_or(p, left(p, k), HIGH)
    carry = bool_and(left(p, 1), LOW)
    return add_bit(x, carry)


# ---- netlist de suma general (la composicion que se emite) ----
NETLIST_OPS = 0


def add(x, y, w=6):
    """(x + y) mod 3^w por incrementos posicionales. Devuelve (valor, ops)."""
    global NETLIST_OPS
    out, ops = x % (3 ** w), 0
    for k in range(w):
        t = (y // (3 ** k)) % 3
        if t == 0:
            continue
        r = left(out, (10 - k) % 10)          # trit k -> posicion 0
        ops += 1
        for _ in range(t):
            r = increment(r)                  # +1 con carry
            ops += 1
        out = left(r, k)                      # posicion 0 -> trit k
        ops += 1
    return out % (3 ** w), ops


def sub(x, y, w=6):
    """(x - y) mod 3^w derivado de add con el complemento."""
    return add(x, (3 ** w) - (y % (3 ** w)), w)


def main():
    # 1) el circuito de incremento sigue verificando all-256 (regresion del port)
    for i in range(256):
        got = increment(i)
        assert got == i + 1, f"increment roto: {i} -> {got}"
    # 2) add exhaustivo sobre el dominio del cifrado
    bad = 0
    ops_max = 0
    rows = []
    for x in range(729):
        for y in range(729):
            got, ops = add(x, y)
            ops_max = max(ops_max, ops)
            if got != (x + y) % 729:
                bad += 1
            elif x % 97 == 0 and y % 89 == 0:
                rows.append({"x": x, "y": y, "got": got, "exp": (x + y) % 729, "ops": ops})
    # 3) sub derivado, mismo barrido
    bad_sub = 0
    for x in range(729):
        for y in range(729):
            got, _ = sub(x, y)
            if got != (x - y) % 729:
                bad_sub += 1
    # 4) identidades
    assert add(728, 1)[0] == 0
    assert sub(0, 1)[0] == 728
    assert add(0x41, 0x41)[0] == 0x82
    assert sub(0x82, 0x41)[0] == 0x41

    doc = {
        "claim_status": "DEMONSTRATED" if bad == 0 and bad_sub == 0 else "FAILED",
        "milestone": "M2 host netlist add/sub (bolge-crypt-v0)",
        "domain": "3^6=729",
        "cases": {"add": 729 * 729, "sub": 729 * 729, "failures": bad + bad_sub},
        "max_gate_ops_per_add": ops_max,
        "composition": "positional increments of the verified +1 circuit (increment_circuit_loop_v1), <= 12 applications, rotations by k",
        "source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "rows_sample": rows[:10],
        "note": "host composition only; HeLL lowering and image emission are M2-image",
    }
    ev = pathlib.Path(__file__).resolve().parent / "evidence"
    ev.mkdir(exist_ok=True)
    (ev / "adder_netlist.json").write_text(json.dumps(doc, indent=2))
    print(f"add 729x729 fallos={bad} | sub fallos={bad_sub} | ops_max={ops_max}")
    print("evidencia:", ev / "adder_netlist.json", doc["claim_status"])


if __name__ == "__main__":
    main()