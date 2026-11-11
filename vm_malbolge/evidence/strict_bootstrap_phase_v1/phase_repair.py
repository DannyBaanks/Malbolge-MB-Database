#!/usr/bin/env python3
"""Find and execute loader-valid, no-I/O phase-repair witnesses."""
import hashlib,importlib.util,json,os,pathlib,re,subprocess
P=pathlib.Path(__file__).resolve().parent; ROOT=pathlib.Path(os.environ['MBDB_ROOT']).resolve() if 'MBDB_ROOT' in os.environ else P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'); M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
V=M.VALID; SE=M.SE; names={'NOP':68,'ROT':39,'CRAZY':62,'DLOAD':40,'HALT':81}
enc=lambda op,pos:33+((op-pos-33)%94)
vals=lambda pos:[v for v in range(33,127) if (v+pos)%94 in V]
sha=lambda b:hashlib.sha256(b).hexdigest()

def find(target,seed,initial,first):
 w=SE.rot(initial) if first=='ROT' else SE.crazy(0,initial)
 states={w:[]}
 for k in range(9):
  if k:
   pos=target+k; nx={}
   for a,path in states.items():
    for x in vals(pos):
     nx.setdefault(SE.crazy(a,x),path+[(pos,'CRAZY',x)])
     nx.setdefault(SE.rot(x),path+[(pos,'ROT',x)])
    nx.setdefault(a,path+[(pos,'NOP',None)])
   states=nx
  for a,path in states.items():
   if SE.crazy(a,w)!=74:continue
   reset=target+k+1
   for rv in vals(reset):
    if rv+1>target:continue
    first_pc=2+target-(seed+1); reset_pc=first_pc+1+k
    final_pc=reset_pc+1+(target-(rv+1))
    if final_pc+1>=41:continue
    return dict(target=target,seed=seed,initial=initial,first=first,intermediate=w,helpers=path,reset_pos=reset,reset_value=rv,accumulator_before_final=a,first_pc=first_pc,reset_pc=reset_pc,final_pc=final_pc,halt_pc=final_pc+1)
 raise ValueError('no witness within bounded search')

def build(p,control=False):
 L=max(p['target'],p['reset_pos'])+2; img=[enc(68,i) for i in range(L)]
 img[0]=enc(40,0);img[1]=enc(40,1);img[41]=p['seed'];img[p['target']]=p['initial']
 img[p['first_pc']]=enc(names[p['first']],p['first_pc'])
 for i,(pos,op,v) in enumerate(p['helpers']):
  if v is not None:img[pos]=v
  pc=p['first_pc']+1+i;img[pc]=enc(names[op],pc)
 img[p['reset_pos']]=p['reset_value'];img[p['reset_pc']]=enc(40,p['reset_pc'])
 img[p['final_pc']]=enc(68 if control else 62,p['final_pc']);img[p['halt_pc']]=enc(81,p['halt_pc'])
 return img

def loader_valid(img):return all(33<=v<=126 and (v+i)%94 in V for i,v in enumerate(img))
ns={};exec(compile(M.B.INDEP.read_text().split('def trits')[0],str(M.B.INDEP),'exec'),ns)
results={'base':'9163d87','max_helpers':8,'search_scope':'fixed seed, first target value/op per target; helper data loader-valid; NOP/ROT/CRAZY; one reset DLOAD; final CRAZY before pc 40','orientation':'crazy(accumulator,cell)=table[cell trit][accumulator trit]','targets':{}}
for target,seed,initial,first in [(47,40,115,'ROT'),(64,57,111,'ROT'),(123,115,39,'CRAZY')]:
 p=find(target,seed,initial,first);img=build(p); ctrl=build(p,True)
 assert loader_valid(img) and loader_valid(ctrl)
 fp=P/f'repair_{target}.mb';fc=P/f'ctrl_no_final_crazy_{target}.mb';fp.write_bytes(bytes(img));fc.write_bytes(bytes(ctrl))
 sc=SE.run(bytes(img),max_steps=200,stdin=b'',collect=True); ind=ns['run'](img,[],maxs=200,guard=True)
 oracle=M.O.oracle_run(str(fp),max_steps=200,stdin_data='',stop_on_eof=True)
 ctrl_sc=SE.run(bytes(ctrl),max_steps=200,stdin=b'',collect=True)
 org=subprocess.run([str(M.B.OLMSTEAD),str(fp)],input=b'',capture_output=True,timeout=10)
 orgctrl=subprocess.run([str(M.B.OLMSTEAD),str(fc)],input=b'',capture_output=True,timeout=10)
 cr=subprocess.run([str(M.B.C_RUNNER),str(fp),'200'],input=b'',capture_output=True,timeout=10)
 for key,r in [('olmstead',org),('control_olmstead',orgctrl),('runner',cr)]:
  (P/f'repair_{target}.{key}.stdout.raw').write_bytes(r.stdout);(P/f'repair_{target}.{key}.stderr.raw').write_bytes(r.stderr)
 events=[{'step':e['step'],'pc':e['pc'],'op':e['op'],'d':e['d']} for e in sc['events']]
 io=any(x['op'] in (5,23) for x in events)
 runner_match=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',cr.stderr)
 check={'strict_image':loader_valid(img),'strict_control':loader_valid(ctrl),'scratch_halt':sc['status']=='HALTED','independent_halt':ind['status']=='HALTED','oracle_halt':oracle['status']=='HALTED','equal_steps':sc['steps']==ind['steps']==oracle['steps'],'no_in_out':not io,'target_74':sc['mem'][target]==ind['mem'][target]==74,'full_mem_match':sc['mem']==ind['mem'],'control_rejects_74':ctrl_sc['mem'][target]!=74,'olmstead_halt':org.returncode==0 and org.stdout==b'' and org.stderr==b'','control_olmstead_halt':orgctrl.returncode==0 and not orgctrl.stdout and not orgctrl.stderr,'runner_halt':cr.returncode==0 and runner_match is not None and int(runner_match.group(1))==sc['steps'] and runner_match.group(2)==b'HALTED'}
 results['targets'][str(target)]={'params':p,'image_sha256':sha(bytes(img)),'control_sha256':sha(bytes(ctrl)),'image_length':len(img),'trace':events,'steps':sc['steps'],'final_target':sc['mem'][target],'control_target':ctrl_sc['mem'][target],'oracle':oracle,'runner_stderr':cr.stderr.decode('latin1'),'checks':check,'all_checks':all(check.values())}
(P/'phase_repair.results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
