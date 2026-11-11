#!/usr/bin/env python3
"""Compare the two actual machine states; synthetic transplant is not a Malbolge bootstrap."""
import hashlib,importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M); S=M.SE;N=M.N

def start(img):
 mem=list(img)+[0]*(N-len(img))
 for i in range(len(img),N):mem[i]=S.crazy(mem[i-1],mem[i-2])
 return {'mem':mem,'a':0,'c':0,'d':0,'input':0,'out':bytearray(),'steps':0}

def step(z,data):
 mem=z['mem'];a=z['a'];c=z['c'];d=z['d'];v=mem[c]
 if not 33<=v<=126:return 'NONPRINT'
 op=(v+c)%94; z['steps']+=1
 if op==4:c=mem[d]
 elif op==5:z['out'].append(a%256)
 elif op==23:
  if z['input']>=len(data):return 'EOF'
  a=data[z['input']];z['input']+=1
 elif op==39:mem[d]=S.rot(mem[d]);a=mem[d]
 elif op==40:d=mem[d]
 elif op==62:mem[d]=S.crazy(a,mem[d]);a=mem[d]
 elif op==81:return 'HALTED'
 if 33<=mem[c]<=126:mem[c]=S.encrypt(mem[c])
 z.update(a=a,c=(c+1)%N,d=(d+1)%N)
 return 'RUN'

old=(ROOT/'vm_malbolge/evidence/epoch_dload_inout_v1/compose_inout.mb').read_bytes();new=(P/'prepare_v2_main.mb').read_bytes()
o=start(old)
while o['c']!=43:
 if step(o,b'')!='RUN':raise RuntimeError('old init stopped')
b=start(new)
while True:
 status=step(b,b'')
 if status!='RUN':break
assert status=='HALTED';assert [b['mem'][x] for x in (47,64,123)]==[74]*3
entry={k:o[k] for k in ('a','c','d','steps')}
halt={k:b[k] for k in ('a','c','d','steps')}
ranges=list(range(42,127))+[143,148]
changes=[{'cell':i,'prepared':b['mem'][i],'needed':o['mem'][i]} for i in ranges if b['mem'][i]!=o['mem'][i]]
# Exact region and register transplant is performed externally, not by Malbolge.
for i in ranges:b['mem'][i]=o['mem'][i]
b.update(a=o['a'],c=o['c'],d=o['d'],input=0,out=bytearray(),steps=0)
o.update(input=0,out=bytearray(),steps=0)
stream=bytes((73*i+195)%256 for i in range(10001)); steps=820000
for i in range(steps):
 if step(o,stream)!='RUN' or step(b,stream)!='RUN':raise RuntimeError('continuation stopped')
matched=bytes(o['out'])==bytes(b['out'])==stream[:10000]
summary={'original_entry':entry,'preparation_halt_registers':halt,'required_cells':ranges,'changed_cell_count':len(changes),'changes':changes,'synthetic_registers':{k:entry[k] for k in ('a','c','d')},'synthetic_continuation':{'steps':steps,'original_input_bytes':o['input'],'transplant_input_bytes':b['input'],'original_output_bytes':len(o['out']),'transplant_output_bytes':len(b['out']),'both_equal_input':matched,'output_sha256':hashlib.sha256(b['out']).hexdigest()},'scope':'host modifies memory and registers directly; NOT a self-contained program or Olmstead execution'}
(P/'state_bridge_v2.results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));assert matched
