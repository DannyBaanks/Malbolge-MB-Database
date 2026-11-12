#!/usr/bin/env python3
"""Cross-check one-cell shared restoration, control and residual state."""
import hashlib,importlib.util,json,pathlib,resource,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';resource.setrlimit(resource.RLIMIT_CORE,(0,0));records={};T=57100;primitive=[58057,58152,58268];clock=58303
for tag,expected in [('positive',40),('control',39)]:
 image=(P/('restore_'+tag+'.mb')).read_bytes();target={int(k):v for k,v in json.loads((P/('restore_'+tag+'_targets.json')).read_text()).items()};mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=0;events=[];inputs=[];outputs=[];initial=None;visits=[]
 for step in range(1,5001):
  if not 33<=mem[c]<=126:raise AssertionError('nonprintable PC')
  op=(mem[c]+c)%94;event={'step':step,'position':c,'opcode':op,'a':a,'d':d,'writes':[]}
  if c==primitive[0] and initial is None:
   mismatches=[{'address':i,'expected':v,'actual':mem[i]} for i,v in target.items() if mem[i]!=v]
   initial={'step':step,'target':mem[T],'primitive_words':{str(i):mem[i] for i in primitive},'clock':mem[clock],'constant':mem[57200],'mismatches':mismatches}
  if c in primitive+[clock]:visits.append({'step':step,'pc':c,'opcode':op,'d':d,'a':a})
  if op==4:
   c=mem[d]
   if not 33<=mem[c]<=126:raise AssertionError('nonprintable jump destination under Olmstead')
  elif op==5:outputs.append(a%256)
  elif op==23:inputs.append(step)
  elif op==39:
   old=mem[d];mem[d]=se.rot(old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==40:d=mem[d]
  elif op==62:
   old=mem[d];mem[d]=se.crazy(a,old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==81:
   if step>=3200:events.append(event)
   break
  if 33<=mem[c]<=126:
   old=mem[c];mem[c]=se.encrypt(old);event['writes'].append({'position':c,'value_before':old,'value_after':mem[c]})
  if step>=3200:events.append(event)
  c=(c+1)%N;d=(d+1)%N
 else:raise AssertionError('budget')
 rea=json.loads((P/('rea_'+tag+'.redacted.json')).read_text());n=rea['normalized_result'];rea_events=[{k:e[k] for k in ('step','position','opcode','a','d','writes')} for e in n['events']]
 native=subprocess.run([str(OL),str(P/('restore_'+tag+'.mb'))],input=b'',capture_output=True,timeout=10)
 target_writes=[{'step':e['step'],**w} for e in events for w in e['writes'] if w['position']==T]
 final={'target':mem[T],'primitive_words':{str(i):mem[i] for i in primitive},'clock':mem[clock],'constant':mem[57200]}
 records[tag]={'image_sha256':hashlib.sha256(image).hexdigest(),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
               'native_rc':native.returncode,'native_stdout_hex':native.stdout.hex(),'native_stderr_hex':native.stderr.hex(),
               'scratch_steps':step,'initial':initial,'final':final,'inputs':inputs,'outputs':outputs,
               'visits':visits,'target_writes':target_writes,'rea_id':rea['evidence_id'],'rea_steps':n['run']['steps'],
               'rea_status':n['run']['status'],'rea_start':rea['parameters']['event_start_step'],
               'rea_events_truncated':n['run']['events_truncated'],'window_events':len(events),'rea_window_equals_scratch':rea_events==events,
               'window_complete_through_halt':bool(events) and events[-1]['opcode']==81}
 assert initial is not None and initial['target']==70 and not initial['mismatches'] and final['target']==expected
 assert [w['value_after'] for w in target_writes]==([60,29524,29484,40] if tag=='positive' else [60,29524,29485,39])
 assert final['primitive_words']==initial['primitive_words'] and final['clock']!=initial['clock'] and final['constant']!=initial['constant']
 assert not inputs and not outputs and native.returncode==0 and not native.stdout and n['run']['status']=='HALTED' and n['run']['steps']==step and events==rea_events
(P/'verification.results.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n');print(json.dumps(records,indent=2,sort_keys=True))
