#!/usr/bin/env python3
"""Build isolated real-Malbolge restore experiment for one encrypted code word."""
import importlib.util,json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge';forge=pathlib.Path(tempfile.mkdtemp(prefix='increment-code-cell-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1,crazy_op
rows=json.loads((P/'code_rearm_v2.results.json').read_text())['rows'];C1=29524
# Prefer a cell not solvable by any ROT^k + one CRAZY; ensure the missing-CRAZY control fails.
row=next(r for r in rows if r['solution'] is None and crazy_op(r['three_crazy']['control'],crazy_op(C1,r['after_execution']))!=r['target'])
old=row['after_execution'];want=row['target'];ctrl=row['three_crazy']['control'];T=57000;C=57010;S=57020;start=58500
assert crazy_op(ctrl,crazy_op(crazy_op(C1,old),crazy_op(C1,old)))==want
code='*jpjpoj'+'*j'*9+'*ojpv';raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[x for x in raw if 33<=x<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template))
reports={}
for tag,ops_code in [('positive',code),('control',code.replace('*jp','*jo',1))]:
 values={T:old,T+1:T-1,T+2:C-1,C:ctrl,C+1:C-1,C+2:T-1,S:C1,S+1:T-1,S-1:start-1}
 for i,ch in enumerate(ops_code):pos=start+i;values[pos]=33+((XLAT1.index(ch)-pos)%94)
 assert source_len<min(values)
 t0=time.monotonic();ops=synthesize_preamble_ops(clean,values,S-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
 reports[tag]={'runtime_ops':ops_code,'plan_length':len(ops),'plan_end':end,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t0,3)}
 if end>source_len-2:raise RuntimeError('plan too long')
 program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
 while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
 program.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(program))
 (P/('code_cell_'+tag+'.mb')).write_bytes(program)
 (P/('code_cell_'+tag+'_targets.json')).write_text(json.dumps(values,indent=2,sort_keys=True)+'\n')
 (P/('code_cell_'+tag+'_plan.ops')).write_text(''.join(ops)+'\n')
z={'source_pc':row['pc'],'source_after_execution':old,'source_original':want,'target_address':T,'constant_address':C,'control':ctrl,
   'programs':reports,'scope':'one code-derived word placed in a data cell; host preinstalls control; no autonomous whole-code rearm or loop'}
(P/'code_cell_synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2))
