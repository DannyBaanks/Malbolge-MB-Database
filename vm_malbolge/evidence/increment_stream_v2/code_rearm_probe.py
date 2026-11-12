#!/usr/bin/env python3
"""Offline reachability of restoring the executed second code block.

Controls are computed by the host. This does not execute the proposed writes
inside Malbolge and does not establish an autonomous reusable loop.
"""
import importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049
image=(P/'increment_three.mb').read_bytes();target={int(k):v for k,v in json.loads((P/'targets.json').read_text()).items()};mem=list(image)+[0]*(N-len(image))
for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=pos=0;data=b'ABC';ins=0
for step in range(1,100000):
 op=(mem[c]+c)%94
 if op==23:
  ins+=1
  if ins==3:break
  a=data[pos];pos+=1
 elif op==4:c=mem[d]
 elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
 elif op==40:d=mem[d]
 elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
 elif op==81:raise AssertionError('halt before third IN')
 if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
 c=(c+1)%N;d=(d+1)%N
else:raise AssertionError('no third IN')
table=((1,0,0),(1,0,2),(2,2,1))
def solve_control(cell,want):
 result=0;power=1
 for _ in range(10):
  choices=[a for a in range(3) if table[cell%3][a]==want%3]
  if not choices:return None
  result+=choices[0]*power;power*=3;cell//=3;want//=3
 return result
rows=[]
for pc in range(58549,58597):
 before=mem[pc];want=target[pc];value=before;solution=None
 for rotations in range(10):
  ctrl=solve_control(value,want)
  if ctrl is not None:
   assert se.crazy(ctrl,value)==want
   solution={'rotations_before_crazy':rotations,'control':ctrl,'control_printable':33<=ctrl<=126};break
  value=se.rot(value)
 rows.append({'pc':pc,'after_execution':before,'target':want,'solution':solution})
report={'input_hex':data.hex(),'third_input_step':step,'code_cells':len(rows),
        'single_crazy_reachable':sum(r['solution'] is not None and r['solution']['rotations_before_crazy']==0 for r in rows),
        'rotate_then_crazy_reachable':sum(r['solution'] is not None for r in rows),
        'printable_control':sum(r['solution'] is not None and r['solution']['control_printable'] for r in rows),
        'rows':rows,'scope':'host-computed controls; no in-Malbolge scheduler, scratch/control rearm or EOF demonstrated'}
(P/'code_rearm.results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
