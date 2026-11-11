#!/usr/bin/env python3
"""Bounded classic-permissive IN -> DLOAD -> OUT loop, plus controls."""
import array, hashlib, importlib.util, json, math, os, pathlib, platform, re, subprocess
P=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(os.environ['MBDB_ROOT']).resolve() if 'MBDB_ROOT' in os.environ else P.parents[2]
OLD=ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
spec=importlib.util.spec_from_file_location('compose',OLD); M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
B=M.B; S=M.SE; N=M.N; R=10000

def sha(b): return hashlib.sha256(b).hexdigest()
def memhash(mem): return sha(array.array('q',mem).tobytes())
def derive(first,second):
    # Positions satisfying (74 + position) mod 94 for two-phase pairs.
    for start in range(34,127):
        if (74+start)%94 != first: continue
        dl=next(x for x in range(start+5,start+200) if (74+x)%94==40)
        pos2=next(x for x in range(start+5,start+200) if (74+x)%94==second)
        if pos2 in range(dl-4,dl+5): continue
        last=max(dl+4,pos2+4)
        for j in range(last+1,last+95):
            jv=(4-j)%94
            if not 33<=jv<=93: continue
            n=j-start+1; k=dl-start; T=start-1
            for d0 in range(j+2,min(N,j+400)):
                v1=d0-n+k+4; W=d0-start+1
                if not (33<=v1<=126 and 33<=W<=126 and (W+41)%94 in M.HARMLESS): continue
                for v0 in range(33,127):
                    d1=v0+n-k
                    cells=[d0+k,v0+n-k-1,d1+k+4,d0-1]
                    if len(set(cells))<4 or min(cells)<=j or max(cells)>=N: continue
                    return dict(s=start,T=T,first=first,second=second,dl=dl,k=k,second_pos=pos2,j=j,jv=jv,n=n,D0=d0,D1=d1,V0=v0,V1=v1,A=cells[0],B=cells[1],C=cells[2],D=cells[3],W=W)
    raise ValueError('no construction found')

def build(p):
    s,T,j=p['s'],p['T'],p['j']; img=[33]*(max(j,p['A'],p['B'],p['C'],p['D'])+2)
    img[0]=40; img[1]=39; img[41]=p['W']
    for pos in range(2,s):
        if pos!=41: img[pos]=B.any_harmless(pos)
    img[T]=T
    paired={s,s+4,p['dl'],p['dl']+4,p['second_pos'],p['second_pos']+4}
    for pos in range(s,j): img[pos]=74 if pos in paired else M.strict_filler(pos)
    img[j]=p['jv']
    for k,v in [('A',p['V0']),('B',T),('C',p['V1']),('D',T)]: img[p[k]]=v
    return img

def check(p,img):
    s,j=p['s'],p['j']; paired={s,s+4,p['dl'],p['dl']+4,p['second_pos'],p['second_pos']+4}
    tests={'printable':all(33<=v<=126 for v in img),'pairs':all(img[x]==74 for x in paired),'pair_opcodes':[(img[x]+x)%94 for x in (s,p['dl'],p['second_pos'])]==[p['first'],40,p['second']],'jmp':(img[j]+j)%94==4,'seed':img[0]==40 and img[1]==39 and img[41]==p['W'] and p['W']+s-1==p['D0'],'tables':img[p['A']]==p['V0'] and img[p['B']]==p['T'] and img[p['C']]==p['V1'] and img[p['D']]==p['T'],'fixed_point':p['V0']+p['n']-p['k']==p['D1'] and p['V1']+p['n']-p['k']-4==p['D0'],'disjoint_data':len({p[x] for x in ('A','B','C','D')})==4 and all(p[x]>j for x in ('A','B','C','D')),'filler':all(all((v+pos)%94 in M.STRICT_HARMLESS for v in next(c for c in B.CYCLES if img[pos] in c)) for pos in range(s,j) if pos not in paired)}
    return tests

