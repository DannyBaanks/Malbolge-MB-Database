"""Read-only audit of P7 evidence: two independent builds, four execution engines and hashes."""
from pathlib import Path
import hashlib,json,sys
pack=Path(sys.argv[1]).resolve()
expected_modes={'positive','control_first','control_second','swapped'}
data=json.loads((pack/'run01/results.json').read_text())
assert set(data)==expected_modes
for mode,row in data.items():
 for suffix in ('mb','plan.json','stdout.raw','stderr.raw'):
  name=f'{mode}.{suffix}'
  assert (pack/'run01'/name).read_bytes()==(pack/'run02'/name).read_bytes(),name
 assert row==json.loads((pack/'run02/results.json').read_text())[mode]
 assert hashlib.sha256((pack/'run01'/f'{mode}.mb').read_bytes()).hexdigest()==row['sha256']
 plan=json.loads((pack/'run01'/f'{mode}.plan.json').read_text())
 assert row['native_rc']==0 and row['clasesbolge_status']=='end' and row['status']=='halt'
 assert row['returns']==['A','B']*3 and len(row['calls'])==6 and len(row['clocks'])==4
 assert row['write_sites']==[plan['mix']] and not row['tail_changed']
 assert all(c['flag']==c['mix']==74 for c in row['clocks'])
 assert [c['d'] for c in row['calls']]==plan['selection']
 assert row['clocks'][0]['values']==[12345,23456]
 for i,call in enumerate(row['calls']):
  chosen=plan['variables'].index(call['d']); other=1-chosen
  assert call['before'][other]==call['after'][other]
  assert call['before']==([12345,23456] if i==0 else row['calls'][i-1]['after'])
 assert row['final_values']==row['calls'][-1]['after']
 assert all(m['pc']==plan['mix'] for m in row['mutations'])
 assert (pack/'run01'/f'{mode}.stdout.raw').read_bytes().hex()==row['output_hex']
 rea=json.loads((pack/'run01/rea.json').read_text())[mode]
 assert rea==json.loads((pack/'run02/rea.json').read_text())[mode]
 assert rea['status']=='HALTED' and rea['all_events_retained']
 for key in ('steps','output_hex','calls','clocks','returns','mutations','final_values'): assert row[key]==rea[key],(mode,key)
assert data['control_first']['final_values'][0]==12345
assert data['control_second']['final_values'][1]==23456
assert all(data[m]['output_hex']!=data['positive']['output_hex'] for m in expected_modes-{'positive'})
for line in (pack/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1); assert hashlib.sha256((pack/name).read_bytes()).hexdigest()==h,name
print('PASS: P7 four cases, variable isolation, persistent state, returns, deterministic builds and hashes')
