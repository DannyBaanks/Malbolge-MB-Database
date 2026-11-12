#!/usr/bin/env python3
"""Two real code cells executed, rearmed, and revisited in one run."""
import json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge';forge=pathlib.Path(tempfile.mkdtemp(prefix='multi-code-rearm-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1,crazy_op
rows={r['pc']:r for r in json.loads((ROOT/'vm_malbolge/evidence/increment_stream_v2/code_rearm_v2.results.json').read_text())['rows']};T1,T2=58550,58573;H1,H2=58000,58100;S=57020;K1,C1=57040,57010;K2,C2=57140,57110;ONE=29524;stop=58200
body='j*jpojpooj'+'*j'*9+'*ojp'+'ooooi';assert len(body)==37
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[v for v in raw if 33<=v<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template));reports={}
for tag in ('positive','control'):
 values={}
 def put(i,v):
  if i in values and values[i]!=v:raise ValueError(f'conflict {i}: {values[i]} vs {v}')
  values[i]=v
 def opchar(pc,ch):return 33+((XLAT1.index(ch)-pc)%94)
 put(S-1,T1-1);put(S,ONE);put(S+1,H1-1);put(S+2,K1-1)
 for T,H,K,C in [(T1,H1,K1,C1),(T2,H2,K2,C2)]:
  want=rows[T]['target'];ctrl=crazy_op(want,ONE);assert (T+want)%94==62 and crazy_op(ctrl,ONE)==want
  for i,v in {K:ONE,K+1:T-1,C:ctrl,C+1:C-1,C+2:T-1,T:want,T+1:opchar(T+1,'i'),T+2:T-1,T+3:C-1,T+5:T-1,T+6:0}.items():put(i,v)
  selected=body.replace('j*jpoj','j*jooj',1) if tag=='control' and T==T1 else body
  assert len(selected)==len(body)
  for i,ch in enumerate(selected):put(H+i,opchar(H+i,ch))
 put(T1+7,T2-1);put(T1+8,0);put(T1+9,H2-1);put(T1+10,K2-1);put(T2+7,stop-1);put(stop,opchar(stop,'v'))
 assert source_len<min(values)
 t0=time.monotonic();ops=synthesize_preamble_ops(clean,values,S-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
 reports[tag]={'target_cells':len(values),'plan_length':len(ops),'plan_end':end,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t0,3)}
 if end>source_len-2:raise ValueError('plan does not fit')
 program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
 while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
 program.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(program))
 (P/('multi_'+tag+'.mb')).write_bytes(program);(P/('multi_'+tag+'_targets.json')).write_text(json.dumps(values,indent=2,sort_keys=True)+'\n');(P/('multi_'+tag+'_plan.ops')).write_text(''.join(ops)+'\n')
z={'source_pcs':[T1,T2],'source_words':[rows[T1]['target'],rows[T2]['target']],'helpers':[H1,H2],'programs':reports,
   'scope':'two isolated source-derived code cells with replacement JMP neighbors; not the original contiguous block, a general loop, or EOF behavior'}
(P/'synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2))
