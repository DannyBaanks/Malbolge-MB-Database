"""Read-only audit of nested-call evidence, controls, reproduction and hashes."""
from pathlib import Path
import json,hashlib,sys
pack=Path(sys.argv[1]).resolve()
left=pack/'run04';right=pack/'run05'
data=json.loads((left/'results.json').read_text())
assert data==json.loads((right/'results.json').read_text())
for mode,row in data.items():
 for ext in ('mb','plan.json','trace.json','stdout.raw','stderr.raw'):
  assert (left/f'{mode}.{ext}').read_bytes()==(right/f'{mode}.{ext}').read_bytes()
 plan=json.loads((left/f'{mode}.plan.json').read_text())
 assert hashlib.sha256((left/f'{mode}.mb').read_bytes()).hexdigest()==row['sha256']
 assert row['native_rc']==0 and row['clasesbolge_status']=='end' and row['status']=='halt'
 assert row['clasesbolge_output_hex']==row['output_hex']==(left/f'{mode}.stdout.raw').read_bytes().hex()
 expected=['A','B']*3 if mode=='positive' else ['B']*3
 assert row['returns']==expected and not row['tails_changed']
 assert len(row['events'])==4*len(expected)
 for offset in range(0,len(row['events']),4):
  entry,inner,after,ret=row['events'][offset:offset+4]
  assert [e['kind'] for e in (entry,inner,after)]==['outer_entry','inner_entry','inner_return']
  assert ret['kind']=='outer_return_'+expected[offset//4]
  assert entry['fo']==inner['fo'] and ((after['fo']==inner['fo'])==(mode!='outer_clobber'))
  assert entry['fi']==inner['fi']==after['fi']==74
 assert len(row['clocks'])==4 and all(c['fo']==c['fi']==c['mix']==74 for c in row['clocks'])
 assert all(m['pc']==plan['mix'] for m in row['mutations'])
 rea=json.loads((left/'rea.json').read_text())[mode]
 assert rea==json.loads((right/'rea.json').read_text())[mode]
 assert rea['status']=='HALTED' and rea['all_events_retained']
 assert len(rea['inner_outer_writes'])==(len(expected) if mode=='outer_clobber' else 0)
 assert [(d['from'],d['to']) for d in rea['depths']]==[(0,1),(1,2),(2,1),(1,0)]*len(expected)
 for key in ('steps','output_hex','events','clocks','mutations'):assert row[key]==rea[key]
assert (pack/'run01/positive.mb').read_bytes()==(pack/'failure_replay/positive.mb').read_bytes()
assert json.loads((pack/'run01/failed.trace.json').read_text())['status']=='frozen'
for line in (pack/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.sha256((pack/name).read_bytes()).hexdigest()==h,name
print('PASS: nested calls at depth 2, outer-state preservation, controls, deterministic builds, failure replay and hashes')
