#!/usr/bin/env python3
"""Develop native CLOCK rearm sled in scratch before full-image synthesis."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT.parent / 'BolgeForge'))
from constants import XLAT1, rot_op

s = importlib.util.spec_from_file_location(
    'compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
se = m.SE
N = 59049
ONE = 29524
CLOCK = 58303
ROT, MOVD, CRAZY = 58057, 58152, 58268
CA, CB = 57798, 57986
SETUP, KCLK, CCLK = 57880, 57940, 57950
S2, T2, C2 = 57380, 57300, 57420
ctrl_clock = se.crazy(117, ONE)
pre_clock = ctrl_clock
for _ in range(9):
    pre_clock = rot_op(pre_clock)
assert rot_op(pre_clock) == ctrl_clock


def opchar(pc, ch):
    return 33 + ((XLAT1.index(ch) - pc) % 94)


def op_at(pc, opcode):
    for v in range(33, 127):
        if (v + pc) % 94 == opcode:
            return v
    raise ValueError(pc, opcode)


def run(mem, c, d, a=0, budget=20000):
    clock_writes = []
    t2_writes = []
    for step in range(1, budget + 1):
        if not 33 <= mem[c] <= 126:
            raise AssertionError(f'nonprint pc={c} step={step}')
        op = (mem[c] + c) % 94
        if op == 4:
            c = mem[d]
            if not 33 <= mem[c] <= 126:
                raise AssertionError(f'bad jmp {c} step={step} d={d}')
        elif op == 39:
            mem[d] = se.rot(mem[d]); a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            before = mem[d]
            mem[d] = se.crazy(a, mem[d]); a = mem[d]
            if d == CLOCK:
                clock_writes.append({'step': step, 'before': before, 'after': mem[d], 'a_before': a})
            if d == T2:
                t2_writes.append({'step': step, 'before': before, 'after': mem[d]})
        elif op == 81:
            return {
                'halt_pc': c, 'steps': step, 'a': a, 'd': d,
                'clock': mem[CLOCK], 'T2': mem[T2],
                'clock_writes': clock_writes, 't2_writes': t2_writes,
            }
        if 33 <= mem[c] <= 126:
            mem[c] = se.encrypt(mem[c])
        c = (c + 1) % N
        d = (d + 1) % N
    raise AssertionError('budget')


mem = [33] * N
# Post-call1-ish
mem[CLOCK] = 58
mem[ROT] = mem[MOVD] = mem[CRAZY] = 74
mem[CA] = mem[CB] = 74
mem[KCLK] = ONE
mem[CCLK] = pre_clock
mem[T2] = 70
mem[C2] = 120
mem[S2] = ONE

for H in (ROT, MOVD, CRAZY, CLOCK, CA, CB):
    mem[H - 1] = 81
    mem[H + 1] = opchar(H + 1, 'i')

# Pointer bank for SETUP d-walk (entry d=SETUP=57880 → +10 → 57890)
mem[57890] = CLOCK - 1
mem[57891] = CA - 1
# After CA: fall to CA+1 JMP. We need d at a cell holding next. Trace-driven fix below.

# call2 island (same CLOCK)
for i, v in {
    C2 - 1: ROT - 1, C2: 120, C2 + 1: ROT - 1, C2 + 3: MOVD - 1, C2 + 4: T2 - 4,
    T2 - 3: MOVD - 1, T2 - 1: CRAZY - 1, T2: 70, T2 + 1: CRAZY - 1,
    T2 + 3: CLOCK - 1, T2 + 4: C2 - 2, T2 + 5: MOVD - 1, T2 + 6: T2 - 4,
    S2 - 1: ROT - 1, S2: ONE, S2 + 1: ROT - 1, S2 + 3: MOVD - 1, S2 + 4: T2 - 4,
}.items():
    mem[i] = v

# --- Build SETUP as a micro-program of JMP-linked blocks ---
# Block0: walk to 57890, MOVD, JMP CA
for i in range(10):
    mem[SETUP + i] = op_at(SETUP + i, 68)
mem[SETUP + 10] = op_at(SETUP + 10, 40)
mem[SETUP + 11] = op_at(SETUP + 11, 4)

# Instrument: run only SETUP→CA first CRAZY and dump state
mem[CA + 1] = op_at(CA + 1, 81)  # halt after first crazy for probe
try:
    probe = run(mem, SETUP, SETUP, a=40, budget=5000)
except AssertionError as e:
    probe = {'error': str(e), 'clock': mem[CLOCK]}
(P / 'scratch_aux_probe1.json').write_text(json.dumps(probe, indent=2) + '\n')
print('probe1', json.dumps(probe, indent=2)[:800])
