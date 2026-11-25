"""Audit the exact Python output and the autonomous Malbolge CALL/body/RET."""
from pathlib import Path
import sys,json,hashlib
p=Path(sys.argv[1]).resolve();a=p/'run02';b=p/'run03'
data=json.loads((a/'results.json').read_text());assert data==json.loads((b/'results.json').read_text())
assert (a/'python.stdout.raw').read_bytes()==(b/'python.stdout.raw').read_bytes()==b'Hola\n'
assert set(data)=={'saludar','alternate','broken_return','bypass'}
bodies=[]
for mode,row in data.items():
 for ext in ('mb','plan.json','trace.json','stdout.raw','stderr.raw'):assert (a/f'{mode}.{ext}').read_bytes()==(b/f'{mode}.{ext}').read_bytes()
 plan=json.loads((a/f'{mode}.plan.json').read_text());image=(a/f'{mode}.mb').read_bytes()
 assert hashlib.sha256(image).hexdigest()==row['sha256']
 assert all(33<=v<=126 and (v+i)%94 in {4,5,23,39,40,62,68,81} for i,v in enumerate(image))
 assert row['native_rc']==0 and row['status']=='halt' and row['clasesbolge_status']=='end'
 assert row['output_hex']==row['clasesbolge_output_hex']==(a/f'{mode}.stdout.raw').read_bytes().hex()
 rea=json.loads((a/'rea.json').read_text())[mode];assert rea==json.loads((b/'rea.json').read_text())[mode]
 assert rea['status']=='HALTED' and rea['capture']['contiguous_steps']==row['steps'] and rea['capture']['equivalent_runs']
 for key in ('steps','output_hex','events','jumps','writes','final_slot','final_journal'):assert rea[key]==row[key]
 kinds=[e['kind'] for e in row['events']]
 if mode in ('saludar','alternate'):
  assert row['output_hex']==b'Hola\n'.hex()
  assert [j['next_pc'] for j in row['jumps']]==[plan['function'],plan['continuation']]
  assert [j['d'] for j in row['jumps']]==[plan['call_pointer'],plan['slot']]
  assert row['jumps'][1]['stored']==plan['continuation']-1
  prints=[e for e in row['events'] if e['kind'].startswith('print_')]
  assert [e['a']%256 for e in prints]==list(b'Hola\n')
  assert all(plan['function']<=e['pc']<plan['function_end'] for e in prints)
  assert kinds[-3:]==['ret','after_call','finished']
  assert row['final_slot']==row['final_journal']==29524
  bodies.append(image[plan['function']:plan['function_end']])
 elif mode=='broken_return':
  assert row['output_hex']==b'Hola\n!'.hex() and row['jumps'][1]['next_pc']==29525 and 'after_call' not in kinds
 else:assert row['output_hex']=='' and 'saludar_entry' not in kinds and 'ret' not in kinds
assert bodies[0]==bodies[1]
for line in (p/'hashes.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert hashlib.sha256((p/name).read_bytes()).hexdigest()==h,name
print('PASS: Python-equivalent Hola LF, separate function CALL/RET, alternate continuation, controls, four engines and hashes')
