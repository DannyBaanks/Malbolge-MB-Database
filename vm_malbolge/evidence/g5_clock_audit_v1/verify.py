#!/usr/bin/env python3
"""Verify orbit clock against scratch, REA source window and Olmstead."""
import hashlib,importlib.util,json,pathlib,resource,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049;OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead';resource.setrlimit(resource.RLIMIT_CORE,(0,0));records={}
for tag in ('positive','control'):
 image=(P/('clock_'+tag+'.mb')).read_bytes();mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
 a=c=d=0;events=[];visits=[];out=bytearray();inputs=0
 for step in range(1,5001):
  if not 33<=mem[c]<=126:raise AssertionError('nonprintable PC')
  pc=c;op=(mem[c]+c)%94;event={'step':step,'position':c,'opcode':op,'a':a,'d':d,'writes':[]}
  if c==58470:visits.append({'step':step,'value':mem[c],'opcode':op,'d':d})
  if op==4:
   c=mem[d]
   if not 33<=mem[c]<=126:raise AssertionError('nonprintable Olmstead jump target')
  elif op==5:out.append(a%256)
  elif op==23:inputs+=1
  elif op==39:
   old=mem[d];mem[d]=se.rot(old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==40:d=mem[d]
  elif op==62:
   old=mem[d];mem[d]=se.crazy(a,old);a=mem[d];event['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
  elif op==81:
   if step>=2600:events.append(event)
   break
  if 33<=mem[c]<=126:
   old=mem[c];mem[c]=se.encrypt(old);event['writes'].append({'position':c,'value_before':old,'value_after':mem[c]})
  if step>=2600:events.append(event)
  c=(c+1)%N;d=(d+1)%N
 else:raise AssertionError('budget exceeded')
 rea=json.loads((P/('rea_'+tag+'.redacted.json')).read_text());n=rea['normalized_result'];rea_events=[{k:e[k] for k in ('step','position','opcode','a','d','writes')} for e in n['events']]
 native=subprocess.run([str(OL),str(P/('clock_'+tag+'.mb'))],input=b'',capture_output=True,timeout=10)
 records[tag]={'image_sha256':hashlib.sha256(image).hexdigest(),'strict_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
    'model_steps':step,'visits':visits,'input_instructions':inputs,'scratch_output_hex':out.hex(),
    'rea_id':rea['evidence_id'],'rea_steps':n['run']['steps'],'rea_status':n['run']['status'],
    'rea_start':rea['parameters']['event_start_step'],'rea_events_truncated':n['run']['events_truncated'],
    'rea_window_events':len(events),'rea_window_equals_scratch':rea_events==events,
    'native_rc':native.returncode,'native_output_hex':native.stdout.hex(),'native_stderr_hex':native.stderr.hex()}
 expect_values=[66,62,76,79] if tag=='positive' else [66,62]
 expect_output=bytes([166])*(3 if tag=='positive' else 1)
 assert [v['value'] for v in visits]==expect_values and native.returncode==0 and bytes(out)==native.stdout==expect_output and not inputs and n['run']['status']=='HALTED' and n['run']['steps']==step and rea_events==events
(P/'verification.results.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n');print(json.dumps(records,indent=2,sort_keys=True))
