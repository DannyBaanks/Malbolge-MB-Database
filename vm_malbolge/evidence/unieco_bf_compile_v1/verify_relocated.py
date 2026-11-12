#!/usr/bin/env python3
"""Native bounded verification of the new reference-derived relocated loop."""
import hashlib
import importlib.util
import json
import os
import pathlib
import resource
import selectors
import subprocess
import tempfile
import time

P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]
spec=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);se=m.SE; N=59049
image=(P/'relocated_candidate.mb').read_bytes(); targets={int(k):v for k,v in json.loads((P/'relocated_targets.json').read_text()).items()}
sha=lambda b:hashlib.sha256(b).hexdigest(); OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead'
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
# Trace installation without input; compare every installed target at handoff.
mem=list(image)+[0]*(N-len(image))
for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=0; pre_io=[]; status='MAX_STEPS'
for st in range(1,100000):
    if not 33<=mem[c]<=126:status='NONPRINT';break
    op=(mem[c]+c)%94
    if op in (5,23):
        pre_io.append({'step':st,'opcode':op,'pc':c,'d':d})
        status='FIRST_IO';break
    if op==4:c=mem[d]
    elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
    elif op==40:d=mem[d]
    elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
    elif op==81:status='HALTED';break
    if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
    c=(c+1)%N;d=(d+1)%N
expected=dict(targets); expected[7656+28200]=se.encrypt(expected[7656+28200])
mismatches=[{'address':i,'expected':v,'actual':mem[i]} for i,v in expected.items() if mem[i]!=v]
installation={'status':status,'first_io':pre_io,'steps':st,'mismatches':mismatches,'target_cells':len(expected),
              'ok':status=='FIRST_IO' and pre_io[0]['opcode']==23 and c==35857 and d==58975 and not mismatches}

def native(program,data,timeout=15):
    with tempfile.TemporaryFile() as f:
        f.write(data);f.seek(0)
        p=subprocess.Popen([str(OL),str(program)],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ)
        output=bytearray();deadline=time.monotonic()+timeout;reason='exited'
        while time.monotonic()<deadline:
            if len(output)>len(data)+512:reason='output_limit';break
            events=selector.select(.05)
            if events:
                chunk=os.read(p.stdout.fileno(),4096)
                if not chunk:break
                output.extend(chunk)
            elif p.poll() is not None:break
        else:reason='timeout'
        if reason!='exited' and p.poll() is None:p.terminate()
        try:rc=p.wait(timeout=2)
        except subprocess.TimeoutExpired:p.kill();rc=p.wait();reason='kill'
        stderr=p.stderr.read();selector.close()
    return {'rc':rc,'reason':reason,'bytes':len(output),'output_hex':bytes(output).hex(),
            'output_sha256':sha(output),'stderr_hex':stderr.hex(),'exact':rc==0 and reason=='exited' and bytes(output)==data}

cases={'empty':b'','nul':b'\0','mixed':b'\0\x0a\x80\xff','all256':bytes(range(256)),
       'long10000':bytes((73*i+195)%256 for i in range(10000))}
cases.update({f'byte_{i:03}':bytes([i]) for i in range(256)})
runs={}
for name,data in cases.items():
    runs[name]=native(P/'relocated_candidate.mb',data)
    if not runs[name]['exact']:print('FAIL',name,runs[name],flush=True);break
print('installation',installation['ok'],'mismatches',len(mismatches),'native_cases',len(runs),'all_exact',all(x['exact'] for x in runs.values()),flush=True)
# Loader-valid mutation of the final preamble CRAZY.
ops=(P/'relocated_plan.ops').read_text().strip();idx=ops.rfind('p');assert idx>=0;pc=99+idx
mutant=bytearray(image);mutant[pc]=33+((68-pc-33)%94);(P/'relocated_no_last_crazy.mb').write_bytes(mutant)
control=native(P/'relocated_no_last_crazy.mb',cases['mixed']);control.update(mutated_pc=pc,rejected=not control['exact'])
# Reject an invalid first instruction in the actual native loader.
bad=bytearray(image);bad[0]=33;(P/'relocated_bad_loader.mb').write_bytes(bad)
loader=native(P/'relocated_bad_loader.mb',b'');loader['rejected']=loader['rc']==1
print('controls',control['rejected'],loader['rejected'],flush=True)
report={'image_sha256':sha(image),'image_bytes':len(image),'loader_valid_all_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
        'installation':installation,'inputs':{k:{'bytes':len(v),'sha256':sha(v)} for k,v in cases.items()},
        'runs':runs,'controls':{'last_writer_mutated':control,'bad_loader':loader},
        'checks':{'strict_loader':loader['rejected'],'installation':installation['ok'],
                  'all_cases_exact':len(runs)==len(cases) and all(r['exact'] for r in runs.values()),
                  'mutant_breaks':control['rejected']},
        'scope':'reference-derived relocated loop; finite tests; does not modify original compact candidate'}
(P/'relocated_verify.results.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
assert all(report['checks'].values())
