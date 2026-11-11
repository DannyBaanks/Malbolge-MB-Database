# Auditor independiente: NO importa nada del repo. Tablas escritas desde la spec.
import sys, json, hashlib, itertools
N=59049
O=[[1,0,0],[1,0,2],[2,2,1]]          # O[d_trit][a_trit] (spec: fila = memoria, col = A)
def crz(a,dv):
    r=0;p=1
    for _ in range(10): r+=O[dv%3][a%3]*p; a//=3; dv//=3; p*=3
    return r
X2="5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
assert len(X2)==94
def rot(v): return v//3+(v%3)*19683
def run(img,inp,maxs=10000,guard=False):
    mem=list(img)+[0]*(N-len(img))
    for i in range(len(img),N): mem[i]=crz(mem[i-1],mem[i-2])
    a=c=d=0; ip=0; out=[]; outpc=[]; st='MAX'
    for s in range(1,maxs+1):
        if guard and not 33<=mem[c]<=126: st='GUARD'; return dict(out=bytes(out),steps=s,status=st,mem=mem,outpc=outpc,pc=c)
        op=(mem[c]+c)%94
        if op==4: c=mem[d]
        elif op==5: out.append(a%256); outpc.append(c)
        elif op==23:
            if ip>=len(inp): return dict(out=bytes(out),steps=s,status='EOF',mem=mem,outpc=outpc,pc=c)
            a=inp[ip]; ip+=1
        elif op==39: mem[d]=rot(mem[d]); a=mem[d]
        elif op==40: d=mem[d]
        elif op==62: mem[d]=crz(a,mem[d]); a=mem[d]
        elif op==81: return dict(out=bytes(out),steps=s,status='HALTED',mem=mem,outpc=outpc,pc=c,read=ip)
        if 33<=mem[c]<=126: mem[c]=ord(X2[mem[c]-33])
        c=(c+1)%N; d=(d+1)%N
    return dict(out=bytes(out),steps=maxs,status=st,mem=mem,outpc=outpc,pc=c)
def trits(v): return [(v//3**i)%3 for i in range(10)]
def req(b,V):
    t=trits(V); return bytes([b]+[2 if x==1 else 0 for x in t]+[2 if x!=0 else 0 for x in t])
img=open(sys.argv[1],'rb').read()
print('img sha',hashlib.sha256(img).hexdigest()[:16],'len',len(img),'printable',all(33<=x<=126 for x in img))
# loader-validity check (Olmstead loader rejects chars whose (v+i)%94 is not an op)
VAL={4,5,23,39,40,62,68,81}
print('loader-valid cells',sum(((v+i)%94) in VAL for i,v in enumerate(img)),'/',len(img))
inst=[(100,93),(100,281),(100,29797),(106,275),(106,29791),(112,269),(112,29785)]
for T,V in inst:
    for g in (False,True):
        r=run(img,req(T-1,V),guard=g); m=r['mem']
        others={t:m[t] for t in (100,106,112) if t!=T}
        print(('C-like ' if g else 'permis ')+'T=%d V=%5d status=%s steps=%d out=%s outpc=%s endpc=%s epochcell=%s others=%s'%(T,V,r['status'],r['steps'],r['out'].hex(),r['outpc'],r['pc'],m[T],others))
# controles
r=run(img,req(105,29797)); print('ctrlA',r['status'],r['out'].hex(),{t:r['mem'][t] for t in (100,106,112)})
q=bytearray(req(99,29797)); q[1]^=2; r=run(img,bytes(q)); print('ctrlB',r['status'],r['out'].hex(),r['mem'][100])
r=run(img,req(49,29797)); print('ctrlC',r['status'],r['steps'],{t:r['mem'][t] for t in (100,106,112)})
# barrido: TODOS los bytes de época 0..255 con payload 29797: ¿dónde cae algo distinto de la máscara?
hits={}
for b in range(256):
    r=run(img,req(b,29797),maxs=20000); m=r['mem']
    land=[t for t in (100,106,112) if m[t]!=29524]
    if land or r['out']: hits[b]=(land,r['status'],r['out'].hex())
print('sweep epoch byte 0..255 -> landings/outputs:',hits)
