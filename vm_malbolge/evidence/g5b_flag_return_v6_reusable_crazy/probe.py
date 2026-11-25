"""P6: repeated A/B returns with one shared crazy site. Outputs must be new directories."""
import importlib.util, pathlib, os, sys, json, subprocess, hashlib
ROOT=pathlib.Path(os.environ.get('MALBOLGE_MB_DATABASE_ROOT','/home/danny/Development/ISyCo Git/MALBOLGE-MB-DATABASE'))
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
  V=41000; P=42000; S=45000; self.v=V; self.a_cont=V+4; self.b_cont=P+1
  t={56000:self.loop-1,56001:S-2,V-2:self.mov,V-1:self.mix-1,V:12345,V+1:self.mix,V+2:self.f-1,V+3:P,
     V+4:self.out-1,V+6:self.out,V+7:self.mov-1,V+8:V-3,
     S-1:self.loop,S:self.k-1}
  if mode=='control_a': t.update({S+2:self.mov-1,S+3:V-3})
  else: t.update({S+2:self.f-1,S+3:S+3,S+4:self.mov-1,S+5:V-3})
  if mode=='control_b': t.update({P+1:self.out-1,P+3:self.out,P+4:self.loop-1,P+5:S-2})
  else: t.update({P+1:self.f-1,P+3:self.out-1,P+5:self.out,P+6:self.loop-1,P+7:S-2})
  self.values=t

def trace(image,plan):
 mem=list(image)+[0]*(59049-len(image))
 for i in range(len(image),59049): mem[i]=p.SE.crazy(mem[i-1],mem[i-2])
 a=c=d=0; out=[]; clocks=[]; calls=[]; returns=[]; writes=[]; active=False
 tails={pc:mem[pc] for pc in plan.code if pc-1 in plan.code}
 tail_changed=False
 for step in range(1,100000):
  if c==plan.k: active=True; clocks.append({'flag':mem[plan.f],'mix':mem[plan.mix],'value':mem[plan.v]})
  if not 33<=mem[c]<=126: status='frozen'; break
  op=(mem[c]+c)%94
  if active and op==4 and d in (plan.a_cont,plan.b_cont): returns.append('A' if d==plan.a_cont else 'B')
  if active and op in (39,62) and d==plan.v: writes.append(c)
  if c==plan.mix: calls.append({'step':step,'a':a,'d':d,'value':mem[d],'flag':mem[plan.f]})
  if op==4: c=mem[d]
  elif op==5: out.append(a%256)
  elif op==23: raise AssertionError('unexpected input')
  elif op==39: a=mem[d]=p.SE.rot(mem[d])
  elif op==40: d=mem[d]
  elif op==62: a=mem[d]=p.SE.crazy(a,mem[d])
  elif op==81: status='halt'; break
  if 33<=mem[c]<=126: mem[c]=p.SE.encrypt(mem[c])
  c=(c+1)%59049; d=(d+1)%59049
  if active and any(mem[x]!=v for x,v in tails.items()): tail_changed=True
 else: status='limit'
 return dict(status=status,steps=step,output_hex=bytes(out).hex(),clocks=clocks,calls=calls,returns=returns,write_sites=sorted(set(writes)),tail_changed=tail_changed)

def main():
 out=pathlib.Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False); results={}
 for mode in ('positive','control_a','control_b'):
  plan=Loop(mode); image=plan.assemble(); path=out/(mode+'.mb'); path.write_bytes(image)
  (out/(mode+'.plan.json')).write_text(json.dumps({'code':plan.code,'data':plan.values,'k':plan.k,'flag':plan.f,'mix':plan.mix,'a_cont':plan.a_cont,'b_cont':plan.b_cont},indent=2)+'\n')
  tr=trace(image,plan); native=subprocess.run([str(p.OLM),str(path)],input=b'',capture_output=True,timeout=20)
  (out/(mode+'.stdout.raw')).write_bytes(native.stdout); (out/(mode+'.stderr.raw')).write_bytes(native.stderr)
  cb=p.cb.execute(image,b'',max_steps=100000)
  assert native.returncode==0 and tr['status']=='halt' and cb.status=='end'
  assert native.stdout.hex()==tr['output_hex']==cb.output.hex()
  assert tr['write_sites']==[plan.mix] and not tr['tail_changed']
  if mode=='positive':
   assert tr['returns']==['A','B']*3,tr
   assert len(tr['calls'])==6 and len(tr['clocks'])==4
   assert all(r['flag']==74 and r['mix']==74 for r in tr['clocks'])
   val=12345; a=55999; expected=[]
   for call in tr['calls']:
    assert call['a']==a and call['d']==plan.v and call['value']==val
    a=val=p.SE.crazy(a,val); expected.append(a%256)
   assert native.stdout==bytes(expected)
  elif mode=='control_a':
   assert tr['returns']==['B']*3 and len(tr['calls'])==3
   assert all(c['flag']==74 for c in tr['clocks'])
  else:
   assert tr['returns']==['A','B','B','B'] and len(tr['calls'])==4
   assert [c['flag'] for c in tr['clocks']]==[74,70,70,70]
  results[mode]={'sha256':hashlib.sha256(image).hexdigest(),'native_rc':native.returncode,'clasesbolge_status':cb.status,**tr}
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__': main()
