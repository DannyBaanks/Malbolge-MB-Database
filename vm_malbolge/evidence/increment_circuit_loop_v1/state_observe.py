#!/usr/bin/env python3
"""Inspect which initialized cells differ at successive IN boundaries."""
import collections,importlib.util,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;root=P.parents[2];run=pathlib.Path(sys.argv[1]);image=(run/'increment.mb').read_bytes()
s=importlib.util.spec_from_file_location('compose',root/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE
lines=(run/'increment.layout').read_text().splitlines();layout=[tuple(map(int,line.split())) for line in lines[1:]]
labels={}
for line in (run/'increment.labels').read_text().splitlines():
    cols=line.split()
    if len(cols)==3 and cols[2].isdigit():labels.setdefault(int(cols[2]),[]).append(cols[0].rstrip(':'))
mem=list(image)+[0]*(59049-len(image))
for i in range(len(image),59049):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=used=0;data=b'ABCD';snapshots=[];resets=[];first_access=[];active=-1;tracked={i:name for i,names in labels.items() for name in names if name in ('t1','t2')}
for step in range(1,100001):
    assert 33<=mem[c]<=126
    op=(mem[c]+c)%94
    if c==56725 and op==23:
        snapshots.append({'step':step,'cells':{i:mem[i] for i,v,t in layout}});resets.append({name:[] for name in tracked.values()});first_access.append({name:[] for name in tracked.values()});active+=1
    if active>=0 and d in tracked and op in (4,39,40,62) and len(first_access[active][tracked[d]])<2:first_access[active][tracked[d]].append({'step':step,'opcode':op})
    if op==4:c=mem[d]
    elif op==5:pass
    elif op==23:a=data[used] if used<len(data) else 59048;used+=1
    elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
    elif op==40:d=mem[d]
    elif op==62:
        old=mem[d];mem[d]=se.crazy(a,mem[d]);a=mem[d]
        if active>=0 and d in tracked and len(resets[active][tracked[d]])<2:resets[active][tracked[d]].append({'step':step,'before':old,'after':mem[d]})
    elif op==81:break
    if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
    c=(c+1)%59049;d=(d+1)%59049
assert len(snapshots)==5
result=[]
for n in range(1,len(snapshots)):
    dif=[{'address':i,'type':t,'initial':snapshots[0]['cells'][i],'current':snapshots[n]['cells'][i],'labels':labels.get(i,[])} for i,v,t in layout if snapshots[0]['cells'][i]!=snapshots[n]['cells'][i]]
    assert all(z['initial']==z['current'] or ((z['initial']+z['address'])%94 not in {4,5,23,39,40,62,81} and (z['current']+z['address'])%94 not in {4,5,23,39,40,62,81}) for z in dif if z['type']==2)
    result.append({'visit':n+1,'step':snapshots[n]['step'],'count_by_layout_type':dict(collections.Counter(str(x['type']) for x in dif)),'differences':dif})
assert all(len(v)==2 and v[-1]['after']==29524 for cycle in resets[:-1] for v in cycle.values())
assert all(all([event['opcode'] for event in events]==[62,62] for events in cycle.values()) and len(cycle)==2 for cycle in first_access[:-1])
print(json.dumps({'scratch_first_access':first_access[:-1],'scratch_first_resets':resets[:-1],'input_hex':data.hex(),'boundary':'before IN, including final EOF read','baseline_step':snapshots[0]['step'],'comparisons':result,'scope':'whole initialized layout; differences are observed, not by themselves evidence of error'},indent=2))
