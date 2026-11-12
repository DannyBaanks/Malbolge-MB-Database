#!/usr/bin/env python3
"""Verify two v4 iterations + iter-clock HALT (scratch + Olmstead)."""
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

TA, TB, HCLOCK = 58550, 58573, 58376
H1, H2 = 58000, 58100


def run_tag(tag):
    image = (P / f'iter_{tag}.mb').read_bytes()
    mem = list(image) + [0] * (N - len(image))
    for i in range(len(image), N):
        mem[i] = se.crazy(mem[i - 1], mem[i - 2])
    a = c = d = 0
    visits = {TA: [], TB: [], HCLOCK: []}
    writes = {TA: [], TB: []}
    for step in range(1, 20001):
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
            before = mem[d]
            mem[d] = se.crazy(a, mem[d]); a = mem[d]
            if d in writes:
                writes[d].append({'step': step, 'before': before, 'after': mem[d]})
        elif op == 81:
            native = subprocess.run(
                [str(OL), str(P / f'iter_{tag}.mb')],
                input=b'', capture_output=True, timeout=15,
            )
            return {
                'image_sha256': hashlib.sha256(image).hexdigest(),
                'strict_cells': all((v + i) % 94 in m.VALID for i, v in enumerate(image)),
                'scratch_steps': step,
                'halt_pc': c,
                'final': {'TA': mem[TA], 'TB': mem[TB], 'hclock': mem[HCLOCK]},
                'visits': {str(k): v for k, v in visits.items()},
                'writes': {str(k): v for k, v in writes.items()},
                'hclock_visits': len(visits[HCLOCK]),
                'native_rc': native.returncode,
                'native_stdout_hex': native.stdout.hex(),
                'native_stderr_hex': native.stderr.hex(),
            }
        if 33 <= mem[c] <= 126:
            mem[c] = se.encrypt(mem[c])
        c = (c + 1) % N
        d = (d + 1) % N
    raise AssertionError('budget')


records = {'positive': run_tag('positive'), 'control': run_tag('control')}
pos, ctl = records['positive'], records['control']
assert pos['halt_pc'] == HCLOCK
assert pos['native_rc'] == 0
assert pos['hclock_visits'] >= 2
assert len(pos['visits'][str(TA)]) >= 1
assert len(pos['visits'][str(TB)]) >= 1
assert ctl['native_rc'] == 0
# Control must differ on TA revisit path (suppressed CRAZY in H1)
assert pos['visits'][str(TA)] != ctl['visits'][str(TA)] or pos['writes'][str(TA)] != ctl['writes'][str(TA)]
(P / 'verification.results.json').write_text(json.dumps(records, indent=2, sort_keys=True) + '\n')
print(json.dumps({
    'positive': {
        'halt_pc': pos['halt_pc'], 'steps': pos['scratch_steps'],
        'hclock_visits': pos['hclock_visits'], 'rc': pos['native_rc'],
        'TA_visits': len(pos['visits'][str(TA)]), 'TB_visits': len(pos['visits'][str(TB)]),
        'final': pos['final'],
    },
    'control': {
        'halt_pc': ctl['halt_pc'], 'steps': ctl['scratch_steps'],
        'hclock_visits': ctl['hclock_visits'], 'rc': ctl['native_rc'],
        'TA_visits': len(ctl['visits'][str(TA)]),
        'differs': True,
    },
}, indent=2))
