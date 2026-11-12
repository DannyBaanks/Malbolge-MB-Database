#!/usr/bin/env python3
"""Compare full REA and scratch traces of code rearm; check native termination."""
import hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';records={}
for tag,expected in [('positive',[62,62]),('control',[62,21])]:
 image=(P/('revisit_'+tag+'.mb')).read_bytes();mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=0;visits=[];writes=[]
 for st in range(1,10000):
  if not 33<=mem[c]<=126:raise AssertionError('nonprint')
  pc=c;op=(mem[c]+c)%94
  if c==58550:visits.append({'step':st,'opcode':op})
  if op in (23,5):raise AssertionError('unexpected I/O')
  if op==4:c=mem[d]
  elif op==39:
   old=mem[d];mem[d]=se.rot(old);a=mem[d]
   if d==58550:writes.append({'step':st,'before':old,'after':mem[d]})
  elif op==40:d=mem[d]
  elif op==62:
   old=mem[d];mem[d]=se.crazy(a,old);a=mem[d]
   if d==58550:writes.append({'step':st,'before':old,'after':mem[d]})
  elif op==81:break
  if 33<=mem[c]<=126:
   old=mem[c];mem[c]=se.encrypt(old)
   if c==58550:writes.append({'step':st,'before':old,'after':mem[c]})
  c=(c+1)%N;d=(d+1)%N
 else:raise AssertionError('max steps')
 rea=json.loads((P/('rea_revisit_'+tag+'.redacted.json')).read_text());n=rea['normalized_result'];rv=[{'step':e['step'],'opcode':e['opcode']} for e in n['events'] if e['position']==58550];rw=[{'step':e['step'],'before':w['value_before'],'after':w['value_after']} for e in n['events'] for w in e['writes'] if w['position']==58550]
 native=subprocess.run([str(OL),str(P/('revisit_'+tag+'.mb'))],input=b'',capture_output=True,timeout=10)
 records[tag]={'image_sha256':hashlib.sha256(image).hexdigest(),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
               'native_rc':native.returncode,'native_stdout_hex':native.stdout.hex(),'native_stderr_hex':native.stderr.hex(),
               'model_steps':st,'visits':visits,'writes':writes,'rea_id':rea['evidence_id'],'rea_status':n['run']['status'],
               'rea_steps':n['run']['steps'],'rea_events_truncated':n['run']['events_truncated'],'rea_visits_match':rv==visits,'rea_writes_match':rw==writes}
 assert [v['opcode'] for v in visits]==expected and native.returncode==0 and not native.stdout and n['run']['status']=='HALTED' and not n['run']['events_truncated'] and rv==visits and rw==writes
(P/'revisit_verification.results.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n');print(json.dumps(records,indent=2,sort_keys=True))
