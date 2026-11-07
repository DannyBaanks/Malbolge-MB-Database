#!/usr/bin/env python3
"""Trace bounded selector rearm attempts; preserves negative outcomes."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'tools')); import oracle_classic as oc

def labels(name):
 wanted={'IN','ENTRY','value','value_C1','save_tmp','save_B','dispatch_01','dispatch_02'};out={}
 for line in (P/(name+'.dbg')).read_text().splitlines():
  if ':' not in line:continue
  k,v=line.split(':',1)
  if k in wanted:out[k]=int(v.split()[-1])
 assert set(out)==wanted,out
 return out

def trace(source,inp,lab,max_steps=300000):
 m=oc.load_memory(source.decode('latin1'));a=c=d=idx=0;events=[];out=[]
 for step in range(1,max_steps+1):
  op=(m[c]+c)%94
  if op==4:c=m[d]
  elif op==5:out.append(a%256)
  elif op==23:
   events.append({'step':step,'pc':c,'d':d,'idx':idx,'a_before':a,'values':{k:m[lab[k]] for k in ('value','value_C1','save_tmp','save_B')}})
   if idx>=len(inp):return bytes(out),step,'EOF',events
   a=inp[idx];idx+=1
  elif op==39:m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
  elif op==40:d=m[d]
  elif op==62:m[d]=oc.crazy_op(a,m[d]);a=m[d]
  elif op==81:return bytes(out),step,'HALTED',events
  if 33<=m[c]<=126:m[c]=oc._ENC[m[c]]
  c=(c+1)%59049;d=(d+1)%59049
 return bytes(out),max_steps,'MAX_STEPS',events

def main():
 cases=[b'',b'\x01',b'\x02',b'\x01\x02\x01',b'\x02\x01\x02']; rows=[]
 for name in ('loop','rearmed','rearmed2'):
  p=P/(name+'.mb');src=p.read_bytes();lab=labels(name)
  for data in cases:
   expected=bytes({1:0x50,2:0x52}[b] for b in data)
   out,steps,status=oc.run(src.decode('latin1'),max_steps=300000,stdin_data=data.decode('latin1'),stop_on_eof=True);out=out.encode('latin1')
   t,ts,tstatus,events=trace(src,data,lab)
   r=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(p),'300000'],input=data,capture_output=True)
   stderr=r.stderr.decode('latin1').strip(); output_match=r.stdout==out+b'\n';step_match=stderr==f'steps: {steps} | status: HALTED';trace_match=(t==out and ts==steps and tstatus==status)
   ok=out==expected and len([e for e in events if e['idx']<len(data)])==len(data) and output_match and step_match and trace_match and status=='EOF'
   rows.append({'candidate':name,'input':data.hex(),'expected':expected.hex(),'oracle':out.hex(),'steps':steps,'status':status,'runner_raw':r.stdout.hex(),'runner_stderr':stderr,'output_match':output_match,'step_match':step_match,'trace_match':trace_match,'contract':ok,'events':events})
   print(f'{name:8} input={data.hex():6} expected={expected.hex():6} oracle={out.hex():10} runner={r.stdout.hex():12} oracle_steps={steps} {status} runner={stderr} contract={ok}',flush=True)
  print('sha256',name,hashlib.sha256(src).hexdigest(),flush=True)
 (P/'results.json').write_text(json.dumps({'cases':rows},indent=2)+'\n',encoding='utf8')
 controls=all(x['contract'] for x in rows if x['candidate']=='loop' and len(bytes.fromhex(x['input']))<=1)
 checks=all(not x['contract'] for x in rows if len(bytes.fromhex(x['input']))==3)
 print('positive single-byte controls',controls,'multi-byte candidates rejected',checks)
 return int(not (controls and checks))
if __name__=='__main__':sys.exit(main())
