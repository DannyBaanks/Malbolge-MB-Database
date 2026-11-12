#!/usr/bin/env python3
"""1-cell R/R2 unrolled: R → rest R2 → R2 → rest R → R → HCLOCK."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile
import time

P = pathlib.Path(__file__).resolve().parent
if 'RR_OUTPUT_DIR' not in os.environ:
    raise SystemExit('set RR_OUTPUT_DIR to a new, empty output directory')
OUT = pathlib.Path(os.environ['RR_OUTPUT_DIR'])
OUT.mkdir(parents=True, exist_ok=True)
if any(OUT.iterdir()):
    raise SystemExit(f'output directory is not empty: {OUT}')
ROOT = P.parents[2]
source = ROOT.parent / 'BolgeForge'
forge = pathlib.Path(tempfile.mkdtemp(prefix='g5-rr-min-'))
(forge / 'tools').mkdir()
(forge / 'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py', 'tools/resynthesize.py', 'reference/malbolge_org/cat.mal']:
    shutil.copyfile(source / name, forge / name)
sys.path.insert(0, str(forge))
from tools.resynthesize import synthesize_preamble_ops  # noqa: E402
from constants import XLAT1, crazy_op, rot_op  # noqa: E402

R, R2, HCLOCK = 57400, 57450, 58376
S, SA, SB = 57001, 57600, 57720
BA, BB = S + 1, R2 + 6  # entry data pointers, separate from code
ONE = 29524
assert HCLOCK % 94 == 2


def opchar(pc, ch):
    return 33 + ((XLAT1.index(ch) - pc) % 94)


def op_at(pc, opcode):
    for v in range(33, 127):
        if (v + pc) % 94 == opcode:
            return v
    raise ValueError(pc, opcode)


def put(values, i, v):
    if i in values and values[i] != v:
        raise ValueError(f'conflict {i}: {values[i]} vs {v}')
    values[i] = v


want_r = opchar(R, 'i')
want_r2 = opchar(R2, 'i')


def plant_sled(values, base, bank, target, want, next_m1):
    """Code at base; data at bank (disjoint). Clobbers target+1..+4."""
    ctrl = crazy_op(want, ONE)
    pre = ctrl
    for _ in range(9):
        pre = rot_op(pre)
    assert rot_op(pre) == ctrl
    put(values, base - 1, 81)
    put(values, bank + 0, ONE)
    put(values, bank + 1, target - 1)
    put(values, bank + 2, target - 1)
    put(values, bank + 3, pre)
    put(values, bank + 4, target - 1)
    # Entry has c=base and d=bank; the two streams are independent.
    gap = 0
    put(values, base + gap + 0, op_at(base + gap + 0, 39))  # ROT ONE
    put(values, base + gap + 1, op_at(base + gap + 1, 40))  # MOVD target
    put(values, base + gap + 2, op_at(base + gap + 2, 62))  # CRAZY1
    put(values, target + 1, base + gap + 9)
    put(values, base + gap + 3, op_at(base + gap + 3, 4))
    put(values, base + gap + 9, 81)
    put(values, target + 2, target - 1)
    put(values, base + gap + 10, op_at(base + gap + 10, 40))
    put(values, base + gap + 11, op_at(base + gap + 11, 62))  # CRAZY2
    put(values, base + gap + 12, op_at(base + gap + 12, 68))
    put(values, base + gap + 13, op_at(base + gap + 13, 68))
    put(values, target + 3, bank + 2)
    put(values, base + gap + 14, op_at(base + gap + 14, 40))
    put(values, base + gap + 15, op_at(base + gap + 15, 39))  # ROT ctrl
    put(values, base + gap + 16, op_at(base + gap + 16, 40))
    put(values, base + gap + 17, op_at(base + gap + 17, 62))  # CRAZY want
    put(values, base + gap + 18, op_at(base + gap + 18, 68))
    put(values, base + gap + 19, op_at(base + gap + 19, 68))
    put(values, base + gap + 20, op_at(base + gap + 20, 68))
    put(values, target + 4, next_m1)
    put(values, base + gap + 21, op_at(base + gap + 21, 4))


raw = (forge / 'reference/malbolge_org/cat.mal').read_bytes()
template = [v for v in raw if 33 <= v <= 126]
source_len = len(template) + 94 * 500
clean = template + [33] * (source_len - len(template))
reports = {}

for tag in ('positive', 'control'):
    values = {}
    put(values, R - 1, 81)
    put(values, R2 - 1, 81)
    put(values, R, want_r)
    put(values, R2, want_r2)

    # Boot → R with d=S so R JMPs to SA-1
    put(values, S - 1, R - 1)
    put(values, S, SA - 1)

    # R → SA (rest R2) → R2 → SB (rest R) → R → HCLOCK
    plant_sled(values, SA, BA, R2, want_r2, R2 - 1)
    put(values, R2 + 5, SB - 1)  # sled exits with d=R2+5

    plant_sled(values, SB, BB, R, want_r, R - 1)
    if tag == 'control':
        values[SB + 17] = op_at(SB + 17, 68)  # omit final rearming CRAZY
    put(values, R + 5, HCLOCK - 1)

    put(values, HCLOCK - 1, 81)
    put(values, HCLOCK, op_at(HCLOCK, 81))
    put(values, HCLOCK + 1, opchar(HCLOCK + 1, 'i'))

    assert source_len < min(values)
    t0 = time.monotonic()
    ops = synthesize_preamble_ops(
        clean, values, S - 1, 9003, 0, template_clean=template, boot='original'
    )
    end = 99 + len(ops)
    reports[tag] = {
        'target_cells': len(values),
        'plan_length': len(ops),
        'plan_end': end,
        'fits': end <= source_len - 2,
        'elapsed_seconds': round(time.monotonic() - t0, 3),
    }
    if end > source_len - 2:
        raise ValueError('plan does not fit')
    program = bytearray(template[:99])
    program.extend(33 + ((XLAT1.index(ch) - i) % 94) for i, ch in enumerate(ops, 99))
    while len(program) < source_len - 2:
        program.append(33 + ((XLAT1.index('o') - len(program)) % 94))
    program.extend(template[-2:])
    assert all(XLAT1[(v - 33 + i) % 94] in 'ji*p</vo' for i, v in enumerate(program))
    (OUT / f'rr_{tag}.mb').write_bytes(program)
    (OUT / f'rr_{tag}_targets.json').write_text(
        json.dumps({str(k): v for k, v in sorted(values.items())}, indent=2) + '\n'
    )
    (OUT / f'rr_{tag}_plan.ops').write_text(''.join(ops) + '\n')

z = {
    'R': R, 'R2': R2, 'want_r': want_r, 'want_r2': want_r2,
    'SA': SA, 'SB': SB, 'hclock': HCLOCK, 'programs': reports,
}
(OUT / 'synthesis.results.json').write_text(json.dumps(z, indent=2) + '\n')
print(json.dumps(z, indent=2))
