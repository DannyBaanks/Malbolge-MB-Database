#!/usr/bin/env python3
"""Record bounded live echo states around the first output for graft planning."""
import collections,importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049
image=(ROOT/'vm_malbolge/evidence/unieco_bf_compile_v1/compiled_relocated.mb').read_bytes();mem=list(image)+[0]*(N-len(image))
for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=pos=0;data=b'\x00\xff';window=collections.deque(maxlen=30);out=[];after=0
for step in range(1,30000):
    v=mem[c];op=(v+c)%94
    event={'step':step,'pc':c,'op':op,'a':a,'d':d,'mem_d':mem[d]}
    window.append(event)
    if op==5:
        out.append({'byte':a%256,'events_before':list(window)});after=1
    elif after:after+=1
    if len(out)==2 and after>1:break
    if op==4:c=mem[d]
    elif op==23:a=data[pos] if pos<len(data) else 59048;pos+=pos<len(data)
    elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
    elif op==40:d=mem[d]
    elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
    elif op==81:break
    if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
    c=(c+1)%N;d=(d+1)%N
report={'input_hex':data.hex(),'outputs':out,'scope':'bounded scratch-model observations, not a graft or native execution'}
(P/'trace_echo_handoff.results.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps({'outputs':len(out),'final_events':[x['events_before'][-5:] for x in out]},indent=2))
assert [x['byte'] for x in out]==[0,255]
