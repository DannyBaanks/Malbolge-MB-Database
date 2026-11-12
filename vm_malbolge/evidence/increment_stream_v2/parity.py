#!/usr/bin/env python3
"""Full-memory orientation parity before interpreting CRAZY-based results."""
import hashlib
import importlib.util
import json
import pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
m=load('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
c=load('trit_common',ROOT.parent.parent/'ISyCo/GUS/04_EXPERIMENTS/GUS_TRIT_ALGEBRA_V0/common.py')
source=c.PONG_MB.read_text(); reference=m.O.load_memory(source); chars=[x for x in source if not x.isspace()];N=m.N
base=[ord(x) for x in chars]+[0]*(N-len(chars));result={}
for mode in ('common','scratch','swapped'):
    mem=list(base)
    for i in range(len(chars),N):
        a,b=mem[i-1],mem[i-2]
        mem[i]=c.crazy(b,a) if mode=='swapped' else (c.crazy(a,b) if mode=='common' else m.SE.crazy(a,b))
    result[mode]=sum(x!=y for x,y in zip(mem,reference))
report={'fixture_sha256':hashlib.sha256(c.PONG_MB.read_bytes()).hexdigest(),'cells':N,'mismatches':result,
        'orientation':'crazy(accumulator,cell)=table[cell][accumulator]'}
(P/'parity.results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert result['common']==result['scratch']==0 and result['swapped']>0
