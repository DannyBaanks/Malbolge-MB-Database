#!/usr/bin/env python3
"""Lower a ternary byte-increment circuit to looping HeLL, no binary template."""
from __future__ import annotations
import pathlib
import json
import sys
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from circuit import LOW,HIGH, crazy, rot, ONE

flags=[];variables={};body=[];serial=0;reg=0; a_slot=None

def emit(s): body.append(s)
def call(var,mode):
    global serial
    serial+=1; f=f'F{len(variables.get(var,[]))+1}';r=f'RET{serial}';
    if f not in flags:flags.append(f)
    variables.setdefault(var,[]).append((f,r))
    emit(f' R_{f}\n MOVED {var}_{mode}\n}}\n{{\n{r}:\n R_{"CRAZY" if mode=="crazy" else "ROT"} R_MOVED')
def constant(x):
    global a_slot
    a_slot=None
    emit(' ROT '+{0:'C0',1:'C1',2:'C2'}[x]+' R_ROT')
def clear(v):
    global serial,a_slot
    serial+=1; loop=f'CLEAR{serial}'
    constant(1);emit(loop+':');call(v,'crazy');emit(' COUNTER2 '+loop);a_slot=v
def load(v):
    global serial,a_slot
    if isinstance(v,str) and a_slot==v:return
    if isinstance(v,int):constant(v);return
    serial+=1; loop=f'LOAD{serial}'
    emit(loop+':');constant(2);call(v,'crazy');emit(' COUNTER2 '+loop);a_slot=v
def copy(src,dst):
    global a_slot
    if isinstance(src,int):
        clear(dst);constant({0:1,1:0,2:2}[src]);call(dst,'crazy');a_slot=dst;return
    clear('aux');clear(dst);load(src);call('aux','crazy');call(dst,'crazy');a_slot=dst
# Build SSA first; overwriting dead operands avoids most data copies.
ir=[]
def gate(a,b):
    global reg
    reg+=1; dst=f'g{reg}';ir.append(('gate',dst,a,b));return dst
def lrot(x,n):
    global reg
    reg+=1; dst=f'g{reg}';ir.append(('rotate',dst,x,(10-n)%10));return dst
def bor(x,y):
    g1=gate(2,y);g2=gate(x,g1);return gate(g2,g1)
def band(x,y):
    g1=gate(2,x);g2=gate(y,y);g3=gate(g1,g2);return gate(g3,y)
def eq2(x):
    g=gate(0,x);return gate(g,g)
def add(x,y):
    g1=gate(2,y);g2=gate(x,0);g3=gate(g2,g1);g4=gate(g3,x);return gate(g4,1)
def eq2or(x,m):
    g=gate(m,x);return gate(g,x)
def andor(x,y,m):
    g1=gate(2,x);g2=gate(g1,y);g3=gate(m,g2);return gate(g3,g3)
