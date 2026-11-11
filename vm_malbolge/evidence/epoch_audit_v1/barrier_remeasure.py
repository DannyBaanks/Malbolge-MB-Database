import sys,itertools
N=59049; O=[[1,0,0],[1,0,2],[2,2,1]]
def crz(a,dv):
    r=0;p=1
    for _ in range(10): r+=O[dv%3][a%3]*p; a//=3; dv//=3; p*=3
    return r
X2="5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
ENC={33+i:ord(ch) for i,ch in enumerate(X2)}
VAL={4,5,23,39,40,62,68,81}
def rot(v): return v//3+(v%3)*19683
def orb(v):
    s=set();x=v
    for _ in range(10): s.add(x); x=rot(x)
    return s
def tr(v): return [(v//3**i)%3 for i in range(10)]
PR=range(33,127)
PORB=set().union(*[orb(p) for p in PR])           # palabras cargables con ROT desde una celda sembrada
print('palabras en órbitas imprimibles:',len(PORB))
def ctrls(v,w):  # TODAS las a con crz(a,w)==v
    opts=[]
    for vd,wd in zip(tr(v),tr(w)):
        c=[a for a in range(3) if O[wd][a]==vd]
        if not c: return []
        opts.append(c)
    return [sum(x*3**i for i,x in enumerate(t)) for t in itertools.product(*opts)]
# M2/M3 con el conjunto completo de controles
pairs=rest=0; mat_first=0; mat_any=0; cells_any=set(); words=set(); multi=0
for c in range(300):
    for v in PR:
        if (v+c)%94 not in VAL: continue
        pairs+=1; cs=ctrls(v,ENC[v])
        if not cs: continue
        rest+=1; multi+= len(cs)>1
        if cs[0] in PORB: mat_first+=1
        hit=[x for x in cs if x in PORB]
        if hit: mat_any+=1; cells_any.add(c); words.update(hit)
print('M2 pares',pairs,'restaurables',rest,'con >1 control',multi)
print('M3 materializable (solo primer control, como el probe):',mat_first)
print('M3 materializable (cualquier control):',mat_any,'en',len(cells_any),'celdas; palabras distintas',len(words))
# M3 ampliado: control alcanzable con ROT + un CRAZY sobre otra palabra sembrada-orbital
S2=set(PORB)
L=sorted(PORB)
for x in L:
    for y in L: S2.add(crz(x,y))
print('palabras alcanzables con ROT+1 CRAZY (desde órbitas imprimibles):',len(S2))
m2=sum(1 for c in range(300) for v in PR if (v+c)%94 in VAL and any(x in S2 for x in ctrls(v,ENC[v])))
print('M3 con un CRAZY extra de preparación:',m2,'/',pairs)
# M4: condición del probe vs condición amplia
p4=n_own=n_any=n_s2=0; cells_own=set(); cells_any4=set()
for c in range(400):
    for v in PR:
        if (v+c)%94 not in VAL: continue
        p4+=1; s=0
        sw=sum((1 if t==0 else 0 if t==1 else 2)*3**i for i,t in enumerate(tr(v)))
        assert crz(sw,29524)==v
        if sw in orb(v): n_own+=1; cells_own.add(c)
        if sw in PORB: n_any+=1; cells_any4.add(c)
        if sw in S2: n_s2+=1
print('M4 pares',p4,'| swap01(v) en órbita de v (probe):',n_own,len(cells_own),'celdas | en cualquier órbita imprimible:',n_any,len(cells_any4),'celdas | con ROT+1 CRAZY:',n_s2)
# M7: celda de relleno del cargador como operando del JMP de retorno
img=open(sys.argv[1],'rb').read(); mem=list(img)+[0]*(N-len(img))
for i in range(len(img),N): mem[i]=crz(mem[i-1],mem[i-2])
fill_dest={mem[i]+1 for i in range(len(img),N) if 128<=mem[i]+1<len(img)}
print('M7 destinos 128..%d alcanzables leyendo una celda de RELLENO (sin escribir nada):'%(len(img)-1),len(fill_dest),sorted(fill_dest)[:15])
print('   valores distintos en el relleno:',len(set(mem[len(img):])))
# semigrupo: modelo del pack (1 operando: a -> crazy(a, k) con k trit fijo de memoria), ambas orientaciones (T24)
def one(T):
    gens=[tuple(T(a,b) for a in range(3)) for b in range(3)]
    seen={(0,1,2)}; fr=[(0,1,2)]
    while fr:
        nx=[]
        for f in fr:
            for g in gens:
                h=tuple(f[g[x]] for x in range(3))
                if h not in seen: seen.add(h); nx.append(h)
        fr=nx
    return seen
A1=one(lambda a,d:O[d][a]); B1=one(lambda a,d:O[a][d])
print('semigrupo 1 operando: orientación correcta',len(A1),'| invertida',len(B1),'| (0,2,0) en correcta:',(0,2,0) in A1,'(0,2,2):',(0,2,2) in A1,'(0,0,2):',(0,0,2) in A1)
# modelo de 2 operandos: f(x) en a, g(x) en memoria -> crazy punto a punto; base identidad + palabras constantes 0/1/2
base={(0,1,2):'x',(0,0,0):'0',(1,1,1):'1',(2,2,2):'2'}
cl=dict(base)
while True:
    nw=dict(cl)
    for (f,nf),(g,ng) in itertools.product(list(cl.items()),repeat=2):
        h=tuple(O[g[i]][f[i]] for i in range(3))
        if h not in nw: nw[h]='crazy(a=%s, mem=%s)'%(nf,ng)
    if len(nw)==len(cl): break
    cl=nw
print('cierre 2 operandos con constantes:',len(cl))
for w in [(0,2,0),(0,2,2),(0,0,2)]: print('  ',w,'=',cl.get(w))
print('constante 59048 (todo 2) alcanzable con ROT+1 CRAZY:',59048 in S2,'| 29524 (todo 1):',29524 in S2)
# épocas candidatas, misma regla que el pack (v = v0 o v0+94, 33<=v<=125)
cand=[T for T in range(34,127) if any(33<=v<=125 for v in ((80-T)%94,(80-T)%94+94))]
print('épocas candidatas (regla del pack):',len(cand))
