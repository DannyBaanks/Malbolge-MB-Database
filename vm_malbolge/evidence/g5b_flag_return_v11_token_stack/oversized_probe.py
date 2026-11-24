"""Native bounded runtime stack of A/B tokens; no host execution of the stack."""
import pathlib,os,sys,importlib.util,json,subprocess,hashlib
ROOT=pathlib.Path(os.environ['MALBOLGE_MB_DATABASE_ROOT']) if 'MALBOLGE_MB_DATABASE_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('p5',ROOT/'vm_malbolge/evidence/g5b_flag_return_v5/probe.py');p.HANDOFF=56000
SCRIPT=[('pop',None),('push','A'),('push','B'),('push','A'),('pop',None),('push','A'),('pop',None),('pop',None),('pop',None),('push','B'),('push','A'),('pop',None),('pop',None)]
class Stack(p.Shared5):
 def __init__(self,mode):
  self.code={};self.values={};self.code_cursor=38000;self.data_cursor=40010
  self.d0=self.make_flag();self.d1=self.make_flag();self.s0=self.make_flag();self.s1=self.make_flag()
  self.entry=self.make_tick(40,60);self.load=self.make_tick(40,60);self.rot=self.make_tick(39,63);self.out=self.make_tick(5,25)
  self.halt=self.code_cursor+10;self.code[self.halt]=p.encode(81,self.halt)
  self.emissions={};self.starts={};self.mode=mode
  end=self.node();self.put(end,self.halt-1)
  next_node=end
  for index in reversed(range(len(SCRIPT))):
   op,token=SCRIPT[index]
   if op=='push':
    overflow=self.emit('O',index,next_node)
    one=self.set_slot(self.s1,token,self.flip(self.d1,next_node))
    zero=self.set_slot(self.s0,token,next_node if mode=='no_push_depth' else self.flip(self.d0,next_node))
    nonempty=self.branch(self.d1,one,overflow)
    start=self.branch(self.d0,zero,nonempty)
   else:
    underflow=self.emit('U',index,next_node)
    branches=[]
    for slot,depth_flag in ((self.s0,self.d0),(self.s0 if mode=='wrong_slot' else self.s1,self.d1)):
     a=self.flip(depth_flag,self.emit('A',index,next_node));b=self.flip(depth_flag,self.emit('B',index,next_node))
     branches.append(self.branch(slot,a,b))
    nonempty=self.branch(self.d1,branches[0],branches[1])
    start=self.branch(self.d0,underflow,nonempty)
   self.starts[start]={'index':index,'op':op,'token':token};next_node=start
  self.put(56000,self.entry-1);self.put(56001,next_node-2)
 def node(self,count=8):
  n=self.reserve_data(count);self.put(n-1,self.entry);return n
 def branch(self,flag,if74,if70):
  n=self.node(9);q=self.reserve_data(6)
  for addr,val in {n:flag-1,n+1:q,n+2:flag,n+3:self.entry-1,n+4:if70-2,q+1:flag,q+2:self.entry-1,q+3:if74-2}.items():self.put(addr,val)
  return n
 def flip(self,flag,next_node):
  n=self.node();self.put(n,flag);self.put(n+1,self.entry-1);self.put(n+2,next_node-2);return n
 def set_slot(self,slot,token,next_node):
  flipped=self.flip(slot,next_node)
  return self.branch(slot,next_node if token=='A' else flipped,flipped if token=='A' else next_node)
 def emit(self,char,index,next_node):
  n=self.node();v=self.reserve_data(12)+2
  for addr,val in {n:self.load-1,n+1:v-3,v-2:self.load,v-1:self.rot-1,v:ord(char)*3,v+1:self.rot,v+2:self.out-1,v+4:self.out,v+5:self.entry-1,v+6:next_node-2}.items():self.put(addr,val)
  self.emissions[v]={'index':index,'char':char};return n
 def metadata(self):
  return {k:getattr(self,k) for k in ('d0','d1','s0','s1','entry','load','rot','out','halt','emissions','starts')}|{'code':self.code,'data':self.values,'script':SCRIPT}

