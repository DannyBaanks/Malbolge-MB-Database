#!/usr/bin/env python3
"""Verify three-invoke restorer end-to-end in scratch (no host bridge)."""
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

T1, T2, T3 = 57100, 57300, 57800
C, C2, C3 = 57200, 57420, 57850
CLOCK, CLOCK2, CLOCK3 = 58303, 58585, 58679
REARM_M1 = se.crazy(29524, CLOCK - 1)
REARM2_M1 = se.crazy(29524, CLOCK2 - 1)


def run_tag(tag):
    image = (P / f'restore3_{tag}.mb').read_bytes()
    mem = list(image) + [0] * (N - len(image))
    for i in range(len(image), N):
        mem[i] = se.crazy(mem[i - 1], mem[i - 2])
    a = c = d = 0
    writes = {T1: [], T2: [], T3: []}
    for step in range(1, 40001):
        if not 33 <= mem[c] <= 126:
            raise AssertionError(f'nonprint pc={c} step={step}')
        op = (mem[c] + c) % 94
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
                [str(OL), str(P / f'restore3_{tag}.mb')],
                input=b'', capture_output=True, timeout=15,
            )
            return {
                'image_sha256': hashlib.sha256(image).hexdigest(),
                'strict_cells': all((v + i) % 94 in m.VALID for i, v in enumerate(image)),
                'scratch_steps': step,
                'halt_pc': c,
                'final': {
                    'T1': mem[T1], 'T2': mem[T2], 'T3': mem[T3],
                    'patch1': mem[T1 + 3], 'patch2': mem[T2 + 3],
                    'C': mem[C], 'C2': mem[C2], 'C3': mem[C3],
                    'clock': mem[CLOCK], 'clock2': mem[CLOCK2], 'clock3': mem[CLOCK3],
                },
                't1_writes': writes[T1],
                't2_writes': writes[T2],
                't3_writes': writes[T3],
                'native_rc': native.returncode,
                'native_stdout_hex': native.stdout.hex(),
                'native_stderr_hex': native.stderr.hex(),
                'patch_ok': mem[T1 + 3] == REARM_M1 and mem[T2 + 3] == REARM2_M1,
            }
        if 33 <= mem[c] <= 126:
            mem[c] = se.encrypt(mem[c])
        c = (c + 1) % N
        d = (d + 1) % N
    raise AssertionError('budget')


records = {'positive': run_tag('positive'), 'control': run_tag('control')}
assert records['positive']['final']['T1'] == 40
assert records['positive']['final']['T2'] == 40
assert records['positive']['final']['T3'] == 40
assert records['positive']['halt_pc'] == CLOCK3
assert records['control']['final']['T1'] == 39
assert records['control']['final']['T2'] == 39
assert records['control']['final']['T3'] == 39
assert records['positive']['native_rc'] == 0
assert records['control']['native_rc'] == 0
(P / 'verification.results.json').write_text(json.dumps(records, indent=2, sort_keys=True) + '\n')
print(json.dumps(records, indent=2, sort_keys=True))
