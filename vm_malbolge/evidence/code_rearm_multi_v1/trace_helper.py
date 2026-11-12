#!/usr/bin/env python3
"""Print every write of the v4 positive rearm window with its operands.

Purpose: identify the exact CRAZY/ROT operands the helper uses, so the generic
restart chain can be characterised. Host-side scratch model only (no REA, no
Olmstead); it mirrors verify_v4.py's tracer and stops after the halt.
"""
import importlib.util, json, pathlib

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
s = importlib.util.spec_from_file_location('compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
se = m.SE; N = 59049

image = (P / 'multi_v4_positive.mb').read_bytes()
mem = list(image) + [0] * (N - len(image))
for i in range(len(image), N):
    mem[i] = se.crazy(mem[i - 1], mem[i - 2])
a = c = d = 0
events = []
for step in range(1, 8001):
    pc = c
    op = (mem[c] + c) % 94
    if op == 4:
        c = mem[d]
    elif op == 39:
        old = mem[d]; mem[d] = se.rot(old); a = mem[d]
    elif op == 40:
        d = mem[d]
    elif op == 62:
        old = mem[d]
        new = se.crazy(a, old)
        if step >= 7080:
            events.append({'step': step, 'op': 'CRAZY', 'at': pc, 'd': d, 'a_before': a, 'cell': old, 'after': new})
        mem[d] = new; a = mem[d]
    elif op == 81:
        break
    if 33 <= mem[c] <= 126:
        mem[c] = se.encrypt(mem[c])
    if op == 39 and step >= 7080:
        events.append({'step': step, 'op': 'ROT', 'at': pc, 'd': d, 'a_before': a})
    c = (c + 1) % N; d = (d + 1) % N
out = P / 'helper_operands.results.json'
out.write_text(json.dumps(events, indent=2) + '\n')
for e in events:
    print(e)
