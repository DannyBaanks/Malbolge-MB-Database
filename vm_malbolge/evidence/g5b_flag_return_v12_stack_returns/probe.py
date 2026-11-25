"""P12: native runtime stack drives actual return continuations of a shared R."""
import pathlib,os,sys,importlib.util,json,subprocess,hashlib
ROOT=pathlib.Path(os.environ['MALBOLGE_MB_DATABASE_ROOT']) if 'MALBOLGE_MB_DATABASE_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load('p11',ROOT/'vm_malbolge/evidence/g5b_flag_return_v11_token_stack/probe.py');p=base.p
class Connected(base.Stack):
 def __init__(self,mode):
  self.code={};self.values={};self.code_cursor=38000;self.data_cursor=40010
  self.d0=self.make_flag();self.d1=self.make_flag();self.s0=self.make_flag();self.s1=self.make_flag()
  self.entry=self.make_tick(40,60);self.load=self.make_tick(40,60);self.rot=self.make_tick(39,63);self.out=self.make_tick(5,25)
  self.r_entry=self.make_tick(40,60);self.mix=self.make_tick(62,82)
  self.halt=self.code_cursor+10;self.code[self.halt]=p.encode(81,self.halt)
  self.variables=[50000,51000];self.emissions={};self.markers={};self.mode=mode
  end=self.node();self.put(end,self.halt-1)
  error=self.emit('E',0,end);overflow=self.emit('O',0,end);underflow=self.emit('U',0,end)
  self.overflow=overflow;self.underflow=underflow
  self.poproot=self.node();self.invoke=self.node();self.resume=self.goto(self.poproot,'resume')
  self.return_b=self.goto(self.emit('B',0,end),'return_B')
  after_b=self.goto(self.invoke,'after_push_B')
  self.push_b=self.push('B',after_b)
  self.return_a=self.goto(self.emit('A',0,self.push_b),'return_A')
  level0=self.branch(self.s0,self.flip(self.d0,self.return_a),self.flip(self.d0,self.return_b))
  level1=self.branch(self.s0 if mode=='wrong_slot' else self.s1,self.flip(self.d1,self.resume),self.flip(self.d1,error))
  chosen=self.branch(self.d1,level0,level1)
  pop=self.branch(self.d0,underflow,chosen);self.link(self.poproot,pop);self.markers[self.poproot]='pop'
  after_inner=self.goto(self.invoke,'after_push_inner')
  self.push_inner=self.push('A',after_inner);self.markers[self.push_inner]='push_inner'
  self.body_v=self.body(self.variables[0],12345,self.push_inner)
  self.body_w=self.body(self.variables[1],23456,self.push_inner if mode=='overflow_call' else self.poproot)
  selected_body=self.branch(self.d1,self.body_v,self.body_w)
  frame=self.reserve_data(8)
  for addr,val in {frame-1:self.r_entry,frame:self.entry-1,frame+1:selected_body-2,self.invoke:self.r_entry-1,self.invoke+1:frame-2}.items():self.put(addr,val)
  after_a=self.goto(self.flip(self.s0,self.invoke) if mode=='tamper_outer' else self.invoke,'after_push_A')
  self.push_a=self.push('A',after_a);self.markers[self.push_a]='push_outer_A';self.markers[self.push_b]='push_outer_B'
  self.put(56000,self.entry-1);self.put(56001,(self.poproot if mode=='underflow_return' else self.push_a)-2)
  assert max(self.values)<59049
 def link(self,node,target):self.put(node,self.entry-1);self.put(node+1,target-2)
 def goto(self,target,kind):
  n=self.node();self.link(n,target);self.markers[n]=kind;return n
 def push(self,token,target):
  one=self.set_slot(self.s1,token,self.flip(self.d1,target));zero=self.set_slot(self.s0,token,self.flip(self.d0,target))
  return self.branch(self.d0,zero,self.branch(self.d1,one,self.overflow))
 def body(self,var,initial,target):
  n=self.node()
  for addr,val in {n:self.load-1,n+1:var-3,var-2:self.load,var-1:self.mix-1,var:initial,var+1:self.mix,var+2:self.entry-1,var+3:target-2}.items():self.put(addr,val)
  return n
 def metadata(self):
  return {k:getattr(self,k) for k in ('d0','d1','s0','s1','entry','load','rot','out','r_entry','mix','halt','variables','emissions','markers','push_a','push_b','push_inner','poproot','return_a','return_b','resume')}|{'code':self.code,'data':self.values,'mode':self.mode}

