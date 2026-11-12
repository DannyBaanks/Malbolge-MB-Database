#!/usr/bin/env python3
"""Scratch: host-rearm CLOCK 58→117, then run call2 island on the same CLOCK."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT.parent / 'BolgeForge'))
from constants import XLAT1

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
T2, C2, S2 = 57300, 57420, 57380
ctrl_clock = se.crazy(117, ONE)
assert ctrl_clock == 29407


def opchar(pc, ch):
    return 33 + ((XLAT1.index(ch) - pc) % 94)


mem = [33] * N
mem[CLOCK] = 58
mem[ROT] = mem[MOVD] = mem[CRAZY] = 74
mem[T2] = 70

# Host-side uniform rearm of CLOCK (proves algebra; native sled comes next).
a = ONE
mem[CLOCK] = se.crazy(a, mem[CLOCK]); a = mem[CLOCK]
mem[CLOCK] = se.crazy(a, mem[CLOCK]); a = mem[CLOCK]
assert mem[CLOCK] == ONE
plant = ctrl_clock
for _ in range(9):
    plant = se.rot(plant)
plant = se.rot(plant); a = plant
assert a == ctrl_clock
mem[CLOCK] = se.crazy(a, mem[CLOCK]); a = mem[CLOCK]
assert mem[CLOCK] == 117
clock_rearmed_to = mem[CLOCK]

# Reset primitives; plant call2 island aimed at the same CLOCK (two_v1 shape).
mem[ROT] = mem[MOVD] = mem[CRAZY] = 74
mem[CLOCK] = 117
for i, v in {
    C2 - 1: ROT - 1, C2: 120, C2 + 1: ROT - 1, C2 + 3: MOVD - 1, C2 + 4: T2 - 4,
    T2 - 3: MOVD - 1, T2 - 1: CRAZY - 1, T2: 70, T2 + 1: CRAZY - 1,
    T2 + 3: CLOCK - 1, T2 + 4: C2 - 2, T2 + 5: MOVD - 1, T2 + 6: T2 - 4,
    S2 - 1: ROT - 1, S2: ONE, S2 + 1: ROT - 1, S2 + 3: MOVD - 1, S2 + 4: T2 - 4,
    CLOCK - 1: 81,
}.items():
    mem[i] = v
for H in (ROT, MOVD, CRAZY, CLOCK):
    mem[H + 1] = opchar(H + 1, 'i')
    mem[H - 1] = 81

a = 0
c = ROT
d = S2
t2_writes = []
halt_pc = None
for step in range(1, 20000):
    if not 33 <= mem[c] <= 126:
        raise SystemExit(f'nonprint pc={c} step={step}')
    op = (mem[c] + c) % 94
    if op == 4:
        c = mem[d]
        if not 33 <= mem[c] <= 126:
            raise SystemExit(f'bad jmp {c} step={step}')
    elif op == 39:
        mem[d] = se.rot(mem[d]); a = mem[d]
    elif op == 40:
        d = mem[d]
    elif op == 62:
        before = mem[d]
        mem[d] = se.crazy(a, mem[d]); a = mem[d]
        if d == T2:
            t2_writes.append({'step': step, 'before': before, 'after': mem[d]})
    elif op == 81:
        halt_pc = c
        break
    if 33 <= mem[c] <= 126:
        mem[c] = se.encrypt(mem[c])
    c = (c + 1) % N
    d = (d + 1) % N
else:
    raise SystemExit('budget')

z = {
    'clock_rearmed_to': clock_rearmed_to,
    'clock_final': mem[CLOCK],
    'T2': mem[T2],
    't2_after': [w['after'] for w in t2_writes],
    'halt_pc': halt_pc,
    'ok': mem[T2] == 40 and halt_pc == CLOCK,
    'note': 'CLOCK rearm still host-side; call2 on same CLOCK is native-shaped scratch',
}
(P / 'scratch_clock_rearm.results.json').write_text(json.dumps(z, indent=2) + '\n')
print(json.dumps(z, indent=2))
assert z['ok']
