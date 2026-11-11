#!/usr/bin/env python3
"""Use BolgeForge's pure inverse function without importing its build side effects."""
import ast,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];path=ROOT.parent/'BolgeForge/tools/resynthesize.py'; text=path.read_text(); tree=ast.parse(text)
nodes=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INV_CRZ' for t in node.targets):nodes.append(node)
 if isinstance(node,ast.FunctionDef) and node.name=='find_a_for_crazy':nodes.append(node)
assert len(nodes)==2
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),ns)
plan=json.loads((ROOT/'vm_malbolge/evidence/unieco_v1/write_plan.results.json').read_text());cases=[]
for row in plan['cases']:
 actual=ns['find_a_for_crazy'](row['prepared'],row['needed']); expected=row['one_crazy_controls']; expected=None if expected is None else expected[0]
 cases.append({'cell':row['cell'],'forge_accumulator':actual,'prior_accumulator':expected,'match':actual==expected})
r={'source':'BolgeForge/tools/resynthesize.py','source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'only pure inverse CRAZY feasibility; not solve_sp, scratchpad bootstrap, full write scheduling, or executable Malbolge','cases':cases,'count':len(cases),'one_step_count':sum(x['forge_accumulator'] is not None for x in cases),'all_agree':all(x['match'] for x in cases)}
(P/'forge_crosscheck_v2.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='cases'},indent=2));assert r['all_agree']
