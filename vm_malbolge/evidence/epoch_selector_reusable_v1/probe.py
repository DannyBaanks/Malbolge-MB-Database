#!/usr/bin/env python3
"""Bounded binary selector, real repeated branch and marker state traces."""
import hashlib,json,random,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'vm_malbolge/tools/native_classic')]
import oracle_classic as oc
from constants import XLAT1

def labels(name):
 wanted={'marker_01','marker_02','dispatch_01','dispatch_02','next_char_rearm','IN','OUT','MOVED','MARK_FLAG','MARK5','MARK2','NO_MORE_CARRY_FLAG','CARRY'};result={}
 for line in (P/(name+'.dbg')).read_text().splitlines():
  m=re.fullmatch(r'(\w+): (?:DATA|CODE) (\d+)',line)
  if m and m[1] in wanted:result[m[1]]=int(m[2])
 assert set(result)==wanted,result
 return result

def trace(src,data,lab,limit=4000000):
 m=oc.load_memory(src.decode('latin1'));a=c=d=i=0;outputs=[];events=[];counts=[0,0];branch=[]
 for step in range(1,limit+1):
  if not 33<=m[c]<=126:return bytes(outputs),step,'NONPRINTABLE',events
  op=(m[c]+c)%94
  if op==4:
   if d in (lab['dispatch_01'],lab['dispatch_02']):branch.append(1 if d==lab['dispatch_01'] else 2)
   c=m[d]
  elif op==5:
   outputs.append(a%256);events.append({'kind':'out','step':step,'value':a%256,'branches':branch[:],'rotations':counts[:],'marker01':m[lab['marker_01']],'marker02':m[lab['marker_02']]});branch=[];counts=[0,0]
  elif op==23:
   events.append({'kind':'in','step':step,'index':i,'pc':c,'marker01':m[lab['marker_01']],'marker02':m[lab['marker_02']],'control':{k:m[lab[k]] for k in ('MOVED','MARK_FLAG','MARK5','MARK2','NO_MORE_CARRY_FLAG','CARRY')}})
   if i==len(data):return bytes(outputs),step,'EOF',events
   a=data[i];i+=1
  elif op==39:
   if d==lab['marker_01']:counts[0]+=1
   if d==lab['marker_02']:counts[1]+=1
   m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
  elif op==40:d=m[d]
  elif op==62:m[d]=oc.crazy_op(a,m[d]);a=m[d]
  elif op==81:return bytes(outputs),step,'HALTED',events
  if 33<=m[c]<=126:m[c]=oc._ENC[m[c]]
  c=(c+1)%59049;d=(d+1)%59049
 return bytes(outputs),limit,'MAX_STEPS',events

