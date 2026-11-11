#!/usr/bin/env python3
"""Adición 2026-11-11 a epoch_audit_v1: auditoría de epoch_rearm_cost_v1 y dialecto Olmstead 1998.

No importa nada del repo: reutiliza el intérprete de indep_interpreter.py (mismo directorio)
leyendo su código. Uso:
  python3 -I addendum_checks.py <dir del pack cost> <resolver_epoch.mb> [binario olmstead]
"""
import sys, subprocess, pathlib
HERE = pathlib.Path(__file__).resolve().parent
exec((HERE / "indep_interpreter.py").read_text().split("img=open")[0])
D = pathlib.Path(sys.argv[1]); RES = sys.argv[2]; OLM = sys.argv[3] if len(sys.argv) > 3 else None
VAL = {4, 5, 23, 39, 40, 62, 68, 81}
for n in ("restore", "no_restore", "rearm"):
    img = (D / f"{n}.mb").read_bytes()
    inv = sum((v + i) % 94 not in VAL for i, v in enumerate(img))
    for g in (False, True):
        r = run(img, b"", maxs=1000, guard=g)
        print(n, "guard" if g else "perm ", r["status"], r["steps"], r["out"].hex(), "| celdas no válidas para el cargador:", inv, "/", len(img))
print("rot(54) =", rot(54), "| crazy(rot(54),74) =", crz(rot(54), 74),
      "| ENC[55] =", ord(X2[55 - 33]), "| crazy(29552, ENC[55]) =", crz(29552, ord(X2[55 - 33])))
img = open(RES, "rb").read()
def req(b, V):
    t = trits(V); return bytes([b] + [2 if x == 1 else 0 for x in t] + [2 if x != 0 else 0 for x in t])
mem = list(img) + [0] * (N - len(img))
for i in range(len(img), N): mem[i] = crz(mem[i - 1], mem[i - 2])
a = c = d = 0; ip = 0; pcs = []; inp = req(99, 29797)
for s in range(5000):
    pcs.append(c); op = (mem[c] + c) % 94
    if op == 4: c = mem[d]
    elif op == 23: a = inp[ip]; ip += 1
    elif op == 39: mem[d] = rot(mem[d]); a = mem[d]
    elif op == 40: d = mem[d]
    elif op == 62: mem[d] = crz(a, mem[d]); a = mem[d]
    elif op == 81: break
    if 33 <= mem[c] <= 126: mem[c] = ord(X2[mem[c] - 33])
    c = (c + 1) % N; d = (d + 1) % N
code = sorted(set(pcs))
print("resolver_epoch (e100_p29797): pasos", len(pcs), "| celdas de código distintas", len(code),
      "| ejecutadas más de una vez", len(pcs) - len(code), "| rango", code[0], "..", code[-1],
      "| dentro de 34..126:", sum(34 <= x <= 126 for x in code))
if OLM:
    for f in [D / "restore.mb", D / "no_restore.mb", D / "rearm.mb", pathlib.Path(RES)]:
        p = subprocess.run([OLM, str(f)], stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        print("olmstead1998", f.name, "->", (p.stdout + p.stderr).decode("latin-1").strip()[:60])
