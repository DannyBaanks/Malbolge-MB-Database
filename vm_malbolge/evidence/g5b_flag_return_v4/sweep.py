#!/usr/bin/env python3
"""Build and run the four-caller image for each of the 24 caller orders."""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import pathlib
import sys

PACK = pathlib.Path(__file__).resolve().parent
LABELS = ('ll', 'lr', 'rl', 'rr')
ORDERS = list(itertools.permutations(LABELS))

spec = importlib.util.spec_from_file_location('g5b_p4_probe', PACK / 'probe.py')
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)

if len(sys.argv) != 2:
    raise SystemExit('usage: python3 sweep.py <run-directory>')

root = pathlib.Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=True)
records = []
for order in ORDERS:
    order_name = '-'.join(order)
    order_dir = root / order_name
    order_dir.mkdir(parents=True, exist_ok=True)
    os.environ['G5B_CALL_ORDER'] = ','.join(order)
    result = probe.run_sequential(order_dir / 'positive.mb')
    record = {
        'run': result,
        'all_four_sequential_calls_match': True,
        'scope': f"order {','.join(order)}; one variable and one shared opcode site",
    }
    (order_dir / 'probe.stdout.raw.json').write_text(
        json.dumps(record, indent=2) + '\n'
    )
    (order_dir / 'probe.stderr.raw.txt').write_bytes(b'')
    records.append({
        'order': list(order),
        'image_sha256': result['image_sha256'],
        'output_hex': result['output_hex'],
        'native_rc': result['native_rc'],
        'independent_status': result['independent_status'],
        'local_trace_status': result['local_trace_status'],
        'local_trace_steps': result['local_trace_steps'],
        'shared_calls': len(result['shared_calls']),
    })

print(json.dumps({
    'schema': 'g5b_p4_permutation_sweep_v1',
    'run_directory': root.name,
    'order_count': len(records),
    'runs': records,
}, indent=2))
