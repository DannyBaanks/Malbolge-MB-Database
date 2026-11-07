#!/usr/bin/env python3
"""One Classic VM: select value, store, read back, return, repeat."""
import hashlib,json,random,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'vm_malbolge/tools/native_classic')]
import oracle_classic as oc
from constants import XLAT1

def labels(name):
 wanted={'compose_scratch','compose_slot','compose_entry','ret_compose_store','ret_compose_read1','ret_compose_read2','marker_01','marker_02','dispatch_01','dispatch_02','IN','OUT','next_char_rearm'};found={}
 for line in (P/(name+'.dbg')).read_text().splitlines():
  m=re.fullmatch(r'(\w+): (?:DATA|CODE) (\d+)',line)
  if m and m[1] in wanted:found[m[1]]=int(m[2])
 assert set(found)==wanted,(wanted-set(found));return found

def trace(src,data,lab,limit=4000000):
 m=oc.load_memory(src.decode('latin1'));a=c=d=i=0;out=[];events=[];branches=[];stores=[];call=0
 for step in range(1,limit+1):
  if not 33<=m[c]<=126:return bytes(out),step,'NONPRINTABLE',events
  op=(m[c]+c)%94
  if op==4:
   if d in (lab['dispatch_01'],lab['dispatch_02']):branches.append(1 if d==lab['dispatch_01'] else 2)
   if d==lab['compose_entry']:call+=1
   c=m[d]
  elif op==5:
   out.append(a%256);events.append({'kind':'out','step':step,'value':a%256,'slot':m[lab['compose_slot']],'scratch':m[lab['compose_scratch']],'branches':branches[:],'writes':stores[:],'calls':call,'marker01':m[lab['marker_01']],'marker02':m[lab['marker_02']]});branches=[];stores=[];call=0
  elif op==23:
   events.append({'kind':'in','step':step,'index':i,'pc':c,'slot':m[lab['compose_slot']],'scratch':m[lab['compose_scratch']],'marker01':m[lab['marker_01']],'marker02':m[lab['marker_02']]})
   if i==len(data):return bytes(out),step,'EOF',events
   branches=[];stores=[];call=0;a=data[i];i+=1
  elif op==39:m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
  elif op==40:d=m[d]
  elif op==62:
   old=m[d];m[d]=oc.crazy_op(a,old);a=m[d]
   if d==lab['compose_slot']:stores.append({'before':old,'after':a,'step':step})
  elif op==81:return bytes(out),step,'HALTED',events
  if 33<=m[c]<=126:m[c]=oc._ENC[m[c]]
  c=(c+1)%59049;d=(d+1)%59049
 return bytes(out),limit,'MAX_STEPS',events

def main():
 rng=random.Random(20261107);cases=[b'',b'\x01',b'\x02',b'\x01\x02\x01',b'\x02\x01\x02',b'\x01'*8,b'\x02'*8,b'\x01\x02'*8,bytes(rng.choice((1,2)) for _ in range(128))]
 p=P/'combined_pruned.mb';img=p.read_bytes();lab=labels('combined_pruned');src=bytes(v for v in img if v not in b' \t\r\n');invalid=[i for i,v in enumerate(src) if not (33<=v<=126 and XLAT1[(v-33+i)%94] in 'ji*p</vo')];rows=[]
 for data in cases:
  expected=bytes(80 if x==1 else 82 for x in data);out,steps,status=oc.run(img.decode('latin1'),max_steps=4000000,stdin_data=data.decode('latin1'),stop_on_eof=True);out=out.encode('latin1')
  r=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(p),'4000000'],input=data,capture_output=True); t,ts,tstatus,events=trace(img,data,lab);ins=[e for e in events if e['kind']=='in'];outs=[e for e in events if e['kind']=='out']
  state=(len(ins)==len(data)+1 and len(outs)==len(data) and all(e['pc']==lab['IN'] for e in ins) and all(e['slot']==e['scratch']==29524 and e['marker01']==80 and e['marker02']==82 for e in ins) and all(e['slot']==want and e['value']==want and e['calls']==1 and e['branches']==[req]*10 and len(e['writes'])==3 and e['writes'][0]['before']==29524 and e['writes'][0]['after']==want and e['writes'][2]['after']==want and e['marker01']==80 and e['marker02']==82 for e,req,want in zip(outs,data,expected)))
  ok=(out==expected and status=='EOF' and r.stdout==expected+b'\n' and r.stderr.decode().strip()==f'steps: {steps} | status: HALTED' and r.returncode==0 and t==out and ts==steps and tstatus==status and state)
  rows.append({'input_hex':data.hex(),'expected_hex':expected.hex(),'oracle_hex':out.hex(),'runner_raw_hex':r.stdout.hex(),'runner_stderr':r.stderr.decode().strip(),'steps':steps,'status':status,'state_ok':state,'ok':ok,'events':events})
  print('len',len(data),'input',data.hex()[:16],'out',out.hex()[:16],'steps',steps,'state',state,'ok',ok,flush=True)
 negatives=[]
 for name in ('mutant_read','mutant_rearm'):
  q=P/(name+'.mb');mut=q.read_bytes()
  for data in (b'\x01',b'\x02',b'\x01\x02\x01'):
   want=bytes(80 if x==1 else 82 for x in data);o,steps,status=oc.run(mut.decode('latin1'),max_steps=1000000,stdin_data=data.decode('latin1'),stop_on_eof=True);o=o.encode('latin1');r=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(q),'1000000'],input=data,capture_output=True)
   unaffected=(name=='mutant_rearm' and data==b'\x02');control=(o==want and r.stdout==want+b'\n') if unaffected else (o!=want and r.stdout!=want+b'\n')
   parity=(r.stdout==o+b'\n' and r.stderr.decode().strip()==f'steps: {steps} | status: HALTED')
   negatives.append({'name':name,'input_hex':data.hex(),'oracle_hex':o.hex(),'steps':steps,'status':status,'runner_raw_hex':r.stdout.hex(),'runner_stderr':r.stderr.decode().strip(),'control':control,'parity':parity})
   print(name,data.hex(),'oracle',o.hex(),'runner',r.stdout.hex(),'control',control,'parity',parity,flush=True)
 # Out-of-domain observations are not treated as successful selector requests.
 boundary=[]
 for data in (b'\x00',b'\x03',b'\xff'):
  o,steps,status=oc.run(img.decode('latin1'),max_steps=1000000,stdin_data=data.decode('latin1'),stop_on_eof=True);r=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(p),'1000000'],input=data,capture_output=True)
  boundary.append({'input_hex':data.hex(),'oracle_hex':o.encode('latin1').hex(),'status':status,'steps':steps,'runner_raw_hex':r.stdout.hex(),'runner_stderr':r.stderr.decode().strip()})
  print('out_of_domain',data.hex(),'oracle',o.encode('latin1').hex(),status,'runner',r.stdout.hex(),r.stderr.decode().strip(),flush=True)
 result={'positive':rows,'negative':negatives,'out_of_domain':boundary,'labels':lab,'loader_invalid_addresses':invalid,'image_sha256':hashlib.sha256(img).hexdigest(),'mutant_sha256':{n:hashlib.sha256((P/(n+'.mb')).read_bytes()).hexdigest() for n in ('mutant_read','mutant_rearm')}}
 (P/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('strict_invalid',len(invalid),'image_sha256',result['image_sha256'],flush=True)
 return int(not(all(x['ok'] for x in rows) and all(x['control'] for x in negatives) and not invalid))
if __name__=='__main__':sys.exit(main())
