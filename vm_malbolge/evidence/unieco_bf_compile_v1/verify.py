#!/usr/bin/env python3
"""Verify the compiled template against Python and BF, plus rejection controls."""
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
BASE = ROOT/'vm_malbolge/evidence/unieco_rea_eof_v2'
TEMPLATE = ROOT/'vm_malbolge/evidence/unieco_strict_relocation_v1/reference_cat_functional.mb'
OLMSTEAD = ROOT.parent/'Malbolge-PureEpoch/build/olmstead'
IMAGE = P/'compiled.mb'
sha = lambda x: hashlib.sha256(x).hexdigest()
spec = importlib.util.spec_from_file_location('bf16', BASE/'bf16.py')
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)
source = (P/'echo.bf').read_text()
cases = {'empty': b'', 'nul': b'\0', 'mixed': b'\0\x0a\x80\xff',
         'all256': bytes(range(256)), 'long10000': bytes((73*i+195)%256 for i in range(10000))}
cases.update({f'byte_{i:03}': bytes([i]) for i in range(256)})
records = {}
for name, data in cases.items():
    py = subprocess.run([sys.executable, str(BASE/'reference.py')], input=data, capture_output=True, timeout=60)
    out, status, steps, consumed = bf.run(source, data)
    mb = subprocess.run([str(OLMSTEAD), str(IMAGE)], input=data, capture_output=True, timeout=60)
    ok = py.returncode == mb.returncode == 0 and py.stdout == out == mb.stdout == data and status == 'HALTED' and consumed == len(data)
    records[name] = {'input_sha256': sha(data), 'input_bytes': len(data), 'python_rc': py.returncode,
                     'bf_status': status, 'bf_steps': steps, 'bf_consumed': consumed,
                     'malbolge_rc': mb.returncode, 'malbolge_stderr_hex': mb.stderr.hex(),
                     'output_sha256': sha(mb.stdout), 'match': ok}
    if not ok:
        raise AssertionError(name)
print('cases', len(records), 'all match', all(r['match'] for r in records.values()), flush=True)
# Each invocation gets a never-before-existing output path.
tmp = pathlib.Path(tempfile.mkdtemp(prefix='unieco-bf-controls-'))
invalid_bf = tmp/'invalid.bf'; invalid_bf.write_text(',[.,]')
bad_template = tmp/'bad.mb'; b = bytearray(TEMPLATE.read_bytes()); b[0] ^= 1; bad_template.write_bytes(b)
controls = {}
for name, input_file, templ, flags in [
    ('other_program', invalid_bf, TEMPLATE, []),
    ('wrong_eof', P/'echo.bf', TEMPLATE, ['--eof','0']),
    ('wrong_cell_width', P/'echo.bf', TEMPLATE, ['--cell-bits','8']),
    ('altered_template', P/'echo.bf', bad_template, []),
]:
    output = tmp/(name+'.mb')
    cmd = [sys.executable,str(P/'compile_bf.py'),str(input_file),'--template',str(templ),'--output',str(output),*flags]
    r = subprocess.run(cmd, capture_output=True, timeout=10)
    controls[name] = {'rc': r.returncode, 'stderr': r.stderr.decode().strip(), 'output_exists': output.exists(),
                      'rejected': r.returncode != 0 and not output.exists()}
    if not controls[name]['rejected']:
        raise AssertionError(name)
print('controls', len(controls), 'all rejected', all(c['rejected'] for c in controls.values()), flush=True)
report = {'template_sha256': sha(TEMPLATE.read_bytes()), 'compiled_sha256': sha(IMAGE.read_bytes()),
          'compiled_equals_template': IMAGE.read_bytes() == TEMPLATE.read_bytes(),
          'compiler': 'exact-pattern specialization; authenticated static template',
          'cases': records, 'controls': controls,
          'scope': 'finite tests; no general BF compilation, state mapping or relocalized image claim'}
(P/'results.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
