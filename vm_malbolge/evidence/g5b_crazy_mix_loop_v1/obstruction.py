#!/usr/bin/env python3
"""Obstruccion del bloque lineal en la imagen (intento 1 de G5b-1a).

O1: residuos pc mod 94 con palabra cargable ('o') cuya orbita xlat2 es toda NOP.
O2: para cada residuo de fase de un opcode que lee d (ROT/MOVD/CRAZY), si la
    celda anterior puede ejecutarse de forma persistente sin leer d. Si no,
    el op solo se alcanza aterrizando en X-1 tras un JMP, que lee d = T-1.
Dos fuentes: BolgeForge constants y xlat1/xlat2 del C del vendor.
"""
import ast
import json
import pathlib
import re
import sys

P = pathlib.Path(__file__).resolve().parent
GIT = P.parents[3]
sys.path.insert(0, str(GIT / 'BolgeForge'))
from constants import XLAT1 as BX1, XLAT2 as BX2  # noqa: E402

src = (GIT / 'Malbolge-PureEpoch/vendor/olmstead_original.c').read_text()


def c_table(name):
    body = re.search(r'const char %s\[\] =\s*((?:"(?:[^"\\]|\\.)*"\s*)+);' % name, src).group(1)
    return ''.join(ast.literal_eval(s) for s in re.findall(r'"(?:[^"\\]|\\.)*"', body))


EFFECT_CH = set('ji*p</v')


def analyse(X1, X2, decode):
    succ = lambda w: ord(X2[w - 33])

    def orbit(w):
        s, v = [], w
        while v not in s:
            s.append(v)
            v = succ(v)
        return s

    good = [r for r in range(94)
            if any(decode(X1, w, r) == 'o' and all(decode(X1, x, r) not in EFFECT_CH for x in orbit(w))
                   for w in range(33, 127))]
    phase = {}
    for ch, name in (('*', 'ROT'), ('j', 'MOVD'), ('p', 'CRAZY'), ('/', 'IN'), ('<', 'OUT')):
        rs = [r for r in range(94) for w in (70, 74)
              if decode(X1, w, r) == ch and decode(X1, succ(w), r) not in EFFECT_CH]
        phase[name] = sorted(set(rs))
    pred = {name: {r: ((r - 1) % 94 in good) for r in rs} for name, rs in phase.items()}
    # O3: orbitas de cualquier longitud con un solo activo y palabra inicial cargable
    long_ok = {}
    for ch, name in (('*', 'ROT'), ('j', 'MOVD'), ('p', 'CRAZY')):
        hits = set()
        for r in range(94):
            for w in range(33, 127):
                o = orbit(w)
                act = [decode(X1, x, r) for x in o if decode(X1, x, r) in EFFECT_CH]
                if act == [ch] and decode(X1, w, r) in set('ji*p</vo') and (r - 1) % 94 in good:
                    hits.add((r, len(o)))
        long_ok[name] = sorted(hits)
    return {'persistent_nop_residues': good, 'phase_residues': phase, 'predecessor_persistent_nop': pred,
            'single_active_any_length_with_persistent_predecessor': long_ok}


def dec_vendor(X1, w, r):
    return X1[(w - 33 + r) % 94]


def dec_forge(X1, w, r):
    # BolgeForge usa la misma tabla XLAT1 con indice (w-33+pc)%94
    return X1[(w - 33 + r) % 94]


A = analyse(BX1, BX2, dec_forge)
B = analyse(c_table('xlat1'), c_table('xlat2'), dec_vendor)
report = {'sources_agree': A == B, **A}
d_ops = ('ROT', 'MOVD', 'CRAZY')
report['d_ops_always_landed'] = all(not v for k in d_ops for v in A['predecessor_persistent_nop'][k].values())
assert report['sources_agree']
print(json.dumps(report, indent=2))