def run(img,p,data,rounds,periodic=False):
    mem=list(img)+[0]*(N-len(img))
    for i in range(len(img),N): mem[i]=S.crazy(mem[i-1],mem[i-2])
    a=c=d=ip=0; output=bytearray(); inputs=bytearray(); per=[]; ops=[]; starts=[]; dests=[]; seen={}; repeat=None; status='MAX'; history=[]
    for step in range(1,rounds*p['n']+3000):
        if c==p['s']:
            starts.append(d)
            if periodic and repeat is None:
                h=sha(array.array('q',mem).tobytes()+repr((a,c,d)).encode())
                if h in seen: repeat=[seen[h],len(starts)-1]
                else: seen[h]=len(starts)-1
        v=mem[c]
        if not 33<=v<=126: status='NONPRINT'; break
        op=(v+c)%94
        if p['s']<=c<=p['j'] and op in M.VALID: history.append(op)
        if op==4:
            target=mem[d]; dests.append(target); per.append(history); history=[]; c=target
        elif op==5: output.append(a%256)
        elif op==23:
            if ip>=len(data): status='EOF'; break
            a=data[ip]; ip+=1; inputs.append(a)
        elif op==39: mem[d]=S.rot(mem[d]); a=mem[d]
        elif op==40: d=mem[d]
        elif op==62: mem[d]=S.crazy(a,mem[d]); a=mem[d]
        elif op==81: status='HALTED'; break
        if 33<=mem[c]<=126: mem[c]=S.encrypt(mem[c])
        c=(c+1)%N; d=(d+1)%N
        if len(dests)>=rounds: status='ROUNDS'; break
    return dict(steps=step,status=status,rounds=len(dests),per=per,starts=starts,dests=dests,input=bytes(inputs),output=bytes(output),mem=mem,registers=[a,c,d],repeat=repeat)

def valid(t,p,R,data):
    return t['status']=='ROUNDS' and t['rounds']==R and all(x==p['T'] for x in t['dests']) and all(x==[23,40,5,4] for x in t['per']) and t['input']==data[:R] and t['output']==data[:R] and len(set(t['starts']))==2

def brief(t):
    return dict(status=t['status'],steps=t['steps'],rounds=t['rounds'],dests=sorted(set(t['dests'])),starts=sorted(set(t['starts'])),per_first8=t['per'][:8],per_distinct=sorted(set(map(tuple,t['per']))),input_bytes=len(t['input']),input_sha256=sha(t['input']),output_bytes=len(t['output']),output_sha256=sha(t['output']),memory_sha256=memhash(t['mem']),registers=t['registers'],repeat=t['repeat'])

def c_run(path,steps,data):
    q=subprocess.run([str(B.C_RUNNER),str(path),str(steps)],input=data,capture_output=True,timeout=120)
    m=re.search(rb'steps:\s*(\d+)\s*\|\s*status:\s*(\w+)',q.stderr)
    return dict(rc=q.returncode,raw=q.stdout,steps=int(m.group(1)) if m else None,status=m.group(2).decode() if m else None,stderr=q.stderr.decode('latin1'))

p=derive(23,5); img=build(p); path=P/'compose_inout.mb'; path.write_bytes(bytes(img)); assert img==build(derive(23,5))
M.TARGETS['IN']=23
rp=M.derive('IN'); reverse=M.build(rp)
reverse[119]=reverse[123]=74
reverse_p={'s':rp['shift'],'T':rp['T'],'first':40,'second':23,'dl':rp['shift'],'k':0,'second_pos':rp['shift']+rp['delta'],'j':rp['jmp'],'jv':rp['jmp_value'],'n':rp['n'],'D0':rp['D0'],'D1':rp['V0']+rp['n'],'V0':rp['V0'],'V1':rp['V1'],'A':rp['A'],'B':rp['B'],'C':rp['C'],'D':rp['D'],'W':rp['W']}
stream=bytes((i*73+195)%256 for i in range(R+1)); assert stream[R-1]==10
trace=run(img,p,stream,R); const=run(img,p,b'A'*(R+1),R,True); steps=trace['steps']
sc=S.run(bytes(img),max_steps=steps,stdin=stream,collect=False)
ns={}; exec(compile(B.INDEP.read_text().split('def trits')[0],str(B.INDEP),'exec'),ns)
ind=ns['run'](img,list(stream),maxs=steps,guard=True)
o=M.O.oracle_run(str(path),max_steps=steps,stdin_data=stream.decode('latin1'),stop_on_eof=True)
c=c_run(path,steps,stream)
expected=stream[:R]; oracle_out=o['output'].encode('latin1')
engine={'trace':brief(trace),'scratch':{'steps':sc['steps'],'status':sc['status'],'out_sha256':sha(sc['out']),'memory_sha256':memhash(sc['mem'])},'independent':{'steps':ind['steps'],'status':ind['status'],'out_sha256':sha(ind['out']),'memory_sha256':memhash(ind['mem'])},'oracle':{'steps':o['steps'],'status':o['status'],'out_sha256':sha(oracle_out)},'c':{'steps':c['steps'],'status':c['status'],'rc':c['rc'],'raw_bytes':len(c['raw']),'raw_sha256':sha(c['raw']),'raw_ends_hex':c['raw'][-8:].hex(),'exact_output_plus_runner_newline':c['raw']==expected+b'\n'}}
controls={}
for name in ('in_phase','out_phase','no_dload','table_off','reverse_order'):
    im=list(img); cp=p
    if name=='in_phase': im[p['s']+4]=70
    elif name=='out_phase': im[p['second_pos']+4]=70
    elif name=='no_dload':
        for pos in (p['dl'],p['dl']+4): im[pos]=M.strict_filler(pos)
    elif name=='table_off': im[p['D']]=p['T']+1
    else: im=reverse; cp=reverse_p
    (P/('ctrl_'+name+'.mb')).write_bytes(bytes(im))
    t=run(im,cp,stream,60)
    controls[name]={'params':cp if name=='reverse_order' else None,'run':brief(t),'criterion_pass':valid(t,cp,60,stream),'output_matches_first_input':t['output']==stream[:len(t['output'])]}
