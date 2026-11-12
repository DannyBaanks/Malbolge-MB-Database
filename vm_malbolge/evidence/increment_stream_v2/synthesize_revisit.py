#!/usr/bin/env python3
"""Execute a code cell, restore it in Malbolge, execute it again, halt."""
import json,pathlib,shutil,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];source=ROOT.parent/'BolgeForge';forge=pathlib.Path(tempfile.mkdtemp(prefix='increment-code-revisit-'));(forge/'tools').mkdir();(forge/'reference/malbolge_org').mkdir(parents=True)
for name in ['constants.py','tools/resynthesize.py','reference/malbolge_org/cat.mal']:shutil.copyfile(source/name,forge/name)
sys.path.insert(0,str(forge));from tools.resynthesize import synthesize_preamble_ops
from constants import XLAT1,crazy_op
row=next(x for x in json.loads((P/'code_rearm_v2.results.json').read_text())['rows'] if x['pc']==58550);T=58550;K=57040;C=57010;S=57020;helper=58000;C1=29524;want=row['target'];old=row['after_execution'];ctrl=crazy_op(want,C1)
assert want==74 and old==70 and (want+T)%94==62
head='j*jpojpooj';tail='*j'*9+'*ojp'+'ooooi';body=head+tail;stop=helper+len(body)
raw=(forge/'reference/malbolge_org/cat.mal').read_bytes();template=[x for x in raw if 33<=x<=126];source_len=len(template)+94*500;clean=template+[33]*(source_len-len(template));reports={}
for tag,body_code in [('positive',body),('control',body.replace('j*jpoj','j*jo oj'.replace(' ',''),1))]:
 # T is real code, followed by a reusable JMP. Scratch pointers send the
 # first visit to helper and the second visit to stop.
 values={S-1:T-1,S:C1,S+1:helper-1,S+2:K-1,K:C1,K+1:T-1,
         C:ctrl,C+1:C-1,C+2:T-1,T:want,T+1:33+((XLAT1.index('i')-(T+1))%94),
         T+2:T-1,T+3:C-1,T+5:T-1,T+6:0,T+7:stop-1,stop:33+((XLAT1.index('v')-stop)%94)}
 for i,ch in enumerate(body_code):pos=helper+i;values[pos]=33+((XLAT1.index(ch)-pos)%94)
 assert len(body_code)==len(body) and source_len<min(values)
 t0=time.monotonic();ops=synthesize_preamble_ops(clean,values,S-1,9003,0,template_clean=template,boot='original');end=99+len(ops)
 reports[tag]={'runtime_ops':body_code,'plan_length':len(ops),'plan_end':end,'fits':end<=source_len-2,'elapsed_seconds':round(time.monotonic()-t0,3)}
 if end>source_len-2:raise RuntimeError('plan too long')
 program=bytearray(template[:99]);program.extend(33+((XLAT1.index(ch)-i)%94) for i,ch in enumerate(ops,99))
 while len(program)<source_len-2:program.append(33+((XLAT1.index('o')-len(program))%94))
 program.extend(template[-2:]);assert all(XLAT1[(v-33+i)%94] in 'ji*p</vo' for i,v in enumerate(program))
 (P/('revisit_'+tag+'.mb')).write_bytes(program);(P/('revisit_'+tag+'_targets.json')).write_text(json.dumps(values,sort_keys=True,indent=2)+'\n');(P/('revisit_'+tag+'_plan.ops')).write_text(''.join(ops)+'\n')
z={'target_pc':T,'original':want,'after_first_execute':old,'control_word':ctrl,'helper_pc':helper,'stop_pc':stop,'programs':reports,
   'scope':'one code cell is executed, rearmed and executed again; no increment loop or EOF branch'}
(P/'revisit_synthesis.results.json').write_text(json.dumps(z,indent=2)+'\n');print(json.dumps(z,indent=2))
