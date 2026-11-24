"""Read-only audit against a Python list stack, independent of the native flag graph."""
from pathlib import Path
import json,sys,hashlib
p=Path(sys.argv[1]).resolve();a=p/'run04';b=p/'run05'
data=json.loads((a/'results.json').read_text());assert data==json.loads((b/'results.json').read_text())
assert set(data)=={c+'__positive' for c in ('lifo','reuse','reuse_top','overflow','underflow')}|{'lifo__no_push_depth','lifo__wrong_slot'}
for label,row in data.items():
 for ext in ('mb','plan.json','trace.json','stdout.raw','stderr.raw'):assert (a/f'{label}.{ext}').read_bytes()==(b/f'{label}.{ext}').read_bytes()
 plan=json.loads((a/f'{label}.plan.json').read_text());image=(a/f'{label}.mb').read_bytes()
 assert hashlib.sha256(image).hexdigest()==row['sha256']
 assert all(33<=v<=126 and (v+i)%94 in {4,5,23,39,40,62,68,81} for i,v in enumerate(image))
 assert row['status']=='halt' and row['native_rc']==0 and row['clasesbolge_status']=='end' and not row['tails_changed']
 assert row['output_hex']==row['clasesbolge_output_hex']==(a/f'{label}.stdout.raw').read_bytes().hex()
 assert len(row['operations'])==len(plan['script'])
 stack=[];expected=[];failures=[]
 for i,(op,token) in enumerate(plan['script']):
  before=row['operations'][i];after=row['operations'][i+1] if i+1<len(plan['script']) else row['final']
  if before['depth']!=len(stack) or before['slots'][:before['depth']]!=stack:failures.append((i,'before'))
  if op=='push':
   emitted='O' if len(stack)==2 else None
   if emitted is None:stack.append(token)
  else:emitted=stack.pop() if stack else 'U'
  if after['depth']!=len(stack) or after['slots'][:after['depth']]!=stack:failures.append((i,'after'))
  actual=[e['char'] for e in row['emissions'] if e['index']==i]
  if actual!=([emitted] if emitted else []):failures.append((i,'emission'))
  if row['mode']=='positive':
   assert 0<=before['depth']<=2 and 0<=after['depth']<=2
   if emitted in ('O','U'):assert before['flags']==after['flags']
  if emitted:expected.append(emitted)
 if row['mode']=='positive':
  assert not failures and not row['specification']['failures']
  assert row['output_hex']==''.join(expected).encode().hex()
 else:assert failures and row['specification']['failures']
 rea=json.loads((a/'rea.json').read_text())[label];assert rea==json.loads((b/'rea.json').read_text())[label]
 assert rea['status']=='HALTED' and rea['capture']['contiguous_steps']==row['steps'] and rea['capture']['equivalent_runs']
 assert rea['flag_reads'] and row['changes']
 for key in ('steps','output_hex','operations','emissions','changes','final'):assert rea[key]==row[key]
assert '70745' in (p/'run01.stderr.raw.txt').read_text()
for line in (p/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.sha256((p/name).read_bytes()).hexdigest()==h,name
print('PASS: bounded runtime token stack, LIFO, both-slot reuse, unchanged overflow/underflow, negative controls, four-engine parity and hashes')
