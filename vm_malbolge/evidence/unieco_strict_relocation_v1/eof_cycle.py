#!/usr/bin/env python3
"""Find an exact repeated state under Classic EOF=59048, bounded in time."""
import array,hashlib,importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('m',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
img=(P/'candidate.mb').read_bytes();par=json.loads((P/'synthesis.results.json').read_text());N=M.N;SE=M.SE;start=par['handoff_c'];mem=list(img)+[0]*(N-len(img))
for i in range(len(img),N):mem[i]=SE.crazy(mem[i-1],mem[i-2])
a=c=d=0; rounds=0;out=bytearray();seen={};repeat=None
for step in range(1,100000):
 if c==start:
  packed=array.array('H',mem).tobytes();key=hashlib.sha256(packed+repr((a,c,d)).encode()).hexdigest()
  if key in seen:
   old,oldstep,oldbytes,oldregs=seen[key];assert packed==oldbytes and (a,c,d)==oldregs
   repeat={'first_round':old,'second_round':rounds,'period':rounds-old,'first_step':oldstep,'second_step':step,'memory_equal_exact':packed==oldbytes,'registers':[a,c,d],'output_bytes_before_repeat':len(out)};break
  seen[key]=(rounds,step,packed,(a,c,d));rounds+=1
 v=mem[c];assert 33<=v<=126;op=(v+c)%94
 if op==4:c=mem[d]
 elif op==5:out.append(a%256)
 elif op==23:a=59048
 elif op==39:mem[d]=SE.rot(mem[d]);a=mem[d]
 elif op==40:d=mem[d]
 elif op==62:mem[d]=SE.crazy(a,mem[d]);a=mem[d]
 elif op==81:raise AssertionError('halt encountered before repeated state')
 if 33<=mem[c]<=126:mem[c]=SE.encrypt(mem[c])
 c=(c+1)%N;d=(d+1)%N
r={'semantics':'empty input, IN returns 59048; finite input state permanently EOF','repeat':repeat,'output_len':len(out),'output_prefix_hex':out[:16].hex(),'all_output_a8':all(x==168 for x in out),'output_sha256':hashlib.sha256(out).hexdigest(),'limit_steps':99999,'scope':'model repeat; native observed only bounded prefix, not infinite execution'}
(P/'eof_cycle.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert repeat and r['all_output_a8']
