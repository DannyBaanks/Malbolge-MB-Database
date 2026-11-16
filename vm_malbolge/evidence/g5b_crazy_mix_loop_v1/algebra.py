#!/usr/bin/env python3
"""G5b-1a algebra: rama EOF nativa, mezcla crazy y reinicios, verificadas en el host.

Cadena AAADA sobre x (byte 0..255 o EOF=59048):
  s1 CRAZY Z  (Z=29524)        Z := sigma(x) = crazy(x, 29524)  (biyectiva por trit, se conserva)
  s2 CRAZY C2 (C2=59048)
  s3 CRAZY C3 (C3=29524)
  s4 a := 59048 (ROT U; CRAZY V4) ; CRAZY C3   (x en la celda, constante en A)
  s5 CRAZY C5 (C5=58319)       -> 57590 para todo byte, 58319 para EOF
Mezcla (solo bytes, a = 57590 tras la rama):
  m1 CRAZY Z ; m2 CRAZY K (K=KEY)  -> OUT a mod 256
Reinicios: t -> 29524 con ROT U; CRAZY t; CRAZY t. t -> c (trits 1/2) con CRAZY Vc; CRAZY t.
"""
import importlib.util
import json
import pathlib

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
spec = importlib.util.spec_from_file_location('compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
crz, rot = m.SE.crazy, m.SE.rot

ONE, ALL2 = 29524, 59048
EOF = 59048
A_CONT, A_HALT = 57590, 58319
C2, C3, C4A, C5 = ALL2, ONE, ALL2, 58319
# Clave: trits {1,2}, fijada por un patron arbitrario documentado (no secreto).
KEY_TRITS = [1, 2, 2, 1, 2, 1, 1, 2, 1, 2]


def word(tr):
    return sum(v * 3 ** i for i, v in enumerate(tr))


def trits(w):
    return [(w // 3 ** i) % 3 for i in range(10)]


KEY = word(KEY_TRITS)


def v_for(c):
    """Celda V (trits 0/2) tal que crazy(V, 29524) == c; invariante bajo crazy(29524, V)."""
    tr = trits(c)
    assert set(tr) <= {1, 2}, c
    return word([0 if t == 1 else 2 for t in tr])


def branch(x):
    z = crz(x, ONE)
    a = z
    a = crz(a, C2)
    c3 = crz(a, C3)
    a = c3
    a = crz(C4A, c3)
    a = crz(a, C5)
    return z, a


def mix(z_sigma):
    y1 = crz(A_CONT, z_sigma)
    return crz(y1, KEY)


def reset_to(c, junk):
    t = crz(ONE, junk)        # ROT U deja a=ONE; CRAZY t
    t = crz(t, t)             # CRAZY t (a = t)
    if c == ONE:
        return t
    v = v_for(c)
    assert crz(ONE, v) == v   # CRAZY Vc con a=ONE no altera Vc; a=v
    return crz(v, t)


report = {'constants': {'ONE': ONE, 'C2': C2, 'C3': C3, 'C4A': C4A, 'C5': C5, 'KEY': KEY,
                        'V_C2': v_for(C2), 'V_C5': v_for(C5), 'V_KEY': v_for(KEY),
                        'A_CONT': A_CONT, 'A_HALT': A_HALT}}
assert rot(ONE) == ONE
assert crz(ONE, C4A) == C4A                    # V4 = 59048 invariante; carga a=59048
targets = {}
outputs = []
for x in list(range(256)) + [EOF]:
    z, r = branch(x)
    targets[x] = r
    if x != EOF:
        outputs.append(mix(z) % 256)
assert all(targets[x] == A_CONT for x in range(256)), 'rama: no todos los bytes van a A_CONT'
assert targets[EOF] == A_HALT
# reinicio exhaustivo sobre cualquier palabra basura
for c in (ONE, C2, C5, KEY):
    assert all(reset_to(c, j) == c for j in range(59049)), c
report['branch'] = {'bytes_to': A_CONT, 'eof_to': A_HALT}
report['reset_exhaustive_59049'] = True
report['mix_output_hex'] = bytes(outputs).hex()
report['mix_distinct_outputs'] = len(set(outputs))
report['mix_injective_on_bytes'] = len(set(mix(crz(x, ONE)) for x in range(256))) == 256
print(json.dumps(report, indent=2))
