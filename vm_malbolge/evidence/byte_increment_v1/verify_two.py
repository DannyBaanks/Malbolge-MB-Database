#!/usr/bin/env python3
"""Test two bounded reads and prove the shared table is restored in a model."""
import hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead'
image=(P/'increment_two.mb').read_bytes();target={int(k):v for k,v in json.loads((P/'two_targets.json').read_text()).items()};sha=lambda b:hashlib.sha256(b).hexdigest()
mem=list(image)+[0]*(N-len(image))
for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=pos=0;stream=b'\xff\xff';inputs=[];out=[];before=None;rearm=[]
for st in range(1,100000):
 if not 33<=mem[c]<=126:raise AssertionError('nonprint')
 op=(mem[c]+c)%94
 if op==23:
  inputs.append({'step':st,'pc':c,'d':d})
  current=[mem[56862+3*b+1] for b in range(256)]
  if before is None:
   before=current
   mismatches=[i for i,v in target.items() if mem[i]!=v]
  else:rearm=[i for i,(x,y) in enumerate(zip(before,current)) if x!=y]
  a=stream[pos] if pos<len(stream) else 59048;pos+=pos<len(stream)
 elif op==4:c=mem[d]
 elif op==5:out.append(a%256)
 elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
 elif op==40:d=mem[d]
 elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
 elif op==81:break
 if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
 c=(c+1)%N;d=(d+1)%N
else:raise AssertionError('max steps')
after=[mem[56862+3*b+1] for b in range(256)];after_mismatch=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
model={'steps':st,'inputs':inputs,'outputs':out,'installation_mismatches':mismatches,'before_second_input_table_mismatches':rearm,
       'at_halt_table_mismatches':after_mismatch,'ok':out==[0,0] and len(inputs)==2 and not mismatches and not rearm and not after_mismatch}
# Two full-domain families: all identical pairs and all ascending neighbouring pairs.
cases={}
for i in range(256):
 cases[f'repeated_{i:03}']=bytes([i,i]);cases[f'next_{i:03}']=bytes([i,(i+1)%256])
results={}
for name,data in cases.items():
 r=subprocess.run([str(OL),str(P/'increment_two.mb')],input=data,capture_output=True,timeout=10);want=bytes((b+1)%256 for b in data)
 results[name]={'input_hex':data.hex(),'stdout_hex':r.stdout.hex(),'stderr_hex':r.stderr.hex(),'rc':r.returncode,'ok':r.returncode==0 and r.stdout==want}
 if not results[name]['ok']:raise AssertionError(name)
controls={}
for data in [b'\x00\x00',b'\xff\xff',b'\x00\xff',b'\x41\x42']:
 r=subprocess.run([str(OL),str(P/'increment_two_control.mb')],input=data,capture_output=True,timeout=10)
 controls[data.hex()]={'stdout_hex':r.stdout.hex(),'rc':r.returncode,'is_echo':r.returncode==0 and r.stdout==data,
                       'detected':r.stdout!=bytes((b+1)%256 for b in data)}
boundaries={}
for data in [b'',b'\x41',b'\x41\x42\x43']:
 r=subprocess.run([str(OL),str(P/'increment_two.mb')],input=data,capture_output=True,timeout=10)
 boundaries[data.hex() or 'empty']={'stdout_hex':r.stdout.hex(),'rc':r.returncode,'expected_stream_hex':bytes((b+1)%256 for b in data).hex(),
                                    'stream_goal_met':r.returncode==0 and r.stdout==bytes((b+1)%256 for b in data)}
report={'image_sha256':sha(image),'image_bytes':len(image),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
        'model':model,'cases':results,'echo_table_controls':controls,'boundaries':boundaries,
        'scope':'two bounded reads; no EOF-aware branch, no general streaming loop'}
(P/'two_verify.results.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
summary={'table_restored':model['ok'],'native_cases':len(results),'all_exact':all(x['ok'] for x in results.values()),
         'controls_detected':all(x['is_echo'] and x['detected'] for x in controls.values()),'boundaries':boundaries}
print(json.dumps(summary,indent=2));assert model['ok'] and summary['all_exact'] and summary['controls_detected'] and not any(x['stream_goal_met'] for x in boundaries.values())
