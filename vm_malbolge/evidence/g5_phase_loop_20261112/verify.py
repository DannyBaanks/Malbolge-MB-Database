#!/usr/bin/env python3
"""Bounded model and native checks for the two-phase loop."""
import hashlib
import importlib.util
import json
import os
import pathlib
import select
import subprocess
import sys
import time

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
out = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('compose', ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
se=m.SE; N=59049
cfg=json.loads((out/'synthesis.json').read_text()); records={}
for tag in ('positive','control'):
    image=(out/f'{tag}.mb').read_bytes(); mem=list(image)+[0]*(N-len(image))
    for i in range(len(image),N): mem[i]=se.crazy(mem[i-1],mem[i-2])
    a=c=d=0; data=b'ABCD'; used=0; output=[]; visits=[]; bad=None
    for step in range(1, 20001):
        if not 33<=mem[c]<=126: bad=f'nonprintable pc {c}'; break
        pc=c; op=(mem[c]+c)%94
        if c in [*cfg['positions'].values(),cfg['end']]:
            visits.append({'step':step,'pc':c,'d':d,'a':a,'word':mem[c],'op':op})
        if op==4:
            c=mem[d]
            if not 33<=mem[c]<=126: bad=f'nonprintable jump {c}'; break
        elif op==5: output.append(a%256)
        elif op==23:
            a=data[used] if used<len(data) else 59048
            used+=1
        elif op==39: mem[d]=se.rot(mem[d]); a=mem[d]
        elif op==40: d=mem[d]
        elif op==62: mem[d]=se.crazy(a,mem[d]); a=mem[d]
        elif op==81: bad='unexpected HALT'; break
        if 33<=mem[c]<=126: mem[c]=se.encrypt(mem[c])
        c=(c+1)%N; d=(d+1)%N
        if len(output)>=5: break
    native=subprocess.Popen(['stdbuf','-o0',str(ROOT.parent/'Malbolge-PureEpoch/build/olmstead'),str(out/f'{tag}.mb')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    native.stdin.write(data); native.stdin.close(); chunks=b''; deadline=time.monotonic()+5
    while len(chunks)<5 and time.monotonic()<deadline:
        ready,_,_=select.select([native.stdout],[],[],max(0,deadline-time.monotonic()))
        if not ready: break
        part=os.read(native.stdout.fileno(),5-len(chunks))
        if not part: break
        chunks+=part
    native.terminate()
    try: native.wait(timeout=2)
    except subprocess.TimeoutExpired: native.kill();native.wait(timeout=2)
    records[tag]={'sha256':hashlib.sha256(image).hexdigest(),'strict':all((v+i)%94 in m.VALID for i,v in enumerate(image)),'model_status':'bounded' if bad is None else bad,'model_steps':step,'model_output_hex':bytes(output).hex(),'model_visits':visits,'native_prefix_hex':chunks.hex(),'native_terminated_by_harness':True,'native_rc':native.returncode}
    assert bad is None and records[tag]['strict'] and chunks==bytes(output)
expected='41424344a8'
assert records['positive']['model_output_hex']==expected
assert records['control']['model_output_hex']!=expected
for name,opcode in [('movd',40),('in',23),('out',5)]:
    v=[x for x in records['positive']['model_visits'] if x['pc']==cfg['positions'][name]]
    assert len(v)>=7 and [x['op'] for x in v[:7:2]]==[opcode]*4
    assert all(x['op'] not in {4,5,23,39,40,62,81} for x in v[1:7:2])
print(json.dumps(records,indent=2))
