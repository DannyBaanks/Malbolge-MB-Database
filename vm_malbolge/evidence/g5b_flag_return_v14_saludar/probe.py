"""Hand lowering of one Python function call to autonomous Classic Malbolge."""
import pathlib,os,sys,importlib.util,json,subprocess,hashlib
ROOT=pathlib.Path(os.environ['MALBOLGE_MB_DATABASE_ROOT']) if 'MALBOLGE_MB_DATABASE_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('p13',ROOT/'vm_malbolge/evidence/g5b_flag_return_v13_numeric_slot/probe.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base);p=base.p
class Greeting(base.Numeric):
 def __init__(self,mode):
  self.code={};self.values={};self.markers={};self.mode=mode
  self.slot=50000;self.journal=50100;self.mask=50200;self.call_pointer=51000;self.sources=[52000]
  self.outputs=[53000,53100,53200,53300,53400,53500];self.function=20000;self.continuation=32000 if mode=='alternate' else 30000
  self.banks=[self.slot,self.journal,self.mask,self.call_pointer,*self.sources,*self.outputs,56000]
  for bank in self.banks:
   self.values[bank+1]=bank-1
   for i,target in enumerate(self.banks):self.values[bank+10+i]=target-1
  self.values.update({self.slot:base.C1,self.journal:base.C1,self.mask:base.C1,self.call_pointer:(self.continuation if mode=='bypass' else self.function)-1,self.sources[0]:self.continuation-1,56000:14999})
  for cell,char in zip(self.outputs,b'Hola\n!'):self.values[cell]=char*3
  self.pc=15000;self.d=56001;self.mark('caller',0)
  self.read(self.sources[0]);self.set_d(self.journal);self.op(62);self.set_d(self.slot);self.op(62);self.mark('return_saved',0)
  self.set_d(self.call_pointer);self.mark('call',0);self.op(4)
  self.pc=self.function;self.d=self.call_pointer+1;self.mark('saludar_entry',0)
  for i,cell in enumerate(self.outputs[:5]):self.set_d(cell);self.op(39);self.mark('print_'+str(i),0);self.op(5)
  if mode=='broken_return':self.reset(self.slot);self.mark('return_corrupted',0)
  self.read(self.slot);self.set_d(self.slot);self.mark('ret',0);self.op(4);self.function_end=self.pc
  self.pc=self.continuation;self.d=self.call_pointer+1 if mode=='bypass' else self.slot+1;self.mark('after_call',0)
  self.reset(self.slot);self.reset(self.journal);self.mark('finished',0);self.op(81)
  self.pc=base.C1+1;self.d=self.slot+1;self.mark('error',-1)
  self.set_d(self.outputs[5]);self.op(39);self.op(5);self.op(81)
 def metadata(self):return {k:getattr(self,k) for k in ('slot','journal','mask','sources','outputs','markers','code','values','mode','function','function_end','continuation','call_pointer')}|{'data':self.values,'mask_value':base.C1}

def check(tr,plan,mode):
 assert tr['status']=='halt'
 assert tr['output_hex']=={'saludar':'486f6c610a','alternate':'486f6c610a','broken_return':'486f6c610a21','bypass':''}[mode]
 kinds=[e['kind'] for e in tr['events']]
 assert kinds[:3]==['caller','return_saved','call']
 if mode=='bypass':assert 'saludar_entry' not in kinds and 'ret' not in kinds and 'after_call' in kinds
 else:
  assert kinds[3:9]==['saludar_entry','print_0','print_1','print_2','print_3','print_4']
  assert tr['jumps'][0]['next_pc']==plan.function and tr['jumps'][0]['d']==plan.call_pointer
  assert tr['jumps'][1]['d']==plan.slot
  if mode=='broken_return':assert tr['jumps'][1]['next_pc']==29525 and 'after_call' not in kinds
  else:
   assert tr['jumps'][1]['stored']==plan.continuation-1 and tr['jumps'][1]['next_pc']==plan.continuation
   assert kinds[-3:]==['ret','after_call','finished']
   assert tr['final_slot']==tr['final_journal']==base.C1

def main():
 out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);results={};bodies=[]
 ref=subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('saludar.py'))],capture_output=True,check=True)
 (out/'python.stdout.raw').write_bytes(ref.stdout);(out/'python.stderr.raw').write_bytes(ref.stderr)
 assert ref.stdout==b'Hola\n'
 for mode in ('saludar','alternate','broken_return','bypass'):
  plan=Greeting(mode);image=plan.assemble();path=out/(mode+'.mb');path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps(plan.metadata(),indent=2)+'\n')
  tr=base.trace(image,plan);(out/(mode+'.trace.json')).write_text(json.dumps(tr,indent=2)+'\n');check(tr,plan,mode)
  native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout);(out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and cb.status=='end' and native.stdout.hex()==cb.output.hex()==tr['output_hex']
  if mode in ('saludar','alternate'):
   assert native.stdout==ref.stdout;bodies.append(image[plan.function:plan.function_end])
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,'clasesbolge_output_hex':cb.output.hex(),'clasesbolge_steps':cb.steps,**tr}
 assert bodies[0]==bodies[1]
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
