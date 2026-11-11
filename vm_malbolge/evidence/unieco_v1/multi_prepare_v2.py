#!/usr/bin/env python3
"""Construct an Olmstead-loadable program preparing three phases, then HALT."""
import hashlib,importlib.util,json,os,pathlib,re,subprocess
P=pathlib.Path(__file__).resolve().parent; ROOT=pathlib.Path(os.environ['MBDB_ROOT']).resolve() if 'MBDB_ROOT' in os.environ else P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'); M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
V=M.VALID;SE=M.SE; enc=lambda op,pos:33+((op-pos-33)%94);sha=lambda b:hashlib.sha256(b).hexdigest()
ops={'NOP':68,'ROT':39,'CRAZY':62,'DLOAD':40,'HALT':81}; commands=[]; d=42; writes={}; data={41:40,42:39,47:115,48:33,49:49,50:125,51:66,52:46,64:111,65:33,66:67,67:50,68:49,122:34,123:104,124:87,125:67,126:102}
def emit(name):commands.append(name)
def walk(target):
 global d
 assert target>=d
 while d<target:emit('NOP');d+=1
def write(target):
 global d
 assert d==target;writes[target]=len(commands);emit('CRAZY');d+=1
def reset(target,value):
 global d
 assert d==target and data[target]==value;emit('DLOAD');d=value+1
walk(47);emit('ROT');d+=1
for op in ('ROT','CRAZY','CRAZY','CRAZY'):emit(op);d+=1
reset(52,46);write(47)
walk(64);emit('ROT');d+=1
for op in ('CRAZY','CRAZY','CRAZY'):emit(op);d+=1
reset(68,49);walk(64);write(64)
walk(122);emit('ROT');d+=1
emit('CRAZY');d+=1
emit('ROT');d+=1
emit('CRAZY');d+=1
reset(126,102);walk(123);write(123);emit('HALT')
# c0 MOVD, c1 ROT mem41, c2 MOVD mem42=39, c3 NOP, c4 JMP mem41.
landing=SE.rot(data[41]);start=landing+1

def build(disable=None):
 img=[enc(68,i) for i in range(start+len(commands)+1)]
 for pos,val in data.items():img[pos]=val
 for pos,op in enumerate((40,39,40,68,4)):img[pos]=enc(op,pos)
 for i,name in enumerate(commands):
  op=68 if disable is not None and i==writes[disable] else ops[name]
  img[start+i]=enc(op,start+i)
 return img

def legal(img):return all(33<=x<=126 and (x+i)%94 in V for i,x in enumerate(img))
ns={};exec(compile(M.B.INDEP.read_text().split('def trits')[0],str(M.B.INDEP),'exec'),ns)
results={'gate_commit':'6209ea1','base':'f6adbc3','landing':landing,'code_start':start,'d_after_jump':42,'initial_a':landing,'write_instruction_positions':{str(k):start+v for k,v in writes.items()},'data_initial':data,'cases':{}}
for label,disable in [('main',None),('no47',47),('no64',64),('no123',123)]:
 img=build(disable);assert legal(img);fp=P/('prepare_v2_'+label+'.mb');fp.write_bytes(bytes(img))
 sc=SE.run(bytes(img),max_steps=1000,stdin=b'',collect=True);ind=ns['run'](img,[],maxs=1000,guard=True)
 o=M.O.oracle_run(str(fp),max_steps=1000,stdin_data='',stop_on_eof=True)
 org=subprocess.run([str(M.B.OLMSTEAD),str(fp)],input=b'',capture_output=True,timeout=10)
 c=subprocess.run([str(M.B.C_RUNNER),str(fp),'1000'],input=b'',capture_output=True,timeout=10)
 for n,r in [('olmstead',org),('runner',c)]:
  (P/f'prepare_v2_{label}.{n}.stdout.raw').write_bytes(r.stdout);(P/f'prepare_v2_{label}.{n}.stderr.raw').write_bytes(r.stderr)
 events=[{'step':e['step'],'pc':e['pc'],'op':e['op'],'d':e['d']} for e in sc['events']]
 match=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',c.stderr)
 vals={str(t):sc['mem'][t] for t in (47,64,123)}
 checks={'strict_loader_all_cells':legal(img),'no_in_out':all(e['op'] not in (5,23) for e in events),'scratch_halt':sc['status']=='HALTED','independent_halt':ind['status']=='HALTED','oracle_halt':o['status']=='HALTED','equal_steps':sc['steps']==ind['steps']==o['steps'],'scratch_independent_memory_equal':sc['mem']==ind['mem'],'olmstead_halt_no_output':org.returncode==0 and org.stdout==b'' and org.stderr==b'','runner_halt':c.returncode==0 and match is not None and int(match.group(1))==sc['steps'] and match.group(2)==b'HALTED','expected_targets':all(v==74 for v in vals.values()) if disable is None else vals[str(disable)]!=74}
 results['cases'][label]={'sha256':sha(bytes(img)),'source_length':len(img),'steps':sc['steps'],'target_values':vals,'checks':checks,'all_checks':all(checks.values()),'trace':events,'oracle':o,'runner_stderr':c.stderr.decode('latin1')}
(P/'multi_prepare_v2.results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
