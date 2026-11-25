"""P10: fixed-depth reentry through the same entry, body and dispatcher."""
import pathlib,os,sys,importlib.util,json,subprocess,hashlib
ROOT=pathlib.Path(os.environ['MALBOLGE_MB_DATABASE_ROOT']) if 'MALBOLGE_MB_DATABASE_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('p5',ROOT/'vm_malbolge/evidence/g5b_flag_return_v5/probe.py');p.HANDOFF=56000
class Reentrant(p.Shared5):
 def __init__(self,mode):
  self.code={};self.values={};self.code_cursor=38000;self.data_cursor=41000
  self.k=self.alloc_code(2);self.code[self.k]=66;self.code[self.k+1]=p.encode(4,self.k+1)
  self.fo=self.make_flag();self.entry=self.make_tick(40,60);self.mix=self.make_tick(62,82)
  self.dispatch=self.make_tick(40,60);self.resume=self.make_tick(68,88)
  self.out=self.make_tick(5,25);self.loop=self.make_tick(40,60)
  self.bridge=self.code_cursor+10;self.code[self.bridge]=p.encode(4,self.bridge)
  V=41000;W=43000;B=42000;I=44000;S=45000;O=46000;R=47000
  self.variables=[V,W];self.a_cont=R+2;self.b_cont=B+1
  t={56000:self.loop-1,56001:S-2,S-1:self.loop,S:self.k-1,
     S+2:self.fo-1,S+3:S+3,S+4:self.entry-1,S+5:V-3,
     O-1:self.dispatch,O:self.entry-1,O+1:W-3,
     I-1:self.dispatch,I:self.fo if mode=='outer_clobber' else self.bridge-1,
     I+1:self.resume-1,I+3:self.resume,I+4:self.dispatch-1,I+5:R-2,
     R-1:self.dispatch,R:self.fo-1,R+1:B,
     R+2:self.out-1,R+4:self.out,R+5:self.entry-1,R+6:V-3,
     B+1:self.fo-1,B+3:self.out-1,B+5:self.out,B+6:self.loop-1,B+7:S-2}
  for var,initial,frame in ((V,12345,I if mode=='bypass_inner' else O),(W,23456,I)):
   t.update({var-2:self.entry,var-1:self.mix-1,var:initial,var+1:self.mix,var+2:self.dispatch-1,var+3:frame-2})
  self.values=t
 def metadata(self):
  return {k:getattr(self,k) for k in ('k','fo','entry','mix','dispatch','resume','bridge','variables','a_cont','b_cont')}|{'code':self.code,'data':self.values}

def trace(image,plan):
 mem=list(image)+[0]*(59049-len(image))
 for i in range(len(image),59049):mem[i]=p.SE.crazy(mem[i-1],mem[i-2])
 a=c=d=0;output=[];events=[];clocks=[];mutations=[];dispatches=[];active=False;status='limit'
 tails={pc:mem[pc] for pc in plan.code if pc-1 in plan.code};tails_changed=False
 for step in range(1,100000):
  state={'fo':mem[plan.fo],'values':[mem[v] for v in plan.variables],'entry_word':mem[plan.entry],'mix_word':mem[plan.mix],'dispatch_word':mem[plan.dispatch]}
  if c==plan.k:active=True;clocks.append({'step':step,**state})
  if not 33<=mem[c]<=126:status='frozen';break
  op=(mem[c]+c)%94
  kind={plan.entry:'entry',plan.mix:'body',plan.resume:'resume'}.get(c)
  if active and op==4 and d in (plan.a_cont,plan.b_cont):kind='return_A' if d==plan.a_cont else 'return_B'
  if kind:events.append({'kind':kind,'step':step,'pc':c,'d':d,'a':a,'argument':mem[d] if kind=='entry' else None,**state})
  if c==plan.dispatch:dispatches.append({'step':step,'pc':c,'d':d,'frame_pointer':mem[d],**state})
  pc=c;before=[mem[v] for v in plan.variables]
  if op==4:c=mem[d]
  elif op==5:output.append(a%256)
  elif op==23:raise AssertionError('unexpected input')
  elif op==39:a=mem[d]=p.SE.rot(mem[d])
  elif op==40:d=mem[d]
  elif op==62:a=mem[d]=p.SE.crazy(a,mem[d])
  elif op==81:status='halt';break
  if 33<=mem[c]<=126:mem[c]=p.SE.encrypt(mem[c])
  after=[mem[v] for v in plan.variables]
  if active and before!=after:mutations.append({'step':step,'pc':pc,'before':before,'after':after})
  c=(c+1)%59049;d=(d+1)%59049
  if active and any(mem[x]!=v for x,v in tails.items()):tails_changed=True
 return dict(status=status,steps=step,output_hex=bytes(output).hex(),events=events,clocks=clocks,mutations=mutations,dispatches=dispatches,final_values=[mem[v] for v in plan.variables],tails_changed=tails_changed)

def check(tr,plan,mode):
 assert tr['status']=='halt' and not tr['tails_changed']
 size=4 if mode=='bypass_inner' else 6;assert len(tr['events'])%size==0
 groups=[tr['events'][i:i+size] for i in range(0,len(tr['events']),size)]
 values=[12345,23456];a=55999;expected=[];returns=[]
 for group in groups:
  kinds=['entry','body','resume'] if mode=='bypass_inner' else ['entry','body','entry','body','resume']
  assert [e['kind'] for e in group[:-1]]==kinds
  for index,(entry,body) in enumerate(zip(group[0:-2:2],group[1:-2:2])):
   assert entry['pc']==plan.entry and body['pc']==plan.mix
   assert entry['argument']==plan.variables[index]-3 and body['d']==plan.variables[index]
   assert entry['values']==body['values']==values
   assert entry['entry_word']==body['mix_word']==74
   assert entry['fo']==body['fo']==group[0]['fo']
   assert body['a']==a
   a=values[index]=p.SE.crazy(a,values[index])
  resume,ret=group[-2:];assert resume['values']==ret['values']==values
  assert (resume['fo']==group[0]['fo'])==(mode!='outer_clobber')
  returns.append(ret['kind'][-1]);expected.append(a%256)
 assert returns==(['B']*3 if mode=='outer_clobber' else ['A','B']*3),returns
 assert tr['output_hex']==bytes(expected).hex() and tr['final_values']==values
 assert len(tr['dispatches'])==len(groups)*(2 if mode=='bypass_inner' else 3)
 assert all(d['pc']==plan.dispatch and d['dispatch_word']==74 for d in tr['dispatches'])
 assert len(tr['clocks'])==4 and all(c['fo']==c['entry_word']==c['mix_word']==c['dispatch_word']==74 for c in tr['clocks'])
 assert all(m['pc']==plan.mix for m in tr['mutations'])
 if mode=='bypass_inner':assert values[1]==23456
 return returns

def main():
 out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);results={}
 for mode in ('positive','outer_clobber','bypass_inner'):
  plan=Reentrant(mode);image=plan.assemble();path=out/(mode+'.mb');path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps(plan.metadata(),indent=2)+'\n')
  tr=trace(image,plan);(out/(mode+'.trace.json')).write_text(json.dumps(tr,indent=2)+'\n');returns=check(tr,plan,mode)
  native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout);(out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and cb.status=='end' and native.stdout.hex()==cb.output.hex()==tr['output_hex']
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,'clasesbolge_output_hex':cb.output.hex(),'clasesbolge_steps':cb.steps,'returns':returns,**tr}
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
