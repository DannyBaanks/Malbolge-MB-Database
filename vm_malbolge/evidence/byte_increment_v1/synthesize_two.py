#!/usr/bin/env python3
"""Try two bounded inputs using a shared table restored inside Malbolge."""
import importlib.util,json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge';forge=pathlib.Path(tempfile.mkdtemp(prefix='increment-two-forge-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1
base=26*2187;start=58500;scratch=58000;second=58020;truth=((1,0,0),(1,0,2),(2,2,1));r1=[1]*7;r2=[1]*7
for i in range(7,10):
 t=(base//3**i)%3;x,y=next((x,y) for x in range(3) for y in range(3) if truth[y][truth[x][0]]==t);r1.append(x);r2.append(y)
mask1=sum(v*3**i for i,v in enumerate(r1));mask2=sum(v*3**i for i,v in enumerate(r2))
# Index by 3*input, rotate each table cell ten times to restore it, output.
block='/ppj'+'*j'*9+'oo'+'ppjj'+'*j'*9+'*<'
code=block+'j'+block+'v';values={scratch-1:start-1}
for sp in (scratch,second):values.update({sp+1:29524,sp+2:29524,sp+3:sp+1,sp+4:mask1,sp+5:mask2,sp+6:sp+4})
for b in range(256):
 idx=base+3*b;values[idx+1]=(b+1)%256;values[idx+2]=idx;values[idx+3]=second-1
for i,ch in enumerate(code):pos=start+i;values[pos]=33+((XLAT1.index(ch)-pos)%94)
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[x for x in raw if 33<=x<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template));assert source_len<min(values)
t0=time.monotonic();ops=synthesize_preamble_ops(clean,values,scratch-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
z={'base':base,'start':start,'scratch':scratch,'second_scratch':second,'mask1':mask1,'mask2':mask2,'target_cells':len(values),'runtime_ops':code,'plan_length':len(ops),'plan_end':end,'source_length':source_len,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t0,3),'scope':'bounded two-input construction, no EOF detection or unbounded loop'}
(P/'two_synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2),flush=True)
if not z['fits']:raise SystemExit(2)
program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
program.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(program))
(P/'increment_two.mb').write_bytes(program);(P/'two_targets.json').write_text(json.dumps(values,sort_keys=True,indent=2)+'\n');(P/'two_plan.ops').write_text(''.join(ops)+'\n')
