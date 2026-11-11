#!/usr/bin/env python3
"""Check a strict-loader EOF cat reference and contrast prior permissive loop."""
import base64, hashlib, importlib.util, json, os, pathlib, platform, re, subprocess, sys
P=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(os.environ['MBDB_ROOT']).resolve() if 'MBDB_ROOT' in os.environ else P.parents[2]
BASE=ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
spec=importlib.util.spec_from_file_location('compose',BASE); M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
B=M.B; MAX=30000000; WALL=15
sha=lambda b:hashlib.sha256(b).hexdigest()
if '--worker' in sys.argv:
    request=json.loads(sys.stdin.read()); image=pathlib.Path(request['image']).read_bytes(); data=base64.b64decode(request['input']); kind=request['engine']
    if kind=='scratch':
        r=M.SE.run(image,max_steps=MAX,stdin=data); out=r['out']; steps=r['steps']; status=r['status']
    elif kind=='independent':
        ns={}; exec(compile(B.INDEP.read_text().split('def trits')[0],str(B.INDEP),'exec'),ns); r=ns['run'](list(image),list(data),maxs=MAX,guard=True); out=r['out']; steps=r['steps']; status=r['status']
    elif kind in ('oracle_default','oracle_stop'):
        r=M.O.oracle_run(request['image'],max_steps=MAX,stdin_data=data.decode('latin1'),stop_on_eof=kind=='oracle_stop'); out=r['output'].encode('latin1'); steps=r['steps']; status=r['status']
    print(json.dumps({'out':base64.b64encode(out).decode(),'steps':steps,'status':status})); raise SystemExit(0)

outdir=P/'raw'; outdir.mkdir()
reference=P/'reference_cat.mb'; broken=P/'reference_cat_bad_eof.mb'; original=ROOT/'vm_malbolge/evidence/epoch_dload_inout_v1/compose_inout.mb'
valid=M.VALID; image=original.read_bytes(); ref=reference.read_bytes()
invalid=next(x for x in range(33,127) if x%94 not in valid)
bad=bytes([invalid])+ref[1:]; (P/'reference_cat_bad_loader.mb').write_bytes(bad)
cases={'empty':b'','zero':b'\0','two':b'\x80\xff','mixed':b'\x00\x0a\x80\xff','all256':bytes(range(256))}

def execute(argv,stdin):
    try:
        r=subprocess.run(argv,input=stdin,capture_output=True,timeout=WALL)
        return r.returncode,False,r.stdout,r.stderr
    except subprocess.TimeoutExpired as e:
        return None,True,e.stdout or b'',e.stderr or b''

def save(tag,stdout,stderr):
    (outdir/(tag+'.stdout')).write_bytes(stdout); (outdir/(tag+'.stderr')).write_bytes(stderr)
    return {'stdout_file':'raw/'+tag+'.stdout','stdout_bytes':len(stdout),'stdout_sha256':sha(stdout),'stderr_file':'raw/'+tag+'.stderr','stderr_sha256':sha(stderr)}

def native(tag,binpath,img,data,runner=False):
    cmd=[str(binpath),str(img)]+([str(MAX)] if runner else [])
    rc,timed,stdout,stderr=execute(cmd,data); result=save(tag,stdout,stderr)
    match=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',stderr) if runner else None
    result.update(rc=rc,timed_out=timed,stdout_equals_input=stdout==data,stdout_equals_input_plus_newline=stdout==data+b'\n',steps=int(match.group(1)) if match else None,status=match.group(2).decode() if match else None)
    return result

def worker(tag,kind,img,data):
    request=json.dumps({'engine':kind,'image':str(img),'input':base64.b64encode(data).decode()}).encode()
    rc,timed,stdout,stderr=execute([sys.executable,'-I',str(P/'probe.py'),'--worker'],request)
    out=b''; parsed=None
    if rc==0 and not timed:
        parsed=json.loads(stdout); out=base64.b64decode(parsed['out'])
    result=save(tag,out,stderr)
    result.update(rc=rc,timed_out=timed,stdout_equals_input=out==data,steps=parsed['steps'] if parsed else None,status=parsed['status'] if parsed else None)
    return result

report={'base':'e42938d','gates_commit':'8f36a7f','platform':platform.platform(),'wall_timeout_seconds':WALL,'step_limit':MAX,'inputs':{k:{'hex':v.hex(),'sha256':sha(v)} for k,v in cases.items()},'images':{'previous':{'length':len(image),'sha256':sha(image),'valid_cells':sum((v+i)%94 in valid for i,v in enumerate(image))},'reference':{'length':len(ref),'sha256':sha(ref),'valid_cells':sum((v+i)%94 in valid for i,v in enumerate(ref))},'reference_bad_eof':{'sha256':sha(broken.read_bytes())},'reference_bad_loader':{'sha256':sha(bad),'first_byte':invalid}},'pairs_initial_opcodes':{},'reference_runs':{},'controls':{},'previous_runs':{}}
for name,positions in {'IN':[43,47],'DLOAD':[60,64],'OUT':[119,123]}.items(): report['pairs_initial_opcodes'][name]=[(image[i]+i)%94 for i in positions]
for label,data in cases.items():
    (outdir/(label+'.input')).write_bytes(data)
    z={'olmstead':native('reference_'+label+'_olmstead',B.OLMSTEAD,reference,data),'runner_c':native('reference_'+label+'_runner',B.C_RUNNER,reference,data,True)}
    if label in ('empty','zero','mixed','all256'):
        for kind in ('scratch','independent','oracle_default','oracle_stop'): z[kind]=worker('reference_'+label+'_'+kind,kind,reference,data)
    report['reference_runs'][label]=z
    print('reference',label,{k:(v['status'],v['timed_out'],v['stdout_equals_input'],v['stdout_equals_input_plus_newline']) for k,v in z.items()},flush=True)
for img,label in ((P/'reference_cat_bad_loader.mb','bad_loader'),(broken,'bad_eof')):
    report['controls'][label]=native('control_'+label,B.OLMSTEAD,img,b'\x00\x0a\x80\xff')
for label in ('empty','zero','two','mixed'):
    data=cases[label]
    z={'runner_c':native('previous_'+label+'_runner',B.C_RUNNER,original,data,True)}
    for kind in ('scratch','independent','oracle_default','oracle_stop'): z[kind]=worker('previous_'+label+'_'+kind,kind,original,data)
    report['previous_runs'][label]=z
    print('previous',label,{k:(v['status'],v['timed_out'],v['stdout_equals_input'],v['stdout_equals_input_plus_newline']) for k,v in z.items()},flush=True)
report['summary']={'reference_olmstead_echo_all':all(not x['olmstead']['timed_out'] and x['olmstead']['rc']==0 and x['olmstead']['stdout_equals_input'] for x in report['reference_runs'].values()),'loader_mutant_rejected':report['controls']['bad_loader']['rc']==1 and not report['controls']['bad_loader']['timed_out'],'eof_control_differs':not report['controls']['bad_eof']['stdout_equals_input'] or report['controls']['bad_eof']['rc']!=0 or report['controls']['bad_eof']['timed_out']}
(P/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('summary',report['summary'],flush=True)
