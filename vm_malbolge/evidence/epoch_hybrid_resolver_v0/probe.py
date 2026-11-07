#!/usr/bin/env python3
"""Finite two-component Classic pipeline: data-dependent selector + reusable store.

Host forwards selector stdout payload, never computes selected value. Batch
transport: this C runner waits for EOF before running the requested image.
"""
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'vm_malbolge/tools/native_classic')]
import oracle_classic as oc

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sel=module(ROOT/'vm_malbolge/evidence/epoch_resolver_dispatch_v0/probe.py','select_probe')
stor=module(ROOT/'vm_malbolge/evidence/epoch_reusable_store_v1/probe.py','store_probe')
SEL=ROOT/'vm_malbolge/evidence/epoch_resolver_dispatch_v0';STORE=ROOT/'vm_malbolge/evidence/epoch_reusable_store_v1'; RUNNER=ROOT/'runners/malbolge-original/malbolge'
REQUESTS={'A':(bytes.fromhex('0141f2'),0x68,29524),'B':(bytes.fromhex('f20141'),0x21,29476)}

def invoke_select(key,mutant=False):
 data,want,branch=REQUESTS[key];path=SEL/('mutant.mb' if mutant else 'dispatch.mb');img=path.read_bytes()
 o,steps,status=oc.run(img.decode('ascii'),stdin_data=data.decode('latin1'),max_steps=10000,stop_on_eof=True);out=o.encode('latin1')
 r=subprocess.run([str(RUNNER),str(path),'10000'],input=data,capture_output=True)
 t,ts,st,events=sel.trace(img,data);pcs=[e['pc'] for e in events if e['type']=='visit']
 agree=(out==t and steps==ts and status==st and r.stdout==out+b'\n' and r.returncode==0)
 accepted=agree and status=='HALTED' and len(out)==1 and branch in pcs and 34 in pcs and r.stderr.decode().strip()==f'steps: {steps} | status: HALTED'
 return {'request':key,'input_hex':data.hex(),'raw_hex':r.stdout.hex(),'oracle_hex':out.hex(),'stderr':r.stderr.decode().strip(),'steps':steps,'status':status,'events':events,'agreement':agree,'accepted':accepted,'output_matches_expected':out==bytes([want])},out

def invoke_store(data,mutant=False):
 name='mutant' if mutant else 'positive';path=STORE/(name+'.mb');img=path.read_bytes();lab=stor.labels(name)
 o,steps,status=oc.run(img.decode('ascii'),stdin_data=data.decode('latin1'),max_steps=4000000,stop_on_eof=True);out=o.encode('latin1')
 r=subprocess.run([str(RUNNER),str(path),'4000000'],input=data,capture_output=True)
 t,ts,st,ev=stor.trace(img,data,lab);ins=[x for x in ev if x['kind']=='in'];outs=[x for x in ev if x['kind']=='out'];writes=[x for x in ev if x['kind']=='write_top']
 words=[29524]*len(data) if mutant else list(data);want=bytes([84])*len(data) if mutant else data
 state=all(e['top']==e['scratch']==29524 for e in ins) and all(any(w['index']==i and w['value']==v for w in writes) for i,v in enumerate(words)) and all(e['top']==v for e,v in zip(outs,words)) and len(ins)==len(outs)==len(data)
 ok=out==want and t==out and status==st=='EOF' and ts==steps and r.stdout==want+b'\n' and r.stderr.decode().strip()==f'steps: {steps} | status: HALTED' and state
 return {'input_hex':data.hex(),'oracle_hex':out.hex(),'raw_hex':r.stdout.hex(),'stderr':r.stderr.decode().strip(),'steps':steps,'status':status,'state_ok':state,'ok':ok,'events':ev}

def main():
 rows=[]
 for requests in ('AB','BABA','AAAABBBBABAB'):
  selected=[];forward=bytearray()
  for key in requests:
   r,b=invoke_select(key);selected.append(r)
   if not r['accepted']:raise RuntimeError('selector failed protocol')
   forward.extend(b)  # forwarding bytes, no arithmetic/value substitution
  positive=invoke_store(bytes(forward));negative=invoke_store(bytes(forward),True)
  entry={'requests':requests,'select':selected,'forwarded_hex':forward.hex(),'store':positive,'store_mutant':negative}
  entry['ok']=all(x['accepted'] and x['output_matches_expected'] for x in selected) and positive['ok'] and negative['ok'] and negative['oracle_hex']!=forward.hex()
  rows.append(entry);print('requests',requests,'forwarded',forward.hex(),'store',positive['oracle_hex'],'mutant',negative['oracle_hex'],'ok',entry['ok'],flush=True)
 bad=[]
 for key in REQUESTS:
  r,_=invoke_select(key,True);bad.append(r);print('selector_mutant',key,'status',r['status'],'agreement',r['agreement'],'accepted',r['accepted'],flush=True)
 result={'cases':rows,'selector_mutants':bad,'all_positive_and_store_control':all(x['ok'] for x in rows),'selector_mutants_rejected':all(not x['accepted'] and x['agreement'] for x in bad),'transport':'host forwards raw output payload in batch; two separate VMs','dependencies':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SEL/'dispatch.mb',SEL/'mutant.mb',STORE/'positive.mb',STORE/'mutant.mb',SEL/'probe.py',STORE/'probe.py',RUNNER]}}
 (P/'results.json').write_text(json.dumps(result,indent=2)+'\n');return int(not(result['all_positive_and_store_control'] and result['selector_mutants_rejected']))
if __name__=='__main__':sys.exit(main())
