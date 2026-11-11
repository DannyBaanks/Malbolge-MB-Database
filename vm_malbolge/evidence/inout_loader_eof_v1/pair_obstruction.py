#!/usr/bin/env python3
"""Exhaust loader-valid initial byte pairs for the three fixed positions."""
import importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]
p=ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
s=importlib.util.spec_from_file_location('compose',p); M=importlib.util.module_from_spec(s); s.loader.exec_module(M)
r={}
for name,pos,op in [('IN',43,23),('DLOAD',60,40),('OUT',119,5)]:
 loader_pairs=0; first_round_only=0; both_rounds=[]
 for a in range(33,127):
  for b in range(33,127):
   if (a+pos)%94 not in M.VALID or (b+pos+4)%94 not in M.VALID: continue
   loader_pairs+=1
   if int((a+pos)%94==op)+int((b+pos+4)%94==op)!=1: continue
   first_round_only+=1
   if int((M.ENC[a]+pos)%94==op)+int((M.ENC[b]+pos+4)%94==op)==1: both_rounds.append([a,b])
 r[name]={'position':pos,'opcode':op,'printable_pairs_tested':94*94,'loader_valid_pairs':loader_pairs,'one_target_first_round':first_round_only,'one_target_both_rounds':len(both_rounds),'solutions':both_rounds}
(P/'pair_obstruction.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
