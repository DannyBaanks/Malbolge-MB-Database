#!/usr/bin/env python3
import importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('m',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
img=(P/'candidate.mb').read_bytes();p=json.loads((P/'synthesis.results.json').read_text());desired={int(k):v for k,v in json.loads((P/'target_cells.json').read_text()).items()};budget=p['plan_length']+300
x=M.SE.run(img,max_steps=budget,stdin=b'A'*10,collect=True)
first=next((e for e in x['events'] if e['op']==23),None)
r={'search_budget':budget,'scratch_status':x['status'],'steps':x['steps'],'first_input':first,'pre_input_outputs':sum(e['op']==5 for e in x['events'][:first['step']-1]) if first else None}
if first:
 y=M.SE.run(img,max_steps=first['step']-1,stdin=b'A',collect=False); expected=dict(desired); expected[p['shift']+42]=M.SE.encrypt(42)
 mismatches=[{'pos':i,'actual':y['mem'][i],'expected':v} for i,v in expected.items() if y['mem'][i]!=v]
 r['handoff']={'pc_ok':first['pc']==p['handoff_c'],'d_ok':first['d']==p['handoff_d'],'expected_memory':len(expected),'mismatches':mismatches,'pre_input_output_empty':not y['out'],'steps_before_first_input':first['step']-1}
 c=subprocess.run([str(M.B.C_RUNNER),str(P/'candidate.mb'),str(first['step'])],input=b'A',capture_output=True,timeout=20)
 (P/'candidate_runner.stdout.raw').write_bytes(c.stdout);(P/'candidate_runner.stderr.raw').write_bytes(c.stderr)
 r['runner']={'rc':c.returncode,'stdout_hex':c.stdout.hex(),'stderr':c.stderr.decode('latin1')}
(P/'probe_candidate.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
