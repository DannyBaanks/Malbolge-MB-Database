#!/usr/bin/env python3
"""L2: orbitas xlat2 y residuos de rearme de fase, desde dos fuentes.

Fuente A: tablas del probe del repo (SE.encrypt, convencion op=(v+pc)%94).
Fuente B: xlat1/xlat2 leidos del C del vendor Olmstead (xlat1[(v-33+pc)%94]).
Tambien mide propiedades de crazy relevantes para el cuerpo "XOR ternario".
"""
import ast
import hashlib
import importlib.util
import json
import pathlib
import re

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
VENDOR = ROOT.parent / 'Malbolge-PureEpoch/vendor/olmstead_original.c'
spec = importlib.util.spec_from_file_location('compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
se = m.SE

ACT_NUM = {4: 'JMP', 5: 'OUT', 23: 'IN', 39: 'ROT', 40: 'MOVD', 62: 'CRAZY', 81: 'HALT'}
ACT_CHR = {'i': 'JMP', '<': 'OUT', '/': 'IN', '*': 'ROT', 'j': 'MOVD', 'p': 'CRAZY', 'v': 'HALT'}


def c_table(name, text):
    body = re.search(r'const char %s\[\] =\s*((?:"(?:[^"\\]|\\.)*"\s*)+);' % name, text).group(1)
    return ''.join(ast.literal_eval(s) for s in re.findall(r'"(?:[^"\\]|\\.)*"', body))


src = VENDOR.read_text()
X1, X2 = c_table('xlat1', src), c_table('xlat2', src)
assert len(X1) == len(X2) == 94

source_a = {
    'enc': lambda v: se.encrypt(v),
    'op': lambda v, pc: ACT_NUM.get((v + pc) % 94),
}
source_b = {
    'enc': lambda v: ord(X2[v - 33]),
    'op': lambda v, pc: ACT_CHR.get(X1[(v - 33 + pc) % 94]),
}


def analyse(s):
    seen, orbits = set(), []
    for v in range(33, 127):
        if v in seen:
            continue
        o, x = [v], s['enc'](v)
        while x != v:
            o.append(x)
            x = s['enc'](x)
        seen |= set(o)
        orbits.append(o)
    period2 = [sorted(o) for o in orbits if len(o) == 2]
    phase = {}
    for o in orbits:
        if len(o) != 2:
            continue
        for r in range(94):
            ops = [s['op'](v, r) for v in o]
            act = [(v, x) for v, x in zip(o, ops) if x]
            if len(act) == 1:
                v, x = act[0]
                phase.setdefault(x, []).append({'residue': r, 'active_word': v})
    single = {}
    for o in orbits:
        for r in range(94):
            act = [x for x in (s['op'](v, r) for v in o) if x]
            if len(act) == 1 and act[0] != 'HALT':
                single.setdefault(act[0], {}).setdefault(r, len(o))
                single[act[0]][r] = min(single[act[0]][r], len(o))
    return {
        'orbit_lengths': sorted(len(o) for o in orbits),
        'period2_orbits': period2,
        'phase_residues': {k: sorted(v, key=lambda e: e['residue']) for k, v in sorted(phase.items())},
        'single_active_residue_count': {k: len(v) for k, v in sorted(single.items())},
    }


A, B = analyse(source_a), analyse(source_b)
agree = A == B

# Control G3b: xlat2 con dos entradas intercambiadas debe romper el acuerdo.
X2m = list(X2)
X2m[0], X2m[1] = X2m[1], X2m[0]
mutant = analyse({'enc': lambda v: ord(X2m[v - 33]), 'op': source_b['op']})

# Propiedades de crazy para el cuerpo propuesto (no es XOR).
crz = se.crazy
TR = [[crz(a, d) for d in range(3)] for a in range(3)]   # tabla por trit (palabras 0..2 = trit bajo)
key_bijective = [a for a in range(3) if len({TR[a][d] % 3 for d in range(3)}) == 3]
data_bijective = [d for d in range(3) if len({TR[a][d] % 3 for a in range(3)}) == 3]
involution_keys = [k for k in range(256) if all(crz(k, crz(k, x)) == x for x in range(256))]
byte_injective_keys = [k for k in range(59049) if k % 3 ** 6 == 0 and len({crz(k, x) for x in range(256)}) == 256][:5]

report = {
    'vendor_sha256': hashlib.sha256(VENDOR.read_bytes()).hexdigest(),
    'sources_agree': agree,
    'table': A,
    'control_swapped_xlat2_detected': mutant != B,
    'crazy': {
        'trit_table_low_trit': [[x % 3 for x in row] for row in TR],
        'keys_trit_bijective_on_data': key_bijective,
        'data_trits_bijective_on_key': data_bijective,
        'byte_keys_where_crazy_k_is_involution_on_0_255': involution_keys,
        'note': 'crazy no es XOR: no existe clave que lo haga involucion; ver cuerpo G5b-1',
    },
}
assert agree
assert A['period2_orbits'] == [[70, 74]]
assert all(len(A['phase_residues'][op]) == 2 for op in ('JMP', 'OUT', 'IN', 'ROT', 'MOVD', 'CRAZY'))
assert report['control_swapped_xlat2_detected']
print(json.dumps(report, indent=2))
