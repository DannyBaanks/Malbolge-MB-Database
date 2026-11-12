#!/usr/bin/env python3
"""Attempt an in-Malbolge installer for the relocated reference EOF loop.

The target state is extracted offline; the emitted candidate, if any, must
install it inside Malbolge. A profile-derived sparse target is experimental.
"""
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import time

P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[2]
source=ROOT/'vm_malbolge/evidence/unieco_strict_relocation_v1/reference_cat_functional.mb'
forge_original=ROOT.parent/'BolgeForge'
# Fresh isolated Forge copy: its import builds a C solver below its own root.
forge=pathlib.Path(tempfile.mkdtemp(prefix='unieco-reloc-forge-'))
(forge/'tools').mkdir(); (forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:
    shutil.copyfile(forge_original/name,forge/name)
sys.path.insert(0,str(forge))
from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1,XLAT2
spec=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
se=m.SE; image=source.read_bytes(); N=59049; shift=94*300; lo=7614; hi=7971
mem=list(image)+[0]*(N-len(image))
for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=pos=0
for count in range(20000):
    op=(mem[c]+c)%94
    if op==23:break
    if op==4:c=mem[d]
    elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
    elif op==40:d=mem[d]
    elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
    elif op in (5,81):raise AssertionError('unexpected preamble output or halt')
    if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
    c=(c+1)%N;d=(d+1)%N
else:raise AssertionError('missing IN')
snapshot=mem.copy(); assert (c,d)==(7657,58975)
# The profile covers every byte value then an extra 00,ff and EOF.
profile=bytes(range(256))+b'\x00\xff'; used=set(); jumps=set(); out=bytearray()
for count in range(200000):
    if lo<=c<=hi:used.add(c)
    op=(mem[c]+c)%94
    if op==4:
        if lo<=mem[d]<=hi:jumps.add(d)
        c=mem[d]
    elif op==5:out.append(a%256)
    elif op==23:
        a=profile[pos] if pos<len(profile) else 59048
        pos+=pos<len(profile)
    elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
    elif op==40:d=mem[d]
    elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
    elif op==81:break
    if 33<=mem[c]<=126:
        if lo<=c<=hi:used.add(c)
        mem[c]=se.encrypt(mem[c])
    c=(c+1)%N;d=(d+1)%N
else:raise AssertionError('reference profile did not halt')
assert bytes(out)==profile
values={i+shift:snapshot[i] for i in used}
for i in range(58800,59049):values[i]=snapshot[i]
for i in jumps:
    if lo<=snapshot[i]<=hi:values[i]=snapshot[i]+shift
# The preamble's final JMP encrypts the cell preceding the first IN.
preceding=7656+shift
values[preceding]=33+XLAT2.index(chr(snapshot[7656]))
assert values[58974]==7656+shift
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes(); template=[x for x in raw if 33<=x<=126]
source_len=len(template)+94*260
assert source_len < min(i for i in values if i<50000)
clean=template+[33]*(source_len-len(template))
start=time.monotonic()
ops=synthesize_preamble_ops(clean,values,58974,9003,0,template_clean=template,boot='original')
end=99+len(ops)
result={'profile_input_bytes':len(profile),'target_cells':len(values),'profile_code_cells':len(used),
        'profile_jump_pointer_cells':len(jumps),'source_len':source_len,'plan_length':len(ops),
        'plan_end':end,'elapsed_seconds':round(time.monotonic()-start,3),
        'fits':end<=source_len-2,'handoff_c':7657+shift,'handoff_d':58975,
        'scope':'profile-derived target; must verify emitted native image independently'}
(P/'synthesis_attempt.results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
if not result['fits']:raise SystemExit(2)
program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-p)%94) for p,ch in enumerate(ops,99))
while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
program.extend(template[-2:])
invalid=[i for i,x in enumerate(program) if XLAT1[(x-33+i)%94] not in 'ji*p</vo']
assert not invalid
(P/'relocated_candidate.mb').write_bytes(program)
(P/'relocated_targets.json').write_text(json.dumps(values,sort_keys=True,indent=2)+'\n')
(P/'relocated_plan.ops').write_text(''.join(ops)+'\n')
