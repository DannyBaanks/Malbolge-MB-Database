"""P8: statically allocated two-level nested calls. Every output directory must be new."""
import pathlib,os,sys,importlib.util,json,subprocess,hashlib
ROOT=pathlib.Path(os.environ['MALBOLGE_MB_DATABASE_ROOT']) if 'MALBOLGE_MB_DATABASE_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
p=load('p5',ROOT/'vm_malbolge/evidence/g5b_flag_return_v5/probe.py'); p.HANDOFF=56000
class Nested(p.Shared5):
 def __init__(self,mode):
  self.code={};self.values={};self.code_cursor=38000;self.data_cursor=41000
  self.k=self.alloc_code(2);self.code[self.k]=66;self.code[self.k+1]=p.encode(4,self.k+1)
  self.fo=self.make_flag(); self.fi=self.make_flag()
  self.entry=self.make_tick(40,60);self.mix=self.make_tick(62,82)
  self.after=self.make_tick(68,88);self.out=self.make_tick(5,25);self.loop=self.make_tick(40,60)
  self.bridge=self.code_cursor+10;self.code[self.bridge]=p.encode(4,self.bridge)
  V=41000; B=42000; I=44000;S=45000
  self.v=V;self.a_cont=I+9;self.b_cont=B+1
  t={56000:self.loop-1,56001:S-2,S-1:self.loop,S:self.k-1,
     V-2:self.entry,V-1:self.mix-1,V:12345,V+1:self.mix,V+2:self.fi-1,V+3:I,
     I+1:self.fi-1,I+3:self.fo if mode=='outer_clobber' else self.bridge-1,
     I+4:self.after-1,I+6:self.after,I+7:self.fo-1,I+8:B,
     I+9:self.out-1,I+11:self.out,I+12:self.entry-1,I+13:V-3,
     B+1:self.fo-1,B+3:self.out-1,B+5:self.out,B+6:self.loop-1,B+7:S-2}
  if mode=='unarmed_a':t.update({S+2:self.entry-1,S+3:V-3})
  else:t.update({S+2:self.fo-1,S+3:S+3,S+4:self.entry-1,S+5:V-3})
  self.values=t
 def metadata(self):
  return {k:getattr(self,k) for k in ('k','fo','fi','entry','mix','after','bridge','v','a_cont','b_cont')}|{'code':self.code,'data':self.values}

def trace(image,plan):
 mem=list(image)+[0]*(59049-len(image))
 for i in range(len(image),59049):mem[i]=p.SE.crazy(mem[i-1],mem[i-2])
 a=c=d=0;output=[];events=[];clocks=[];mutations=[];active=False;status='limit'
 tails={pc:mem[pc] for pc in plan.code if pc-1 in plan.code};tails_changed=False
 for step in range(1,100000):
  if c==plan.k:
   active=True;clocks.append({'step':step,'fo':mem[plan.fo],'fi':mem[plan.fi],'mix':mem[plan.mix],'value':mem[plan.v]})
  if not 33<=mem[c]<=126:status='frozen';break
  op=(mem[c]+c)%94
  kind={plan.entry:'outer_entry',plan.mix:'inner_entry',plan.after:'inner_return'}.get(c)
  # Entry MOVD is tick-rearmed by a JMP that skips re-execution of the op.
  if active and op==4 and d in (plan.a_cont,plan.b_cont):kind='outer_return_A' if d==plan.a_cont else 'outer_return_B'
  if kind:events.append({'kind':kind,'step':step,'pc':c,'d':d,'a':a,'fo':mem[plan.fo],'fi':mem[plan.fi],'value':mem[plan.v]})
  pc=c;before=mem[plan.v]
  if op==4:c=mem[d]
  elif op==5:output.append(a%256)
  elif op==23:raise AssertionError('unexpected input')
  elif op==39:a=mem[d]=p.SE.rot(mem[d])
  elif op==40:d=mem[d]
  elif op==62:a=mem[d]=p.SE.crazy(a,mem[d])
  elif op==81:status='halt';break
  if 33<=mem[c]<=126:mem[c]=p.SE.encrypt(mem[c])
  if active and before!=mem[plan.v]:mutations.append({'step':step,'pc':pc,'before':before,'after':mem[plan.v]})
  c=(c+1)%59049;d=(d+1)%59049
  if active and any(mem[x]!=v for x,v in tails.items()):tails_changed=True
 return dict(status=status,steps=step,output_hex=bytes(output).hex(),events=events,clocks=clocks,mutations=mutations,final_value=mem[plan.v],tails_changed=tails_changed)

def check(tr,plan,mode):
 assert tr['status']=='halt' and not tr['tails_changed']
 events=tr['events'];assert len(events)%4==0
 groups=[events[i:i+4] for i in range(0,len(events),4)]
 returns=[];value=12345;a=55999;expected=[]
 for group in groups:
  enter,inner,after,ret=group
  assert [e['kind'] for e in group[:3]]==['outer_entry','inner_entry','inner_return']
  assert ret['kind'] in ('outer_return_A','outer_return_B');returns.append(ret['kind'][-1])
  assert enter['fo']==inner['fo']
  assert (after['fo']==inner['fo'])==(mode!='outer_clobber')
  assert enter['fi']==inner['fi']==after['fi']==74
  assert inner['d']==plan.v and inner['value']==value and inner['a']==a
  a=value=p.SE.crazy(a,value);expected.append(a%256)
  assert after['value']==ret['value']==value
 assert tr['output_hex']==bytes(expected).hex() and tr['final_value']==value
 assert all(m['pc']==plan.mix for m in tr['mutations'])
 assert len(tr['clocks'])==4 and all(c['fo']==c['fi']==c['mix']==74 for c in tr['clocks'])
 assert returns==(['A','B']*3 if mode=='positive' else ['B']*3),returns
 if mode=='positive':assert [g[0]['fo'] for g in groups]==[70,74]*3
 return returns

def main():
 out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);results={}
 for mode in ('positive','outer_clobber','unarmed_a'):
  plan=Nested(mode);image=plan.assemble();path=out/(mode+'.mb');path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps(plan.metadata(),indent=2)+'\n')
  tr=trace(image,plan)
  (out/(mode+'.trace.json')).write_text(json.dumps(tr,indent=2)+'\n')
  returns=check(tr,plan,mode)
  native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout);(out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and cb.status=='end'
  assert native.stdout.hex()==cb.output.hex()==tr['output_hex']
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,'clasesbolge_output_hex':cb.output.hex(),'clasesbolge_steps':cb.steps,'returns':returns,**tr}
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
