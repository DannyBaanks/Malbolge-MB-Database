#!/usr/bin/env python3
"""Finite one-shot exact byte store/readback and negative mutant."""
import hashlib, json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent
ROOT = P.parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'vm_malbolge/tools/native_classic')]
import oracle_classic as oc
from constants import char_for_op, XLAT1

def image(mutant=False):
    ops=[40,40,62,40,62,40,62,23,40,62,40,62]+[40,39]*10+[5,81]
    if mutant: ops[11]=68
    mem=bytearray(ord(char_for_op(68,i)) for i in range(130))
    for i,op in enumerate(ops): mem[i]=ord(char_for_op(op,i))
    for i,v in {41:69,70:40,71:89,90:40,91:89,92:69}.items(): mem[i]=v
    return bytes(mem)

def trace(src, byte):
    mem=oc.load_memory(src.decode('ascii')); a=c=d=0; rows=[]
    for step in range(1,35):
        op=(mem[c]+c)%94; oldc=c; oldd=d
        if op==40: d=mem[d]
        elif op==62: mem[d]=oc.crazy_op(a,mem[d]);a=mem[d]
        elif op==39: mem[d]=mem[d]//3+(mem[d]%3)*19683;a=mem[d]
        elif op==23: a=byte
        elif op==81: break
        if step in (3,5,7,10,12,32): rows.append({'step':step,'c':oldc,'d':oldd,'op':op,'a':a,'mem70':mem[70],'mem90':mem[90]})
        if 33<=mem[c]<=126: mem[c]=oc._ENC[mem[c]]
        c=(c+1)%oc.MEM_SIZE; d=(d+1)%oc.MEM_SIZE
    return rows

def run():
    good=image(); bad=image(True)
    (P/'store.mal').write_bytes(good); (P/'mutant.mal').write_bytes(bad)
    cases=[]; runner=ROOT/'runners/malbolge-original/malbolge'
    for v in range(256):
        item={'input':v}
        for label,src in [('positive',good),('mutant',bad)]:
            out,steps,status=oc.run(src.decode('ascii'),max_steps=1000,stdin_data=chr(v),stop_on_eof=True)
            proc=subprocess.run([str(runner),str(P/('store.mal' if label=='positive' else 'mutant.mal')),'1000'],input=bytes([v]),capture_output=True)
            expected=bytes([v]) if label=='positive' else bytes([29524&255])
            t=trace(src,v)
            ok=(out.encode('latin1')==expected and proc.stdout in (expected,expected+b'\n') and status=='HALTED' and proc.returncode==0 and t[4]['mem90']==(v if label=='positive' else 29524))
            item[label]={'oracle':out.encode('latin1').hex(),'runner_raw':proc.stdout.hex(),'runner_stderr':proc.stderr.decode('utf8','replace').strip(),'steps':steps,'status':status,'trace':t,'ok':ok}
        cases.append(item)
    invalid=[i for i,v in enumerate(good) if XLAT1[(v-33+i)%94] not in 'ji*p</vo']
    payload={'hypothesis':'One-shot store and read back any input byte exactly','cases':cases,'strict_invalid_addresses':invalid,'positive_all':all(x['positive']['ok'] for x in cases),'mutant_all':all(x['mutant']['ok'] for x in cases),'sha256':hashlib.sha256(good).hexdigest(),'mutant_sha256':hashlib.sha256(bad).hexdigest()}
    (P/'results.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf8')
    print('positive:',sum(x['positive']['ok'] for x in cases),'/256; mutant:',sum(x['mutant']['ok'] for x in cases),'/256')
    print('strict loader invalid addresses:',invalid)
    for v in [0,10,13,65,255]:
        x=cases[v]; print('input',v,'positive stdout raw',x['positive']['runner_raw'],'mutant stdout raw',x['mutant']['runner_raw'],'mem90 at store',x['positive']['trace'][4]['mem90'])
    print('sha256',payload['sha256']);print('mutant_sha256',payload['mutant_sha256'])
    return 0 if payload['positive_all'] and payload['mutant_all'] else 1
if __name__=='__main__': sys.exit(run())
