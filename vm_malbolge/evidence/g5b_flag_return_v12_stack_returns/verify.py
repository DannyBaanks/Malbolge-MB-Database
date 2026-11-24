"""Read-only audit: abstract LIFO tokens must select the physical R continuations."""
from pathlib import Path
import json,sys,hashlib
p=Path(sys.argv[1]).resolve();a=p/'run01';b=p/'run02'
data=json.loads((a/'results.json').read_text());assert data==json.loads((b/'results.json').read_text())
expected={'positive':'AB','tamper_outer':'B','wrong_slot':'AE','overflow_call':'O','underflow_return':'U'}
assert set(data)==set(expected)
for mode,row in data.items():
 for ext in ('mb','plan.json','trace.json','stdout.raw','stderr.raw'):assert (a/f'{mode}.{ext}').read_bytes()==(b/f'{mode}.{ext}').read_bytes()
 plan=json.loads((a/f'{mode}.plan.json').read_text());image=(a/f'{mode}.mb').read_bytes()
 assert 'fo' not in plan
 assert hashlib.sha256(image).hexdigest()==row['sha256']
 assert all(33<=v<=126 and (v+i)%94 in {4,5,23,39,40,62,68,81} for i,v in enumerate(image))
 assert row['native_rc']==0 and row['status']=='halt' and row['clasesbolge_status']=='end' and not row['tails_changed']
 assert row['output_hex']==row['clasesbolge_output_hex']==(a/f'{mode}.stdout.raw').read_bytes().hex()==expected[mode].encode().hex()
 rea=json.loads((a/'rea.json').read_text())[mode];assert rea==json.loads((b/'rea.json').read_text())[mode]
 assert rea['status']=='HALTED' and rea['capture']['contiguous_steps']==row['steps'] and rea['capture']['equivalent_runs']
 for key in ('steps','output_hex','events','changes','mutations','final'):assert row[key]==rea[key]
 assert len([x for x in rea['pops'] if not x['matches_catalog']])==(1 if mode=='wrong_slot' else 0)
 assert all(m['pc']==plan['mix'] for m in row['mutations'])
 for event in rea['body_events']:
  snapshot=next(e for e in row['events'] if e['step']==event['step'])
  assert event['d']==plan['variables'][snapshot['depth']-1]
  assert [w['position'] for w in event['writes'] if w['position'] in plan['variables']]==[event['d']]
 if mode=='positive':
  stack=[];pending=None;live=0;returns=[]
  for e in row['events']:
   if e['kind'].startswith('after_push'):
    stack.append('B' if e['kind']=='after_push_B' else 'A')
   elif e['kind']=='r_entry':
    live+=1;assert e['pc']==plan['r_entry'] and live==e['depth']
   elif e['kind']=='body':assert e['pc']==plan['mix'] and live==e['depth']
   elif e['kind']=='pop':
    assert pending is None and stack
    token=stack[-1];pending='resume' if len(stack)==2 and token=='A' else 'return_'+token
   elif e['kind'] in ('resume','return_A','return_B'):
    assert e['kind']==pending;pending=None;stack.pop();live-=1;returns.append(e['kind'])
   assert e['depth']==len(stack) and e['slots'][:e['depth']]==stack
  assert stack==[] and pending is None and live==0
  assert returns==['resume','return_A','resume','return_B']
  assert [(x['depth'],x['token'],x['actual_target']) for x in rea['pops']]==[(2,'A','resume'),(1,'A','return_A'),(2,'A','resume'),(1,'B','return_B')]
 if mode=='tamper_outer':
  pushed=next(e for e in row['events'] if e['kind']=='after_push_A');entry=next(e for e in row['events'] if e['kind']=='r_entry')
  assert pushed['slots'][0]=='A' and entry['slots'][0]=='B'
  assert any(pushed['step']<c['step']<entry['step'] and c['before'][2]!=c['after'][2] for c in row['changes'])
 if mode in ('overflow_call','underflow_return'):
  event=next(e for e in row['events'] if e['kind']=='emit_'+expected[mode]);index=row['events'].index(event)
  previous=next(e for e in reversed(row['events'][:index]) if e['kind'] in ('push_inner','pop'))
  for key in ('flags','values'):assert previous[key]==event[key]==row['final'][key]
  assert row['final']['depth']==(2 if mode=='overflow_call' else 0)
for line in (p/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.sha256((p/name).read_bytes()).hexdigest()==h,name
print('PASS: runtime LIFO selects actual nested R returns, tamper/wrong-slot controls, guards, reproducibility and hashes')
