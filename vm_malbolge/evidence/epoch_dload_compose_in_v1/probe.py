#!/usr/bin/env python3
import array, hashlib, importlib.util, json, math, os, pathlib, platform, re, subprocess
P=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(os.environ['MBDB_ROOT']).resolve() if 'MBDB_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
source=ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
spec=importlib.util.spec_from_file_location('compose',source)
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
M.TARGETS['IN']=23
p=M.derive('IN'); img=M.build(p); path=P/'compose_in.mb'; path.write_bytes(bytes(img))
N=M.N; S=M.SE; rounds=10000

def sha(b): return hashlib.sha256(b).hexdigest()
def memhash(mem): return sha(array.array('q',mem).tobytes())
def trace(img, input_bytes, limit_rounds, periodic=False):
    mem=list(img)+[0]*(N-len(img))
    for i in range(len(img),N): mem[i]=S.crazy(mem[i-1],mem[i-2])
    a=c=d=ip=0; opn=dln=0; ops=set(); dests=[]; starts=[]; opds=[]; seen={}; repeat=None; read=[]; counts=[]; status='MAX'
    maxsteps=limit_rounds*p['n']+3000
    for step in range(1,maxsteps+1):
        if c==p['shift']:
            starts.append(d)
            if periodic and repeat is None:
                h=sha(array.array('q',mem).tobytes()+repr((a,c,d)).encode())
                if h in seen: repeat=[seen[h],len(starts)-1]
                else: seen[h]=len(starts)-1
        v=mem[c]
        if not 33<=v<=126: status='NONPRINT'; break
        op=(v+c)%94
        if p['shift']<=c<=p['jmp']:
            if op in M.VALID: ops.add(op)
            if op==23: opn+=1; opds.append(d)
            if op==40: dln+=1
        if op==4:
            dest=mem[d]; dests.append(dest); counts.append([opn,dln]); opn=dln=0; c=dest
        elif op==5: pass
        elif op==23:
            if ip>=len(input_bytes): status='EOF'; break
            a=input_bytes[ip]; read.append(a); ip+=1
        elif op==39: mem[d]=S.rot(mem[d]); a=mem[d]
        elif op==40: d=mem[d]
        elif op==62: mem[d]=S.crazy(a,mem[d]); a=mem[d]
        elif op==81: status='HALTED'; break
        if 33<=mem[c]<=126: mem[c]=S.encrypt(mem[c])
        c=(c+1)%N; d=(d+1)%N
        if len(dests)>=limit_rounds: status='ROUNDS'; break
    return dict(steps=step,status=status,rounds=len(dests),dests=dests,starts=starts,opds=opds,ops=sorted(ops),counts=counts,read=bytes(read),repeat=repeat,mem=mem,registers=[a,c,d])

def valid(t,R):
    return (t['rounds']==R and all(x==p['T'] for x in t['dests']) and all(x==[1,1] for x in t['counts']) and t['ops']==sorted([4,23,40]) and len(set(t['starts']))==2 and all(x>p['jmp'] and x not in [p['A'],p['B'],p['C'],p['D']] for x in t['opds']))
def brief(t):
    return dict(steps=t['steps'],status=t['status'],rounds=t['rounds'],destinations=sorted(set(t['dests'])),d_start=sorted(set(t['starts'])),d_at_in=sorted(set(t['opds'])),body_ops=t['ops'],counts_first8=t['counts'][:8],counts_distinct=sorted(set(map(tuple,t['counts']))),input_count=len(t['read']),input_sha256=sha(t['read']),repeat=t['repeat'],memory_sha256=memhash(t['mem']),registers=t['registers'])
stream=bytes((i*73+19)%256 for i in range(rounds+1))
t=trace(img,stream,rounds)
constant=trace(img,bytes([65])*(rounds+1),rounds,True)
sc=S.run(bytes(img),max_steps=t['steps'],stdin=stream,collect=True)
ns={}; ind_path=M.B.INDEP; exec(compile(ind_path.read_text().split('def trits')[0],str(ind_path),'exec'),ns)
ind=ns['run'](img,list(stream),maxs=t['steps'],guard=True)
o=M.O.oracle_run(str(path),max_steps=t['steps'],stdin_data=stream.decode('latin1'),stop_on_eof=True)
c=subprocess.run([str(M.B.C_RUNNER),str(path),str(t['steps'])],input=stream,capture_output=True,timeout=120)
controls={}
for name,image in M.control_images(p,img).items():
    (P/('ctrl_in_'+name+'.mb')).write_bytes(bytes(image))
    z=trace(image,stream,60); controls[name]={'criterion':valid(z,60),'observed':brief(z)}
