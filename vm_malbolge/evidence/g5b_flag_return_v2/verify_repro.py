#!/usr/bin/env python3
"""Verify the four-caller positive run, negative control, and G4 image replay."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: verify_repro.py <run01-dir> <run02-dir>')
r1, r2 = map(lambda s: pathlib.Path(s).resolve(), sys.argv[1:])
positive1 = (r1 / 'positive.mb').read_bytes()
positive2 = (r2 / 'positive.mb').read_bytes()
assert positive1 == positive2, 'G4 image mismatch'
positive = json.loads((r1 / 'probe.stdout.raw.json').read_text())
negative = json.loads((r1 / 'control.stdout.raw.json').read_text())
p = positive['run']
n = negative['run']
assert p['call_order'] == ['ll', 'lr', 'rl', 'rr']
assert p['shared_op_address'] == 38058 and p['variable_address'] == 40006
assert p['continuation_visits'] == [15000, 15004, 15008, 15012]
assert p['output_hex'] == '62e66ee6' and p['native_rc'] == 0
assert p['independent_status'] == 'end' and p['local_trace_status'] == 'halt'
assert len(p['shared_calls']) == 4
assert all(x['d'] == 40006 for x in p['shared_calls'])
assert all(s['flags'] == [74, 74, 74] and s['shared_op'] == 74 for s in p['states_at_cont'])
assert p['tails_unchanged']
assert n['observed_return_order'] == [15000, 15012]
assert n['output_hex'] == '62e6' and n['native_rc'] == 0
assert n['negative_control_detected']
assert (r1 / 'positive.mb.native.stdout.raw').read_bytes() == bytes.fromhex('62e66ee6')
assert (r1 / 'negative.mb.native.stdout.raw').read_bytes() == bytes.fromhex('62e6')
assert not (r1 / 'positive.mb.native.stderr.raw').read_bytes()
assert not (r1 / 'negative.mb.native.stderr.raw').read_bytes()
print(json.dumps({
    'g0_loader_ok': True,
    'g1_native_positive': p['output_hex'],
    'g2_independent_positive': p['independent_status'],
    'g3_negative_control': n['output_hex'],
    'g4_reproducible': True,
    'positive_image_sha256': hashlib.sha256(positive1).hexdigest(),
    'control_image_sha256': hashlib.sha256((r1 / 'negative.mb').read_bytes()).hexdigest(),
    'positive_calls': len(p['shared_calls']),
    'negative_calls': len(n['shared_calls']),
}, indent=2))
