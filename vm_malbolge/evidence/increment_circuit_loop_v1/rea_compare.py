#!/usr/bin/env python3
"""Compare saved REA Olmstead windows with the independent scratch interpreter."""
import importlib.util,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];run=pathlib.Path(sys.argv[1]);image=(run/'increment.mb').read_bytes()
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE
results={}
for tag,data in [('empty',b''),('ascii',b'ABCD'),('binary',bytes.fromhex('00ff80fe')),('allbytes',bytes(range(256)))]:
    rea=json.loads((run/f'rea_olmstead_{tag}.redacted.json').read_text());n=rea['normalized_result'];window=n['events'];start=window[0]['step'];mem=list(image)+[0]*(59049-len(image))
    for i in range(len(image),59049):mem[i]=se.crazy(mem[i-1],mem[i-2])
    a=c=d=used=0;events=[];out=[]
    for step in range(1,n['run']['steps']+2):
        if not 33<=mem[c]<=126:raise AssertionError('nonprintable pc')
        pc=c;op=(mem[c]+c)%94;e={'step':step,'position':pc,'opcode':op,'a':a,'d':d,'writes':[]}
        if op==4:
            c=mem[d]
            if not 33<=mem[c]<=126:raise AssertionError('nonprintable jump')
        elif op==5:out.append(a%256)
        elif op==23:a=data[used] if used<len(data) else 59048;used+=1
        elif op==39:
            old=mem[d];mem[d]=se.rot(old);a=mem[d];e['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
        elif op==40:d=mem[d]
        elif op==62:
            old=mem[d];mem[d]=se.crazy(a,old);a=mem[d];e['writes'].append({'position':d,'value_before':old,'value_after':mem[d]})
        elif op==81:
            if step>=start:events.append(e)
            break
        if 33<=mem[c]<=126:
            old=mem[c];mem[c]=se.encrypt(old);e['writes'].append({'position':c,'value_before':old,'value_after':mem[c]})
        if step>=start:events.append(e)
        c=(c+1)%59049;d=(d+1)%59049
    normalized=[{k:e[k] for k in ('step','position','opcode','a','d','writes')} for e in window]
    assert events==normalized and n['run']['status']=='HALTED' and step==n['run']['steps'] and out==n['output_bytes']
    results[tag]={'rea_evidence_id':rea['evidence_id'],'window_start':start,'window_events':len(events),'last_step':step,'window_equal':True,'output_hex':bytes(out).hex(),'scope':'window only; earlier steps not captured by REA'}
print(json.dumps(results,indent=2))
