#!/usr/bin/env python3
"""Check independently compiled byte-increment stream and negative controls."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import pathlib
import resource
import random
import subprocess
import sys
import tempfile

P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];IMAGE=pathlib.Path(sys.argv[1]);OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead'
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bf=module('bf16',ROOT/'vm_malbolge/evidence/unieco_rea_eof_v2/bf16.py');m=module('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');se=m.SE
bf_source=(ROOT/'vm_malbolge/evidence/byte_increment_v1/increment.bf').read_text();reference=ROOT/'vm_malbolge/evidence/byte_increment_v1/reference.py';image=IMAGE.read_bytes()
cases={'empty':b'','ascii':b'ABCD','nul_ff_repeated':bytes([0,255,0,255,128,128]),'all_bytes':bytes(range(256)),'long_10000':bytes((73*i+195)%256 for i in range(10000))}
cases.update({f'byte_{i:03}':bytes([i]) for i in range(256)})
rng=random.Random(20261112)
for i in range(256):
    cases[f'random_{i:03}']=bytes(rng.randrange(256) for _ in range(rng.randrange(0,257)))
records={}
for name,data in cases.items():
    expected=bytes((b+1)&255 for b in data)
    py=subprocess.run([sys.executable,str(reference)],input=data,capture_output=True,timeout=20)
    bout,status,bsteps,consumed=bf.run(bf_source,data)
    native=subprocess.run([str(OL),str(IMAGE)],input=data,capture_output=True,timeout=20)
    assert py.returncode==native.returncode==0 and py.stdout==bout==native.stdout==expected and status=='HALTED' and consumed==len(data),name
    records[name]={'input_bytes':len(data),'input_sha256':hashlib.sha256(data).hexdigest(),'output_sha256':hashlib.sha256(native.stdout).hexdigest(),'python_rc':py.returncode,'bf_status':status,'bf_steps':bsteps,'bf_consumed':consumed,'native_rc':native.returncode,'native_stderr_hex':native.stderr.hex()}
# Instrumented independent model: no host stop at EOF; record actual same-PC visits.
def trace(data):
    mem=list(image)+[0]*(59049-len(image))
    for i in range(len(image),59049):mem[i]=se.crazy(mem[i-1],mem[i-2])
    a=c=d=used=0;out=bytearray();visits=[]
    for step in range(1,250000):
        if not 33<=mem[c]<=126:raise AssertionError('nonprintable instruction')
        pc=c;op=(mem[c]+c)%94
        if pc in (56725,56707,58689):visits.append({'step':step,'pc':pc,'word':mem[c],'opcode':op,'d':d,'a':a})
        if op==4:
            c=mem[d]
            if not 33<=mem[c]<=126:raise AssertionError('nonprintable jump')
        elif op==5:out.append(a%256)
        elif op==23:
            a=data[used] if used<len(data) else 59048;used+=1
        elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
        elif op==40:d=mem[d]
        elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
        elif op==81:return {'status':'HALTED','steps':step,'output_hex':out.hex(),'input_instructions':used,'visits':visits}
        if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
        c=(c+1)%59049;d=(d+1)%59049
    raise AssertionError('model exceeded step budget')
models={}
for name in ('empty','ascii','nul_ff_repeated'):
    data=cases[name];v=trace(data);assert v['output_hex']==bytes((b+1)&255 for b in data).hex() and v['input_instructions']==len(data)+1
    models[name]=v
assert len([v for v in models['ascii']['visits'] if v['pc']==56725 and v['opcode']==23])==5
assert len([v for v in models['ascii']['visits'] if v['pc']==56707 and v['opcode']==5])==4
with tempfile.TemporaryDirectory(prefix='increment-controls-') as tmp:
    t=pathlib.Path(tmp)
    badloader=bytearray(image);badloader[0]=33;badpath=t/'loader.mb';badpath.write_bytes(badloader)
    br=subprocess.run([str(OL),str(badpath)],input=b'ABCD',capture_output=True,timeout=3)
    assert br.returncode!=0 and not br.stdout
    # An installer corruption control: substitute NOP for CRAZY at 56205.
    sys.path.insert(0,str(ROOT/'vm_malbolge/tools/increment_bf/backend'))
    from constants import XLAT1
    pos=56205;assert (image[pos]+pos)%94==62
    corrupt=bytearray(image);corrupt[pos]=33+((XLAT1.index('o')-pos)%94);cp=t/'writer.mb';cp.write_bytes(corrupt)
    assert all((v+i)%94 in m.VALID for i,v in enumerate(corrupt))
    try:
        cr=subprocess.run([str(OL),str(cp)],input=b'ABCD',capture_output=True,timeout=2)
        control={'status':'exited','rc':cr.returncode,'stdout_hex':cr.stdout.hex()}
        assert cr.returncode!=0 or cr.stdout!=b'BCDE'
    except subprocess.TimeoutExpired as e:control={'status':'timeout','stdout_hex':(e.stdout or b'').hex()}
    # Suppress the final installer write to the first EOF-branch code cell.
    eofpos=56098;assert (image[eofpos]+eofpos)%94==62
    broken_eof=bytearray(image);broken_eof[eofpos]=33+((XLAT1.index('o')-eofpos)%94);ep=t/'eof.mb';ep.write_bytes(broken_eof)
    assert all((v+i)%94 in m.VALID for i,v in enumerate(broken_eof))
    try:
        er=subprocess.run([str(OL),str(ep)],input=b'',capture_output=True,timeout=1)
        eof_control={'status':'exited','rc':er.returncode,'stdout_hex':er.stdout.hex()}
        assert er.returncode!=0 or er.stdout
    except subprocess.TimeoutExpired as e:eof_control={'status':'timeout','stdout_hex':(e.stdout or b'').hex()}
    compiler=ROOT/'vm_malbolge/tools/increment_bf/compile.py';badbf=t/'bad.bf';badbf.write_text(',+[-.,+]')
    refused=subprocess.run([sys.executable,str(compiler),str(badbf),'--output',str(t/'bad.mb')],capture_output=True,text=True,timeout=3)
    badsem=subprocess.run([sys.executable,str(compiler),str(ROOT/'vm_malbolge/evidence/byte_increment_v1/increment.bf'),'--output',str(t/'badsem.mb'),'--eof','0'],capture_output=True,text=True,timeout=3)
    assert refused.returncode==2 and badsem.returncode==2 and not (t/'bad.mb').exists() and not (t/'badsem.mb').exists()
    controls={'loader_rc':br.returncode,'loader_stderr_hex':br.stderr.hex(),'writer_pc':pos,'writer':control,'eof_writer_pc':eofpos,'eof_writer':eof_control,'bf_pattern_refused_rc':refused.returncode,'bf_eof_refused_rc':badsem.returncode}
print(json.dumps({'image_sha256':hashlib.sha256(image).hexdigest(),'strict':all((v+i)%94 in m.VALID for i,v in enumerate(image)),'cases':records,'models':models,'controls':controls,'scope':'finite cases, BF16 EOF 65535, Olmstead EOF 59048'},indent=2))
