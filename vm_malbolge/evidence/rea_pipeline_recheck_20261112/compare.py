#!/usr/bin/env python3
"""Cross-check four-byte increment references and the native image."""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
base = ROOT / 'vm_malbolge/evidence/byte_increment_v1'
inc = ROOT / 'vm_malbolge/evidence/increment_stream_v2'
spec = importlib.util.spec_from_file_location('bf16', ROOT / 'vm_malbolge/evidence/unieco_rea_eof_v2/bf16.py')
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)
source = (base / 'increment.bf').read_text()
olmstead = ROOT.parent / 'Malbolge-PureEpoch/build/olmstead'
records = []
for data in (bytes.fromhex('41424344'), bytes.fromhex('00ff80fe'), bytes(4), bytes([255])*4):
    expected = bytes((x + 1) & 255 for x in data)
    py = subprocess.run([sys.executable, str(base / 'reference.py')], input=data, capture_output=True, timeout=10)
    output, status, steps, consumed = bf.run(source, data)
    native = subprocess.run([str(olmstead), str(inc / 'increment_four.mb')], input=data, capture_output=True, timeout=10)
    record = {'input_hex': data.hex(), 'expected_hex': expected.hex(), 'python': {'rc': py.returncode, 'stdout_hex': py.stdout.hex(), 'stderr_hex': py.stderr.hex()}, 'bf': {'status': status, 'stdout_hex': output.hex(), 'steps': steps, 'consumed': consumed}, 'olmstead': {'rc': native.returncode, 'stdout_hex': native.stdout.hex(), 'stderr_hex': native.stderr.hex()}}
    assert py.returncode == 0 and native.returncode == 0 and py.stdout == output == native.stdout == expected and status == 'HALTED' and consumed == len(data)
    records.append(record)
control = subprocess.run([str(olmstead), str(inc / 'increment_four_control.mb')], input=b'ABCD', capture_output=True, timeout=10)
assert control.returncode == 0 and control.stdout != b'BCDE'
print(json.dumps({'cases': records, 'control': {'rc': control.returncode, 'stdout_hex': control.stdout.hex(), 'stderr_hex': control.stderr.hex()}, 'sha256': {str(x.relative_to(ROOT.parent)): hashlib.sha256(x.read_bytes()).hexdigest() for x in [base / 'reference.py', base / 'increment.bf', inc / 'increment_four.mb', inc / 'increment_four_control.mb', olmstead]}}, indent=2))
