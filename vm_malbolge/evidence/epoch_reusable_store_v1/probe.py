#!/usr/bin/env python3
"""Read-only replay of two assembled candidates, bounded stream + VM trace."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'vm_malbolge/tools/native_classic')]
import oracle_classic as oc
from constants import XLAT1

def labels(name):
    wanted={'stack_scratch','stack_top','next_char','ENTRY','IN','OUT','CRAZY'}; result={}
    for line in (P/f'{name}.dbg').read_text().splitlines():
        if ':' not in line:continue
        k,rest=line.split(':',1)
        if k in wanted:result[k]=int(rest.split()[-1])
    assert set(result)==wanted,result
    return result

def trace(source, data, lab):
    mem=oc.load_memory(source.decode('latin-1')); a=c=d=steps=0; output=[]; i=0; events=[]
    while steps<4000000:
        steps+=1; op=(mem[c]+c)%94; jumped=False
        if op==4:target=mem[d];jumped=True
        elif op==5:
            output.append(a%256);events.append({'kind':'out','pc':c,'step':steps,'out':a%256,'scratch':mem[lab['stack_scratch']],'top':mem[lab['stack_top']]})
        elif op==23:
            if i>=len(data):return bytes(output),steps,'EOF',events
            a=data[i];events.append({'kind':'in','pc':c,'step':steps,'byte':a,'scratch':mem[lab['stack_scratch']],'top':mem[lab['stack_top']]});i+=1
        elif op==39:mem[d]=(mem[d]//3)+(mem[d]%3)*19683;a=mem[d]
        elif op==40:d=mem[d]
        elif op==62:
            mem[d]=oc.crazy_op(a,mem[d]);a=mem[d]
            if d==lab['stack_top']:events.append({'kind':'write_top','pc':c,'step':steps,'value':a,'index':i-1})
        elif op==81:return bytes(output),steps,'HALTED',events
        if jumped:c=target
        if 33<=mem[c]<=126:mem[c]=oc._ENC[mem[c]]
        c=(c+1)%oc.MEM_SIZE;d=(d+1)%oc.MEM_SIZE
    return bytes(output),steps,'MAX_STEPS',events

def main():
    tests=[b'',b'A',b'AB',b'ABA',b'\x00\x0a\x0d\xff',bytes(range(256)),bytes(range(255,-1,-1))]
    rows=[]
    for data in tests:
        entry={'input_hex':data.hex(),'bytes':len(data)}
        for name in ('positive','mutant'):
            img=(P/f'{name}.mb').read_bytes(); lab=labels(name)
            expected=data if name=='positive' else b'\x54'*len(data)
            out,steps,status=oc.run(img.decode('latin-1'),max_steps=4000000,stdin_data=data.decode('latin-1'),stop_on_eof=True)
            raw=out.encode('latin-1');p=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(P/f'{name}.mb'),'4000000'],input=data,capture_output=True)
            tout,tsteps,tstatus,events=trace(img,data,lab)
            ins=[x for x in events if x['kind']=='in']; outs=[x for x in events if x['kind']=='out']; writes=[x for x in events if x['kind']=='write_top']
            words=list(data) if name=='positive' else [29524]*len(data)
            slot_ok=all(any(w['index']==i and w['value']==v for w in writes) for i,v in enumerate(words))
            rearm_ok=all(x['scratch']==29524 and x['top']==29524 for x in ins)
            output_top_ok=all(x['top']==v for x,v in zip(outs,words))
            ok=(raw==expected and p.stdout==expected+b'\n' and p.returncode==0 and p.stderr.decode('utf8','replace').strip()==f'steps: {steps} | status: HALTED' and status=='EOF' and tout==raw and steps==tsteps and tstatus==status and len(ins)==len(data) and len(outs)==len(data) and slot_ok and rearm_ok and output_top_ok)
            entry[name]={'ok':ok,'oracle_hex':raw.hex(),'runner_raw_hex':p.stdout.hex(),'runner_stderr':p.stderr.decode('utf8','replace').strip(),'steps':steps,'status':status,'slot_ok':slot_ok,'rearm_ok':rearm_ok,'output_top_ok':output_top_ok,'events':events}
        rows.append(entry); print(f"len={len(data):3} positive={entry['positive']['ok']} mutant={entry['mutant']['ok']} steps={entry['positive']['steps']} rearm={entry['positive']['rearm_ok']} slot={entry['positive']['slot_ok']}",flush=True)
    imgs={name:(P/f'{name}.mb').read_bytes() for name in ('positive','mutant')}
    strict={name:sum(not (33<=v<=126 and XLAT1[(v-33+i)%94] in 'ji*p</vo') for i,v in enumerate(bytes(x for x in im if x not in b'\t\n\r\v\f '))) for name,im in imgs.items()}
    result={'cases':rows,'strict_invalid_counts':strict,'labels':{n:labels(n) for n in imgs},'image_sha256':{n:hashlib.sha256(im).hexdigest() for n,im in imgs.items()},'source_sha256':hashlib.sha256((ROOT/'vm_malbolge/src/cell_stack_loop_echo.hell').read_bytes()).hexdigest()}
    (P/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('strict invalid byte counts:',strict); print('sha256:',result['image_sha256']); return int(not (all(r[n]['ok'] for r in rows for n in imgs) and all(v==0 for v in strict.values())))
if __name__=='__main__':sys.exit(main())
