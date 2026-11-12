#!/usr/bin/env python3
"""Observe code/data accesses of the reference cat after its first IN."""
import hashlib
import importlib.util
import json
import pathlib

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
spec = importlib.util.spec_from_file_location('compose', ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
se = m.SE
image = (ROOT/'vm_malbolge/evidence/unieco_strict_relocation_v1/reference_cat_functional.mb').read_bytes()
N = 59049
memory = list(image) + [0]*(N-len(image))
for i in range(len(image), N):
    memory[i] = se.crazy(memory[i-1], memory[i-2])
a = c = d = pos = 0
data = bytes([0, 255])
output = bytearray()
executed, accessed, written = set(), set(), set()
first = None
ins = []
status = 'MAX_STEPS'
for step in range(1, 20001):
    pc = c
    op = (memory[c] + c) % 94
    if op == 23 and first is None:
        first = {'step': step, 'pc': c, 'd': d, 'a': a}
    if first:
        executed.add(pc)
        if op in (4, 39, 40, 62):
            accessed.add(d)
        if op in (39, 62):
            written.add(d)
    if op == 4:
        c = memory[d]
    elif op == 5:
        output.append(a % 256)
    elif op == 23:
        a = data[pos] if pos < len(data) else 59048
        pos += pos < len(data)
        ins.append({'step': step, 'pc': pc, 'value': a})
    elif op == 39:
        memory[d] = se.rot(memory[d]); a = memory[d]
    elif op == 40:
        d = memory[d]
    elif op == 62:
        memory[d] = se.crazy(a, memory[d]); a = memory[d]
    elif op == 81:
        status = 'HALTED'
        break
    if 33 <= memory[c] <= 126:
        memory[c] = se.encrypt(memory[c])
        if first:
            written.add(c)
    c = (c + 1) % N
    d = (d + 1) % N
report = {'image_sha256': hashlib.sha256(image).hexdigest(), 'input_hex': data.hex(),
          'output_hex': output.hex(), 'status': status, 'steps': step,
          'first_input': first, 'inputs': ins,
          'executed_positions': sorted(executed), 'data_access_positions': sorted(accessed),
          'written_positions': sorted(written),
          'counts': {'executed': len(executed), 'data_access': len(accessed), 'written': len(written)},
          'scope': 'model trace only for input 00ff and EOF; not a general relocation recipe'}
assert status == 'HALTED' and bytes(output) == data and ins[-1]['value'] == 59048
(P/'reference_footprint.results.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if not k.endswith('_positions')},indent=2))
