"""Read-only audit of numeric save/restore and actual indirect jump targets."""
from pathlib import Path
import sys,json,hashlib
p=Path(sys.argv[1]).resolve();a=p/'run01';b=p/'run02'
data=json.loads((a/'results.json').read_text());assert data==json.loads((b/'results.json').read_text())
assert set(data)=={'positive','skip_restore','tamper_slot'}
for mode,row in data.items():
 for ext in ('mb','plan.json','trace.json','stdout.raw','stderr.raw'):assert (a/f'{mode}.{ext}').read_bytes()==(b/f'{mode}.{ext}').read_bytes()
 plan=json.loads((a/f'{mode}.plan.json').read_text());image=(a/f'{mode}.mb').read_bytes()
 assert hashlib.sha256(image).hexdigest()==row['sha256']
 assert all(33<=v<=126 and (v+i)%94 in {4,5,23,39,40,62,68,81} for i,v in enumerate(image))
 assert row['native_rc']==0 and row['status']=='halt' and row['clasesbolge_status']=='end'
 assert row['output_hex']==row['clasesbolge_output_hex']==(a/f'{mode}.stdout.raw').read_bytes().hex()==('ABC' if mode=='positive' else 'E').encode().hex()
 rea=json.loads((a/'rea.json').read_text())[mode];assert rea==json.loads((b/'rea.json').read_text())[mode]
 assert rea['status']=='HALTED' and rea['capture']['contiguous_steps']==row['steps'] and rea['capture']['equivalent_runs']
 for key in ('steps','output_hex','events','jumps','writes','final_slot','final_journal'):assert rea[key]==row[key]
 assert all(j['d']==plan['slot'] and j['next_pc']==(j['stored']+1)%59049 for j in row['jumps'])
 if mode=='positive':
  assert [j['next_pc'] for j in row['jumps']]==plan['targets']
  for i,target in enumerate(plan['targets']):
   e={x['kind']:x for x in row['events'] if x['index']==i};value=target-1
   assert e['source_loaded']['a']==value and e['source_loaded']['sources'][i]==value
   assert e['begin']['slot']==e['begin']['journal']==29524
   assert e['slot_written']['slot']==value and e['clobbered']['slot']==29524
   assert e['journal_saved']['journal']==e['clobbered']['journal']==e['journal_loaded']['a']==e['journal_loaded']['journal']
   assert e['restored']['slot']==e['read_back']['slot']==e['read_back']['a']==e['indirect_jump']['slot']==value
   assert e['continuation_'+chr(65+i)]['pc']==target
   assert e['rearmed']['slot']==e['rearmed']['journal']==29524
  assert row['final_slot']==row['final_journal']==29524
 else:
  assert len(row['jumps'])==1
  assert row['jumps'][0]['next_pc']==(29525 if mode=='skip_restore' else 26350)
for run in (a,b):
 algebra=json.loads((run/'algebra.json').read_text());assert algebra==json.loads((run/'algebra_rea.json').read_text())
 assert algebra=={'word_count':59049,'mask':29524,'double_crazy_identity':True}
for line in (p/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.sha256((p/name).read_bytes()).hexdigest()==h,name
print('PASS: numeric slot/journal reuse, exact recovery, three physical indirect returns, controls, four engines and hashes')