p=eq2or('input','highmask')
for k in (1,2,4):p=andor(p,lrot(p,k),'highmask')
eof_first=gate(p,'eofmask1');eof_word=gate(eof_first,'eofmask2')
ir.append(('branch',None,eof_word,None))
carry=band(lrot(p,1),'lowmask');answer=add('input',carry)
# Evaluate the finite declared input domain to justify encoded-copy rewrites.
vals={'input':list(range(256))+[59048], 'highmask':[HIGH]*257, 'lowmask':[LOW]*257, 'eofmask1':[58680]*257, 'eofmask2':[29528]*257}
def words(v):return [v*ONE]*257 if isinstance(v,int) else vals[v]
def boolean_words(ws):return all(all((x//(3**i))%3 != 2 for i in range(10)) for x in ws)
boolean_operands={}
for ix,(kind,dst,a,b) in enumerate(ir):
    if kind=='branch':continue
    boolean_operands[ix]=boolean_words(words(a))
    if kind=='gate':vals[dst]=[crazy(x,y) for x,y in zip(words(a),words(b))]
    else:
        out=[]
        for x in words(a):
            for _ in range(b):x=rot(x)
            out.append(x)
        vals[dst]=out
from collections import Counter
uses=Counter()
for kind,dst,a,b in ir:
    if isinstance(a,str):uses[a]+=1
    if kind=='gate' and isinstance(b,str):uses[b]+=1
uses[answer]+=1
physical={'input':'input','lowmask':'lowmask','highmask':'highmask','eofmask1':'eofmask1','eofmask2':'eofmask2'}
free=[]; nextslot=0
def allocate():
    global nextslot
    if free:return free.pop()
    nextslot+=1;return f't{nextslot}'
def consume(x):
    if isinstance(x,str):uses[x]-=1
def release(x,keep):
    if isinstance(x,str) and uses[x]==0 and x not in ('lowmask','highmask'):
        slot=physical[x]
        if slot!=keep and slot not in free:free.append(slot)

emit('next_char:\n R_MOVED\nENTRY:')
clear('aux');clear('input')
for mv,cv in [('eofmask1','ctrlmask1'),('eofmask2','ctrlmask2')]:
    clear(mv);load(cv);call(mv,'crazy')
emit(' IN ?- R_IN');call('aux','crazy');call('input','crazy');a_slot='input'
meta=[]
for ix,(kind,dst,a,b) in enumerate(ir):
    emit(f'TRACE{ix}:')
    pa=physical[a] if isinstance(a,str) else a
    if kind=='branch':
        consume(a);eof_slot=pa
        emit(f' MOVED {eof_slot}\n}}\n{{\nEOF_CONTINUE:\n R_MOVED')
        release(a,None)
        continue
    if kind=='gate':
        pb=physical[b] if isinstance(b,str) else b
        consume(a);consume(b)
        reuse=isinstance(b,str) and uses[b]==0 and b not in ('lowmask','highmask')
        slot=pb if reuse else allocate()
        if not reuse:
            if isinstance(pb,str) and boolean_operands[ix]:
                # f1(b) is a valid encoded copy when the CRAZY accumulator
                # has only 0/1 trits: T[f1(b)][a] == T[b][a].
                clear(slot);load(pb);call(slot,'crazy');a_slot=slot
            else:copy(pb,slot)
        load(pa);call(slot,'crazy');a_slot=slot
        release(a,slot);release(b,slot)
    else:
        consume(a)
        reuse=isinstance(a,str) and uses[a]==0 and a not in ('lowmask','highmask')
        slot=pa if reuse else allocate()
        if not reuse:copy(pa,slot)
        # Counter cycles are restored upon their full period.
        if b in (5,6,9):
            serial+=1;loop=f'RLOOP{serial}';end=f'REND{serial}';emit(f' R_MOVED\n{loop}:\n R_MOVED');call(slot,'rot');emit(f' COUNTER{b} {end}\n MOVED {loop}\n}}\n{{\n{end}:')
        elif b==8:
            serial+=1;loop=f'RLOOP{serial}';end=f'RHALF{serial}';prep=f'RPREP{serial}'
            emit(f'{prep}:\n R_MOVED\n{loop}:\n R_MOVED');call(slot,'rot');emit(f' COUNTER4 {end}\n MOVED {loop}\n}}\n{{\n{end}:\n COUNTER2 {prep}')
        else:
            for _ in range(b):call(slot,'rot')
        a_slot=slot
        release(a,slot)
    physical[dst]=slot
    meta.append({'index':ix,'kind':kind,'dst':dst,'a':a,'b':b,'slot':slot})
emit(f'TRACE{len(ir)}:')
load(physical[answer]);emit(' OUT ?- R_OUT\n MOVED next_char')

head='''.CODE
MOVED: MovD/Nop\n Jmp\n\nCRAZY: Opr/Nop\n Jmp\n\nROT: Rot/Nop\n Jmp\n\nIN: In/Nop\n Jmp\n\nOUT: Out/Nop\n Jmp\n\nNOP: Jmp\n\nHALT: Hlt\n\n@58329\nNON_EOF_0: RNop\n RNop\n Jmp\n\n@58338\nNON_EOF_1: RNop\n RNop\n Jmp\n\n@58365\nNON_EOF_2: RNop\n RNop\n Jmp\n\n@58446\nNON_EOF_3: RNop\n RNop\n Jmp\n\n@58689\nEOF_CODE: RNop\n Jmp\n\nCOUNTER2: MovD/Nop\n Jmp\n\nCOUNTER4: Nop/Nop/Nop/MovD\n Jmp\n\nCOUNTER5: Nop/Nop/Nop/Nop/MovD\n Jmp\n\nCOUNTER6: Nop/Nop/Nop/Nop/Nop/MovD\n Jmp\n\nCOUNTER9: Nop/Nop/Nop/Nop/Nop/Nop/Nop/Nop/MovD\n Jmp\n\n'''
head+='\n'.join(f'{f}: Nop/MovD\n Jmp\n' for f in flags)
data='\n.DATA\n'
for var,calls in variables.items():
    data+='\n{\n'+f'{var}_crazy: U_CRAZY {var}\n'
    if any(var+'_rot' in line for line in body):data+=f'{var}_rot: U_ROT {var}\n'
    value=LOW if var=='lowmask' else HIGH if var=='highmask' else 58324 if var=='ctrlmask1' else 8 if var=='ctrlmask2' else 'C1'
    data+=f'{var}: {value}\n'
    if var==eof_slot:data+=' U_NOP EOF_SKIP\n U_NOP EOF_STOP\n U_NOP EOF_NOT\nEOF_STOP: HALT\nEOF_NOT: R_MOVED\n MOVED EOF_CONTINUE\nEOF_SKIP:\n'
    for f,r in calls:data+=f' {f} {r} R_{f}\n'
    data+='}\n'
source=head+data+'\n{\n'+'\n'.join(body)+'\n}\n'
if len(sys.argv)!=2:raise SystemExit('usage: build_hell.py <new-output.hell>')
out=pathlib.Path(sys.argv[1]);out.write_text(source,encoding='utf-8',errors='strict') if not out.exists() else (_ for _ in ()).throw(FileExistsError(out))
print(f'flags={len(flags)} registers={reg} variables={len(variables)} source_bytes={len(source)}')
