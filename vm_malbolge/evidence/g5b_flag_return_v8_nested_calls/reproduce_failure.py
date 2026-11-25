"""Reconstruct the first failed layout without modifying its preserved evidence."""
import pathlib,sys,json
from probe import Nested,trace
out=pathlib.Path(sys.argv[1]);out.mkdir(exist_ok=False,parents=True)
plan=Nested('positive');old=plan.loop+2
plan.code.pop(plan.bridge);plan.bridge=old
import probe
plan.code[old]=probe.p.encode(4,old)
for address in (44009,44011,44012,44013):plan.values.pop(address)
plan.values.update({44003:old-1,44010:plan.out-1,44012:plan.out,44013:plan.entry-1,44014:40997});plan.a_cont=44010
image=plan.assemble();(out/'positive.mb').write_bytes(image)
result=trace(image,plan);(out/'trace.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['status']=='frozen' and result['tails_changed']
print('REPRODUCED: initial layout freezes and changes JMP tail')
