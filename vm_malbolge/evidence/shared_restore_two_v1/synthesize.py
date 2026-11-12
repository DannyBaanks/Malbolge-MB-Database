#!/usr/bin/env python3
"""Synthesize two-invoke shared restorer — CLOCK2+C2 so STORE is only a JMP to call2."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import time

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
source = ROOT.parent / 'BolgeForge'
forge = pathlib.Path(tempfile.mkdtemp(prefix='shared-restore-two-'))
(forge / 'tools').mkdir()
(forge / 'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py', 'tools/resynthesize.py', 'reference/malbolge_org/cat.mal']:
    shutil.copyfile(source / name, forge / name)
sys.path.insert(0, str(forge))
from tools.resynthesize import synthesize_preamble_ops  # noqa: E402
from constants import XLAT1, crazy_op  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    'compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
se = _mod.SE

K, T1, C, T2 = 57000, 57100, 57200, 57300
C2, S2 = 57420, 57380
ROT, MOVD, CRAZY, CLOCK = 58057, 58152, 58268, 58303
CLOCK2 = 58397  # same pc%94==23 orbit as CLOCK
PCRAZY, STORE = 57610, 57700
ONE, want = 29524, 40
intermediate = ONE - want
ctrl = crazy_op(intermediate, ONE)
REARM_M1 = se.crazy(ONE, CLOCK - 1)
REARM = REARM_M1 + 1
assert CLOCK2 % 94 == 23 and REARM_M1 == 57564 and ctrl == 40
assert PCRAZY % 94 == 82


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


raw = (forge / 'reference/malbolge_org/cat.mal').read_bytes()
template = [v for v in raw if 33 <= v <= 126]
source_len = len(template) + 94 * 500
clean = template + [33] * (source_len - len(template))
reports = {}

for tag in ('positive', 'control'):
    values = {}
    for H in (ROT, MOVD, CRAZY, CLOCK, CLOCK2):
        put(values, H - 1, 81)
        put(values, H, 117 if H in (CLOCK, CLOCK2) else 74)
        put(values, H + 1, opchar(H + 1, 'i'))

    # call1
    for i, v in {
        K - 1: ROT - 1, K: ONE, K + 1: ROT - 1, K + 3: MOVD - 1, K + 4: T1 - 4,
        T1 - 3: MOVD - 1, T1 - 1: CRAZY - 1, T1: 70, T1 + 1: CRAZY - 1,
        T1 + 2: PCRAZY - 1, T1 + 3: CLOCK - 1, T1 + 4: T1 + 1,
        T1 + 5: MOVD - 1, T1 + 6: T1 - 4,
        C - 1: ROT - 1, C: 3 * (ctrl if tag == 'positive' else 39),
        C + 1: ROT - 1, C + 3: MOVD - 1, C + 4: T1 - 4,
    }.items():
        put(values, i, v)

    # PCRAZY patch + exit
    put(values, PCRAZY, 74)
    for pc in range(PCRAZY + 1, PCRAZY + 7):
        put(values, pc, op_at(pc, 68))
    put(values, PCRAZY + 7, op_at(PCRAZY + 7, 40))
    put(values, PCRAZY + 8, op_at(PCRAZY + 8, 39))
    put(values, PCRAZY + 9, op_at(PCRAZY + 9, 68))
    put(values, PCRAZY + 10, op_at(PCRAZY + 10, 68))
    put(values, PCRAZY + 11, op_at(PCRAZY + 11, 4))
    put(values, 57110, C - 1)

    # REARM → STORE
    put(values, REARM_M1, 81)
    put(values, 57108, T1 - 1)
    put(values, 57111, STORE - 1)
    for i in range(17):
        if i < 4 or 5 < i < 16:
            opc = 68
        elif i == 4:
            opc = 40
        elif i == 5:
            opc = 62
        else:
            opc = 4
        put(values, REARM + i, op_at(REARM + i, opc))

    # STORE: entry d=57112; NOPs→57114; MOVD loads S2-2; JMP via S2-1 → ROT@S2 (ONE)
    put(values, 57114, S2 - 2)
    put(values, STORE, op_at(STORE, 68))
    put(values, STORE + 1, op_at(STORE + 1, 68))
    put(values, STORE + 2, op_at(STORE + 2, 40))  # MOVD
    put(values, STORE + 3, op_at(STORE + 3, 4))   # JMP → ROT, d=S2

    # C2 island for call2 (positive 120 / control 117) + T2 + S2
    c2_word = 120 if tag == 'positive' else 117
    for i, v in {
        C2 - 1: ROT - 1, C2: c2_word, C2 + 1: ROT - 1, C2 + 3: MOVD - 1, C2 + 4: T2 - 4,
        T2 - 3: MOVD - 1, T2 - 1: CRAZY - 1, T2: 70, T2 + 1: CRAZY - 1,
        T2 + 3: CLOCK2 - 1, T2 + 4: C2 - 2, T2 + 5: MOVD - 1, T2 + 6: T2 - 4,
        S2 - 1: ROT - 1, S2: ONE, S2 + 1: ROT - 1, S2 + 3: MOVD - 1, S2 + 4: T2 - 4,
    }.items():
        put(values, i, v)

    assert source_len < min(values)
    t0 = time.monotonic()
    ops = synthesize_preamble_ops(
        clean, values, K - 1, 9003, 0, template_clean=template, boot='original'
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
    (P / f'restore2_{tag}.mb').write_bytes(program)
    (P / f'restore2_{tag}_targets.json').write_text(
        json.dumps({str(k): v for k, v in sorted(values.items())}, indent=2) + '\n'
    )
    (P / f'restore2_{tag}_plan.ops').write_text(''.join(ops) + '\n')

z = {
    'T1': T1, 'T2': T2, 'C2': C2, 'want': want,
    'clock': CLOCK, 'clock2': CLOCK2,
    'rearm': REARM, 'store': STORE, 's2': S2,
    'programs': reports,
    'scope': 'two fixed restores; CLOCK2+C2 avoid STORE rearm; STORE is JMP to call2',
}
(P / 'synthesis.results.json').write_text(json.dumps(z, indent=2) + '\n')
print(json.dumps(z, indent=2))
