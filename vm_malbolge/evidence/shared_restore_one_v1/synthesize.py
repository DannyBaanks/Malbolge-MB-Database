#!/usr/bin/env python3
"""Build one-target restorer from phase-shared ROT, CRAZY and MOVD cells."""
import json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge';forge=pathlib.Path(tempfile.mkdtemp(prefix='shared-restore-one-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1,crazy_op,rot_op
K,T,C=57000,57100,57200;ROT,MOVD,CRAZY,CLOCK=58057,58152,58268,58303;ONE=29524;want=40;intermediate=ONE-want;ctrl=crazy_op(intermediate,ONE)
assert [x%94 for x in [ROT,MOVD,CRAZY,CLOCK]]==[59,60,82,23]
assert crazy_op(intermediate,intermediate)==want and ctrl==40
opchar=lambda pc,ch:33+((XLAT1.index(ch)-pc)%94)
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[v for v in raw if 33<=v<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template));reports={}
for tag in ('positive','control'):
 values={}
 def put(i,v):
  if i in values and values[i]!=v:raise ValueError(f'conflict {i}: {values[i]} vs {v}')
  values[i]=v
 for H in (ROT,MOVD,CRAZY,CLOCK):
  put(H-1,81);put(H,117 if H==CLOCK else 74);put(H+1,opchar(H+1,'i'))
 for i,v in {K-1:ROT-1,K:ONE,K+1:ROT-1,K+3:MOVD-1,K+4:T-4,
             T-3:MOVD-1,T-1:CRAZY-1,T:70,T+1:CRAZY-1,T+3:CLOCK-1,
             T+4:C-2,T+5:MOVD-1,T+6:T-4,
             C-1:ROT-1,C:3*(ctrl if tag=='positive' else 39),C+1:ROT-1,C+3:MOVD-1,C+4:T-4}.items():put(i,v)
 assert source_len<min(values)
 t=time.monotonic();ops=synthesize_preamble_ops(clean,values,K-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
 reports[tag]={'target_cells':len(values),'plan_length':len(ops),'plan_end':end,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t,3)}
 if end>source_len-2:raise ValueError('plan does not fit')
 program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
 while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
 program.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(program))
 (P/('restore_'+tag+'.mb')).write_bytes(program);(P/('restore_'+tag+'_targets.json')).write_text(json.dumps(values,sort_keys=True,indent=2)+'\n');(P/('restore_'+tag+'_plan.ops')).write_text(''.join(ops)+'\n')
z={'T':T,'target_initial':70,'target_want':want,'intermediate':intermediate,'control':ctrl,'clock_pc':CLOCK,
   'clock_expected_opcodes':[46,40,49,81],'primitive_pcs':{'ROT':ROT,'MOVD':MOVD,'CRAZY':CRAZY},
   'programs':reports,'scope':'one fixed value, four-phase driver; no generic, repeatable scheduler or EOF'}
(P/'synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2))
