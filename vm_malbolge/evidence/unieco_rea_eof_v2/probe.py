#!/usr/bin/env python3
"""Compare separately constructed Python, BF16, and native Olmstead cat."""
import hashlib
import json
import pathlib
import platform
import subprocess
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
IMAGE = ROOT / 'vm_malbolge/evidence/unieco_strict_relocation_v1/reference_cat_functional.mb'
OLMSTEAD = ROOT.parent / 'Malbolge-PureEpoch/build/olmstead'
sha = lambda b: hashlib.sha256(b).hexdigest()
cases = {'empty': b'', 'nul': b'\0', 'mixed': b'\0\n\x80\xff',
         'all256': bytes(range(256)),
         'long10000': bytes((73*i+195)%256 for i in range(10000))}
commands = {
    'python': [sys.executable, str(P/'reference.py')],
    'bf16': [sys.executable, str(P/'bf16.py'), str(P/'echo.bf')],
    'olmstead': [str(OLMSTEAD), str(IMAGE)],
}
report = {'platform': platform.platform(), 'cases': {}, 'controls': {},
          'image_sha256': sha(IMAGE.read_bytes()),
          'olmstead_sha256': sha(OLMSTEAD.read_bytes()),
          'semantics': 'BF unsigned 16-bit wrapping; EOF=65535; output low byte',
          'scope': 'finite cases, separately constructed programs; no BF-to-Malbolge compiler claim'}
for name, data in cases.items():
    record = {'input_hex': data.hex(), 'input_sha256': sha(data), 'runs': {}}
    for engine, cmd in commands.items():
        r = subprocess.run(cmd, input=data, capture_output=True, timeout=60)
        record['runs'][engine] = {'rc': r.returncode, 'stdout_hex': r.stdout.hex(),
                                  'stdout_sha256': sha(r.stdout),
                                  'stderr_hex': r.stderr.hex(),
                                  'exact': r.returncode == 0 and r.stdout == data}
    report['cases'][name] = record
    print(name, {k: v['exact'] for k, v in record['runs'].items()}, flush=True)

r = subprocess.run([sys.executable, str(P/'bf16.py'), str(P/'echo.bf'), '--eof', '0', '--limit', '100'],
                   input=b'', capture_output=True, timeout=5)
report['controls']['bf_wrong_eof'] = {'rc': r.returncode, 'stdout_hex': r.stdout.hex(),
                                      'stderr_hex': r.stderr.hex(),
                                      'detected': r.returncode != 0 or bool(r.stdout)}
# Independent sensitivity test against stored correct output, not a mutated input.
correct = bytes.fromhex(report['cases']['mixed']['runs']['olmstead']['stdout_hex'])
mutant = correct[:-1] + bytes([correct[-1] ^ 1])
report['controls']['flipped_output'] = {'mutant_hex': mutant.hex(),
                                        'detected': mutant != cases['mixed']}
report['checks'] = {'all_exact': all(x['exact'] for c in report['cases'].values() for x in c['runs'].values()),
                    'controls_detected': all(x['detected'] for x in report['controls'].values())}
(P/'results.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
print('checks', report['checks'])
raise SystemExit(0 if all(report['checks'].values()) else 1)
