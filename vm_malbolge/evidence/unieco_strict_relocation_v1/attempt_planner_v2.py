#!/usr/bin/env python3
"""Experimental Forge preamble installs the compact loop in high memory."""
import hashlib,json,os,pathlib,sys,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];forge=pathlib.Path(os.environ['ISOLATED_FORGE_ROOT']).resolve();sys.path.insert(0,str(forge))
from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1
original=(ROOT/'vm_malbolge/evidence/epoch_dload_inout_v1/compose_inout.mb').read_bytes(); raw=(forge/'reference/malbolge_org/cat.mal').read_bytes(); template=[x for x in raw if 33<=x<=126]
shift=94*624; source_len=len(template)+94*200; clean=template+[33]*(source_len-len(template)); assert source_len<shift+42
values={shift+i:original[i] for i in list(range(42,127))+[143,148]}
values[shift+42]=42
for i in (125,126):values[shift+i]=shift+42
values[shift+143]=shift+62;values[shift+148]=shift+65
start=time.monotonic()
ops=synthesize_preamble_ops(clean,values,shift+125,9003,0,template_clean=template,boot='original')
end=99+len(ops); assert end<=source_len-2,(end,source_len)
out=bytearray(template[:99]);out.extend(33+((XLAT1.index(ch)-pos)%94) for pos,ch in enumerate(ops,99))
while len(out)<source_len-2:out.append(33+((XLAT1.index('o')-len(out))%94))
out.extend(template[-2:]);valid='ji*p</vo';invalid=[i for i,x in enumerate(out) if XLAT1[(x-33+i)%94] not in valid]
result={'shift':shift,'source_len':len(out),'plan_length':len(ops),'plan_end':end,'handoff_c':shift+43,'handoff_d':shift+126,'target_cells':len(values),'invalid_cells':len(invalid),'target_sha256':hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest(),'source_sha256':hashlib.sha256(out).hexdigest(),'tail_bytes':list(out[-2:])}
(P/'candidate.mb').write_bytes(out);(P/'target_cells.json').write_text(json.dumps(values,indent=2,sort_keys=True)+'\n');(P/'plan.ops').write_text(''.join(ops)+'\n');(P/'synthesis.results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
assert not invalid
