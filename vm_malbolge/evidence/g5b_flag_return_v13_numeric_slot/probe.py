"""Native numeric-address journal and indirect returns; output directories must be new."""
import pathlib,os,sys,importlib.util,json,subprocess,hashlib
ROOT=pathlib.Path(os.environ['MALBOLGE_MB_DATABASE_ROOT']) if 'MALBOLGE_MB_DATABASE_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('p5',ROOT/'vm_malbolge/evidence/g5b_flag_return_v5/probe.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);p.HANDOFF=56000
C1=29524;TARGETS=[20000,25000,30000]
class Numeric(p.Shared5):
 def __init__(self,mode):
  self.code={};self.values={};self.markers={};self.mode=mode
  self.slot=50000;self.journal=50100;self.mask=50200;self.sources=[52000,52100,52200];self.outputs=[53000,53100,53200,53300]
  self.banks=[self.slot,self.journal,self.mask,*self.sources,*self.outputs,56000]
  for bank in self.banks:
   self.values[bank+1]=bank-1
   for i,target in enumerate(self.banks):self.values[bank+10+i]=target-1
  self.values.update({self.slot:C1,self.journal:C1,self.mask:C1})
  for source,target in zip(self.sources,TARGETS):self.values[source]=target-1
  for cell,char in zip(self.outputs,'ABCE'):self.values[cell]=ord(char)*3
  self.values[56000]=14999;self.pc=15000;self.d=56001;self.transaction(0)
  for i,target in enumerate(TARGETS):
   self.pc=target;self.d=self.slot+1;self.mark('continuation_'+chr(65+i),i)
   self.set_d(self.outputs[i]);self.op(39);self.op(5)
   self.reset(self.slot);self.reset(self.journal);self.mark('rearmed',i)
   if i+1<len(TARGETS):self.transaction(i+1)
   else:self.op(81)
  wrong=p.SE.rot(TARGETS[0]-1)+1
  for target in sorted({C1+1,wrong}):
   self.pc=target;self.d=self.slot+1;self.mark('error',-1)
   self.set_d(self.outputs[3]);self.op(39);self.op(5);self.op(81)
 def mark(self,kind,index):self.markers.setdefault(self.pc,[]).append({'kind':kind,'index':index})
 def op(self,opcode):
  assert self.pc not in self.code,(self.pc,opcode)
  self.code[self.pc]=p.encode(opcode,self.pc);self.pc+=1;self.d=(self.d+1)%59049
 def set_d(self,target):
  if self.d==target:return
  bank=next((b for b in self.banks if b+1<=self.d<=b+20),None);assert bank is not None,self.d
  pos=bank+1 if target==bank and self.d==bank+1 else bank+10+self.banks.index(target)
  assert pos>=self.d,(pos,self.d)
  while self.d<pos:self.op(68)
  self.op(40);self.d=target
 def read(self,cell,count=10):
  for _ in range(count):self.set_d(cell);self.op(39)
 def reset(self,cell):
  self.read(self.mask,1)
  for _ in range(2):self.set_d(cell);self.op(62)
 def transaction(self,index):
  self.mark('begin',index);self.read(self.sources[index]);self.mark('source_loaded',index)
  self.set_d(self.journal);self.op(62);self.mark('journal_saved',index)
  self.set_d(self.slot);self.op(62);self.mark('slot_written',index)
  self.reset(self.slot);self.mark('clobbered',index)
  self.read(self.journal);self.mark('journal_loaded',index);self.set_d(self.slot)
  if self.mode!='skip_restore':self.op(62)
  self.mark('restored' if self.mode!='skip_restore' else 'restore_skipped',index)
  if self.mode=='tamper_slot' and index==0:self.read(self.slot,1);self.mark('tampered',index)
  self.read(self.slot);self.mark('read_back',index)
  self.set_d(self.slot);self.mark('indirect_jump',index);self.op(4)
 def metadata(self):
  return {k:getattr(self,k) for k in ('slot','journal','mask','sources','outputs','markers')}|{'code':self.code,'data':self.values,'targets':TARGETS,'mode':self.mode,'mask_value':C1}

