#!/usr/bin/env python3
"""Loader-valid rotation prefixes and exact one-step crazy reachability."""
import hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'); M=importlib.util.module_from_spec(s); s.loader.exec_module(M)
V=M.VALID; T=((1,0,0),(1,0,2),(2,2,1)); sha=lambda b:hashlib.sha256(b).hexdigest()
def char(op,pos):return 33+((op-pos-33)%94)
def valid_source(img):return all(33<=x<=126 and (x+i)%94 in V for i,x in enumerate(img))
def witness(cell,target):
 a=0; mul=1
 for _ in range(10):
  opts=[x for x in range(3) if T[cell%3][x]==target%3]
  if not opts:return None
  a+=opts[0]*mul; mul*=3;cell//=3;target//=3
 return a

def img_for(target,seed,initial):
 img=[char(68,i) for i in range(target+2)]
 img[0]=char(40,0);img[1]=char(40,1);img[41]=seed;img[target]=initial
 at=2+target-(seed+1); img[at]=char(39,at); img[at+1]=char(81,at+1)
 return img,at
result={'base':'2eadc75','gates_commit':'9163d87','orientation':'crazy(accumulator,cell) = T[cell trit][accumulator trit]','direct_crazy':{},'rotate_then_crazy_algebra':{},'prefixes':{}}
for target in (47,64,123):
 initial=[v for v in range(33,127) if (v+target)%94 in V]
 direct=[{'initial':v,'accumulator':a} for v in initial if (a:=witness(v,74)) is not None]
 indirect=[]
 for v in initial:
  rotated=M.SE.rot(v); a=witness(rotated,74)
  if a is not None:
   assert M.SE.crazy(a,rotated)==74
   indirect.append({'initial':v,'rotated':rotated,'arbitrary_accumulator_needed':a})
 result['direct_crazy'][str(target)]={'legal_initial':initial,'reachable_74':direct}
 result['rotate_then_crazy_algebra'][str(target)]=indirect
ns={}; exec(compile(M.B.INDEP.read_text().split('def trits')[0],str(M.B.INDEP),'exec'),ns)
for target,seed,initial in [(47,40,115),(64,57,111)]:
 img,at=img_for(target,seed,initial); control=list(img);control[at]=char(68,at)
 assert valid_source(img) and valid_source(control)
 image=P/('prefix_'+str(target)+'.mb'); cp=P/('ctrl_norot_'+str(target)+'.mb'); image.write_bytes(bytes(img)); cp.write_bytes(bytes(control))
 sc=M.SE.run(bytes(img),max_steps=100,stdin=b'',collect=True); ind=ns['run'](img,[],maxs=100,guard=True); oracle=M.O.oracle_run(str(image),max_steps=100,stdin_data='',stop_on_eof=True)
 sr=M.SE.run(bytes(control),max_steps=100,stdin=b'',collect=True)
 original=subprocess.run([str(M.B.OLMSTEAD),str(image)],input=b'',capture_output=True,timeout=10)
 c=subprocess.run([str(M.B.C_RUNNER),str(image),'100'],input=b'',capture_output=True,timeout=10)
 for n,r in [('olmstead',original),('runner_c',c)]:
  (P/(f'prefix_{target}.{n}.stdout.raw')).write_bytes(r.stdout);(P/(f'prefix_{target}.{n}.stderr.raw')).write_bytes(r.stderr)
 events=[{'step':e['step'],'pc':e['pc'],'op':e['op'],'d':e['d']} for e in sc['events']]
 result['prefixes'][str(target)]={'image_sha256':sha(bytes(img)),'control_sha256':sha(bytes(control)),'source_loader_valid':valid_source(img),'control_loader_valid':valid_source(control),'rotation_pc':at,'trace':events,'scratch_steps':sc['steps'],'scratch_status':sc['status'],'independent_steps':ind['steps'],'independent_status':ind['status'],'oracle':oracle,'original_rc':original.returncode,'original_stdout_hex':original.stdout.hex(),'original_stderr':original.stderr.decode('latin1'),'runner_rc':c.returncode,'runner_stdout_hex':c.stdout.hex(),'runner_stderr':c.stderr.decode('latin1'),'target_initial':initial,'target_expected':M.SE.rot(initial),'scratch_target':sc['mem'][target],'independent_target':ind['mem'][target],'control_target':sr['mem'][target],'no_in_out':all(e['op'] not in (5,23) for e in sc['events']),'changed_to_74':sc['mem'][target]==74,'memory_equal':sc['mem']==ind['mem']}
 result['prefixes'][str(target)]['checks_pass']=all([sc['status']==ind['status']=='HALTED',sc['steps']==ind['steps']==oracle['steps'],original.returncode==0,not original.stdout,not original.stderr,sc['mem'][target]==ind['mem'][target]==M.SE.rot(initial),sr['mem'][target]==initial,result['prefixes'][str(target)]['no_in_out'],result['prefixes'][str(target)]['memory_equal']])
(P/'results.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
