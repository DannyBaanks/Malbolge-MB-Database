#!/usr/bin/env python3
"""Three v4 body iterations + pc≡2 iter clock self-loop to HALT."""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import time

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
source = ROOT.parent / 'BolgeForge'
forge = pathlib.Path(tempfile.mkdtemp(prefix='g5-iter3-'))
(forge / 'tools').mkdir()
(forge / 'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py', 'tools/resynthesize.py', 'reference/malbolge_org/cat.mal']:
    shutil.copyfile(source / name, forge / name)
sys.path.insert(0, str(forge))
from tools.resynthesize import synthesize_preamble_ops  # noqa: E402
from constants import XLAT1, crazy_op, rot_op  # noqa: E402

rows = {
    r['pc']: r
    for r in json.loads(
        (ROOT / 'vm_malbolge/evidence/increment_stream_v2/code_rearm_v2.results.json').read_text()
    )['rows']
}

TA, TB, TC = 58550, 58573, 58585
H1, H2, H3 = 58000, 58100, 58200
S = 57020
K1, C1 = 57040, 57010
K2, C2 = 57140, 57110
K3, C3 = 57240, 57210
HCLOCK = 58376
ONE = 29524
body = 'j*jpojpooj*ojpooooi'
assert len(body) == 19 and HCLOCK % 94 == 2
wants = {TA: rows[TA]['target'], TB: rows[TB]['target'], TC: rows[TC]['target']}
for T, w in wants.items():
    assert (T + w) % 94 in (39, 62)

raw = (forge / 'reference/malbolge_org/cat.mal').read_bytes()
template = [v for v in raw if 33 <= v <= 126]
source_len = len(template) + 94 * 500
clean = template + [33] * (source_len - len(template))
reports = {}


def opchar(pc, ch):
    return 33 + ((XLAT1.index(ch) - pc) % 94)


for tag in ('positive', 'control'):
    values = {}

    def put(i, v):
        if i in values and values[i] != v:
            raise ValueError(f'conflict {i}: {values[i]} vs {v}')
        values[i] = v

    put(S - 1, TA - 1)
    put(S, ONE)
    put(S + 1, H1 - 1)
    put(S + 2, K1 - 1)

    islands = (
        (TA, H1, K1, C1, wants[TA]),
        (TB, H2, K2, C2, wants[TB]),
        (TC, H3, K3, C3, wants[TC]),
    )
    for T, H, K, C, w in islands:
        ctrl = crazy_op(w, ONE)
        assert crazy_op(ctrl, ONE) == w
        pre = ctrl
        for _ in range(9):
            pre = rot_op(pre)
        assert rot_op(pre) == ctrl
        for i, v in {
            K: ONE, K + 1: T - 1, C: pre, C + 1: C - 1, C + 2: T - 1,
            T: w, T + 1: opchar(T + 1, 'i'), T + 2: T - 1, T + 3: C - 1,
            T + 5: T - 1, T + 6: 0,
        }.items():
            put(i, v)
        selected = body.replace('j*jpoj', 'j*jooj', 1) if tag == 'control' and T == TA else body
        for i, ch in enumerate(selected):
            put(H + i, opchar(H + i, ch))

    # TA → TB → TC → HCLOCK drain
    put(TB - 1, 81)
    put(TC - 1, 81)
    put(TA + 7, TB - 1)
    put(TA + 8, 0)
    put(TA + 9, H2 - 1)
    put(TA + 10, K2 - 1)
    put(TB + 7, TC - 1)
    put(TB + 8, 0)
    put(TB + 9, H3 - 1)
    put(TB + 10, K3 - 1)
    put(TC + 7, HCLOCK - 1)
    put(HCLOCK - 1, 81)
    put(HCLOCK, 66)
    put(HCLOCK + 1, opchar(HCLOCK + 1, 'i'))
    for off in range(0, 16):
        put(TC + 8 + off, HCLOCK - 1)

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
    (P / f'iter3_{tag}.mb').write_bytes(program)
    (P / f'iter3_{tag}_targets.json').write_text(
        json.dumps({str(k): v for k, v in sorted(values.items())}, indent=2) + '\n'
    )
    (P / f'iter3_{tag}_plan.ops').write_text(''.join(ops) + '\n')

z = {
    'targets': [TA, TB, TC],
    'wants': wants,
    'helpers': [H1, H2, H3],
    'hclock': HCLOCK,
    'programs': reports,
    'scope': 'three v4 body passes then pc≡2 clock HALT; not mutual R/R2',
}
(P / 'synthesis.results.json').write_text(json.dumps(z, indent=2) + '\n')
print(json.dumps(z, indent=2))
