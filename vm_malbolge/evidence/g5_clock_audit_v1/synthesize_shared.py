#!/usr/bin/env python3
"""Synthesize a finite driver of one phase-reusable CRAZY instruction."""
import json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge';forge=pathlib.Path(tempfile.mkdtemp(prefix='shared-crazy-forge-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1
H=58456;D=57000;stop=58300;assert H%94==82
opchar=lambda pc,ch:33+((XLAT1.index(ch)-pc)%94)
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[v for v in raw if 33<=v<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template));reports={}
for tag in ('positive','control'):
 values={D-1:H-1,H-1:81,H:74 if tag=='positive' else 70,H+1:opchar(H+1,'i'),stop-1:81,stop:opchar(stop,'v')}
 for k in range(6):
  values[D+2*k]=29524
  values[D+2*k+1]=(H-1 if k<5 else stop-1)
 assert source_len<min(values)
 t=time.monotonic();ops=synthesize_preamble_ops(clean,values,D-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
 reports[tag]={'target_cells':len(values),'plan_length':len(ops),'plan_end':end,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t,3)}
 if end>source_len-2:raise RuntimeError('plan too long')
 prog=bytearray(template[:99]);prog.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
 while len(prog)<source_len-2:prog.append(33+((XLAT1.index('o')-len(prog))%94))
 prog.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(prog))
 (P/('shared_'+tag+'.mb')).write_bytes(prog);(P/('shared_'+tag+'_targets.json')).write_text(json.dumps(values,sort_keys=True,indent=2)+'\n');(P/('shared_'+tag+'_plan.ops')).write_text(''.join(ops)+'\n')
z={'pc':H,'positive_initial':74,'control_initial':70,'expected_positive_opcodes':[62,58,62,58,62,58],
   'positive_target_cells':[D,D+4,D+8],'control_target_cells':[D+2,D+6,D+10],
   'return_scheme':'six preinstalled D-pointer values; final pointer goes to HALT',
   'scope':'phase-shared single instruction with finite driver, not a complete reusable restorer', 'programs':reports}
(P/'shared_synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2))
