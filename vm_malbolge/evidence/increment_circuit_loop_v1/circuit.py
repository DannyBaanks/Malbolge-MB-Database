#!/usr/bin/env python3
"""Straight-line ternary circuit for byte increment; host oracle only."""
from __future__ import annotations
import hashlib
import json
import pathlib
import sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT.parent/'BolgeForge'))
from constants import crazy_op as crazy, rot_op as rot  # noqa: E402
ONE=29524; TWO=59048
LOW=sum(3**i for i in range(6)); HIGH=ONE-LOW

def left(x,n):
    for _ in range((10-n)%10): x=rot(x)
    return x

def bool_or(x,y):
    g1=crazy(TWO,y); g2=crazy(x,g1); return crazy(g2,g1)

def bool_and(x,y):
    g1=crazy(TWO,x); g2=crazy(y,y); g3=crazy(g1,g2); return crazy(g3,y)

def eq2(x):
    g=crazy(0,x); return crazy(g,g)

def add_bit(x,y):
    g1=crazy(TWO,y); g2=crazy(x,0); g3=crazy(g2,g1); g4=crazy(g3,x); return crazy(g4,ONE)

def eq2_or(x,mask):
    g=crazy(mask,x); return crazy(g,x)

def and_or(x,y,mask):
    g1=crazy(TWO,x); g2=crazy(g1,y); g3=crazy(mask,g2); return crazy(g3,g3)

def increment(x,mutate=False):
    p=eq2_or(x,HIGH)
    for k in (1,2,4):
        p=and_or(p,left(p,k),HIGH)
    carry=bool_and(left(p,1),LOW)
    if mutate: carry=bool_and(left(p,1),HIGH)
    return add_bit(x,carry)

def main():
    rows=[{'input':i,'word':increment(i),'expected_word':i+1,'output_byte':increment(i)%256,'control_byte':increment(i,True)%256} for i in range(256)]
    assert all(r['word']==r['expected_word'] for r in rows)
    assert any(r['control_byte']!=r['output_byte'] for r in rows)
    print(json.dumps({'scope':'host arithmetic only; no native circuit or EOF established','orientation':'crazy(accumulator,cell)=table[cell][accumulator]','low_mask':LOW,'high_mask':HIGH,'rows':rows,'control_mismatches':sum(r['control_byte']!=r['output_byte'] for r in rows),'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()},indent=2))
if __name__=='__main__': main()
