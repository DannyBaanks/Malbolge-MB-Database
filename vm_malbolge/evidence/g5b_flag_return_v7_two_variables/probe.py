"""P7: one shared crazy site, two persistent variables and repeated A/B returns."""
import importlib.util, pathlib, os, sys, json, subprocess, hashlib
ROOT=pathlib.Path(os.environ['MALBOLGE_MB_DATABASE_ROOT']) if 'MALBOLGE_MB_DATABASE_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
p=load('p5',ROOT/'vm_malbolge/evidence/g5b_flag_return_v5/probe.py')
p.HANDOFF=56000
class Loop(p.Shared5):
 def __init__(self,mode):
  self.code={}; self.values={}; self.code_cursor=38000; self.data_cursor=41000
  self.k=self.alloc_code(2); self.code[self.k]=66; self.code[self.k+1]=p.encode(4,self.k+1)
  self.f=self.make_flag(); self.mov=self.make_tick(40,60); self.mix=self.make_tick(62,82)
  self.out=self.make_tick(5,25); self.loop=self.make_tick(40,60)
  V=41000; W=43000; P=42000; S=45000
  self.variables=[V,W]; self.a_conts=[V+4,W+4]; self.b_cont=P+1
  first=W if mode in ('control_first','swapped') else V
  second=V if mode in ('control_second','swapped') else W
  self.selection=[first,second]*3
  t={56000:self.loop-1,56001:S-2,S-1:self.loop,S:self.k-1,
     S+2:self.f-1,S+3:S+3,S+4:self.mov-1,S+5:first-3,
     P+1:self.f-1,P+3:self.out-1,P+5:self.out,P+6:self.loop-1,P+7:S-2}
  for var,initial in ((V,12345),(W,23456)):
   t.update({var-2:self.mov,var-1:self.mix-1,var:initial,var+1:self.mix,var+2:self.f-1,var+3:P,
             var+4:self.out-1,var+6:self.out,var+7:self.mov-1,var+8:second-3})
  self.values=t

def trace(image,plan):
 mem=list(image)+[0]*(59049-len(image))
 for i in range(len(image),59049): mem[i]=p.SE.crazy(mem[i-1],mem[i-2])
 a=c=d=0; out=[]; clocks=[]; calls=[]; returns=[]; writes=[]; active=False
 mutations=[]
 tails={pc:mem[pc] for pc in plan.code if pc-1 in plan.code}
 tail_changed=False
 for step in range(1,100000):
  if c==plan.k: active=True; clocks.append({'flag':mem[plan.f],'mix':mem[plan.mix],'values':[mem[v] for v in plan.variables]})
  if not 33<=mem[c]<=126: status='frozen'; break
  op=(mem[c]+c)%94
  if active and op==4 and d in (*plan.a_conts,plan.b_cont): returns.append('A' if d in plan.a_conts else 'B')
  if active and op in (39,62) and d in plan.variables: writes.append(c)
  before=[mem[v] for v in plan.variables]; pc_before=c
  if c==plan.mix: calls.append({'step':step,'a':a,'d':d,'value':mem[d],'flag':mem[plan.f],'before':before})
  if op==4: c=mem[d]
  elif op==5: out.append(a%256)
  elif op==23: raise AssertionError('unexpected input')
  elif op==39: a=mem[d]=p.SE.rot(mem[d])
  elif op==40: d=mem[d]
  elif op==62: a=mem[d]=p.SE.crazy(a,mem[d])
  elif op==81: status='halt'; break
  if 33<=mem[c]<=126: mem[c]=p.SE.encrypt(mem[c])
  after=[mem[v] for v in plan.variables]
  if pc_before==plan.mix: calls[-1]['after']=after
  if active and before!=after: mutations.append({'step':step,'pc':pc_before,'before':before,'after':after})
  c=(c+1)%59049; d=(d+1)%59049
  if active and any(mem[x]!=v for x,v in tails.items()): tail_changed=True
 else: status='limit'
 return dict(status=status,steps=step,output_hex=bytes(out).hex(),clocks=clocks,calls=calls,returns=returns,write_sites=sorted(set(writes)),mutations=mutations,final_values=[mem[v] for v in plan.variables],tail_changed=tail_changed)

def main():
 out=pathlib.Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False); results={}
 for mode in ('positive','control_first','control_second','swapped'):
  plan=Loop(mode); image=plan.assemble(); path=out/(mode+'.mb'); path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps({'code':plan.code,'data':plan.values,'k':plan.k,'flag':plan.f,'mix':plan.mix,'variables':plan.variables,'selection':plan.selection,'a_conts':plan.a_conts,'b_cont':plan.b_cont},indent=2)+'\n')
  tr=trace(image,plan); native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout); (out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and tr['status']=='halt' and cb.status=='end'
  assert native.stdout.hex()==tr['output_hex']==cb.output.hex()
  assert tr['write_sites']==[plan.mix] and not tr['tail_changed']
  assert tr['returns']==['A','B']*3,tr
  assert len(tr['calls'])==6 and len(tr['clocks'])==4
  assert all(r['flag']==74 and r['mix']==74 for r in tr['clocks'])
  values=[12345,23456]; a=55999; expected=[]
  for call,var in zip(tr['calls'],plan.selection):
   i=plan.variables.index(var)
   assert call['a']==a and call['d']==var and call['before']==values
   assert call['value']==values[i]
   a=values[i]=p.SE.crazy(a,values[i]); expected.append(a%256)
   assert call['after']==values
  assert native.stdout==bytes(expected) and tr['final_values']==values
  assert all(m['pc']==plan.mix for m in tr['mutations'])
  nominal=plan.variables*3
  assert ([c['d'] for c in tr['calls']]==nominal)==(mode=='positive')
  if mode=='control_first': assert values[0]==12345
  if mode=='control_second': assert values[1]==23456
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,**tr}
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__': main()
