"""Canonical Classic (3^10) Malbolge interpreter — independent reference oracle.

This is an independent Python oracle used by runner_doctor.ps1 to cross-check
the C engine (malbolge.exe) against an established known-vector
(hello_world_40.mb -> "Hello World!", 40 steps, HALTED).

Validated against the ISyCo canonical interpreter (same semantics) and the
malbolge-lisp-forensics oracle (Hello World! at 40 steps).

Evidence kind: REFERENCE_MODEL (host_language = Python, variant = classic 3^10).
"""
from __future__ import annotations

MEM_SIZE = 3 ** 10

_ORIGINAL = r"""!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"""
_TRANSLATED = r"""5z]&gqtyfr$(we4{WP)H-Zn,[%\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G"i@"""
assert len(_ORIGINAL) == 94 and len(_TRANSLATED) == 94
_ENC = {ord(o): ord(t) for o, t in zip(_ORIGINAL, _TRANSLATED)}

_CRAZY = (
    (1, 0, 0),
    (1, 0, 2),
    (2, 2, 1),
)


def crazy_op(x: int, y: int) -> int:
    res = 0
    p = 1
    for _ in range(10):
        res += _CRAZY[y % 3][x % 3] * p
        x //= 3
        y //= 3
        p *= 3
    return res


def load_memory(source: str):
    chars = [c for c in source if not c.isspace()]
    mem = [0] * MEM_SIZE
    for i, c in enumerate(chars):
        v = ord(c)
        if not (33 <= v <= 126):
            raise ValueError("non-printable source char at %s: %s" % (i, v))
        mem[i] = v
    for i in range(len(chars), MEM_SIZE):
        mem[i] = crazy_op(mem[i - 1], mem[i - 2])
    return mem


def run(source: str, max_steps: int = 2000000, stdin_data: str = ""):
    mem = load_memory(source)
    a = 0
    c = 0
    d = 0
    out = []
    stdin_iter = iter(stdin_data)
    steps = 0

    while steps < max_steps:
        steps += 1
        cell = mem[c]
        op = (cell + c) % 94
        jumped = False
        c_target = 0

        if op == 4:
            c_target = mem[d]
            jumped = True
        elif op == 5:
            out.append(a % 256)
        elif op == 23:
            ch = next(stdin_iter, None)
            a = -1 if ch is None else ord(ch)
        elif op == 39:
            v = mem[d]
            mem[d] = (v // 3) + (v % 3) * (3 ** 9)
            a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
        elif op == 68:
            pass
        elif op == 81:
            return bytes(out).decode("latin-1"), steps, "HALTED"
        else:
            pass

        if jumped:
            c = c_target
        if 33 <= mem[c] <= 126:
            mem[c] = _ENC[mem[c]]
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE

    return bytes(out).decode("latin-1"), steps, "MAX_STEPS"


def oracle_run(source_file: str, max_steps: int = 2000000, stdin_data: str = ""):
    with open(source_file, "r", encoding="ascii") as f:
        source = f.read()
    text, steps, status = run(source, max_steps, stdin_data)
    return {"output": text, "steps": steps, "status": status}


if __name__ == "__main__":
    import json
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else None
    if not src:
        sys.exit("usage: py oracle_classic.py <program.mb> [max_steps]")
    max_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 2000000
    r = oracle_run(src, max_steps)
    print(json.dumps(r))
    sys.exit(0)