def snapshot(mem,plan):
 flags=[mem[x] for x in (plan.d0,plan.d1,plan.s0,plan.s1)]
 depth={(74,74):0,(70,74):1,(70,70):2}.get(tuple(flags[:2]),-1)
 return {'flags':flags,'depth':depth,'slots':['A' if x==74 else 'B' if x==70 else '?' for x in flags[2:]]}
def trace(image,plan):
 mem=list(image)+[0]*(59049-len(image))
 for i in range(len(image),59049):mem[i]=p.SE.crazy(mem[i-1],mem[i-2])
 a=c=d=0;output=[];operations=[];emissions=[];changes=[];active=False;status='limit'
 tails={pc:mem[pc] for pc in plan.code if pc-1 in plan.code};tails_changed=False
 for step in range(1,100000):
  if not 33<=mem[c]<=126:status='frozen';break
  op=(mem[c]+c)%94
  if c==plan.entry and mem[d]+2 in plan.starts:
   active=True;operations.append({'step':step,**plan.starts[mem[d]+2],**snapshot(mem,plan)})
  if c==plan.rot and d in plan.emissions:emissions.append({'step':step,**plan.emissions[d],**snapshot(mem,plan)})
  before=snapshot(mem,plan)['flags'];pc=c
  if op==4:c=mem[d]
  elif op==5:output.append(a%256)
  elif op==23:raise AssertionError('unexpected input')
  elif op==39:a=mem[d]=p.SE.rot(mem[d])
  elif op==40:d=mem[d]
  elif op==62:a=mem[d]=p.SE.crazy(a,mem[d])
  elif op==81:status='halt';break
  if 33<=mem[c]<=126:mem[c]=p.SE.encrypt(mem[c])
  after=snapshot(mem,plan)['flags']
  if active and before!=after:changes.append({'step':step,'pc':pc,'before':before,'after':after})
  c=(c+1)%59049;d=(d+1)%59049
  if active and any(mem[x]!=v for x,v in tails.items()):tails_changed=True
 return dict(status=status,steps=step,output_hex=bytes(output).hex(),operations=operations,emissions=emissions,changes=changes,final=snapshot(mem,plan),tails_changed=tails_changed)

def specification(tr):
 stack=[];expected_output=[];failures=[];model=[]
 for i,(op,token) in enumerate(SCRIPT):
  expected_before=list(stack)
  if op=='push':
   emitted='O' if len(stack)==2 else None
   if emitted is None:stack.append(token)
  else:emitted=stack.pop() if stack else 'U'
  if emitted:expected_output.append(emitted)
  actual=tr['operations'][i]
  if actual['depth']!=len(expected_before) or actual['slots'][:actual['depth']]!=expected_before:failures.append(f'operation {i}: before-state')
  after=tr['operations'][i+1] if i+1<len(SCRIPT) else tr['final']
  if after['depth']!=len(stack) or after['slots'][:after['depth']]!=stack:failures.append(f'operation {i}: after-state')
  actual_emitted=[e['char'] for e in tr['emissions'] if e['index']==i]
  if actual_emitted!=([emitted] if emitted else []):failures.append(f'operation {i}: emitted token')
  model.append({'index':i,'before':expected_before,'after':list(stack),'emitted':emitted})
 if tr['output_hex']!=''.join(expected_output).encode().hex():failures.append('output')
 return {'failures':failures,'model':model,'expected_output':''.join(expected_output)}
def main():
 out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);results={}
 for mode in ('positive','no_push_depth','wrong_slot'):
  plan=Stack(mode);image=plan.assemble();path=out/(mode+'.mb');path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps(plan.metadata(),indent=2)+'\n')
  tr=trace(image,plan);(out/(mode+'.trace.json')).write_text(json.dumps(tr,indent=2)+'\n')
  assert tr['status']=='halt' and not tr['tails_changed'] and len(tr['operations'])==len(SCRIPT),tr
  spec=specification(tr);assert (not spec['failures'])==(mode=='positive'),spec
  native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout);(out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and cb.status=='end' and native.stdout.hex()==cb.output.hex()==tr['output_hex']
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,'clasesbolge_output_hex':cb.output.hex(),'clasesbolge_steps':cb.steps,'specification':spec,**tr}
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
