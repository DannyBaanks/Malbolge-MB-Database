#!/usr/bin/env python3
"""Capture raw input and outputs independently of the summary probe."""
import importlib.util, pathlib, subprocess
P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[2]
OLD=ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
spec=importlib.util.spec_from_file_location('compose',OLD)
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
image=(P/'compose_inout.mb').read_bytes()
data=bytes((i*73+195)%256 for i in range(10001)); limit=820043
scratch=M.SE.run(image,max_steps=limit,stdin=data)
ns={}; exec(compile(M.B.INDEP.read_text().split('def trits')[0],str(M.B.INDEP),'exec'),ns)
ind=ns['run'](list(image),list(data),maxs=limit,guard=True)
oracle=M.O.oracle_run(str(P/'compose_inout.mb'),max_steps=limit,stdin_data=data.decode('latin1'),stop_on_eof=True)
c=subprocess.run([str(M.B.C_RUNNER),str(P/'compose_inout.mb'),str(limit)],input=data,capture_output=True,check=True,timeout=120)
outputs={'input.raw':data,'scratch.raw':scratch['out'],'independent.raw':ind['out'],'oracle.raw':oracle['output'].encode('latin1'),'runner_c.raw':c.stdout,'runner_c.stderr.raw':c.stderr}
for name,content in outputs.items():
 with (P/name).open('xb') as f: f.write(content)
assert scratch['out']==ind['out']==oracle['output'].encode('latin1')==data[:10000]
assert c.stdout==data[:10000]+b'\n'
assert scratch['steps']==ind['steps']==oracle['steps']==limit
print('raw input and four outputs captured; byte comparisons matched; runner C includes final wrapper newline')
