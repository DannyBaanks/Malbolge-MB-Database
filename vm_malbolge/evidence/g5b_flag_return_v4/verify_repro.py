#!/usr/bin/env python3
"""Verify all 24 G5b P4 orders, runner parity, the control, and replay."""
from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: python3 verify_repro.py <run01-dir> <run02-dir>')

r1, r2 = (pathlib.Path(arg).resolve() for arg in sys.argv[1:])
orders = list(itertools.permutations(('ll', 'lr', 'rl', 'rr')))
continuations = [15000, 15004, 15008, 15012]
expected_calls = [12130, 21990, 7534, 21990]
rows = []

for order in orders:
    order_name = '-'.join(order)
    d1, d2 = r1 / order_name, r2 / order_name
    img1 = (d1 / 'positive.mb').read_bytes()
    img2 = (d2 / 'positive.mb').read_bytes()
    assert img1 == img2, f'G4 image mismatch for {order_name}'
    p1 = json.loads((d1 / 'probe.stdout.raw.json').read_text())['run']
    p2 = json.loads((d2 / 'probe.stdout.raw.json').read_text())['run']

    for p in (p1, p2):
        assert p['call_order'] == list(order), (order_name, p['call_order'])
        assert p['shared_op_address'] == 38058 and p['variable_address'] == 40006
        assert p['continuation_visits'] == continuations
        assert p['output_hex'] == '62e66ee6' and p['native_rc'] == 0
        assert p['independent_status'] == 'end' and p['local_trace_status'] == 'halt'
        assert [call['value_after'] for call in p['shared_calls']] == expected_calls
        assert len(p['shared_calls']) == 4
        assert all(call['d'] == 40006 for call in p['shared_calls'])
        assert all(state['flags'] == [74, 74, 74] and state['shared_op'] == 74
                   for state in p['states_at_cont'])
        assert p['tails_unchanged']

    for run_dir, order_dir in ((r1, d1), (r2, d2)):
        assert (order_dir / 'positive.mb.native.stdout.raw').read_bytes() == bytes.fromhex('62e66ee6')
        assert not (order_dir / 'positive.mb.native.stderr.raw').read_bytes()
        assert not (order_dir / 'probe.stderr.raw.txt').read_bytes()

    rows.append({
        'order': list(order),
        'image_sha256': hashlib.sha256(img1).hexdigest(),
        'image_bytes': len(img1),
        'output_hex': p1['output_hex'],
        'local_steps': p1['local_trace_steps'],
        'replay_local_steps': p2['local_trace_steps'],
        'positive_images_identical': True,
    })

control_dir = r1 / 'control'
control = json.loads((control_dir / 'control.stdout.raw.json').read_text())['run']
assert control['call_order'] == ['rr', 'll', 'rl', 'lr']
assert control['fault'] == 'rr caller incorrectly toggles f_root and routes to lr'
assert control['observed_return_order'] == [15012]
assert control['output_hex'] == '62' and control['native_rc'] == 0
assert control['independent_status'] == 'end' and control['local_trace_status'] == 'halt'
assert len(control['shared_calls']) == 1 and control['negative_control_detected']
assert (control_dir / 'negative.mb.native.stdout.raw').read_bytes() == b'\x62'
assert not (control_dir / 'negative.mb.native.stderr.raw').read_bytes()
assert not (control_dir / 'control.stderr.raw.txt').read_bytes()

aggregate1 = json.loads((r1 / 'sweep.stdout.raw.json').read_text())
aggregate2 = json.loads((r2 / 'sweep.stdout.raw.json').read_text())
assert aggregate1['order_count'] == aggregate2['order_count'] == 24

result = {
    'g0_loader_images': 48,
    'g1_native_positive_runs': 48,
    'g2_parity_orders': 24,
    'g3_control_output_hex': control['output_hex'],
    'g4_reproducible_orders': 24,
    'distinct_orders': len({tuple(row['order']) for row in rows}),
    'positive_output_hex': '62e66ee6',
    'positive_calls_per_order': 4,
    'control_calls': len(control['shared_calls']),
    'orders': rows,
}
(r1 / 'g4_reproducibility.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
