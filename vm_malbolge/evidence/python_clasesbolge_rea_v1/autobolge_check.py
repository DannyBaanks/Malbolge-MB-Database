#!/usr/bin/env python3
"""Evaluate the generated image with Autobolge's dense Classic runtime."""
import hashlib,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];auto=ROOT.parent/'Autobolge';sys.path.insert(0,str(auto))
from relational.classic import run_reference
program=(P/'echo4.mb').read_text(encoding='ascii');r={}
for key,data in [('four','Ab9!'),('short','Ab9'),('empty','')]:
 out,steps,terminated,state=run_reference(program,input_data=data,max_steps=20)
 r[key]={'input_hex':data.encode().hex(),'output_hex':out.encode('latin1').hex(),'steps':steps,'terminated':terminated,'stop_reason':state.stop_reason,'reason_code':state.reason_code}
r['source_sha256']=hashlib.sha256((auto/'relational/classic.py').read_bytes()).hexdigest()
(P/'autobolge_check.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
