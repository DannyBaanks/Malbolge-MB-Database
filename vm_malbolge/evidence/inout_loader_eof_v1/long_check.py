#!/usr/bin/env python3
import base64,hashlib,json,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[2]; Q=P/'attempt_02'; img=Q/'reference_cat.mb'; out=P/'long_raw'; out.mkdir()
data=bytes((73*i+195)%256 for i in range(10000)); (out/'input.bin').write_bytes(data)
olm=ROOT.parent/'Malbolge-PureEpoch/build/olmstead'; runner=ROOT/'runners/malbolge-original/malbolge'
commands={'olmstead':[str(olm),str(img)],'runner':[str(runner),str(img),'30000000']}
results={}
for name,cmd in commands.items():
 try:
  p=subprocess.run(cmd,input=data,capture_output=True,timeout=30); code=p.returncode; raw=p.stdout; err=p.stderr; timed=False
 except subprocess.TimeoutExpired as e:
  code=None; raw=e.stdout or b''; err=e.stderr or b''; timed=True
 (out/(name+'.out')).write_bytes(raw); (out/(name+'.err')).write_bytes(err)
 results[name]={'rc':code,'timed_out':timed,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'exact':raw==data,'exact_plus_runner_newline':raw==data+b'\n','stderr':err.decode('latin1')}
for name in ('scratch','independent','oracle_default','oracle_stop'):
 req=json.dumps({'engine':name,'image':str(img),'input':base64.b64encode(data).decode()}).encode()
 try:
  p=subprocess.run([sys.executable,'-I',str(Q/'probe.py'),'--worker'],input=req,capture_output=True,timeout=30,env={'MBDB_ROOT':str(ROOT)}); code=p.returncode; timed=False; err=p.stderr; result=json.loads(p.stdout) if code==0 else None
 except subprocess.TimeoutExpired as e:
  code=None; timed=True; err=e.stderr or b''; result=None
 raw=base64.b64decode(result['out']) if result else b''
 (out/(name+'.out')).write_bytes(raw); (out/(name+'.err')).write_bytes(err)
 results[name]={'rc':code,'timed_out':timed,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'exact':raw==data,'steps':result['steps'] if result else None,'status':result['status'] if result else None}
(P/'long_results.json').write_text(json.dumps(results,indent=2)+'\n'); print(json.dumps(results,indent=2))
