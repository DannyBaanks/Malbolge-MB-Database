#!/usr/bin/env python3
"""G5b-1a: imagen hibrida nativa (codigo en el relleno de la imagen, datos via preambulo).

Uso: MIX_OUTPUT_DIR=<dir-nuevo-vacio> python3 synthesize.py
Genera positive / control_kreset / control_c5 (+ layout y planes).
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile
import time

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
if 'MIX_OUTPUT_DIR' not in os.environ:
    raise SystemExit('set MIX_OUTPUT_DIR to a new, empty output directory')
OUT = pathlib.Path(os.environ['MIX_OUTPUT_DIR'])
OUT.mkdir(parents=True, exist_ok=True)
if any(OUT.iterdir()):
    raise SystemExit(f'output directory is not empty: {OUT}')

source = ROOT.parent / 'BolgeForge'
forge = pathlib.Path(tempfile.mkdtemp(prefix='g5b-mix-'))
(forge / 'tools').mkdir()
(forge / 'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py', 'tools/resynthesize.py', 'reference/malbolge_org/cat.mal']:
    shutil.copyfile(source / name, forge / name)
sys.path.insert(0, str(forge))
from constants import XLAT1, XLAT2  # noqa: E402
from tools.resynthesize import synthesize_preamble_ops  # noqa: E402

spec = importlib.util.spec_from_file_location('alg', P / 'algebra.py')
alg = importlib.util.module_from_spec(spec)
_stdout = sys.stdout
sys.stdout = open(os.devnull, 'w')
spec.loader.exec_module(alg)  # ejecuta sus asserts; silencia su JSON
sys.stdout.close()
sys.stdout = _stdout

N = 59049
EFFECTS = {4, 5, 23, 39, 40, 62, 81}
OPC = {'JMP': 4, 'OUT': 5, 'IN': 23, 'ROT': 39, 'MOVD': 40, 'CRAZY': 62, 'HALT': 81}
VALID = set('ji*p</vo')


def succ(w):
    return ord(XLAT2[w - 33])


def orbit(w):
    seq, v = [], w
    while v not in seq:
        seq.append(v)
        v = succ(v)
    return seq


def loads(pc, w):
    return XLAT1[(w - 33 + pc) % 94] in VALID


def quiet(pc):
    ws = [w for w in range(33, 127)
          if XLAT1[(w - 33 + pc) % 94] == 'o' and all((x + pc) % 94 not in EFFECTS for x in orbit(w))]
    if not ws:
        raise ValueError(f'no loadable persistent NOP at {pc}')
    return min(ws, key=lambda w: (len(orbit(w)), w))


def phase_word(pc, op):
    for w in (74, 70):
        if (w + pc) % 94 == op and (succ(w) + pc) % 94 not in EFFECTS and loads(pc, w):
            return w
    return None


def op_at(pc, op):
    for w in range(33, 127):
        if (w + pc) % 94 == op and loads(pc, w):
            return w
    raise ValueError((pc, op))


# ---- memoria por encima de la imagen ----
raw = (forge / 'reference/malbolge_org/cat.mal').read_bytes()
template = [v for v in raw if 33 <= v <= 126]
K94 = 325
SOURCE_LEN = len(template) + 94 * K94
BLOCK_START = 15000
DATA_BASE, DATA_STEP = 41000, 400
NAMES = ['U', 'Z', 'C2', 'C3', 'V4', 'C5', 'V5', 'K', 'VK', 'PF']
CELL = {n: DATA_BASE + i * DATA_STEP for i, n in enumerate(NAMES)}
HANDOFF = 56000
PASS2_PF_HINT = 50000   # PF se fija en CELL['PF']; la pasada 2 lee desde ahi
INIT = {'U': alg.ONE, 'Z': alg.ONE, 'C2': alg.C2, 'C3': alg.C3, 'V4': alg.C4A,
        'C5': alg.C5, 'V5': alg.v_for(alg.C5), 'K': alg.KEY, 'VK': alg.v_for(alg.KEY)}
A_CONT, A_HALT = alg.A_CONT, alg.A_HALT
assert SOURCE_LEN < min(CELL.values()) and max(CELL.values()) + 300 < A_CONT


def M():
    return ('MOVD', None)


def C(c):
    return ('CRAZY', c)


def R(c):
    return ('ROT', c)


def reset(t, to_const=None, v=None):
    seq = [M(), R('U'), M(), C(t), M(), C(t)]
    if to_const:
        seq += [M(), C(v), M(), C(t)]
    return seq


def program(tag):
    seq = [M(), ('IN', None), C('Z'),
           M(), C('C2'),
           M(), C('C3'),
           M(), R('U'), M(), C('V4'), M(), C('C3'),
           M(), C('C5'),
           M(), ('JMPC', 'C5'),
           M(), C('Z'),
           M(), C('K'),
           ('OUT', None)]
    seq += reset('Z')
    seq += reset('C2', True, 'V4')
    seq += reset('C3')
    seq += reset('C5', True, 'V5')
    kres = reset('K', True, 'VK')
    if tag == 'control_kreset':
        kres = kres[:-2]          # omite MOVD + CRAZY final que fija K
    seq += kres
    seq += [M(), ('JMPF', 'PF')]
    return seq


class Conflict(Exception):
    pass


def build(tag):
    values = {}

    def put(a, v):
        if not 0 <= a < N:
            raise Conflict(f'address out of range {a}')
        if a in values and values[a] != v:
            raise Conflict(f'{a}: {values[a]} vs {v}')
        values[a] = v

    for n, v in INIT.items():
        put(CELL[n], v)
    if tag == 'control_c5':
        values[CELL['C5']] = alg.C2   # rama EOF rota: C5 = 59048 en vez de 58319
    code = {}                          # pc -> (op, word)
    seq = program(tag)
    pc = BLOCK_START
    start = None
    d_at = None                        # funcion: d al ejecutar pc
    i = 0
    pending = None                     # (pc_movd, d_movd) esperando el siguiente d-op
    jmpc_pc = None
    while i < len(seq):
        op, arg = seq[i]
        if op in ('JMPC', 'JMPF'):
            p = pc + 1
            w = op_at(p, OPC['JMP'])
        else:
            p = pc + 1
            while phase_word(p, OPC[op]) is None:
                p += 1
            w = phase_word(p, OPC[op])
        if start is None:
            start = p
            d_ref = (start, HANDOFF + 1)      # d al ejecutar start
        if op == 'MOVD':
            d_m = d_ref[1] + (p - d_ref[0])
            pending = (p, d_m)
            code[p] = (op, w)
            pc = p
            i += 1
            continue
        if op in ('IN', 'OUT'):
            code[p] = (op, w)
            pc = p
            i += 1
            continue
        # d-op: CRAZY/ROT sobre celda, JMPC lee C5, JMPF lee PF
        target = CELL[arg]
        pm, dm = pending
        ptr = target - (p - pm)
        try:
            put(dm, ptr)
        except Conflict:
            # desplazar el MOVD 94 celdas y reintentar desde el
            del code[pm]
            pc = pm  # el bucle buscara el siguiente residuo valido > pm
            i -= 1
            while seq[i][0] != 'MOVD':
                i -= 1
            # quitar instrucciones colocadas entre MOVD y este d-op (IN/OUT)
            for q in [q for q in code if q > pm]:
                del code[q]
            pc = pm + 93
            pending = None
            continue
        code[p] = (op, w)
        d_ref = (p, target)
        pending = None
        pc = p
        if op == 'JMPC':
            jmpc_pc = p
            put(CELL['C5'] + 1, p + 1)                 # leido por el JMP en A_CONT+1
            pc = p + 1                                 # p+1 = almohadilla de aterrizaje
            d_ref = (p + 2, CELL['C5'] + 2)
        if op == 'JMPF':
            jmpf_pc = p
            put(CELL['PF'], start - 1)
        i += 1

    # pasada 2: MOVD/CRAZY/ROT/IN/OUT en fase NOP; solo saltan JMPC y JMPF.
    d2_start = CELL['PF'] + 1
    d_j2 = d2_start + (jmpc_pc - start)
    put(d_j2, jmpc_pc + 1)
    d_f2 = d_j2 + 1 + (jmpf_pc - (jmpc_pc + 2))
    put(d_f2, start - 1)
    first_ptr = values[HANDOFF + 1] if HANDOFF + 1 in values else None
    # handoff: el JMP del preambulo lee HANDOFF; el MOVD de start lee HANDOFF+1
    put(HANDOFF, start - 1)
    # el primer MOVD ya puso su puntero en HANDOFF+1 (d_m de start); pasada 3 lee d_f2+1
    put(d_f2 + 1, values[HANDOFF + 1])
    # aterrizajes de la rama
    put(A_CONT, 81)
    put(A_CONT + 1, op_at(A_CONT + 1, OPC['JMP']))
    put(A_HALT, 81)
    put(A_HALT + 1, op_at(A_HALT + 1, OPC['HALT']))
    return values, code, start, jmpc_pc, jmpf_pc, {'pass2_reads': [d_j2, d_f2, d_f2 + 1]}


reports = {}
images = {}
for tag in ('positive', 'control_kreset', 'control_c5'):
    values, code, start, jmpc, jmpf, extra = build(tag)
    assert SOURCE_LEN < min(values), min(values)
    clean = template + [33] * (SOURCE_LEN - len(template))
    t0 = time.monotonic()
    ops = synthesize_preamble_ops(clean, values, HANDOFF, 9003, 0, template_clean=template, boot='original')
    end_ops = 99 + len(ops)
    if end_ops >= BLOCK_START - 1:
        raise ValueError(f'preamble {end_ops} overlaps block {BLOCK_START}')
    prog = bytearray(template[:99])
    prog.extend(33 + ((XLAT1.index(ch) - i) % 94) for i, ch in enumerate(ops, 99))
    while len(prog) < SOURCE_LEN - 2:
        prog.append(33 + ((XLAT1.index('o') - len(prog)) % 94))
    prog.extend(template[-2:])
    for pc in range(start - 1, jmpf + 1):
        prog[pc] = code[pc][1] if pc in code else quiet(pc)
    assert jmpf < SOURCE_LEN - 2
    assert all(XLAT1[(v - 33 + i) % 94] in VALID for i, v in enumerate(prog)), 'loader'
    (OUT / f'{tag}.mb').write_bytes(prog)
    (OUT / f'{tag}_plan.ops').write_text(''.join(ops) + '\n')
    (OUT / f'{tag}_targets.json').write_text(json.dumps({str(k): v for k, v in sorted(values.items())}, indent=2) + '\n')
    layout = {'start': start, 'jmpc': jmpc, 'jmpf': jmpf,
              'code': {str(k): [v[0], v[1]] for k, v in sorted(code.items())},
              'cells': CELL, 'handoff': HANDOFF, 'a_cont': A_CONT, 'a_halt': A_HALT, **extra}
    (OUT / f'{tag}_layout.json').write_text(json.dumps(layout, indent=2) + '\n')
    reports[tag] = {'targets': len(values), 'plan_length': len(ops), 'preamble_end': end_ops,
                    'block': [start - 1, jmpf], 'block_cells': jmpf - start + 2,
                    'active_cells': len(code), 'image_len': len(prog),
                    'elapsed_seconds': round(time.monotonic() - t0, 3)}
summary = {'source_len': SOURCE_LEN, 'block_start': BLOCK_START, 'cells': CELL, 'programs': reports}
(OUT / 'synthesis.results.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
