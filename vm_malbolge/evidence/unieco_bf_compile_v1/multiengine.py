#!/usr/bin/env python3
"""Verify the compiled relocated image under the scratch model and C runner."""
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess

P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
spec=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
image=(P/'compiled_relocated.mb').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest(); cap=10000000
cases={'empty':b'','nul':b'\0','mixed':b'\0\x0a\x80\xff','all256':bytes(range(256)),
       'long10000':bytes((73*i+195)%256 for i in range(10000))}
report={'image_sha256':sha(image),'step_limit':cap,'cases':{}}
for name,data in cases.items():
    scratch=m.SE.run(image,max_steps=cap,stdin=data)
    runner=subprocess.run([str(m.B.C_RUNNER),str(P/'compiled_relocated.mb'),str(cap)],input=data,capture_output=True,timeout=90)
    match=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',runner.stderr)
    record={'scratch':{'status':scratch['status'],'steps':scratch['steps'],'output_sha256':sha(scratch['out']),
                       'exact':scratch['status']=='HALTED' and scratch['out']==data},
            'runner':{'rc':runner.returncode,'status':match.group(2).decode() if match else None,
                      'steps':int(match.group(1)) if match else None,'stdout_hex':runner.stdout.hex(),
                      'stderr_hex':runner.stderr.hex(),
                      'exact':bool(match) and match.group(2)==b'HALTED' and runner.stdout==data+b'\n'}}
    report['cases'][name]=record
    print(name,record['scratch']['exact'],record['runner']['exact'],flush=True)
(P/'multiengine.results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
assert all(v['scratch']['exact'] and v['runner']['exact'] for v in report['cases'].values())
