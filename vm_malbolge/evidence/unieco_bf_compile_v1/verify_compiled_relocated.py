#!/usr/bin/env python3
"""Compare the compiled relocated template against the BF contract."""
import hashlib
import importlib.util
import json
import pathlib
import subprocess

P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]
BASE=ROOT/'vm_malbolge/evidence/unieco_rea_eof_v2'
spec=importlib.util.spec_from_file_location('bf16',BASE/'bf16.py'); bf=importlib.util.module_from_spec(spec);spec.loader.exec_module(bf)
image=(P/'compiled_relocated.mb').read_bytes();template=(P/'relocated_candidate.mb').read_bytes();source=(P/'echo.bf').read_text()
olmstead=ROOT.parent/'Malbolge-PureEpoch/build/olmstead'; sha=lambda b:hashlib.sha256(b).hexdigest()
cases={'empty':b'','nul':b'\0','mixed':b'\0\x0a\x80\xff','all256':bytes(range(256)),
       'long10000':bytes((73*i+195)%256 for i in range(10000))}
report={'compiled_sha256':sha(image),'template_sha256':sha(template),'identical':image==template,'cases':{}}
for name,data in cases.items():
    expected,status,steps,consumed=bf.run(source,data)
    result=subprocess.run([str(olmstead),str(P/'compiled_relocated.mb')],input=data,capture_output=True,timeout=60)
    report['cases'][name]={'input_sha256':sha(data),'bf_status':status,'bf_steps':steps,'bf_consumed':consumed,
                           'rc':result.returncode,'output_hex':result.stdout.hex(),'stderr_hex':result.stderr.hex(),
                           'exact':result.returncode==0 and status=='HALTED' and expected==result.stdout==data}
    print(name,report['cases'][name]['exact'],flush=True)
(P/'compiled_relocated.results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
assert report['identical'] and all(x['exact'] for x in report['cases'].values())
