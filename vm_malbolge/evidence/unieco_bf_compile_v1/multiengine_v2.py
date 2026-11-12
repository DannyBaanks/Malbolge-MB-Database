#!/usr/bin/env python3
"""Scratch-model checks including long input; bounded C-runner checks."""
import hashlib, importlib.util, json, pathlib, re, subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
image=(P/'compiled_relocated.mb').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();cap=10000000
cases={'empty':b'','nul':b'\0','mixed':b'\0\x0a\x80\xff','all256':bytes(range(256)),
       'long10000':bytes((73*i+195)%256 for i in range(10000))}
report={'image_sha256':sha(image),'step_limit':cap,'cases':{},'note':'C runner stopped by host on EOF in source e7faeb1; status HALTED does not prove opcode halt'}
for name,data in cases.items():
    r=m.SE.run(image,max_steps=cap,stdin=data)
    z={'scratch':{'status':r['status'],'steps':r['steps'],'output_sha256':sha(r['out']),
                  'exact':r['status']=='HALTED' and r['out']==data}}
    if len(data)<=256:
        c=subprocess.run([str(m.B.C_RUNNER),str(P/'compiled_relocated.mb'),str(cap)],input=data,capture_output=True,timeout=90)
        match=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',c.stderr)
        z['runner']={'rc':c.returncode,'status':match.group(2).decode() if match else None,
                     'steps':int(match.group(1)) if match else None,'stdout_hex':c.stdout.hex(),
                     'stderr_hex':c.stderr.hex(),'output_exact_with_framing':c.stdout==data+b'\n'}
    else:z['runner']={'status':'NOT_DEMONSTRATED','reason':'previous long-input attempt timed out after 90 seconds'}
    report['cases'][name]=z
    print(name,'scratch',z['scratch']['exact'],'runner',z['runner'].get('output_exact_with_framing','NOT_DEMONSTRATED'),flush=True)
(P/'multiengine_v2.results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
assert all(v['scratch']['exact'] for v in report['cases'].values())
assert all(v['runner'].get('output_exact_with_framing',True) for v in report['cases'].values())
