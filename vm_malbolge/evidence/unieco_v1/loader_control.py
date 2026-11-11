#!/usr/bin/env python3
import hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('m',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
b=bytearray((P/'prepare_v2_main.mb').read_bytes());old=b[0];b[0]=33;assert 33 not in m.VALID
f=P/'ctrl_invalid_loader.mb';f.write_bytes(b)
r=subprocess.run([str(m.B.OLMSTEAD),str(f)],input=b'',capture_output=True,timeout=10)
(P/'ctrl_invalid_loader.stdout.raw').write_bytes(r.stdout);(P/'ctrl_invalid_loader.stderr.raw').write_bytes(r.stderr)
x={'original_first':old,'mutant_first':33,'sha256':hashlib.sha256(b).hexdigest(),'rc':r.returncode,'stderr':r.stderr.decode('latin1'),'rejected':r.returncode==1 and b'invalid character' in r.stderr};(P/'loader_control.results.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x,indent=2));assert x['rejected']
