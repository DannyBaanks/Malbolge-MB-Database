#!/usr/bin/env python3
"""Cross-check native execution and REA window against separate scratch tracer."""
import hashlib,importlib.util,json,pathlib,resource,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';resource.setrlimit(resource.RLIMIT_CORE,(0,0));records={}
for tag in ('positive','control'):
 image=(P/('multi_v4_'+tag+'.mb')).read_bytes();mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=0;events=[];jump_destinations=[]
 for step in range(1,8001):
  if not 33<=mem[c]<=126:raise AssertionError('nonprint pc')
  pc=c;op=(mem[c]+c)%94;event={'step':step,'position':c,'opcode':op,'a':a,'d':d,'writes':[]}
  if op in (23,5):raise AssertionError('unexpected IO')
  if op==4:
   c=mem[d];jump_destinations.append({'step':step,'target_before_increment':c,'cell':mem[c]})
   if not 33<=mem[c]<=126:raise AssertionError('Olmstead would encrypt a nonprintable jump target')
  elif op==39:
   old=mem[d];mem[d]=se.rot(old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==40:d=mem[d]
  elif op==62:
   old=mem[d];mem[d]=se.crazy(a,old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==81:
   if step>=7000:events.append(event)
   break
  if 33<=mem[c]<=126:
   old=mem[c];mem[c]=se.encrypt(old);event['writes'].append({'position':c,'value_before':old,'value_after':mem[c]})
  if step>=7000:events.append(event)
  c=(c+1)%N;d=(d+1)%N
 else:raise AssertionError('max steps')
 rea=json.loads((P/('rea_v4_'+tag+'.redacted.json')).read_text());n=rea['normalized_result']
 rea_events=[{k:e[k] for k in ('step','position','opcode','a','d','writes')} for e in n['events']]
 visits=[{'step':e['step'],'pc':e['position'],'opcode':e['opcode']} for e in events if e['position'] in (58550,58573,58585)]
 expected=[(58550,62),(58550,62 if tag=='positive' else 21),(58573,62),(58573,62),(58585,39),(58585,39)]
 native=subprocess.run([str(OL),str(P/('multi_v4_'+tag+'.mb'))],input=b'',capture_output=True,timeout=10)
 records[tag]={'image_sha256':hashlib.sha256(image).hexdigest(),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
               'native_rc':native.returncode,'native_stdout_hex':native.stdout.hex(),'native_stderr_hex':native.stderr.hex(),
               'scratch_steps':step,'rea_id':rea['evidence_id'],'rea_steps':n['run']['steps'],'rea_status':n['run']['status'],
               'rea_event_start':rea['parameters']['event_start_step'],'rea_events_truncated':n['run']['events_truncated'],
               'window_events':len(events),'window_complete_through_halt':bool(events) and events[-1]['opcode']==81,
               'rea_window_equals_scratch':rea_events==events,'visits':visits,'jump_targets_printable':True,
               'target_writes':[{'step':e['step'],**w} for e in events for w in e['writes'] if w['position'] in (58550,58573,58585)]}
 assert [(v['pc'],v['opcode']) for v in visits]==expected and native.returncode==0 and not native.stdout and n['run']['status']=='HALTED' and rea_events==events and n['run']['steps']==step
(P/'verification_v4.results.json').write_text(json.dumps(records,sort_keys=True,indent=2)+'\n');print(json.dumps(records,sort_keys=True,indent=2))
