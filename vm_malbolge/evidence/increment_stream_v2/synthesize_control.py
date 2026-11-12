#!/usr/bin/env python3
"""Three-read increment experiment: rearm scratch in native Malbolge.

Still straight-line code, no EOF branch and no arbitrary-length claim.
"""
import json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge'
forge=pathlib.Path(tempfile.mkdtemp(prefix='increment-three-forge-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1,crazy_op
base=26*2187;start=58500;first=58000;S=58020;C1=29524;truth=((1,0,0),(1,0,2),(2,2,1));r1=[1]*7;r2=[1]*7
for i in range(7,10):
 t=(base//3**i)%3;x,y=next((x,y) for x in range(3) for y in range(3) if truth[y][truth[x][0]]==t);r1.append(x);r2.append(y)
mask1=sum(v*3**i for i,v in enumerate(r1));mask2=sum(v*3**i for i,v in enumerate(r2));ctrl1=crazy_op(mask1,C1);ctrl2=crazy_op(mask2,C1)
assert crazy_op(ctrl1,C1)==mask1 and crazy_op(ctrl2,C1)==mask2
block='/ppj'+'*j'*9+'oo'+'ppjj'+'*j'*9+'*<'
# Entry d=S after prior OUT and table's return MOVD.
reset=('*p'+'o'*5+'j'+'ppjp'+'o'+'p'+'o'*3+'j'+'ppjp'
       +'o'*3+'*j'*9+'*'+'o'+'j'+'p'
       +'o'*7+'*j'*9+'*'+'o'+'j'+'p'
       +'o'*9+'j')
reset=reset.replace('*p','*o',1)
code=block+'j'+block+'j'+reset+block+'v';values={first-1:start-1}
for sp in (first,S):values.update({sp+1:C1,sp+2:C1,sp+3:sp+1,sp+4:mask1,sp+5:mask2,sp+6:sp+4})
values.update({S:C1,S+7:S,S+8:S+3,S+9:ctrl1,S+10:S+8,S+11:S+3,S+12:ctrl2,S+13:S+11,S+14:S+4,S+15:S-1})
for b in range(256):
 idx=base+3*b;values[idx+1]=(b+1)%256;values[idx+2]=idx;values[idx+3]=S-1
for i,ch in enumerate(code):pos=start+i;values[pos]=33+((XLAT1.index(ch)-pos)%94)
assert start+len(code)<59049
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[x for x in raw if 33<=x<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template));assert source_len<min(values)
t0=time.monotonic();ops=synthesize_preamble_ops(clean,values,first-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
z={'base':base,'start':start,'first_scratch':first,'reusable_scratch':S,'mask1':mask1,'mask2':mask2,'ctrl1':ctrl1,'ctrl2':ctrl2,
   'rearm_ops':reset,'runtime_ops':code,'runtime_length':len(code),'target_cells':len(values),'plan_length':len(ops),'plan_end':end,
   'source_length':source_len,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t0,3),
   'scope':'three unrolled reads; scratch reset only; no code rearm, loop, or EOF branch'}
(P/'control_synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2),flush=True)
if not z['fits']:raise SystemExit(2)
program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
program.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(program))
(P/'increment_three_control.mb').write_bytes(program);(P/'control_targets.json').write_text(json.dumps(values,sort_keys=True,indent=2)+'\n');(P/'control_plan.ops').write_text(''.join(ops)+'\n')
