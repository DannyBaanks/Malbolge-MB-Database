#!/usr/bin/env python3
"""Verify G5b P3 positive, crossed-order control, and byte-identical replay."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: python3 verify_repro.py <run01-dir> <run02-dir>')

r1, r2 = (pathlib.Path(arg).resolve() for arg in sys.argv[1:])
positive1 = (r1 / 'positive.mb').read_bytes()
positive2 = (r2 / 'positive.mb').read_bytes()
assert positive1 == positive2, 'G4 image mismatch'

p = json.loads((r1 / 'probe.stdout.raw.json').read_text())['run']
n = json.loads((r1 / 'control.stdout.raw.json').read_text())['run']
p2 = json.loads((r2 / 'probe.stdout.raw.json').read_text())['run']
order = ['rr', 'll', 'rl', 'lr']
continuations = [15000, 15004, 15008, 15012]

assert p['call_order'] == order
assert p['shared_op_address'] == 38058 and p['variable_address'] == 40006
assert p['continuation_visits'] == continuations
assert p['output_hex'] == '62e66ee6' and p['native_rc'] == 0
assert p['independent_status'] == 'end' and p['local_trace_status'] == 'halt'
assert p['local_trace_steps'] == 4014
assert [call['value_after'] for call in p['shared_calls']] == [12130, 21990, 7534, 21990]
assert len(p['shared_calls']) == 4
assert all(call['d'] == 40006 for call in p['shared_calls'])
assert all(state['flags'] == [74, 74, 74] and state['shared_op'] == 74
           for state in p['states_at_cont'])
assert p['tails_unchanged']
assert p2['call_order'] == order and p2['output_hex'] == '62e66ee6'
assert p2['local_trace_steps'] == 4014 and p2['native_rc'] == 0

assert n['call_order'] == order
assert n['observed_return_order'] == [15012]
assert n['output_hex'] == '62' and n['native_rc'] == 0
assert n['independent_status'] == 'end' and n['local_trace_status'] == 'halt'
assert n['local_trace_steps'] == 3944
assert len(n['shared_calls']) == 1 and n['shared_calls'][0]['d'] == 40006
assert n['negative_control_detected'] and n['tails_unchanged']

for run_dir, expected in ((r1, bytes.fromhex('62e66ee6')),
                          (r2, bytes.fromhex('62e66ee6'))):
    assert (run_dir / 'positive.mb.native.stdout.raw').read_bytes() == expected
    assert not (run_dir / 'positive.mb.native.stderr.raw').read_bytes()
assert (r1 / 'negative.mb.native.stdout.raw').read_bytes() == bytes.fromhex('62')
assert not (r1 / 'negative.mb.native.stderr.raw').read_bytes()
assert not (r1 / 'probe.stderr.raw.txt').read_bytes()
assert not (r1 / 'control.stderr.raw.txt').read_bytes()
assert not (r2 / 'probe.stderr.raw.txt').read_bytes()

result = {
    'g0_loader_ok': True,
    'g1_native_positive': p['output_hex'],
    'g2_independent_positive': p['independent_status'],
    'g3_negative_control': n['output_hex'],
    'g4_reproducible': True,
    'positive_image_sha256': hashlib.sha256(positive1).hexdigest(),
    'control_image_sha256': hashlib.sha256((r1 / 'negative.mb').read_bytes()).hexdigest(),
    'positive_calls': len(p['shared_calls']),
    'negative_calls': len(n['shared_calls']),
    'positive_local_steps': p['local_trace_steps'],
    'negative_local_steps': n['local_trace_steps'],
}
print(json.dumps(result, indent=2))