def trace(image,plan):
 mem=list(image)+[0]*(59049-len(image))
 for i in range(len(image),59049):mem[i]=p.SE.crazy(mem[i-1],mem[i-2])
 a=c=d=0;output=[];events=[];changes=[];mutations=[];active=False;status='limit'
 tails={pc:mem[pc] for pc in plan.code if pc-1 in plan.code};tails_changed=False
 def state():return {**base.snapshot(mem,plan),'values':[mem[v] for v in plan.variables]}
 for step in range(1,100000):
  if not 33<=mem[c]<=126:status='frozen';break
  op=(mem[c]+c)%94;kind=None
  if c==plan.entry and mem[d]+2 in plan.markers:active=True;kind=plan.markers[mem[d]+2]
  if c==plan.r_entry:kind='r_entry'
  if c==plan.mix:kind='body'
  if c==plan.rot and d in plan.emissions:kind='emit_'+plan.emissions[d]['char']
  if kind:events.append({'kind':kind,'step':step,'pc':c,'d':d,'a':a,**state()})
  before=state();pc=c
  if op==4:c=mem[d]
  elif op==5:output.append(a%256)
  elif op==23:raise AssertionError('unexpected input')
  elif op==39:a=mem[d]=p.SE.rot(mem[d])
  elif op==40:d=mem[d]
  elif op==62:a=mem[d]=p.SE.crazy(a,mem[d])
  elif op==81:status='halt';break
  if 33<=mem[c]<=126:mem[c]=p.SE.encrypt(mem[c])
  after=state()
  if active and before['flags']!=after['flags']:changes.append({'step':step,'pc':pc,'before':before['flags'],'after':after['flags']})
  if active and before['values']!=after['values']:mutations.append({'step':step,'pc':pc,'before':before['values'],'after':after['values']})
  c=(c+1)%59049;d=(d+1)%59049
  if active and any(mem[x]!=v for x,v in tails.items()):tails_changed=True
 return dict(status=status,steps=step,output_hex=bytes(output).hex(),events=events,changes=changes,mutations=mutations,final=state(),tails_changed=tails_changed)

def check(tr,plan,mode):
 assert tr['status']=='halt' and not tr['tails_changed']
 expected={'positive':'AB','tamper_outer':'B','wrong_slot':'AE','overflow_call':'O','underflow_return':'U'}[mode]
 assert tr['output_hex']==expected.encode().hex(),(mode,tr)
 assert all(m['pc']==plan.mix for m in tr['mutations'])
 entries=[e for e in tr['events'] if e['kind']=='r_entry'];bodies=[e for e in tr['events'] if e['kind']=='body']
 assert len(entries)==len(bodies)
 values=[12345,23456]
 for entry,body in zip(entries,bodies):
  assert entry['depth'] in (1,2) and body['depth']==entry['depth']
  index=entry['depth']-1;assert body['d']==plan.variables[index] and body['values']==values
  values[index]=p.SE.crazy(body['a'],values[index])
 assert tr['final']['values']==values
 if mode=='positive':
  assert [e['depth'] for e in entries]==[1,2,1,2]
  returns=[e for e in tr['events'] if e['kind'] in ('resume','return_A','return_B')]
  assert [(e['kind'],e['depth']) for e in returns]==[('resume',1),('return_A',0),('resume',1),('return_B',0)]
  assert [e['slots'][:e['depth']] for e in tr['events'] if e['kind'].startswith('after_push')]==[['A'],['A','A'],['B'],['B','A']]
  assert tr['final']['depth']==0
 if mode in ('overflow_call','underflow_return'):
  event=next(e for e in tr['events'] if e['kind']=='emit_'+expected)
  previous=next(e for e in reversed(tr['events'][:tr['events'].index(event)]) if e['kind'] in ('push_inner','pop'))
  assert previous['flags']==event['flags']==tr['final']['flags']

def main():
 out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);results={}
 for mode in ('positive','tamper_outer','wrong_slot','overflow_call','underflow_return'):
  plan=Connected(mode);image=plan.assemble();path=out/(mode+'.mb');path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps(plan.metadata(),indent=2)+'\n')
  tr=trace(image,plan);(out/(mode+'.trace.json')).write_text(json.dumps(tr,indent=2)+'\n');check(tr,plan,mode)
  native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout);(out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and cb.status=='end' and native.stdout.hex()==cb.output.hex()==tr['output_hex']
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,'clasesbolge_output_hex':cb.output.hex(),'clasesbolge_steps':cb.steps,**tr}
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
