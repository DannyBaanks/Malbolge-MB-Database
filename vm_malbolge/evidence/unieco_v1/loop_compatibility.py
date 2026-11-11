#!/usr/bin/env python3
"""Compare post-preparation memory with the earlier compact loop requirements."""
import hashlib,importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
prepared=(P/'prepare_v2_main.mb').read_bytes(); original=(ROOT/'vm_malbolge/evidence/epoch_dload_inout_v1/compose_inout.mb').read_bytes()
sc=M.SE.run(prepared,max_steps=1000,stdin=b''); assert sc['status']=='HALTED'; mem=sc['mem'];p=43;j=124
points=[]
for pos in range(p,j):
 if pos in (43,47,60,64,119,123):continue
 v=33+((68-pos-33)%94); cyc=next(c for c in M.B.CYCLES if v in c);ops=sorted({(z+pos)%94 for z in cyc}&M.VALID)
 points.append({'pos':pos,'loader_nop':v,'cycle_len':len(cyc),'valid_ops':ops,'safe':all(x==68 for x in ops)})
relevant=sorted(set(range(43,125))|{125,126,143,148})
differences=[{'pos':i,'post_prepare':mem[i],'old_image':original[i],'equal':mem[i]==original[i]} for i in relevant if mem[i]!=original[i]]
r={'prepared_sha256':hashlib.sha256(prepared).hexdigest(),'original_sha256':hashlib.sha256(original).hexdigest(),'prepared_halted_steps':sc['steps'],'required_phase_cells':{str(x):mem[x] for x in (47,64,123)},'loader_nop_fillers':points,'unsafe_count':sum(not x['safe'] for x in points),'unsafe_positions':[x['pos'] for x in points if not x['safe']],'differences_against_original_source_count':len(differences),'differences_against_original_source':differences,'caveat':'old_image is original source, not necessarily first loop-entry runtime state; differences do not individually prove failure'}
(P/'loop_compatibility.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
