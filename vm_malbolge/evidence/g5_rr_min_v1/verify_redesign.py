#!/usr/bin/env python3
"""Trace the isolated R/R2 images and run the reference interpreter."""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
OUT = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
se = m.SE
N = 59049
R, R2, CLOCK = 57400, 57450, 58376
records = {}
for tag in ('positive', 'control'):
    path = OUT / f'rr_{tag}.mb'
    image = path.read_bytes()
    mem = list(image) + [0] * (N - len(image))
    for i in range(len(image), N):
        mem[i] = se.crazy(mem[i - 1], mem[i - 2])
    a = c = d = 0
    visits, writes, io = [], [], []
    outcome = 'budget'
    for step in range(1, 12001):
        if not 33 <= mem[c] <= 126:
            outcome = 'nonprintable_pc'
            visits.append({'step': step, 'pc': c, 'word': mem[c], 'opcode': None})
            break
        op = (mem[c] + c) % 94
        if c in (R, R2, CLOCK):
            visits.append({'step': step, 'pc': c, 'word': mem[c], 'opcode': op})
        if op == 4:
            c = mem[d]
            if not 33 <= mem[c] <= 126:
                outcome = 'nonprintable_jump'
                break
        elif op in (5, 23):
            io.append({'step': step, 'opcode': op})
            if op == 23:
                a = N - 1
        elif op in (39, 62):
            old = mem[d]
            mem[d] = se.rot(old) if op == 39 else se.crazy(a, old)
            a = mem[d]
            if d in (R, R2):
                writes.append({'step': step, 'pc': c, 'address': d, 'before': old, 'after': mem[d]})
        elif op == 40:
            d = mem[d]
        elif op == 81:
            outcome = 'halt'
            break
        if 33 <= mem[c] <= 126:
            old = mem[c]
            mem[c] = se.encrypt(old)
            if c in (R, R2):
                writes.append({'step': step, 'pc': c, 'address': c, 'before': old, 'after': mem[c], 'kind': 'encryption'})
        c = (c + 1) % N
        d = (d + 1) % N
    try:
        native = subprocess.run([str(ROOT.parent / 'Malbolge-PureEpoch/build/olmstead'), str(path)], input=b'', capture_output=True, timeout=10)
        native_result = {'rc': native.returncode, 'stdout_hex': native.stdout.hex(), 'stderr_hex': native.stderr.hex()}
    except subprocess.TimeoutExpired:
        native_result = {'timeout': True}
    records[tag] = {'sha256': hashlib.sha256(image).hexdigest(), 'strict': all((v+i)%94 in m.VALID for i,v in enumerate(image)), 'outcome': outcome, 'steps': step, 'visits': visits, 'writes': writes, 'io': io, 'olmstead': native_result}
assert records['positive']['outcome'] == 'halt'
assert records['positive']['olmstead']['rc'] == 0
assert [v['opcode'] for v in records['positive']['visits'] if v['pc'] == R] == [4, 4]
assert records['control']['outcome'] == 'nonprintable_pc'
assert records['control']['visits'][-1]['pc'] == R
assert all(records[t]['strict'] and not records[t]['io'] for t in records)
(OUT / 'verification.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps(records, indent=2))
