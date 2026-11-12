#!/usr/bin/env python3
"""Observe installed memory and scratch resets over 256 byte iterations."""
from __future__ import annotations
import collections,hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];pack=ROOT/'vm_malbolge/evidence/increment_circuit_loop_v1/run02';image=(pack/'increment.mb').read_bytes()
spec=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);se=m.SE
sys_path=ROOT/'vm_malbolge/tools/increment_bf/backend'
import sys
sys.path.insert(0,str(sys_path));from constants import XLAT2
layout=[tuple(map(int,x.split())) for x in (pack/'increment.layout').read_text().splitlines()[1:]]
labels={}
for line in (pack/'increment.labels').read_text().splitlines():
    cols=line.split()
    if len(cols)==3 and cols[2].isdigit():labels.setdefault(int(cols[2]),[]).append(cols[0].rstrip(':'))
scratch={address:name for address,names in labels.items() for name in names if name in ('t1','t2')}
assert set(scratch.values())=={'t1','t2'}
mem=list(image)+[0]*(59049-len(image))
for i in range(len(image),59049):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=used=0;data=bytes(range(256));out=[];baseline=None;visits=0;changed={};unexpected=[];resets=[];current=None;reserved={i for i,v,t in layout if t==4};reserved_reads=[]
for step in range(1,1600001):
    if not 33<=mem[c]<=126:raise AssertionError(f'nonprintable pc {c}')
    op=(mem[c]+c)%94
    if c==56725 and op==23:
        visits+=1;current={name:[] for name in scratch.values()};resets.append(current)
        if baseline is None:baseline={addr:mem[addr] for addr,_,_ in layout}
        else:
            for addr,_,kind in layout:
                if mem[addr]!=baseline[addr]:
                    record=changed.setdefault(addr,{'kind':kind,'labels':labels.get(addr,[]),'values':set(),'different_visits':0});record['values'].add(mem[addr]);record['different_visits']+=1
                    if kind==3 and addr not in scratch:unexpected.append({'step':step,'address':addr,'kind':kind})
    if current is not None and d in scratch and op in (4,39,40,62) and len(current[scratch[d]])<2:
        current[scratch[d]].append({'step':step,'opcode':op,'a':a,'before':mem[d]})
    if baseline is not None and d in reserved and op in (4,39,40,62):reserved_reads.append({'step':step,'d':d,'op':op})
    if op==4:
        c=mem[d]
        if not 33<=mem[c]<=126:raise AssertionError('nonprintable jump')
    elif op==5:out.append(a%256)
    elif op==23:a=data[used] if used<len(data) else 59048;used+=1
    elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
    elif op==40:d=mem[d]
    elif op==62:
        mem[d]=se.crazy(a,mem[d]);a=mem[d]
        if current is not None and d in scratch and current[scratch[d]] and current[scratch[d]][-1]['step']==step:current[scratch[d]][-1]['after']=mem[d]
    elif op==81:break
    if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
    c=(c+1)%59049;d=(d+1)%59049
else:raise AssertionError('budget exhausted')
expected=bytes((x+1)&255 for x in data)
assert visits==257 and used==257 and bytes(out)==expected and not unexpected
for cycle in resets[:-1]:
    for name,events in cycle.items():
        assert len(events)==2 and [e['opcode'] for e in events]==[62,62] and events[0]['a']==29524 and events[1]['a']==events[0]['after'] and events[-1].get('after')==29524,(name,events)
effects={4,5,23,39,40,62,81};code=[]
for addr,record in changed.items():
    record['values']=sorted(record['values'])
    if record['kind']==2:
        word=baseline[addr];orbit=[]
        while word not in orbit:
            orbit.append(word);word=ord(XLAT2[word-33])
        no_effect=all((w+addr)%94 not in effects for w in orbit)
        code.append({'address':addr,'labels':record['labels'],'orbit_length':len(orbit),'all_phases_nop':no_effect,'observed_values':record['values']})
        if not no_effect:unexpected.append({'address':addr,'kind':'variable_active_code'})
assert not unexpected and not reserved_reads
assert all(se.crazy(se.crazy(29524,x),se.crazy(29524,x))==29524 for x in range(59049))
native=subprocess.run([str(ROOT.parent/'Malbolge-PureEpoch/build/olmstead'),str(pack/'increment.mb')],input=data,capture_output=True,timeout=20)
assert native.returncode==0 and native.stdout==expected
print(json.dumps({'input_sha256':hashlib.sha256(data).hexdigest(),'image_sha256':hashlib.sha256(image).hexdigest(),'visits_including_eof':visits,'model_steps':step,'model_status':'HALTED','output_sha256':hashlib.sha256(bytes(out)).hexdigest(),'native_rc':native.returncode,'native_stdout_sha256':hashlib.sha256(native.stdout).hexdigest(),'scratch_addresses':scratch,'scratch_reset_cycles':len(resets)-1,'scratch_all_first_two_accesses_reset':True,'changed_kind_counts':dict(collections.Counter(str(v['kind']) for v in changed.values())),'changed_code':code,'changed_cells':{str(k):v for k,v in changed.items()},'reserved_data_reads':reserved_reads,'reset_algebra_words_checked':59049,'unexpected':unexpected,'scope':'one 256-byte stream and EOF; full state is not byte-identical'},indent=2))
