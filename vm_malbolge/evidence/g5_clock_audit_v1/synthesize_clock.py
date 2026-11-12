#!/usr/bin/env python3
"""Synthesize bounded orbit-clock image with three separate output sites."""
import json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge';forge=pathlib.Path(tempfile.mkdtemp(prefix='g5-clock-forge-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1
H=58470;D=57000;sites=[58050,58150,58250];stop=58300;assert H%94==2
opchar=lambda pc,ch:33+((XLAT1.index(ch)-pc)%94)
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[v for v in raw if 33<=v<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template));reports={}
for tag in ('positive','control'):
 values={D-1:H-1,H-1:81,H:66,H+1:opchar(H+1,'i'),stop-1:81,stop:opchar(stop,'v')}
 for k,pc in enumerate(sites):
  values[pc-1]=81;values[pc]=opchar(pc,'<');values[pc+1]=opchar(pc+1,'i')
  values[D+4*k+1]=(stop-1 if tag=='control' and k==1 else pc-1)
  values[D+4*k+3]=H-1
 assert source_len<min(values)
 t=time.monotonic();ops=synthesize_preamble_ops(clean,values,D-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
 reports[tag]={'target_cells':len(values),'plan_length':len(ops),'plan_end':end,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t,3)}
 if end>source_len-2:raise RuntimeError('plan too long')
 prog=bytearray(template[:99]);prog.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
 while len(prog)<source_len-2:prog.append(33+((XLAT1.index('o')-len(prog))%94))
 prog.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(prog))
 (P/('clock_'+tag+'.mb')).write_bytes(prog);(P/('clock_'+tag+'_targets.json')).write_text(json.dumps(values,sort_keys=True,indent=2)+'\n');(P/('clock_'+tag+'_plan.ops')).write_text(''.join(ops)+'\n')
z={'clock_pc':H,'clock_initial':66,'clock_expected_values':[66,62,76,79],'clock_expected_opcodes':[68,64,78,81],
   'output_sites':sites,'body_scope':'three distinct OUT sites selected by D pointer sequence; not one reusable body',
   'control':'second branch jumps to halt island','programs':reports}
(P/'synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2))
