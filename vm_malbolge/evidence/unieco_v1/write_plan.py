#!/usr/bin/env python3
"""Per-cell arithmetic feasibility, not an executable write schedule."""
import importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('m',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
T=((1,0,0),(1,0,2),(2,2,1))
def solve(cell,target,depth):
 controls=[0]*depth;mul=1
 for _ in range(10):
  x=cell%3;wanted=target%3
  if depth==1: options=[(a,) for a in range(3) if T[x][a]==wanted]
  else:options=[(a,b) for a in range(3) for b in range(3) if T[T[x][a]][b]==wanted]
  if not options:return None
  for i,v in enumerate(options[0]):controls[i]+=v*mul
  cell//=3;target//=3;mul*=3
 return controls
r=json.loads((P/'state_bridge_v2.results.json').read_text());cases=[]
for x in r['changes']:
 a=solve(x['prepared'],x['needed'],1);b=solve(x['prepared'],x['needed'],2)
 if a is not None:assert m.SE.crazy(a[0],x['prepared'])==x['needed']
 if b is not None:assert m.SE.crazy(b[1],m.SE.crazy(b[0],x['prepared']))==x['needed']
 cases.append({**x,'one_crazy_controls':a,'two_crazy_controls':b})
summary={'cell_count':len(cases),'one_crazy_solvable':sum(x['one_crazy_controls'] is not None for x in cases),'two_crazy_solvable':sum(x['two_crazy_controls'] is not None for x in cases),'conditions':'assumes an arbitrary independent accumulator can be supplied before EACH operation and d points at the cell; does not synthesize those operations or an Olmstead program','cases':cases}
(P/'write_plan.results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
