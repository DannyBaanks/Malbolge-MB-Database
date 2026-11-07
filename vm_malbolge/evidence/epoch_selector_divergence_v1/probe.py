#!/usr/bin/env python3
"""Compare preserved instrumented C pre-state and reference C full delta trace."""
import gzip,hashlib,json,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];PREV=ROOT/'vm_malbolge/evidence/epoch_selector_rearm_v0'
sys.path.insert(0,str(ROOT/'tools'));import oracle_classic as oc

def pretrace():
 m=oc.load_memory((PREV/'rearmed2.mb').read_text(encoding='latin1'));a=c=d=i=0;data=[1,2,1];matched=0
 with gzip.open(P/'runner_trace.stderr.gz','rt') as f:
  for line in f:
   if not line.startswith('TRACE '):continue
   _,n,aa,cc,dd,ins,ii=line.split();n=int(n);cur=[a,c,d,m[c],i];ref=list(map(int,(aa,cc,dd,ins,ii)))
   if cur!=ref:return {'kind':'prestate_mismatch','step':n,'python':cur,'instrumented_runner':ref,'matched_before':matched}
   if not 33<=m[c]<=126:return {'kind':'nonprintable','step':n,'prestate':cur,'matched_before':matched,'python_decoded':(m[c]+c)%94}
   matched+=1;op=(m[c]+c)%94
   if op==4:c=m[d]
   elif op==23:
    if i>=len(data):return {'kind':'early_eof','step':n}
    a=data[i];i+=1
   elif op==39:m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
   elif op==40:d=m[d]
   elif op==62:m[d]=oc.crazy_op(a,m[d]);a=m[d]
   elif op==81:return {'kind':'early_halt','step':n}
   if 33<=m[c]<=126:m[c]=oc._ENC[m[c]]
   c=(c+1)%59049;d=(d+1)%59049
 return {'kind':'trace_exhausted','matched_before':matched}

def compare_ref():
 m=oc.load_memory((PREV/'rearmed2.mb').read_text(encoding='latin1'));a=c=d=i=0;data=[1,2,1];matched=0
 with gzip.open(P/'trace_c.jsonl.gz','rt') as f:
  for line in f:
   z=json.loads(line);step=z['step'];pre=[a,c,d,i];changes={};emitted=[];op=(m[c]+c)%94
   if pre!=z['pre'] or op!=z['opcode']:return {'kind':'pre_mismatch','step':step}
   if not 33<=m[c]<=126:return {'kind':'nonprintable','step':step,'matched_before':matched,'pre':pre,'mem_c':m[c],'c_terminal':z['terminal']}
   if op==4:c=m[d]
   elif op==5:emitted=[a%256]
   elif op==23:
    if i>=len(data):return {'kind':'unexpected_eof','step':step}
    a=data[i];i+=1
   elif op==39:
    old=m[d];m[d]=old//3+(old%3)*19683;a=m[d];changes[d]=(old,m[d])
   elif op==40:d=m[d]
   elif op==62:
    old=m[d];m[d]=oc.crazy_op(a,old);a=m[d];changes[d]=(old,m[d])
   elif op==81:return {'kind':'unexpected_halt','step':step}
   if 33<=m[c]<=126:
    old=m[c];m[c]=oc._ENC[old];changes[c]=(changes.get(c,(old,old))[0],m[c])
   c=(c+1)%59049;d=(d+1)%59049
   delta=[[k,v[0],v[1]] for k,v in sorted(changes.items()) if v[0]!=v[1]]
   if [a,c,d,i]!=z['post'] or delta!=z['changes'] or emitted!=z['output']:return {'kind':'post_mismatch','step':step}
   matched+=1
 return {'kind':'trace_exhausted','matched_before':matched}

def snapshots():
 labels={}
 for line in (PREV/'rearmed2.dbg').read_text().splitlines():
  z=re.fullmatch(r'(\w+): CODE (\d+)',line)
  if z:labels[int(z.group(2))]=z.group(1)
 m=oc.load_memory((PREV/'rearmed2.mb').read_text(encoding='latin1'));a=c=d=i=0;data=[1,2,1];sn=[]
 for step in range(1,100000):
  op=(m[c]+c)%94
  if op==23:
   sn.append((step,a,c,d,m.copy()))
   if len(sn)==2:break
   a=data[i];i+=1
  elif op==4:c=m[d]
  elif op==39:m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
  elif op==40:d=m[d]
  elif op==62:m[d]=oc.crazy_op(a,m[d]);a=m[d]
  elif op==81:break
  if 33<=m[c]<=126:m[c]=oc._ENC[m[c]]
  c=(c+1)%59049;d=(d+1)%59049
 if len(sn)!=2:return {'error':'no second input'}
 first,second=sn;changes=[{'address':p,'label':label,'first':first[4][p],'second':second[4][p]} for p,label in sorted(labels.items()) if first[4][p]!=second[4][p]]
 return {'first':{'step':first[0],'a':first[1],'c':first[2],'d':first[3]},'second':{'step':second[0],'a':second[1],'c':second[2],'d':second[3]},'labelled_code_changes':changes}

def main():
 div=pretrace();ref=compare_ref();snap=snapshots();inputs=[b'\x01',b'\x02',b'\x01\x02\x01',b'\x02\x01\x02'];attempts=[]
 for name in ('reset_carry','conditional_flag'):
  path=P/(name+'.mb');src=path.read_bytes()
  for data in inputs:
   o,steps,status=oc.run(src.decode('latin1'),stdin_data=data.decode('latin1'),max_steps=300000,stop_on_eof=True);out=o.encode('latin1')
   c=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(path),'300000'],input=data,capture_output=True)
   expected=bytes({1:0x50,2:0x52}[x] for x in data);contract=(out==expected and c.stdout==expected+b'\n' and c.stderr.decode().strip()==f'steps: {steps} | status: HALTED' and status=='EOF')
   entry={'name':name,'input':data.hex(),'expected':expected.hex(),'oracle':out.hex(),'oracle_status':status,'oracle_steps':steps,'runner_raw':c.stdout.hex(),'runner_stderr':c.stderr.decode().strip(),'contract':contract};attempts.append(entry)
   print(name,data.hex(),'expected',expected.hex(),'oracle',out.hex(),steps,status,'runner_raw',c.stdout.hex(),'contract',contract,flush=True)
 print('first divergence',div,flush=True);print('independent C reference',ref,flush=True);print('reentry code changes',snap['labelled_code_changes'],flush=True)
 trace_ref_last=None
 with gzip.open(P/'trace_c.jsonl.gz','rt') as f:
  for line in f:trace_ref_last=json.loads(line)
 evidence={'divergence':div,'reference_comparison':ref,'reentry':snap,'trace_ref_last':trace_ref_last,'attempts':attempts}
 (P/'results.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
 passed=ref.get('kind')=='nonprintable' and ref.get('matched_before')==59691 and div.get('kind')=='nonprintable' and div.get('step')==59692 and div.get('prestate')==[9814,71,52333,0,2] and trace_ref_last['terminal']=='STALL' and all(not x['contract'] for x in attempts)
 print('diagnostic_contract',passed,flush=True);return int(not passed)
if __name__=='__main__':sys.exit(main())
