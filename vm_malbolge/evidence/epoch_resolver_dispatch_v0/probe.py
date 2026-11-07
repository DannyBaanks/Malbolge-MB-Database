#!/usr/bin/env python3
"""Two-command dispatch/return probe, no PureEpoch integration claim."""
import sys,json,hashlib,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'vm_malbolge/tools/native_classic')]
import oracle_classic as oc
from constants import char_for_op

def trace(src, inp, limit=10000):
 m=oc.load_memory(src.decode('ascii'));a=c=d=0;idx=0;out=[];ev=[]
 for steps in range(1,limit+1):
  op=(m[c]+c)%94; pc=c; dd=d; jump=False
  if pc in (34,29524,29476,29554,29434):ev.append({'type':'visit','pc':pc,'step':steps,'slot':m[46]})
  if op==4:target=m[d];jump=True;ev.append({'type':'jump','pc':pc,'target':target+1,'step':steps,'slot':m[46]})
  elif op==5:out.append(a%256)
  elif op==23:
   if idx==len(inp):return bytes(out),steps,'EOF',ev
   a=inp[idx];idx+=1
  elif op==39:m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
  elif op==40:d=m[d]
  elif op==62:
   m[d]=oc.crazy_op(a,m[d]);a=m[d]
   if dd==46:ev.append({'type':'store','pc':pc,'step':steps,'slot':a})
  elif op==81:return bytes(out),steps,'HALTED',ev
  if jump:c=target
  if 33<=m[c]<=126:m[c]=oc._ENC[m[c]]
  c=(c+1)%59049;d=(d+1)%59049
 return bytes(out),limit,'MAX_STEPS',ev

def main():
 src=(P/'dispatch.mb').read_bytes();mut=bytearray(src);mut[6]=ord(char_for_op(68,6));(P/'mutant.mb').write_bytes(mut)
 vectors=[('push-A-pop',bytes.fromhex('0141f2'),bytes.fromhex('68'),29524,True),('pop-push-A',bytes.fromhex('f20141'),bytes.fromhex('21'),29476,True),('push-B-pop',bytes.fromhex('0142f2'),bytes.fromhex('69'),29524,True),('two-push',bytes.fromhex('01410142'),b'',29524,True)]
 rows=[]
 for name,data,want,branch,_ in vectors:
  row={'case':name,'input':data.hex()}
  for variant,image in [('positive',src),('mutant',bytes(mut))]:
   got,steps,status=oc.run(image.decode('ascii'),stdin_data=data.decode('latin1'),max_steps=10000,stop_on_eof=True); got=got.encode('latin1')
   c=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(P/('dispatch.mb' if variant=='positive' else 'mutant.mb')),'10000'],input=data,capture_output=True)
   out,ts,st,ev=trace(image,data); visits=[x['pc'] for x in ev if x['type']=='visit']; agreement=got==out and steps==ts and status==st and c.stdout in (out,out+b'\n') and c.returncode==0
   success=agreement and status=='HALTED' and out==want and branch in visits and 34 in visits
   row[variant]={'output':out.hex(),'c_stdout_raw':c.stdout.hex(),'c_stderr':c.stderr.decode('latin1').strip(),'steps':steps,'status':status,'agreement':agreement,'contract':success,'events':ev}
  rows.append(row);print(name,'positive=',row['positive']['contract'],'mutant_contract=',row['mutant']['contract'],'mutant_agreement=',row['mutant']['agreement'],flush=True)
 payload={'cases':rows,'source_sha256':hashlib.sha256(src).hexdigest(),'mutant_sha256':hashlib.sha256(mut).hexdigest(),'all_positive':all(r['positive']['contract'] for r in rows),'all_mutant_rejected':all(not r['mutant']['contract'] for r in rows),'mutant_agreement':all(r['mutant']['agreement'] for r in rows)}
 (P/'results.json').write_text(json.dumps(payload,indent=2)+'\n');print('positive',payload['all_positive'],'mutants rejected',payload['all_mutant_rejected'],'mutant parity',payload['mutant_agreement']);return int(not (payload['all_positive'] and payload['all_mutant_rejected'] and payload['mutant_agreement']))
if __name__=='__main__':sys.exit(main())
