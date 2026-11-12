#!/usr/bin/env python3
"""Synthesize three-invoke shared restorer — CLOCK2/CLOCK3 + REARM2 in free space."""
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
forge = pathlib.Path(tempfile.mkdtemp(prefix='shared-restore-three-'))
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
T3, C3, S3 = 57800, 57850, 57750
ROT, MOVD, CRAZY, CLOCK = 58057, 58152, 58268, 58303
# CLOCK2 chosen so crazy(ONE, CLOCK2-1) lands with room for a 17-cell REARM2 sled
# (58397 from two_v1 yields REARM2_M1=58392, which collides with CLOCK2).
CLOCK2, CLOCK3 = 58585, 58679
PCRAZY, STORE = 57610, 57700
# next CRAZY-phase cell after STORE (57700..57703); %94==82 like PCRAZY
PCRAZY2, STORE2 = 57704, 57720
ONE, want = 29524, 40
intermediate = ONE - want
ctrl = crazy_op(intermediate, ONE)
REARM_M1 = se.crazy(ONE, CLOCK - 1)
REARM = REARM_M1 + 1
REARM2_M1 = se.crazy(ONE, CLOCK2 - 1)
REARM2 = REARM2_M1 + 1
assert CLOCK % 94 == CLOCK2 % 94 == CLOCK3 % 94 == 23
assert REARM_M1 == 57564 and REARM2_M1 == 58338 and ctrl == 40
assert PCRAZY % 94 == PCRAZY2 % 94 == 82


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


def plant_pcrazy(values, base, jmp_cell, jmp_val):
    put(values, base, 74)
    for pc in range(base + 1, base + 7):
        put(values, pc, op_at(pc, 68))
    put(values, base + 7, op_at(base + 7, 40))
    put(values, base + 8, op_at(base + 8, 39))
    put(values, base + 9, op_at(base + 9, 68))
    put(values, base + 10, op_at(base + 10, 68))
    put(values, base + 11, op_at(base + 11, 4))
    put(values, jmp_cell, jmp_val)


def plant_rearm(values, rearm, movd_cell, movd_val, jmp_cell, jmp_val):
    put(values, rearm - 1, 81)
    put(values, movd_cell, movd_val)
    put(values, jmp_cell, jmp_val)
    for i in range(17):
        if i < 4 or 5 < i < 16:
            opc = 68
        elif i == 4:
            opc = 40
        elif i == 5:
            opc = 62
        else:
            opc = 4
        put(values, rearm + i, op_at(rearm + i, opc))


def plant_store(values, store, movd_ptr, dest_s):
    put(values, movd_ptr, dest_s - 2)
    put(values, store, op_at(store, 68))
    put(values, store + 1, op_at(store + 1, 68))
    put(values, store + 2, op_at(store + 2, 40))
    put(values, store + 3, op_at(store + 3, 4))


raw = (forge / 'reference/malbolge_org/cat.mal').read_bytes()
template = [v for v in raw if 33 <= v <= 126]
source_len = len(template) + 94 * 500
clean = template + [33] * (source_len - len(template))
reports = {}

for tag in ('positive', 'control'):
    values = {}
    for H in (ROT, MOVD, CRAZY, CLOCK, CLOCK2, CLOCK3):
        put(values, H - 1, 81)
        put(values, H, 117 if H in (CLOCK, CLOCK2, CLOCK3) else 74)
        put(values, H + 1, opchar(H + 1, 'i'))

    # call1 (same as two_v1)
    for i, v in {
        K - 1: ROT - 1, K: ONE, K + 1: ROT - 1, K + 3: MOVD - 1, K + 4: T1 - 4,
        T1 - 3: MOVD - 1, T1 - 1: CRAZY - 1, T1: 70, T1 + 1: CRAZY - 1,
        T1 + 2: PCRAZY - 1, T1 + 3: CLOCK - 1, T1 + 4: T1 + 1,
        T1 + 5: MOVD - 1, T1 + 6: T1 - 4,
        C - 1: ROT - 1, C: 3 * (ctrl if tag == 'positive' else 39),
        C + 1: ROT - 1, C + 3: MOVD - 1, C + 4: T1 - 4,
    }.items():
        put(values, i, v)
    plant_pcrazy(values, PCRAZY, 57110, C - 1)
    plant_rearm(values, REARM, 57108, T1 - 1, 57111, STORE - 1)
    plant_store(values, STORE, 57114, S2)

    # call2 with divert → REARM2 → STORE2 → S3
    c2_word = 120 if tag == 'positive' else 117
    for i, v in {
        C2 - 1: ROT - 1, C2: c2_word, C2 + 1: ROT - 1, C2 + 3: MOVD - 1, C2 + 4: T2 - 4,
        T2 - 3: MOVD - 1, T2 - 1: CRAZY - 1, T2: 70, T2 + 1: CRAZY - 1,
        T2 + 2: PCRAZY2 - 1, T2 + 3: CLOCK2 - 1, T2 + 4: T2 + 1,
        T2 + 5: MOVD - 1, T2 + 6: T2 - 4,
        S2 - 1: ROT - 1, S2: ONE, S2 + 1: ROT - 1, S2 + 3: MOVD - 1, S2 + 4: T2 - 4,
    }.items():
        put(values, i, v)
    plant_pcrazy(values, PCRAZY2, 57310, C2 - 1)
    plant_rearm(values, REARM2, 57308, T2 - 1, 57311, STORE2 - 1)
    plant_store(values, STORE2, 57314, S3)

    # call3: simple island, halt on CLOCK3
    c3_word = 120 if tag == 'positive' else 117
    for i, v in {
        C3 - 1: ROT - 1, C3: c3_word, C3 + 1: ROT - 1, C3 + 3: MOVD - 1, C3 + 4: T3 - 4,
        T3 - 3: MOVD - 1, T3 - 1: CRAZY - 1, T3: 70, T3 + 1: CRAZY - 1,
        T3 + 3: CLOCK3 - 1, T3 + 4: C3 - 2, T3 + 5: MOVD - 1, T3 + 6: T3 - 4,
        S3 - 1: ROT - 1, S3: ONE, S3 + 1: ROT - 1, S3 + 3: MOVD - 1, S3 + 4: T3 - 4,
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
    (P / f'restore3_{tag}.mb').write_bytes(program)
    (P / f'restore3_{tag}_targets.json').write_text(
        json.dumps({str(k): v for k, v in sorted(values.items())}, indent=2) + '\n'
    )
    (P / f'restore3_{tag}_plan.ops').write_text(''.join(ops) + '\n')

z = {
    'T1': T1, 'T2': T2, 'T3': T3, 'want': want,
    'clock': CLOCK, 'clock2': CLOCK2, 'clock3': CLOCK3,
    'rearm': REARM, 'rearm2': REARM2, 'store': STORE, 'store2': STORE2,
    's2': S2, 's3': S3,
    'programs': reports,
    'scope': 'three fixed restores; CLOCK2 relocated for free REARM2; CLOCK3 halts',
}
(P / 'synthesis.results.json').write_text(json.dumps(z, indent=2) + '\n')
print(json.dumps(z, indent=2))