boundaries={}
for size in (0,1,2,257):
    limited=stream[:size]
    tr=trace(img,limited,rounds)
    oi=M.O.oracle_run(str(path),max_steps=t['steps'],stdin_data=limited.decode('latin1'),stop_on_eof=True)
    ii=ns['run'](img,list(limited),maxs=t['steps'],guard=True)
    ci=subprocess.run([str(M.B.C_RUNNER),str(path),str(t['steps'])],input=limited,capture_output=True,timeout=120)
    cm=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',ci.stderr)
    boundaries[str(size)]={'trace_step':tr['steps'],'trace_status':tr['status'],'trace_reads':len(tr['read']),'oracle_step':oi['steps'],'oracle_status':oi['status'],'independent_step':ii['steps'],'independent_status':ii['status'],'c_step':int(cm.group(1)) if cm else None,'c_status':cm.group(2).decode() if cm else None,'c_rc':ci.returncode}
cycles=sorted(set(M._clen(img[x]) for x in list(range(p['shift'],p['jmp']+1))+[p['T']]))
period=constant['repeat'][1]-constant['repeat'][0] if constant['repeat'] else None
empty_o=M.O.oracle_run(str(path),max_steps=t['steps'],stdin_data='',stop_on_eof=True)
empty_i=ns['run'](img,[],maxs=t['steps'],guard=True)
empty_s=S.run(bytes(img),max_steps=t['steps'],stdin=b'',collect=True)
empty_c=subprocess.run([str(M.B.C_RUNNER),str(path),str(t['steps'])],input=b'',capture_output=True,timeout=120)
olm=subprocess.run([str(M.B.OLMSTEAD),str(path)],input=b'',capture_output=True,timeout=60)
reder=M.independent_derive('IN'); keys=['shift','T','delta','e','jmp','n','D0','V0','V1','A','B','C','D','d_op']
gates={
 'G0':M.check_image(img,p)['ok'] and all(reder[k]==p[k] for k in keys),
 'G1':valid(t,rounds) and t['read']==stream[:rounds] and sc['steps']==ind['steps']==o['steps']==t['steps'] and sc['status']=='MAX' and ind['status']=='MAX' and o['status']=='MAX_STEPS' and memhash(t['mem'])==memhash(sc['mem'])==memhash(ind['mem']) and sc['out']==ind['out']==o['output'].encode('latin1'),
 'G2':all(not x['criterion'] for x in controls.values()),
 'G3':valid(constant,rounds) and period==math.lcm(*cycles) and all(constant['starts'][i]==constant['starts'][i+2] for i in range(len(constant['starts'])-2)),
 'G4':all(x['trace_status']=='EOF' and x['oracle_status']=='EOF' and x['independent_status']=='EOF' and x['c_status']=='HALTED' and x['c_rc']==0 and x['trace_step']==x['oracle_step']==x['independent_step']==x['c_step'] and x['trace_reads']==int(k) for k,x in boundaries.items()) and olm.returncode in (0,1)}
result={'environment':platform.platform(),'base':'55a574f','params':p,'image_sha256':sha(bytes(img)),'length':len(img),'structure':M.check_image(img,p),'independent_params':reder,'variable':brief(t),'constant':brief(constant),'period_prediction':math.lcm(*cycles),'cycle_lengths':cycles,'input_prefix_hex':stream[:32].hex(),'input_matched_exactly':t['read']==stream[:rounds],'engines':{'oracle':o,'scratch':{'steps':sc['steps'],'status':sc['status'],'memory_sha256':memhash(sc['mem'])},'independent':{'steps':ind['steps'],'status':ind['status'],'memory_sha256':memhash(ind['mem'])},'c':{'rc':c.returncode,'stdout_hex':c.stdout.hex(),'stderr':c.stderr.decode('latin1')}},'controls':controls,'input_boundaries':boundaries,'eof':{'oracle':empty_o,'independent':{'steps':empty_i['steps'],'status':empty_i['status']},'scratch':{'steps':empty_s['steps'],'status':empty_s['status']},'c':{'rc':empty_c.returncode,'stdout_hex':empty_c.stdout.hex(),'stderr':empty_c.stderr.decode('latin1')}},'olmstead':{'rc':olm.returncode,'stderr':olm.stderr.decode('latin1'),'valid_cells':sum((v+i)%94 in M.VALID for i,v in enumerate(img))},'gates':gates}
(P/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'params':p,'variable':brief(t),'constant':brief(constant),'cycles':cycles,'period_prediction':math.lcm(*cycles),'engines':result['engines'],'controls':{k:v['observed'] for k,v in controls.items()},'input_boundaries':boundaries,'eof':result['eof'],'olmstead':result['olmstead'],'gates':gates},ensure_ascii=False,indent=2))
