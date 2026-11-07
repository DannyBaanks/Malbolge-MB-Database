#!/usr/bin/env python3
"""Bounded observation of output availability before input EOF."""
import os,select,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
p=subprocess.Popen(['stdbuf','-o0',str(ROOT/'runners/malbolge-original/malbolge'),str(ROOT/'vm_malbolge/evidence/epoch_reusable_store_v1/positive.mb'),'4000000'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
before=[]
for v in (104,33):
 p.stdin.write(bytes([v]));p.stdin.flush();ready=bool(select.select([p.stdout],[],[],1)[0]);before.append(os.read(p.stdout.fileno(),1).hex() if ready else 'NO_OUTPUT_1S')
p.stdin.close();after=p.stdout.read();err=p.stderr.read();rc=p.wait();print('before_eof',before);print('after_eof',after.hex());print('runner',err.decode().strip(),'returncode',rc)
sys.exit(0 if before==['NO_OUTPUT_1S']*2 and after==b'\x68\x21\n' and rc==0 else 1)