def main():
 rng=random.Random(20261107)
 cases=[b'',b'\x01',b'\x02',b'\x01\x02\x01',b'\x02\x01\x02',b'\x01'*8,b'\x02'*8,b'\x01\x02'*8,bytes(rng.choice((1,2)) for _ in range(128))]
 image=(P/'marker_loop4.mb').read_bytes(); lab=labels('marker_loop4');rows=[]
 source=bytes(v for v in image if v not in b' \t\r\n');invalid=[i for i,v in enumerate(source) if not (33<=v<=126 and XLAT1[(v-33+i)%94] in 'ji*p</vo')]
 for data in cases:
  want=bytes(0x50 if v==1 else 0x52 for v in data);out,steps,status=oc.run(image.decode('latin1'),stdin_data=data.decode('latin1'),max_steps=4000000,stop_on_eof=True);out=out.encode('latin1')
  run=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(P/'marker_loop4.mb'),'4000000'],input=data,capture_output=True)
  t,ts,tstatus,events=trace(image,data,lab);ins=[x for x in events if x['kind']=='in'];outs=[x for x in events if x['kind']=='out']
  state_ok=(len(ins)==len(data)+1 and len(outs)==len(data) and all(e['marker01']==80 and e['marker02']==82 for e in ins) and all(all(e['control'][k]==ins[0]['control'][k] for k in ('MOVED','MARK_FLAG','MARK5','MARK2')) for e in ins) and all(e['branches']==[v]*10 and e['rotations']==([10,0] if v==1 else [0,10]) and e['marker01']==80 and e['marker02']==82 for e,v in zip(outs,data)))
  ok=(out==want and status=='EOF' and run.stdout==want+b'\n' and run.returncode==0 and run.stderr.decode().strip()==f'steps: {steps} | status: HALTED' and t==out and ts==steps and tstatus==status and state_ok)
  rows.append({'input_hex':data.hex(),'expected_hex':want.hex(),'oracle_hex':out.hex(),'runner_raw_hex':run.stdout.hex(),'runner_stderr':run.stderr.decode().strip(),'steps':steps,'status':status,'state_ok':state_ok,'ok':ok,'events':events})
  print('len',len(data),'input',data.hex()[:16],'output',out.hex()[:16],'steps',steps,'state',state_ok,'ok',ok,flush=True)
 negatives=[]
 for data in (b'\x01',b'\x02',b'\x01\x02\x01'):
  p=P/'marker_mutant.mb';img=p.read_bytes();want=bytes(0x50 if v==1 else 0x52 for v in data)
  out,steps,status=oc.run(img.decode('latin1'),stdin_data=data.decode('latin1'),max_steps=1000000,stop_on_eof=True);out=out.encode('latin1');r=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(p),'1000000'],input=data,capture_output=True)
  # Mutant must fail A cases; B is unaffected positive control. Python/C can diverge after non-printable code.
  control=(out==want and r.stdout==want+b'\n') if data==b'\x02' else (out!=want and r.stdout!=want+b'\n')
  negatives.append({'name':'marker_mutant','input_hex':data.hex(),'oracle_hex':out.hex(),'oracle_steps':steps,'oracle_status':status,'runner_raw_hex':r.stdout.hex(),'runner_stderr':r.stderr.decode().strip(),'control':control})
  print('mutant',data.hex(),'oracle',out.hex(),'runner_raw',r.stdout.hex(),'control',control,flush=True)
 # Earlier predecessor restores MOVED but does not restore marker literals.
 data=b'\x01\x01\x01'; p=P/'rearm_moved.mb';img=p.read_bytes();want=b'PPP'
 out,steps,status=oc.run(img.decode('latin1'),stdin_data=data.decode('latin1'),max_steps=1000000,stop_on_eof=True);out=out.encode('latin1');r=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(p),'1000000'],input=data,capture_output=True)
 control=(out!=want and r.stdout!=want+b'\n' and r.stdout==out+b'\n' and r.stderr.decode().strip()==f'steps: {steps} | status: HALTED' and status=='EOF')
 negatives.append({'name':'no_marker_restore','input_hex':data.hex(),'oracle_hex':out.hex(),'oracle_steps':steps,'oracle_status':status,'runner_raw_hex':r.stdout.hex(),'runner_stderr':r.stderr.decode().strip(),'control':control})
 print('predecessor',data.hex(),'oracle',out.hex(),'runner_raw',r.stdout.hex(),'control',control,flush=True)
 payload={'cases':rows,'negative_controls':negatives,'labels':lab,'loader_invalid_addresses':invalid,'positive_sha256':hashlib.sha256(image).hexdigest(),'mutant_sha256':hashlib.sha256((P/'marker_mutant.mb').read_bytes()).hexdigest()}
 (P/'results.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf8');print('strict_invalid',len(invalid),'positive_sha256',payload['positive_sha256'],'mutant_sha256',payload['mutant_sha256'])
 return int(not(all(r['ok'] for r in rows) and all(x['control'] for x in negatives) and not invalid))
if __name__=='__main__':sys.exit(main())