boundaries={}
for n in (0,1,2,257):
    data=stream[:n]; t=run(img,p,data,R)
    si=S.run(bytes(img),max_steps=t['steps'],stdin=data)
    ii=ns['run'](img,list(data),maxs=steps,guard=True)
    oo=M.O.oracle_run(str(path),max_steps=steps,stdin_data=data.decode('latin1'),stop_on_eof=True)
    cc=c_run(path,steps,data)
    boundaries[str(n)]={'trace_status':t['status'],'trace_steps':t['steps'],'trace_output_sha256':sha(t['output']),'input_echoed':t['output']==data,'scratch_at_eof_step':si['status'],'scratch_output_equals_input':si['out']==data,'independent_status':ii['status'],'independent_steps':ii['steps'],'independent_output_equals_input':ii['out']==data,'oracle_status':oo['status'],'oracle_steps':oo['steps'],'oracle_output_equals_input':oo['output'].encode('latin1')==data,'c_status':cc['status'],'c_steps':cc['steps'],'c_rc':cc['rc'],'c_raw_equals_input_plus_newline':cc['raw']==data+b'\n'}
# JMP changes c before XLAT2, so the trampoline is encrypted, not the JMP cell.
cycles=sorted(set(M._clen(img[x]) for x in list(range(p['s'],p['j']))+[p['T']]))
period=const['repeat'][1]-const['repeat'][0] if const['repeat'] else None
olm=subprocess.run([str(B.OLMSTEAD),str(path)],input=b'',capture_output=True,timeout=60)
gates={'G0':all(check(p,img).values()),'G1':valid(trace,p,R,stream) and all(x==steps for x in [sc['steps'],ind['steps'],o['steps'],c['steps']]) and sc['status']=='MAX' and ind['status']=='MAX' and o['status']=='MAX_STEPS' and c['status']=='TIMEOUT' and c['rc']==0 and sc['out']==ind['out']==oracle_out==expected and c['raw']==expected+b'\n' and memhash(trace['mem'])==memhash(sc['mem'])==memhash(ind['mem']),'G2':all(not x['criterion_pass'] for x in controls.values()) and not controls['reverse_order']['output_matches_first_input'],'G3':valid(const,p,R,b'A'*(R+1)) and period==math.lcm(*cycles) and all(const['starts'][i]==const['starts'][i+2] for i in range(len(const['starts'])-2)),'G4':all(x['trace_status']==x['independent_status']==x['oracle_status']=='EOF' and x['trace_steps']==x['independent_steps']==x['oracle_steps']==x['c_steps'] and x['c_status']=='HALTED' and x['c_rc']==0 and x['input_echoed'] and x['independent_output_equals_input'] and x['oracle_output_equals_input'] and x['c_raw_equals_input_plus_newline'] for x in boundaries.values()) and olm.returncode in (0,1)}
res={'base':'96d14c0','environment':platform.platform(),'params':p,'reverse_params':reverse_p,'image_sha256':sha(bytes(img)),'image_length':len(img),'structure':check(p,img),'input_pattern':'(73*i+195)%256','input_len':len(stream),'output_last_byte':expected[-1],'engines':engine,'constant':brief(const),'cycles':cycles,'period_predicted':math.lcm(*cycles),'controls':controls,'boundaries':boundaries,'olmstead':{'rc':olm.returncode,'stderr':olm.stderr.decode('latin1'),'valid_cells':sum((v+i)%94 in M.VALID for i,v in enumerate(img))},'gates':gates}
(P/'results.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(res,indent=2,ensure_ascii=False))
