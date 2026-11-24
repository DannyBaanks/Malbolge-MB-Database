"""Read-only verification of fixed-depth same-routine reentry and preserved evidence."""
from pathlib import Path
import sys,json,hashlib
pack=Path(sys.argv[1]).resolve();a=pack/'run01';b=pack/'run02'
data=json.loads((a/'results.json').read_text());assert data==json.loads((b/'results.json').read_text())
assert set(data)=={'positive','outer_clobber','bypass_inner'}
for mode,row in data.items():
 for ext in ('mb','plan.json','trace.json','stdout.raw','stderr.raw'):
  assert (a/f'{mode}.{ext}').read_bytes()==(b/f'{mode}.{ext}').read_bytes()
 plan=json.loads((a/f'{mode}.plan.json').read_text());v,w=plan['variables']
 assert v!=w and len({plan['entry'],plan['mix'],plan['dispatch'],plan['resume']})==4
 assert hashlib.sha256((a/f'{mode}.mb').read_bytes()).hexdigest()==row['sha256']
 assert row['native_rc']==0 and row['status']=='halt' and row['clasesbolge_status']=='end'
 assert row['output_hex']==row['clasesbolge_output_hex']==(a/f'{mode}.stdout.raw').read_bytes().hex()
 expected=['B']*3 if mode=='outer_clobber' else ['A','B']*3
 assert row['returns']==expected and not row['tails_changed']
 size=4 if mode=='bypass_inner' else 6
 assert len(row['events'])==size*len(expected)
 for i in range(len(expected)):
  group=row['events'][size*i:size*(i+1)]
  kinds=['entry','body','resume'] if size==4 else ['entry','body','entry','body','resume']
  assert [e['kind'] for e in group]==kinds+['return_'+expected[i]]
  assert group[0]['pc']==plan['entry'] and group[1]['pc']==plan['mix']
  assert group[0]['argument']==v-3 and group[1]['d']==v
  assert group[0]['values']==group[1]['values']
  if size==6:
   assert group[2]['pc']==group[0]['pc'] and group[3]['pc']==group[1]['pc']
   assert group[2]['argument']==w-3 and group[3]['d']==w
   assert group[2]['values']==group[3]['values']
   assert group[3]['values'][0]==group[-2]['values'][0]
   assert all(e['fo']==group[0]['fo'] for e in group[:4])
  assert (group[-2]['fo']==group[0]['fo'])==(mode!='outer_clobber')
  assert group[-2]['values']==group[-1]['values']
 assert len(row['dispatches'])==len(expected)*(2 if size==4 else 3)
 assert all(d['pc']==plan['dispatch'] and d['dispatch_word']==74 for d in row['dispatches'])
 assert len(row['clocks'])==4 and all(c['fo']==c['entry_word']==c['mix_word']==c['dispatch_word']==74 for c in row['clocks'])
 assert all(m['pc']==plan['mix'] for m in row['mutations'])
 if mode=='bypass_inner':assert row['final_values'][1]==23456
 rea=json.loads((a/'rea.json').read_text())[mode];assert rea==json.loads((b/'rea.json').read_text())[mode]
 assert rea['status']=='HALTED' and rea['max_depth']==(1 if size==4 else 2)
 assert rea['capture']['equivalent_runs'] and rea['capture']['contiguous_steps']==row['steps']
 assert len(rea['inner_outer_writes'])==(3 if mode=='outer_clobber' else 0)
 pattern=[(0,1),(1,1),(1,1),(1,0)] if size==4 else [(0,1),(1,1),(1,2),(2,2),(2,1),(1,0)]
 assert [(d['from'],d['to']) for d in rea['depths']]==pattern*len(expected)
 for key in ('steps','output_hex','events','clocks','mutations','dispatches'):assert row[key]==rea[key]
 assert [e['d'] for e in rea['body_events']]==([v] if size==4 else [v,w])*len(expected)
 for e in rea['body_events']:
  variable_writes=[x['position'] for x in e['writes'] if x['position'] in (v,w)]
  assert variable_writes==[e['d']]
for line in (pack/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.sha256((pack/name).read_bytes()).hexdigest()==h,name
print('PASS: same-routine reentry depth 2, separate live contexts, common dispatcher, controls, reproducibility and hashes')
