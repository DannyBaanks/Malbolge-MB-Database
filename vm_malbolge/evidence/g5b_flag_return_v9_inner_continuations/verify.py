"""Read-only verification of P9 evidence and its content hashes."""
from pathlib import Path
import json,hashlib,sys
pack=Path(sys.argv[1]).resolve();a=pack/'run01';b=pack/'run02'
data=json.loads((a/'results.json').read_text());assert data==json.loads((b/'results.json').read_text())
assert set(data)=={'positive','inner_misselected','outer_clobber'}
for mode,row in data.items():
 for ext in ('mb','plan.json','trace.json','stdout.raw','stderr.raw'):
  assert (a/f'{mode}.{ext}').read_bytes()==(b/f'{mode}.{ext}').read_bytes()
 plan=json.loads((a/f'{mode}.plan.json').read_text())
 assert plan['after_x']!=plan['after']
 assert hashlib.sha256((a/f'{mode}.mb').read_bytes()).hexdigest()==row['sha256']
 assert row['native_rc']==0 and row['status']=='halt' and row['clasesbolge_status']=='end'
 assert row['output_hex']==row['clasesbolge_output_hex']==(a/f'{mode}.stdout.raw').read_bytes().hex()
 expected=['B']*3 if mode=='outer_clobber' else ['A','B']*3
 assert row['returns']==expected and not row['tails_changed']
 size=4 if mode=='inner_misselected' else 6;combinations=set()
 assert len(row['events'])==size*len(expected)
 for i in range(len(expected)):
  group=row['events'][i*size:(i+1)*size]
  kinds=['outer_entry','inner_entry','inner_return_Y'] if size==4 else ['outer_entry','inner_entry','inner_return_X','inner_entry','inner_return_Y']
  assert [e['kind'] for e in group]==kinds+['outer_return_'+expected[i]]
  for j in range(1,size-1,2):
   inner,after=group[j:j+2];combinations.add((expected[i],after['kind'][-1]))
   assert inner['fo']==group[0]['fo']
   assert (inner['fo']==after['fo'])==(mode!='outer_clobber' or after['kind']=='inner_return_X')
   assert after['fi']==74 and inner['fi']==(70 if after['kind']=='inner_return_X' else 74)
 if mode=='positive':assert combinations=={('A','X'),('A','Y'),('B','X'),('B','Y')}
 assert len(row['clocks'])==4 and all(c['fo']==c['fi']==c['mix']==74 for c in row['clocks'])
 assert all(m['pc']==plan['mix'] for m in row['mutations'])
 rea=json.loads((a/'rea.json').read_text())[mode];assert rea==json.loads((b/'rea.json').read_text())[mode]
 assert rea['status']=='HALTED' and rea['all_events_retained']
 assert rea['capture']['equivalent_runs'] and rea['capture']['contiguous_steps']==row['steps']
 assert rea['capture']['prefix_range'][1]>=rea['capture']['suffix_range'][0]
 assert len(rea['inner_outer_writes'])==(len(expected) if mode=='outer_clobber' else 0)
 pattern=[(0,1),(1,2),(2,1),(1,0)] if size==4 else [(0,1),(1,2),(2,1),(1,2),(2,1),(1,0)]
 assert [(d['from'],d['to']) for d in rea['depths']]==pattern*len(expected)
 for key in ('steps','output_hex','events','clocks','mutations'):assert row[key]==rea[key]
 assert len(rea['site_events'])==(6 if mode!='positive' else 12)
for line in (pack/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.sha256((pack/name).read_bytes()).hexdigest()==h,name
print('PASS: P9 two inner continuations under both outer returns, controls, complete REA coverage, reproducibility and hashes')
