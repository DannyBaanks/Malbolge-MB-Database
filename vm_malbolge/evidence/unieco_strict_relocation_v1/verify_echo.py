#!/usr/bin/env python3
"""Verify relocated strict loop; explicitly bound the nonterminating EOF case."""
import array,hashlib,importlib.util,json,pathlib,re,selectors,subprocess,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('m',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
SE=M.SE;N=M.N;img=(P/'candidate.mb').read_bytes();p=json.loads((P/'synthesis.results.json').read_text()); start=p['handoff_c'];shift=p['shift'];jmp=shift+124;tramp=shift+42
stream=bytes((73*i+195)%256 for i in range(10001)); expected=stream[:10000];cap=4040+820000
sha=lambda b:hashlib.sha256(b).hexdigest()
def memhash(m):return sha(array.array('q',m).tobytes())
def trace(image,limit,data):
 mem=list(image)+[0]*(N-len(image))
 for i in range(len(image),N):mem[i]=SE.crazy(mem[i-1],mem[i-2])
 a=c=d=ip=0;out=bytearray();body=[];rounds=[];starts=[];dests=[];pre_io=[];started=False;status='MAX'
 for st in range(1,limit+1):
  if c==start:started=True;starts.append(d)
  v=mem[c]
  if not 33<=v<=126:status='NONPRINT';break
  op=(v+c)%94
  if not started and op in (5,23):pre_io.append(op)
  if start<=c<=jmp and op in M.VALID:body.append(op)
  if op==4:
   dst=mem[d]
   if start<=c<=jmp:rounds.append(body);body=[];dests.append(dst)
   c=dst
  elif op==5:out.append(a%256)
  elif op==23:
   if ip>=len(data):status='EOF';break
   a=data[ip];ip+=1
  elif op==39:mem[d]=SE.rot(mem[d]);a=mem[d]
  elif op==40:d=mem[d]
  elif op==62:mem[d]=SE.crazy(a,mem[d]);a=mem[d]
  elif op==81:status='HALTED';break
  if 33<=mem[c]<=126:mem[c]=SE.encrypt(mem[c])
  c=(c+1)%N;d=(d+1)%N
 return {'steps':st,'status':status,'mem':mem,'out':bytes(out),'consumed':ip,'pre_io':pre_io,'rounds':rounds,'starts':starts,'dests':dests,'regs':[a,c,d]}
t=trace(img,cap,stream); sc=SE.run(img,max_steps=cap,stdin=stream)
ns={};exec(compile(M.B.INDEP.read_text().split('def trits')[0],str(M.B.INDEP),'exec'),ns); ind=ns['run'](list(img),list(stream),maxs=cap,guard=True)
o=M.O.oracle_run(str(P/'candidate.mb'),max_steps=cap,stdin_data=stream.decode('latin1'),stop_on_eof=True);oo=o['output'].encode('latin1')
c=subprocess.run([str(M.B.C_RUNNER),str(P/'candidate.mb'),str(cap)],input=stream,capture_output=True,timeout=120)
for name,b in [('input.raw',stream),('trace_output.raw',t['out']),('scratch_output.raw',sc['out']),('independent_output.raw',ind['out']),('oracle_output.raw',oo),('runner_output.raw',c.stdout),('runner_stderr.raw',c.stderr)]: (P/name).write_bytes(b)
# The original Olmstead process does not stop on EOF: capture bounded output and terminate only this child.
input_path=P/'native_input.raw';input_path.write_bytes(expected)
with input_path.open('rb') as f:
 proc=subprocess.Popen([str(M.B.OLMSTEAD),str(P/'candidate.mb')],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
 sel=selectors.DefaultSelector();sel.register(proc.stdout,selectors.EVENT_READ);buf=bytearray();deadline=time.monotonic()+15
 while len(buf)<len(expected)+100 and time.monotonic()<deadline:
  if not sel.select(timeout=.2):
   if proc.poll() is not None:break
   continue
  b=proc.stdout.read(8192)
  if not b:break
  buf.extend(b)
 stopped=proc.poll() is None
 if stopped:proc.terminate()
 tail,err=proc.communicate(timeout=5);buf.extend(tail or b'');sel.close()
(P/'olmstead_bounded.stdout.raw').write_bytes(buf);(P/'olmstead_bounded.stderr.raw').write_bytes(err)
# Loader-valid mutation of final preamble CRAZY, checked under the same finite budget.
ops=(P/'plan.ops').read_text().strip(); idx=ops.rfind('p');assert idx>=0;pos=99+idx
ctl=bytearray(img);ctl[pos]=33+((M.O._DECODE.index('o')-pos)%94) if hasattr(M.O,'_DECODE') else 33+((68-pos-33)%94)
# NOP uses normalized opcode 68, independent of decode table representation.
ctl[pos]=33+((68-pos-33)%94);(P/'ctrl_no_last_crazy.mb').write_bytes(ctl)
control=trace(ctl,cap,stream)
match=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',c.stderr)
checks={'10000_rounds':len(t['rounds'])==10000,'one_in_dload_out_jmp':all(x==[23,40,5,4] for x in t['rounds']),'all_jumps':len(t['dests'])==10000 and all(x==tramp for x in t['dests']),'two_d_values':len(set(t['starts']))==2,'no_pre_io':not t['pre_io'],'all_outputs':t['out']==sc['out']==ind['out']==oo==expected and c.stdout==expected+b'\n','all_steps':t['steps']==sc['steps']==ind['steps']==o['steps']==cap and match is not None and int(match.group(1))==cap,'memory_equal':memhash(t['mem'])==memhash(sc['mem'])==memhash(ind['mem']),'olmstead_prefix':bytes(buf[:len(expected)])==expected,'olmstead_produces_post_eof_bytes':len(buf)>len(expected),'control_breaks':control['out']!=expected or len(control['rounds'])!=10000}
r={'cap':cap,'stream_sha256':sha(stream),'expected_output_sha256':sha(expected),'trace':{'status':t['status'],'steps':t['steps'],'input_consumed':t['consumed'],'output_bytes':len(t['out']),'rounds':len(t['rounds']),'first_three_rounds':t['rounds'][:3],'d_starts':sorted(set(t['starts'])),'jmp_destinations':sorted(set(t['dests'])),'pre_io':t['pre_io'],'memory_sha256':memhash(t['mem']),'registers':t['regs']},'engines':{'scratch':{'status':sc['status'],'steps':sc['steps'],'memory_sha256':memhash(sc['mem'])},'independent':{'status':ind['status'],'steps':ind['steps'],'memory_sha256':memhash(ind['mem'])},'oracle':{'status':o['status'],'steps':o['steps']},'runner':{'rc':c.returncode,'stderr':c.stderr.decode('latin1'),'output_sha256':sha(c.stdout)}},'olmstead_bounded':{'stdout_bytes':len(buf),'stdout_sha256':sha(buf),'prefix_equal':bytes(buf[:len(expected)])==expected,'post_eof_bytes_first16':bytes(buf[len(expected):len(expected)+16]).hex(),'terminated_by_harness':stopped,'returncode':proc.returncode,'stderr':err.decode('latin1')},'control':{'mutated_pc':pos,'original_normalized_op':(img[pos]+pos)%94,'new_normalized_op':(ctl[pos]+pos)%94,'status':control['status'],'steps':control['steps'],'rounds':len(control['rounds']),'output_bytes':len(control['out']),'output_sha256':sha(control['out'])},'checks':checks,'all_checks':all(checks.values()),'eof_clean':'NOT_DEMONSTRATED; native process emitted bytes after EOF and was terminated by harness'}
(P/'verify_echo.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
