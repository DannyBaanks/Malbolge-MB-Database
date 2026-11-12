#!/usr/bin/env python3
"""Cross-check native halt, scratch memory writes and full REA replay."""
import hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';records={}
for tag,expected in [('positive',74),('control',33)]:
 image=(P/('code_cell_'+tag+'.mb')).read_bytes();mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=0;events=[]
 for step in range(1,10000):
  if not 33<=mem[c]<=126:raise AssertionError('nonprint')
  op=(mem[c]+c)%94
  if op in (23,5):raise AssertionError('unexpected input/output')
  if op==4:c=mem[d]
  elif op==39:
   old=mem[d];mem[d]=se.rot(old);a=mem[d]
   if d==57000:events.append({'step':step,'before':old,'after':mem[d]})
  elif op==40:d=mem[d]
  elif op==62:
   old=mem[d];mem[d]=se.crazy(a,old);a=mem[d]
   if d==57000:events.append({'step':step,'before':old,'after':mem[d]})
  elif op==81:break
  if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
  c=(c+1)%N;d=(d+1)%N
 else:raise AssertionError('timeout')
 rea=json.loads((P/('rea_code_cell_'+tag+'.redacted.json')).read_text());n=rea['normalized_result']
 rea_writes=[{'step':e['step'],'before':w['value_before'],'after':w['value_after']} for e in n['events'] for w in e['writes'] if w['position']==57000 and e['opcode_name'] in ('crazy','rotate')]
 native=subprocess.run([str(OL),str(P/('code_cell_'+tag+'.mb'))],input=b'',capture_output=True,timeout=10)
 records[tag]={'image_sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'native_stdout_hex':native.stdout.hex(),'native_stderr_hex':native.stderr.hex(),
               'model_steps':step,'final_word':mem[57000],'expected':expected,'writes':events,
               'rea_id':rea['evidence_id'],'rea_steps':n['run']['steps'],'rea_status':n['run']['status'],
               'rea_events_truncated':n['run']['events_truncated'],'rea_writes_match_model':rea_writes==events,
               'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image))}
 assert native.returncode==0 and not native.stdout and mem[57000]==expected and n['run']['status']=='HALTED' and not n['run']['events_truncated'] and rea_writes==events
(P/'code_cell_verification.results.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n')
print(json.dumps(records,indent=2,sort_keys=True))
