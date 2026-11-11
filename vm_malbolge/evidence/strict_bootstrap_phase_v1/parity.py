#!/usr/bin/env python3
import hashlib,importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
M=load('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'); C=load('trit_common',ROOT.parent/'ISyCo/GUS/04_EXPERIMENTS/GUS_TRIT_ALGEBRA_V0/common.py')
src=C.PONG_MB.read_text(); reference=M.O.load_memory(src); chars=[c for c in src if not c.isspace()]; N=M.N
base=[ord(c) for c in chars]+[0]*(N-len(chars)); results={}
for mode in ('common','scratch','swapped'):
 mem=list(base)
 for i in range(len(chars),N):
  a,b=mem[i-1],mem[i-2]
  mem[i]=C.crazy(b,a) if mode=='swapped' else (C.crazy(a,b) if mode=='common' else M.SE.crazy(a,b))
 results[mode]=sum(a!=b for a,b in zip(mem,reference))
result={'fixture_sha256':hashlib.sha256(C.PONG_MB.read_bytes()).hexdigest(),'orientation':'crazy(accumulator,cell)=table[cell trit][accumulator trit]','cells':N,'mismatches':results}
(P/'parity.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); assert results['common']==results['scratch']==0 and results['swapped']>0
