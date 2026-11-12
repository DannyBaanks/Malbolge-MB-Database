#!/usr/bin/env python3
"""Mutate the last bootstrap write to each requested phase cell."""
import hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('m',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
image=(P/'candidate.mb').read_bytes();p=json.loads((P/'synthesis.results.json').read_text());shift=p['shift']; init=M.SE.run(image,max_steps=4040,stdin=b'',collect=True)
targets={'in0':shift+43,'in1':shift+47,'dload0':shift+60,'dload1':shift+64,'out0':shift+119,'out1':shift+123,'jump_table':shift+125}
data=b'AbcdQ'; cap=4040+4*82
r={}
for name,target in targets.items():
 writes=[e for e in init['events'] if e['d']==target and e['op'] in (39,62)];assert writes
 e=writes[-1];pc=e['pc'];image2=bytearray(image);image2[pc]=33+((68-pc-33)%94)
 legal=all(33<=v<=126 and (v+i)%94 in M.VALID for i,v in enumerate(image2));assert legal
 f=P/('ctrl_writer_'+name+'.mb');f.write_bytes(image2)
 sc=M.SE.run(bytes(image2),max_steps=cap,stdin=data,collect=True)
 c=subprocess.run([str(M.B.C_RUNNER),str(f),str(cap)],input=data,capture_output=True,timeout=15)
 (P/('ctrl_writer_'+name+'.runner.stdout.raw')).write_bytes(c.stdout);(P/('ctrl_writer_'+name+'.runner.stderr.raw')).write_bytes(c.stderr)
 r[name]={'target':target,'mutated_pc':pc,'original_op':e['op'],'new_op':(image2[pc]+pc)%94,'loader_valid':legal,'sha256':hashlib.sha256(image2).hexdigest(),'scratch_status':sc['status'],'scratch_steps':sc['steps'],'scratch_output_hex':sc['out'].hex(),'runner_rc':c.returncode,'runner_output_hex':c.stdout.hex(),'runner_stderr':c.stderr.decode('latin1'),'breaks_observed_echo':sc['out']!=data[:4],'runner_matches_scratch_plus_newline':c.stdout==sc['out']+b'\n'}
(P/'phase_controls.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
