#!/usr/bin/env python3
"""State-driven phase selection and PureEpoch M1b journal adaptation."""
import hashlib,json,random,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'vm_malbolge/tools/native_classic')]
import oracle_classic as oc
from constants import XLAT1

def labels(name):
 wanted={'compose_scratch','compose_slot','epoch_journal','EPOCH_PHASE','epoch_even','epoch_odd','marker_01','marker_02','dispatch_01','dispatch_02','IN','OUT'};found={}
 for line in (P/(name+'.dbg')).read_text().splitlines():
  z=re.fullmatch(r'(\w+): (?:DATA|CODE) (\d+)',line)
  if z and z[1] in wanted:found[z[1]]=int(z[2])
 assert set(found)==wanted,(name,wanted-set(found));return found

def trace(src,data,lab,limit=4000000):
 m=oc.load_memory(src.decode('latin1'));a=c=d=i=0;out=[];events=[];branches=[];slotwrites=[];jwrites=[];jrots=0;phases=[];routes=[]
 for step in range(1,limit+1):
  if not 33<=m[c]<=126:return bytes(out),step,'NONPRINTABLE',events
  op=(m[c]+c)%94
  if c==lab['EPOCH_PHASE']:phases.append({'step':step,'value':m[c],'opcode':op})
  if op==4:
   if d in (lab['dispatch_01'],lab['dispatch_02']):branches.append(1 if d==lab['dispatch_01'] else 2)
   if d in (lab['epoch_even'],lab['epoch_odd']):routes.append('even' if d==lab['epoch_even'] else 'odd')
   c=m[d]
  elif op==5:
   out.append(a%256);events.append({'kind':'out','step':step,'value':a%256,'slot':m[lab['compose_slot']],'journal':m[lab['epoch_journal']],'branches':branches[:],'slotwrites':slotwrites[:],'journalwrites':jwrites[:],'journal_rotations':jrots,'phases':phases[:],'routes':routes[:]});branches=[];slotwrites=[];jwrites=[];jrots=0;phases=[];routes=[]
  elif op==23:
   events.append({'kind':'in','step':step,'index':i,'pc':c,'slot':m[lab['compose_slot']],'scratch':m[lab['compose_scratch']],'journal':m[lab['epoch_journal']],'phase':m[lab['EPOCH_PHASE']],'marker01':m[lab['marker_01']],'marker02':m[lab['marker_02']]})
   if i==len(data):return bytes(out),step,'EOF',events
   branches=[];slotwrites=[];jwrites=[];jrots=0;phases=[];routes=[];a=data[i];i+=1
  elif op==39:
   if d==lab['epoch_journal']:jrots+=1
   m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
  elif op==40:d=m[d]
  elif op==62:
   old=m[d];old_a=a;m[d]=oc.crazy_op(a,old);a=m[d]
   event={'step':step,'before':old,'a_before':old_a,'after':a}
   if d==lab['compose_slot']:slotwrites.append(event)
   if d==lab['epoch_journal']:jwrites.append(event)
  elif op==81:return bytes(out),step,'HALTED',events
  if 33<=m[c]<=126:m[c]=oc._ENC[m[c]]
  c=(c+1)%59049;d=(d+1)%59049
 return bytes(out),limit,'MAX_STEPS',events

def execute(name,data):
 p=P/(name+'.mb');img=p.read_bytes();lab=labels(name);expected=bytes(80 if b==1 else 82 for b in data)
 output,steps,status=oc.run(img.decode('latin1'),max_steps=4000000,stdin_data=data.decode('latin1'),stop_on_eof=True);output=output.encode('latin1')
 c=subprocess.run([str(ROOT/'runners/malbolge-original/malbolge'),str(p),'4000000'],input=data,capture_output=True)
 t,ts,tstatus,events=trace(img,data,lab);ins=[e for e in events if e['kind']=='in'];outs=[e for e in events if e['kind']=='out']
 io=(output==expected and status=='EOF' and c.stdout==expected+b'\n' and c.returncode==0 and c.stderr.decode().strip()==f'steps: {steps} | status: HALTED' and t==output and ts==steps and tstatus==status)
 state=(len(ins)==len(data)+1 and len(outs)==len(data) and all(e['pc']==lab['IN'] and e['scratch']==e['slot']==e['journal']==29524 and e['marker01']==80 and e['marker02']==82 and e['phase']==(ins[0]['phase'] if i%2==0 else 144-ins[0]['phase']) for i,e in enumerate(ins)) and all(e['slot']==v and e['journal']==oc.crazy_op(v,29524) and e['branches']==[req]*10 and len(e['slotwrites'])==4 and e['slotwrites'][0]['before']==29524 and e['slotwrites'][0]['after']==v and e['slotwrites'][2]['after']==29524 and e['slotwrites'][3]['after']==v and len(e['journalwrites'])==1 and e['journalwrites'][0]['before']==29524 and e['journalwrites'][0]['after']==oc.crazy_op(v,29524) and e['journal_rotations']==10 and len(e['phases'])==1 and e['phases'][0]['value']==ins[i]['phase'] and e['routes']==(['even'] if e['phases'][0]['opcode']==40 else ['odd']) for i,(e,req,v) in enumerate(zip(outs,data,expected))))
 return {'input_hex':data.hex(),'expected_hex':expected.hex(),'oracle_hex':output.hex(),'runner_raw_hex':c.stdout.hex(),'runner_stderr':c.stderr.decode().strip(),'steps':steps,'status':status,'io':io,'state':state,'events':events}

def main():
 rng=random.Random(20261107);cases=[b'',b'\x01',b'\x02',b'\x01\x02\x01',b'\x02\x01\x02',b'\x01'*8,b'\x02'*8,b'\x01\x02'*8,bytes(rng.choice((1,2)) for _ in range(128))]
 rows=[]
 for data in cases:
  r=execute('journal',data);rows.append(r);print('len',len(data),'input',data.hex()[:16],'out',r['oracle_hex'][:16],'steps',r['steps'],'io',r['io'],'state',r['state'],flush=True)
 controls=[]
 for name in ('mutant_journal','mutant_phase'):
  for data in (b'\x01',b'\x02',b'\x01\x02\x01'):
   r=execute(name,data);r['name']=name;r['rejected']=not(r['io'] and r['state']);controls.append(r)
   print(name,data.hex(),'out',r['oracle_hex'],'io',r['io'],'state',r['state'],'rejected',r['rejected'],flush=True)
 img=(P/'journal.mb').read_bytes();src=bytes(v for v in img if v not in b' \t\r\n');invalid=[i for i,v in enumerate(src) if not(33<=v<=126 and XLAT1[(v-33+i)%94] in 'ji*p</vo')]
 result={'cases':rows,'controls':controls,'labels':{n:labels(n) for n in ('journal','mutant_journal','mutant_phase')},'loader_invalid_addresses':invalid,'images':{n:hashlib.sha256((P/(n+'.mb')).read_bytes()).hexdigest() for n in ('journal','mutant_journal','mutant_phase')}}
 (P/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('strict_invalid',len(invalid),'sha256',result['images'],flush=True)
 return int(not(all(x['io'] and x['state'] for x in rows) and all(x['rejected'] for x in controls) and all(x['io'] for x in controls if x['name']=='mutant_phase') and not invalid))
if __name__=='__main__':sys.exit(main())
