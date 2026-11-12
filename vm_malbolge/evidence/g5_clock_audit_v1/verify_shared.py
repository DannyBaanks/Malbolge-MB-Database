#!/usr/bin/env python3
"""Compare phase-shared code executions and data writes across engines."""
import hashlib,importlib.util,json,pathlib,resource,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';resource.setrlimit(resource.RLIMIT_CORE,(0,0));records={};H=58456
for tag in ('positive','control'):
 image=(P/('shared_'+tag+'.mb')).read_bytes();mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=0;events=[];visits=[];inputs=0
 for step in range(1,5001):
  if not 33<=mem[c]<=126:raise AssertionError('nonprintable PC')
  pc=c;op=(mem[c]+c)%94;event={'step':step,'position':c,'opcode':op,'a':a,'d':d,'writes':[]}
  if c==H:visits.append({'step':step,'value':mem[c],'opcode':op,'d':d,'a':a})
  if op==4:
   c=mem[d]
   if not 33<=mem[c]<=126:raise AssertionError('nonprintable jump destination')
  elif op==5:raise AssertionError('unexpected output')
  elif op==23:inputs+=1
  elif op==39:
   old=mem[d];mem[d]=se.rot(old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==40:d=mem[d]
  elif op==62:
   old=mem[d];mem[d]=se.crazy(a,old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==81:
   if step>=2000:events.append(event)
   break
  if 33<=mem[c]<=126:
   old=mem[c];mem[c]=se.encrypt(old);event['writes'].append({'position':c,'value_before':old,'value_after':mem[c]})
  if step>=2000:events.append(event)
  c=(c+1)%N;d=(d+1)%N
 else:raise AssertionError('budget')
 rea=json.loads((P/('rea_shared_'+tag+'.redacted.json')).read_text());n=rea['normalized_result'];rea_events=[{k:e[k] for k in ('step','position','opcode','a','d','writes')} for e in n['events']]
 native=subprocess.run([str(OL),str(P/('shared_'+tag+'.mb'))],input=b'',capture_output=True,timeout=10)
 target_writes=[{'step':e['step'],**w} for e in events if e['position']==H and e['opcode']==62 for w in e['writes'] if w['position']!=H]
 expected_opcodes=[62,58]*3 if tag=='positive' else [58,62]*3
 expected_targets=[57000,57004,57008] if tag=='positive' else [57002,57006,57010]
 records[tag]={'image_sha256':hashlib.sha256(image).hexdigest(),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
   'native_rc':native.returncode,'native_stdout_hex':native.stdout.hex(),'native_stderr_hex':native.stderr.hex(),
   'scratch_steps':step,'inputs':inputs,'visits':visits,'target_writes':target_writes,
   'rea_id':rea['evidence_id'],'rea_steps':n['run']['steps'],'rea_status':n['run']['status'],
   'rea_event_start':rea['parameters']['event_start_step'],'rea_events_truncated':n['run']['events_truncated'],
   'window_events':len(events),'window_equal':rea_events==events,'window_through_halt':events[-1]['opcode']==81}
 assert native.returncode==0 and not native.stdout and inputs==0 and [v['opcode'] for v in visits]==expected_opcodes and [w['position'] for w in target_writes]==expected_targets and all(w['value_after']!=w['value_before'] for w in target_writes) and rea_events==events and n['run']['status']=='HALTED' and n['run']['steps']==step
(P/'shared_verification.results.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n');print(json.dumps(records,indent=2,sort_keys=True))
