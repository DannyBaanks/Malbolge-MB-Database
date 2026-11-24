"""Check reproducibility, recorded execution, and SHA-256. Run after probe.py and rea.mjs."""
from pathlib import Path
import sys,json,hashlib
p=Path(sys.argv[1]).resolve()
for mode in ('positive','control_a','control_b'):
 for ext in ('mb','plan.json','stdout.raw','stderr.raw'):
  name=f'{mode}.{ext}'
  assert (p/'run01'/name).read_bytes()==(p/'run02'/name).read_bytes(),name
r=json.loads((p/'run01/results.json').read_text())
rea=json.loads((p/'run01/rea.json').read_text())
assert r['positive']['returns']==['A','B']*3
for mode in r:
 assert r[mode]['output_hex']==rea[mode]['output_hex']
 assert r[mode]['returns']==rea[mode]['returns']
 assert r[mode]['steps']==rea[mode]['steps']
 assert r[mode]['native_rc']==0 and r[mode]['status']=='halt' and r[mode]['clasesbolge_status']=='end'
for row in (p/'hashes.sha256').read_text().splitlines():
 h,name=row.split('  ',1); assert hashlib.sha256((p/name).read_bytes()).hexdigest()==h,name
print('PASS: reproducible images, three modes, REA agreement, all hashes')
