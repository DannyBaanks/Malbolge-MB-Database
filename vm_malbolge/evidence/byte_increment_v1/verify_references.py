#!/usr/bin/env python3
"""Compare a Python oracle and an actual BF16 loop with EOF=65535."""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('bf16',ROOT/'vm_malbolge/evidence/unieco_rea_eof_v2/bf16.py');bf=importlib.util.module_from_spec(s);s.loader.exec_module(bf)
source=(P/'increment.bf').read_text();sha=lambda b:hashlib.sha256(b).hexdigest()
cases={'empty':b'', 'nul':b'\0','ff':b'\xff','mixed':b'\x00\x7f\xfe\xff',
       'all256':bytes(range(256)), 'long10000':bytes((73*i+195)%256 for i in range(10000))}
cases.update({f'byte_{i:03}':bytes([i]) for i in range(256)})
records={}
for name,data in cases.items():
    want=bytes((v+1)&255 for v in data)
    py=subprocess.run([sys.executable,str(P/'reference.py')],input=data,capture_output=True,timeout=60)
    output,status,steps,consumed=bf.run(source,data)
    ok=py.returncode==0 and py.stdout==output==want and status=='HALTED' and consumed==len(data)
    records[name]={'input_hex':data.hex(),'expected_hex':want.hex(),'python_rc':py.returncode,
                   'python_stdout_hex':py.stdout.hex(),'python_stderr_hex':py.stderr.hex(),
                   'bf_stdout_hex':output.hex(),'bf_status':status,'bf_steps':steps,'bf_consumed':consumed,'ok':ok}
    if not ok:raise AssertionError(name)
# Same bytes without the extra + yield echo and must be caught.
control,status,_,_=bf.run(',+[-.,+]',b'\x00\xff')
controls={'mutant_echo':{'input_hex':'00ff','actual_hex':control.hex(),'expected_hex':'0100',
                         'detected':control!=b'\x01\x00','status':status}}
report={'semantics':'BF unsigned 16-bit cells; modulo 65536; EOF=65535; output low byte',
        'bf_source_sha256':sha(source.encode()),'cases':records,'controls':controls,
        'scope':'BF and Python only; no Malbolge implementation claimed'}
(P/'references.results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'cases':len(records),'all_equal':all(r['ok'] for r in records.values()),
                  'mutant_detected':controls['mutant_echo']['detected']}))
assert controls['mutant_echo']['detected']