def trace(image,plan):
 mem=list(image)+[0]*(59049-len(image))
 for i in range(len(image),59049):mem[i]=p.SE.crazy(mem[i-1],mem[i-2])
 a=c=d=0;out=[];events=[];jumps=[];writes=[];active=False;status='limit'
 for step in range(1,100000):
  if c in plan.markers:
   active=True
   for mark in plan.markers[c]:events.append({**mark,'step':step,'pc':c,'d':d,'a':a,'slot':mem[plan.slot],'journal':mem[plan.journal],'mask':mem[plan.mask],'sources':[mem[x] for x in plan.sources]})
  if not 33<=mem[c]<=126:status='frozen';break
  op=(mem[c]+c)%94;pc=c
  if active and op==4:jumps.append({'step':step,'pc':c,'d':d,'stored':mem[d],'next_pc':(mem[d]+1)%59049})
  before=[mem[plan.slot],mem[plan.journal]]
  if op==4:c=mem[d]
  elif op==5:out.append(a%256)
  elif op==23:raise AssertionError('unexpected input')
  elif op==39:a=mem[d]=p.SE.rot(mem[d])
  elif op==40:d=mem[d]
  elif op==62:a=mem[d]=p.SE.crazy(a,mem[d])
  elif op==81:status='halt';break
  if 33<=mem[c]<=126:mem[c]=p.SE.encrypt(mem[c])
  after=[mem[plan.slot],mem[plan.journal]]
  if active and before!=after:writes.append({'step':step,'pc':pc,'before':before,'after':after})
  c=(c+1)%59049;d=(d+1)%59049
 return dict(status=status,steps=step,output_hex=bytes(out).hex(),events=events,jumps=jumps,writes=writes,final_slot=mem[plan.slot],final_journal=mem[plan.journal])
def check(tr,plan,mode):
 assert tr['status']=='halt' and tr['output_hex']==('ABC' if mode=='positive' else 'E').encode().hex(),tr
 if mode=='positive':
  assert [j['next_pc'] for j in tr['jumps']]==TARGETS and tr['final_slot']==tr['final_journal']==C1
  for index,target in enumerate(TARGETS):
   ev={e['kind']:e for e in tr['events'] if e['index']==index};x=target-1;g=p.SE.crazy(x,C1)
   assert ev['begin']['slot']==ev['begin']['journal']==C1
   assert ev['source_loaded']['a']==x and ev['source_loaded']['sources'][index]==x
   assert ev['journal_saved']['journal']==g and ev['slot_written']['slot']==x
   assert ev['clobbered']['slot']==C1 and ev['clobbered']['journal']==g
   assert ev['journal_loaded']['a']==g and ev['journal_loaded']['journal']==g
   assert ev['restored']['slot']==ev['read_back']['a']==ev['read_back']['slot']==x
   assert ev['indirect_jump']['d']==plan.slot and ev['indirect_jump']['slot']==x
   assert ev['rearmed']['slot']==ev['rearmed']['journal']==C1
 else:
  expected=C1 if mode=='skip_restore' else p.SE.rot(TARGETS[0]-1)
  assert len(tr['jumps'])==1 and tr['jumps'][0]['stored']==expected and tr['jumps'][0]['d']==plan.slot
def main():
 out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);results={}
 for mode in ('positive','skip_restore','tamper_slot'):
  plan=Numeric(mode);image=plan.assemble();path=out/(mode+'.mb');path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps(plan.metadata(),indent=2)+'\n')
  tr=trace(image,plan);(out/(mode+'.trace.json')).write_text(json.dumps(tr,indent=2)+'\n');check(tr,plan,mode)
  native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout);(out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and cb.status=='end' and native.stdout.hex()==cb.output.hex()==tr['output_hex']
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,'clasesbolge_output_hex':cb.output.hex(),'clasesbolge_steps':cb.steps,**tr}
 algebra=all(p.SE.crazy(p.SE.crazy(x,C1),C1)==x for x in range(59049));assert algebra
 (out/'algebra.json').write_text(json.dumps({'word_count':59049,'mask':C1,'double_crazy_identity':algebra})+'\n')
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
