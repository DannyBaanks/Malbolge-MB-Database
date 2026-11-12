#!/usr/bin/env python3
"""Build a strict, one-input increment program using a runtime lookup table."""
import hashlib,importlib.util,json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge'
forge=pathlib.Path(tempfile.mkdtemp(prefix='increment-forge-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
base=16*2187;start=40000;scratch=50000;truth=((1,0,0),(1,0,2),(2,2,1))
rows1=[1]*7;rows2=[1]*7
for i in range(7,10):
 target=(base//3**i)%3
 rows1_i,rows2_i=next((x,y) for x in range(3) for y in range(3) if truth[y][truth[x][0]]==target)
 rows1.append(rows1_i);rows2.append(rows2_i)
mask1=sum(v*3**i for i,v in enumerate(rows1));mask2=sum(v*3**i for i,v in enumerate(rows2))
# IN, preserve word through the involution, multiply by 3 via nine ROTs,
# form the table index with two CRAZYs, use MOVD twice, ROT, OUT, HALT.
code='/ppj'+'*j'*9+'oo'+'ppjj*<v'
values={scratch-1:start-1,scratch+1:29524,scratch+2:29524,
        scratch+3:scratch+1,scratch+4:mask1,scratch+5:mask2,scratch+6:scratch+4}
for b in range(256):values[base+3*b+1]=3*((b+1)%256)
for i,ch in enumerate(code):
 pos=start+i;values[pos]=33+((XLAT1.index(ch)-pos)%94)
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[x for x in raw if 33<=x<=126]
source_len=len(template)+94*260;clean=template+[33]*(source_len-len(template));assert source_len<min(values)
t0=time.monotonic();ops=synthesize_preamble_ops(clean,values,scratch-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
report={'base':base,'start':start,'scratch':scratch,'mask1':mask1,'mask2':mask2,'runtime_ops':code,
        'target_cells':len(values),'plan_length':len(ops),'plan_end':end,'source_length':source_len,
        'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t0,3),
        'scope':'one input only; no EOF handling or reusable streaming loop'}
(P/'oneshot_synthesis.results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if not report['fits']:raise SystemExit(2)
program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
program.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(program))
(P/'increment_oneshot.mb').write_bytes(program);(P/'oneshot_targets.json').write_text(json.dumps(values,indent=2,sort_keys=True)+'\n');(P/'oneshot_plan.ops').write_text(''.join(ops)+'\n')
