#!/usr/bin/env python3
"""Barrido de las 120 permutaciones de cinco llamadores (G5b P5c).

Generaliza el barrido de P4 (24 órdenes de cuatro llamadores) al caso de cinco
hojas de P5. Cada orden genera su propia imagen y se verifica con el mismo
probe de P5: cargador Classic, Olmstead nativo, clasesbolge y trazador local.

Uso: python3 sweep.py <directorio-de-salida> [--limit N]
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import pathlib
import sys
import time

PACK = pathlib.Path(__file__).resolve().parent
LABELS = ('lll', 'llr', 'lr', 'rl', 'rr')
ORDERS = list(itertools.permutations(LABELS))

spec = importlib.util.spec_from_file_location('g5b_p5_probe', PACK.parent / 'g5b_flag_return_v5' / 'probe.py')
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)

if len(sys.argv) < 2:
    raise SystemExit('uso: python3 sweep.py <directorio-de-salida> [--limit N]')

root = pathlib.Path(sys.argv[1]).resolve()
limit = None
if '--limit' in sys.argv:
    limit = int(sys.argv[sys.argv.index('--limit') + 1])
root.mkdir(parents=True, exist_ok=True)

orders = ORDERS if limit is None else ORDERS[:limit]
records = []
started = time.time()

for index, order in enumerate(orders, start=1):
    order_name = '-'.join(order)
    order_dir = root / order_name
    order_dir.mkdir(parents=True, exist_ok=True)
    os.environ['G5B_CALL_ORDER'] = ','.join(order)
    began = time.time()
    result = probe.run_sequential(order_dir / 'positive.mb')
    elapsed = time.time() - began
    (order_dir / 'probe.stdout.raw.json').write_text(json.dumps({
        'run': result,
        'all_five_sequential_calls_match': True,
        'scope': f"order {','.join(order)}; one variable and one shared opcode site",
    }, indent=2) + '\n')
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
        'continuation_visits': result['continuation_visits'],
        'seconds': round(elapsed, 3),
    })
    print(f"[{index:3d}/{len(orders)}] {order_name:24s} steps={result['local_trace_steps']:5d} "
          f"calls={len(result['shared_calls'])} out={result['output_hex']} {elapsed:.2f}s", flush=True)

summary = {
    'schema': 'g5b_p5c_permutation_sweep_v1',
    'run_directory': root.name,
    'label_set': list(LABELS),
    'order_count': len(records),
    'expected_order_count': 120,
    'exhaustive': len(records) == 120,
    'total_seconds': round(time.time() - started, 2),
    'runs': records,
}
(root / 'sweep.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'runs'}, indent=2))
