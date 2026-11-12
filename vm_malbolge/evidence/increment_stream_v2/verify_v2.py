#!/usr/bin/env python3
"""Bounded tests for three-read scratch rearm; this is not a streaming proof."""
import hashlib,importlib.util,json,pathlib,resource,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';resource.setrlimit(resource.RLIMIT_CORE,(0,0))
image=(P/'increment_three.mb').read_bytes();params=json.loads((P/'synthesis.results.json').read_text());target={int(k):v for k,v in json.loads((P/'targets.json').read_text()).items()};sha=lambda b:hashlib.sha256(b).hexdigest();scratch=58020;addresses=[scratch+1,scratch+2,scratch+4,scratch+5,scratch+9,scratch+12]

def trace(data):
 mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=pos=0;ins=[];outs=[];snapshot=None;dirty=None;table_changes=[];code_changes=None
 for st in range(1,120000):
  if not 33<=mem[c]<=126:return {'status':'NONPRINT','step':st}
  op=(mem[c]+c)%94
  if op==23:
   if snapshot is None:
    snapshot={i:mem[i] for i in addresses};table=[mem[56862+3*b+1] for b in range(256)];mismatches=[i for i,v in target.items() if mem[i]!=v]
   else:
    table_changes.append(sum(mem[56862+3*b+1]!=table[b] for b in range(256)))
   ins.append({'step':st,'pc':c,'d':d,'scratch':{str(i):mem[i] for i in addresses}})
   if len(ins)==3:
    # Code block 2 has executed; compare with initial target bytes to expose remaining rearm.
    block2_start=58500+49;block_len=48
    code_changes=sum(mem[i]!=target[i] for i in range(block2_start,block2_start+block_len))
   a=data[pos] if pos<len(data) else 59048;pos+=pos<len(data)
  elif op==4:c=mem[d]
  elif op==5:
   outs.append(a%256)
   if len(outs)==2:dirty={str(i):mem[i] for i in addresses}
  elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
  elif op==40:d=mem[d]
  elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
  elif op==81:break
  if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
  c=(c+1)%N;d=(d+1)%N
 else:return {'status':'MAX_STEPS'}
 original={str(i):v for i,v in snapshot.items()};third=ins[2]['scratch'] if len(ins)==3 else {}
 return {'status':'HALTED','steps':st,'inputs':ins,'outputs':outs,'initial_scratch':original,'after_second_output':dirty,
         'scratch_before_third_equals_initial':third==original,'scratch_changed_after_second':dirty!=original,
         'table_changes_before_second_and_third':table_changes,'code_block2_changed_cells':code_changes,'installation_mismatches':mismatches}

traces={}
for data in (bytes([0,0,0]),bytes([255,255,255]),bytes([65,66,67])):
 t=trace(data);traces[data.hex()]=t
 assert t['status']=='HALTED' and t['outputs']==[(b+1)%256 for b in data] and t['scratch_before_third_equals_initial'] and not t['installation_mismatches'] and t['table_changes_before_second_and_third']==[0,0]

cases={}
for b in range(256):
 cases[f'repeated_{b:03}']=bytes([b,b,b]);cases[f'varied_{b:03}']=bytes([b,(73*b+195)%256,(17*b+13)%256])
results={}
for name,data in cases.items():
 r=subprocess.run([str(OL),str(P/'increment_three.mb')],input=data,capture_output=True,timeout=10);want=bytes((x+1)%256 for x in data)
 results[name]={'input_hex':data.hex(),'output_hex':r.stdout.hex(),'stderr_hex':r.stderr.hex(),'rc':r.returncode,'ok':r.returncode==0 and r.stdout==want}
 if not results[name]['ok']:raise AssertionError(name)
controls={}
for data in [b'ABC',b'\0\0\0',b'\xff\xff\xff',b'\0\xff\x80']:
 r=subprocess.run([str(OL),str(P/'increment_three_control.mb')],input=data,capture_output=True,timeout=10);want=bytes((x+1)%256 for x in data)
 controls[data.hex()]={'rc':r.returncode,'output_hex':r.stdout.hex(),'expected_hex':want.hex(),'detected':r.returncode!=0 or r.stdout!=want}
assert controls['414243']['detected']
boundaries={}
for data in [b'',b'A',b'AB',b'ABCD']:
 r=subprocess.run([str(OL),str(P/'increment_three.mb')],input=data,capture_output=True,timeout=10);want=bytes((x+1)%256 for x in data)
 boundaries[data.hex() or 'empty']={'rc':r.returncode,'output_hex':r.stdout.hex(),'expected_hex':want.hex(),'matches':r.returncode==0 and r.stdout==want}
assert not any(x['matches'] for x in boundaries.values())
report={'image_sha256':sha(image),'image_bytes':len(image),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
        'traces':traces,'native_cases':results,'controls':controls,'boundaries':boundaries,
        'scope':'exactly three unrolled reads; no EOF branch and no loop'}
(P/'verification_v2.results.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps({'native_cases':len(results),'native_all_ok':all(x['ok'] for x in results.values()),
                  'scratch_restored_in_traces':all(x['scratch_before_third_equals_initial'] for x in traces.values()),
                  'code_changes':[x['code_block2_changed_cells'] for x in traces.values()],
                  'controls':controls,'boundaries':boundaries},indent=2))
