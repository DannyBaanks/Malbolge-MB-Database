#!/usr/bin/env python3
"""Negative control: the first lll caller also toggles the extra selector."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

PACK = pathlib.Path(__file__).resolve().parent
os.environ['G5B_CALL_ORDER'] = 'lll,rr,lr,rl,llr'
os.environ['G5B_FAULT_EXTRA_FIRST'] = '1'
spec = importlib.util.spec_from_file_location('g5b_p5_probe', PACK / 'probe.py')
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)


def run_control(image_path: pathlib.Path) -> dict:
    plan = probe.Shared5()
    image = plan.assemble()
    image_path = image_path.resolve()
    image_path.parent.mkdir(parents=True, exist_ok=True)
    if image_path.exists():
        raise FileExistsError(image_path)
    image_path.write_bytes(image)

    local = probe.trace(image, plan)
    native = subprocess.run([str(probe.OLM), str(image_path)], input=b'', capture_output=True, timeout=20)
    independent = probe.cb.execute(image, b'', max_steps=2_000_000)
    image_path.with_suffix(image_path.suffix + '.native.stdout.raw').write_bytes(native.stdout)
    image_path.with_suffix(image_path.suffix + '.native.stderr.raw').write_bytes(native.stderr)

    expected = b'\x62'
    assert local['status'] == 'halt' and local['output'] == expected
    assert local['cont_visits'] == [plan.cont['llr']], local['cont_visits']
    assert len(local['shared_calls']) == 1, local['shared_calls']
    assert local['shared_calls'][0]['d'] == plan.d_addr
    assert local['shared_calls'][0]['value_after'] == 12130
    assert native.returncode == 0 and native.stdout == expected
    assert independent.status == 'end' and independent.output == expected
    return {
        'call_order': list(plan.call_order),
        'fault': 'first lll caller incorrectly toggles f_extra and selects llr',
        'shared_op_address': plan.shared_op,
        'variable_address': plan.d_addr,
        'observed_return_order': local['cont_visits'],
        'output_hex': native.stdout.hex(),
        'shared_calls': local['shared_calls'],
        'native_rc': native.returncode,
        'independent_status': independent.status,
        'local_trace_status': local['status'],
        'local_trace_steps': local['steps'],
        'image_sha256': hashlib.sha256(image).hexdigest(),
        'negative_control_detected': True,
    }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('uso: python3 control.py <negative.mb>')
    result = run_control(pathlib.Path(sys.argv[1]))
    print(json.dumps({'run': result}, indent=2))
