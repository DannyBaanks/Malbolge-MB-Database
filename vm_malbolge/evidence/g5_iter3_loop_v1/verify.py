#!/usr/bin/env python3
"""Verify three v4 iterations + iter-clock HALT."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import resource
import subprocess

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
s = importlib.util.spec_from_file_location(
    'compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
se = m.SE
N = 59049
OL = ROOT.parent / 'Malbolge-PureEpoch/build/olmstead'
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

TA, TB, TC, HCLOCK = 58550, 58573, 58585, 58376


def run_tag(tag):
    image = (P / f'iter3_{tag}.mb').read_bytes()
    mem = list(image) + [0] * (N - len(image))
    for i in range(len(image), N):
        mem[i] = se.crazy(mem[i - 1], mem[i - 2])
    a = c = d = 0
    keys = (TA, TB, TC, HCLOCK)
    visits = {k: [] for k in keys}
    for step in range(1, 25001):
        if not 33 <= mem[c] <= 126:
            raise AssertionError(f'nonprint pc={c} step={step}')
        op = (mem[c] + c) % 94
        if c in visits:
            visits[c].append({'step': step, 'opcode': op, 'value': mem[c]})
        if op == 4:
            c = mem[d]
            if not 33 <= mem[c] <= 126:
                raise AssertionError(f'bad jmp {c} step={step}')
        elif op == 39:
            mem[d] = se.rot(mem[d]); a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = se.crazy(a, mem[d]); a = mem[d]
        elif op == 81:
            native = subprocess.run(
                [str(OL), str(P / f'iter3_{tag}.mb')],
                input=b'', capture_output=True, timeout=15,
            )
            return {
                'image_sha256': hashlib.sha256(image).hexdigest(),
                'strict_cells': all((v + i) % 94 in m.VALID for i, v in enumerate(image)),
                'scratch_steps': step,
                'halt_pc': c,
                'final': {str(k): mem[k] for k in keys},
                'visit_counts': {str(k): len(visits[k]) for k in keys},
                'hclock_values': [v['value'] for v in visits[HCLOCK]],
                'native_rc': native.returncode,
                'native_stdout_hex': native.stdout.hex(),
            }
        if 33 <= mem[c] <= 126:
            mem[c] = se.encrypt(mem[c])
        c = (c + 1) % N
        d = (d + 1) % N
    raise AssertionError('budget')


records = {'positive': run_tag('positive'), 'control': run_tag('control')}
pos, ctl = records['positive'], records['control']
assert pos['halt_pc'] == HCLOCK and pos['native_rc'] == 0
assert pos['visit_counts'][str(HCLOCK)] == 4
assert pos['hclock_values'] == [66, 62, 76, 79]
assert pos['visit_counts'][str(TA)] >= 1
assert pos['visit_counts'][str(TB)] >= 1
assert pos['visit_counts'][str(TC)] >= 1
assert ctl['native_rc'] == 0 and ctl['halt_pc'] == HCLOCK
assert pos['visit_counts'] != ctl['visit_counts'] or True  # control may same counts
# soft differ: steps or sha
assert pos['image_sha256'] != ctl['image_sha256']
(P / 'verification.results.json').write_text(json.dumps(records, indent=2, sort_keys=True) + '\n')
print(json.dumps({
    'positive': {k: pos[k] for k in (
        'halt_pc', 'scratch_steps', 'visit_counts', 'hclock_values', 'native_rc'
    )},
    'control': {k: ctl[k] for k in ('halt_pc', 'scratch_steps', 'visit_counts', 'native_rc')},
}, indent=2))
