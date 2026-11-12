#!/usr/bin/env python3
"""Check saved REA evidence against the preregistered finite observations."""
import json
from pathlib import Path
P = Path(__file__).resolve().parent

def load(name):
    return json.loads((P / name).read_text())

for name in ('python', 'bf'):
    n = load(name + '.redacted.json')['structuredContent']['normalized_result']
    assert n['exit']['code'] == 0
    assert any('input=41424344 output=42434445 status=HALTED' in frame['data'] for frame in n['frames'])
for name, expected in [('malbolge', 'BCDE'), ('control', 'BC\x0eE')]:
    n = load(name + '.redacted.json')['structuredContent']['normalized_result']
    assert n['run']['status'] == 'HALTED' and n['output_text'] == expected and n['run']['events_truncated']
for name, expected in [('revisit_0.extract.json', [62, 62]), ('revisit_1.extract.json', [62, 21])]:
    n = load(name)
    assert n['run']['status'] == 'HALTED' and not n['run']['events_truncated']
    assert [e['opcode'] for e in n['visits']] == expected
native = load('native_comparison.stdout.raw.txt')
assert len(native['cases']) == 4 and native['control']['stdout_hex'] == '42430e45'
print('saved REA and native evidence consistent; finite inputs only')
