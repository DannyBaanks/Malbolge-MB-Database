#!/usr/bin/env python3
"""Exhaust the byte and EOF domains for the branch and arithmetic circuit."""
import json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;root=P.parents[2];sys.path.insert(0,str(root/'vm_malbolge/tools/increment_bf'))
from circuit import HIGH,LOW,ONE,TWO,crazy,left,eq2_or,and_or,increment
rows=[]
for x in list(range(256))+[TWO]:
    p=eq2_or(x,HIGH)
    for shift in (1,2,4):p=and_or(p,left(p,shift),HIGH)
    branch=crazy(crazy(p,58680),29528)
    expected=58688 if x==TWO else None
    if x!=TWO:assert branch in (58328,58337,58364,58445) and increment(x)==x+1
    else:assert branch==expected
    rows.append({'input':x,'branch':branch,'output_word':None if x==TWO else increment(x)})
wrong=sum(1 for x in range(256) if crazy(crazy(eq2_or(x,HIGH),58680),29528)==58688)
print(json.dumps({'orientation':'crazy(accumulator,cell)=table[cell][accumulator]','cases':len(rows),'distinct_byte_branch_values':sorted({r['branch'] for r in rows[:-1]}),'eof_branch':rows[-1]['branch'],'early_branch_control_false_positives':wrong,'rows':rows},indent=2))
