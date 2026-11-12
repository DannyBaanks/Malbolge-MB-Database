#!/usr/bin/env python3
"""Hex wrapper for a bounded REA process capture of each reference."""
import importlib.util
import pathlib
import subprocess
import sys
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
data=bytes.fromhex(sys.argv[2]);mode=sys.argv[1]
if mode=='python':
    r=subprocess.run([sys.executable,str(P/'reference.py')],input=data,capture_output=True,check=True)
    out=r.stdout;status='HALTED'
elif mode=='brainfuck':
    s=importlib.util.spec_from_file_location('bf',ROOT/'vm_malbolge/evidence/unieco_rea_eof_v2/bf16.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    out,status,_,_=m.run((P/'increment.bf').read_text(),data)
else:raise ValueError('unknown mode')
print('input='+data.hex()+' output='+out.hex()+' status='+status)
