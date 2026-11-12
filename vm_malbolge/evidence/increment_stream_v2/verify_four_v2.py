#!/usr/bin/env python3
"""Measure two consecutive scratch rearms in a four-read unrolled image."""
import hashlib,importlib.util,json,pathlib,resource,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';resource.setrlimit(resource.RLIMIT_CORE,(0,0))
image=(P/'increment_four.mb').read_bytes();target={int(k):v for k,v in json.loads((P/'four_targets.json').read_text()).items()};sha=lambda b:hashlib.sha256(b).hexdigest();addresses=[58021,58022,58024,58025,58029,58032]
def trace(data):
 mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=pos=0;ins=[];outs=[];snapshot=None;table=None;mismatches=None
 for st in range(1,120000):
  if not 33<=mem[c]<=126:raise AssertionError('nonprint')
  op=(mem[c]+c)%94
  if op==23:
   curr={str(i):mem[i] for i in addresses};curtable=[mem[56862+3*b+1] for b in range(256)]
   if snapshot is None:
    snapshot=curr;table=curtable;mismatches=[i for i,v in target.items() if mem[i]!=v]
   ins.append({'step':st,'pc':c,'d':d,'scratch_matches_initial':curr==snapshot,'table_matches_initial':curtable==table})
   a=data[pos] if pos<len(data) else 59048;pos+=pos<len(data)
  elif op==4:c=mem[d]
  elif op==5:outs.append(a%256)
  elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
  elif op==40:d=mem[d]
  elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
  elif op==81:break
  if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
  c=(c+1)%N;d=(d+1)%N
 else:raise AssertionError('step budget')
 return {'status':'HALTED','steps':st,'inputs':ins,'outputs':outs,'installation_mismatches':mismatches,
         'two_rearms_ok':len(ins)==4 and all(i['scratch_matches_initial'] and i['table_matches_initial'] for i in ins[1:])}
traces={}
for data in (bytes([0]*4),bytes([255]*4),b'ABCD'):
 t=trace(data);traces[data.hex()]=t;assert t['two_rearms_ok'] and not t['installation_mismatches'] and t['outputs']==[(b+1)%256 for b in data]
cases={}
for b in range(256):
 cases[f'repeated_{b:03}']=bytes([b]*4);cases[f'varied_{b:03}']=bytes([b,(73*b+195)%256,(17*b+13)%256,(43*b+7)%256])
records={}
for name,data in cases.items():
 r=subprocess.run([str(OL),str(P/'increment_four.mb')],input=data,capture_output=True,timeout=10);want=bytes((x+1)%256 for x in data)
 records[name]={'input_hex':data.hex(),'output_hex':r.stdout.hex(),'stderr_hex':r.stderr.hex(),'rc':r.returncode,'ok':r.returncode==0 and r.stdout==want}
 if not records[name]['ok']:raise AssertionError(name)
controls={}
for data in [b'ABCD',bytes([0]*4),bytes([255]*4),b'\x00\xff\x80\x42']:
 r=subprocess.run([str(OL),str(P/'increment_four_control.mb')],input=data,capture_output=True,timeout=10);want=bytes((x+1)%256 for x in data)
 controls[data.hex()]={'rc':r.returncode,'output_hex':r.stdout.hex(),'expected_hex':want.hex(),'detected':r.returncode!=0 or r.stdout!=want}
assert controls['41424344']['detected']
boundaries={}
for data in [b'',b'A',b'ABC',b'ABCDE']:
 want=bytes((x+1)%256 for x in data)
 try:
  r=subprocess.run([str(OL),str(P/'increment_four.mb')],input=data,capture_output=True,timeout=1)
  boundaries[data.hex() or 'empty']={'rc':r.returncode,'output_hex':r.stdout.hex(),'expected_hex':want.hex(),'matches':r.returncode==0 and r.stdout==want,'timed_out':False}
 except subprocess.TimeoutExpired as e:
  boundaries[data.hex() or 'empty']={'rc':None,'output_hex':(e.stdout or b'').hex(),'expected_hex':want.hex(),'matches':False,'timed_out':True}
assert not any(x['matches'] for x in boundaries.values())
report={'image_sha256':sha(image),'image_bytes':len(image),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
        'traces':traces,'native_cases':records,'controls':controls,'boundaries':boundaries,'scope':'exactly four unrolled reads; not a general loop or EOF branch'}
(P/'four_verification_v2.results.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps({'cases':len(records),'all_exact':all(x['ok'] for x in records.values()),'traces_rearmed':all(x['two_rearms_ok'] for x in traces.values()),'controls':controls,'boundaries':boundaries},indent=2))
