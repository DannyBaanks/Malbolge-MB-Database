#!/usr/bin/env python3
"""Check compiler refusal and preservation of an existing output."""
import hashlib,json,pathlib,subprocess,sys,tempfile
P=pathlib.Path(__file__).resolve().parent;root=P.parents[2];compiler=root/'vm_malbolge/tools/increment_bf/compile.py';bf=root/'vm_malbolge/evidence/byte_increment_v1/increment.bf'
with tempfile.TemporaryDirectory(prefix='bf-compiler-controls-') as tmp:
    p=pathlib.Path(tmp);existing=p/'existing.mb';existing.write_bytes(b'keep this exact content\n');old=hashlib.sha256(existing.read_bytes()).hexdigest()
    cases={'existing_output':[sys.executable,str(compiler),str(bf),'--output',str(existing)],'wrong_cell_bits':[sys.executable,str(compiler),str(bf),'--output',str(p/'bits.mb'),'--cell-bits','8'],'wrong_eof':[sys.executable,str(compiler),str(bf),'--output',str(p/'eof.mb'),'--eof','0']}
    bad=p/'mutant.bf';bad.write_text(',+[-.,+]');cases['changed_bf']=[sys.executable,str(compiler),str(bad),'--output',str(p/'mutant.mb')]
    results={}
    for name,cmd in cases.items():
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=10);results[name]={'rc':r.returncode,'stderr':r.stderr.strip()};assert r.returncode==2
    new=hashlib.sha256(existing.read_bytes()).hexdigest();assert old==new
    assert all(not (p/name).exists() for name in ('bits.mb','eof.mb','mutant.mb'))
    print(json.dumps({'cases':results,'existing_sha256_before':old,'existing_sha256_after':new,'unchanged':old==new},indent=2))
