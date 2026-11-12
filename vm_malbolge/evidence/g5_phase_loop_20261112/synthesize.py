#!/usr/bin/env python3
"""Generate a two-phase reusable IN/OUT block, not an EOF-safe program."""
from __future__ import annotations
import json
import os
import pathlib
import shutil
import sys
import tempfile

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
if 'PHASE_OUTPUT_DIR' not in os.environ:
    raise SystemExit('set PHASE_OUTPUT_DIR to a new empty directory')
out = pathlib.Path(os.environ['PHASE_OUTPUT_DIR'])
out.mkdir(parents=True, exist_ok=True)
if any(out.iterdir()):
    raise SystemExit('output directory must be empty')
forge_source = ROOT.parent / 'BolgeForge'
forge = pathlib.Path(tempfile.mkdtemp(prefix='phase-loop-forge-'))
(forge / 'tools').mkdir()
(forge / 'reference/malbolge_org').mkdir(parents=True)
for name in ('constants.py', 'tools/resynthesize.py', 'reference/malbolge_org/cat.mal'):
    shutil.copyfile(forge_source / name, forge / name)
sys.path.insert(0, str(forge))
from constants import XLAT1, XLAT2  # noqa: E402
from tools.resynthesize import synthesize_preamble_ops  # noqa: E402

# All opcodes other than the seven effectful values behave as NOP at runtime.
effects = {4, 5, 23, 39, 40, 62, 81}
def successor(x): return ord(XLAT2[x-33])
def orbit(x):
    seq, value = [], x
    while value not in seq:
        seq.append(value)
        value = successor(value)
    assert value == x
    return seq

def quiet(pc):
    words = [w for w in range(33, 127) if all((x + pc) % 94 not in effects for x in orbit(w))]
    if not words: raise ValueError(f'no persistent NOP at {pc}')
    return min(words, key=lambda w: (len(orbit(w)), w))

def active(pc, op):
    words = [w for w in range(33, 127) if (w+pc)%94 == op and len(orbit(w)) == 2 and (successor(w)+pc)%94 not in effects]
    return words[0] if words else None

start = 58000
while active(start, 40) is None: start += 1
positions = {'movd': start}
for name, opcode in [('in', 23), ('out', 5)]:
    pos = positions[list(positions)[-1]] + 1
    while active(pos, opcode) is None: pos += 1
    positions[name] = pos
end = positions['out'] + 1
length = end - start + 1
S = 57000
first_branch = S + length - 2
second_branch = S + 2 * length - 2
entry_d = second_branch + 1
assert entry_d < start - 1
source_raw = (forge / 'reference/malbolge_org/cat.mal').read_bytes()
template = [x for x in source_raw if 33 <= x <= 126]
source_len = len(template) + 94 * 500
clean = template + [33] * (source_len - len(template))
assert source_len < S
report = {'start': start, 'end': end, 'length': length, 'S': S, 'first_branch': first_branch, 'second_branch': second_branch, 'entry_d': entry_d, 'positions': positions, 'programs': {}}
for tag in ('positive', 'control'):
    values = {start-1: 81, first_branch: start-1, second_branch: start-1, entry_d: S-1}
    for pc in range(start, end): values[pc] = quiet(pc)
    for name, opcode in [('movd',40), ('in',23), ('out',5)]:
        pc = positions[name]
        values[pc] = active(pc, opcode)
    if tag == 'control':
        values[positions['in']] = successor(values[positions['in']])
    values[end] = 33 + ((XLAT1.index('i') - end) % 94)
    ops = synthesize_preamble_ops(clean, values, entry_d-1, 9003, 0, template_clean=template, boot='original')
    if 99 + len(ops) > source_len - 2: raise ValueError('bootstrap exceeds loader image')
    program = bytearray(template[:99])
    program.extend(33 + ((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops, 99))
    while len(program) < source_len-2:
        program.append(33 + ((XLAT1.index('o') - len(program)) % 94))
    program.extend(template[-2:])
    assert all(XLAT1[(w-33+i)%94] in 'ji*p</vo' for i,w in enumerate(program))
    (out / f'{tag}.mb').write_bytes(program)
    (out / f'{tag}.targets.json').write_text(json.dumps(values, sort_keys=True, indent=2)+'\n')
    (out / f'{tag}.ops').write_text(''.join(ops)+'\n')
    report['programs'][tag] = {'cells':len(values), 'plan_length':len(ops)}
(out / 'synthesis.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
