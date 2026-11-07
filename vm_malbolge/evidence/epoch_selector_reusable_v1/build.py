#!/usr/bin/env python3
"""Rebuild the bounded 01/02 selector and negative mutant in a new dir."""
import argparse,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; BASE=ROOT/'vm_malbolge/evidence/epoch_selector_rearm_v0/rearmed2.hell'
ap=argparse.ArgumentParser();ap.add_argument('output_dir',type=Path);out=ap.parse_args().output_dir;out.mkdir(parents=True,exist_ok=False)
s=BASE.read_text(encoding='utf8');old='\tOUT ?- R_OUT\n\tMOVED next_char_rearm\n';new='\tOUT ?- R_OUT\n\tR_MOVED\n\tMOVED next_char_rearm\n';assert s.count(old)==18;s=s.replace(old,new)
s=s.replace('.CODE\n','.CODE\nMARK_FLAG:\n\tNop/MovD\n\tJmp\n\nMARK5:\n\tNop/Nop/Nop/Nop/MovD\n\tJmp\n\nMARK2:\n\tNop/MovD\n\tJmp\n\n',1)
anchor='{\nnext_char_rearm:';assert s.count(anchor)==1
extra=''
for x,ch in [('01','P'),('02','R')]:extra+=f"marker_{x}_rot:\n\tU_ROT marker_{x}\nmarker_{x}:\n\t'{ch}'\n\tMARK_FLAG marker_{x}_return R_MARK_FLAG\n\n"
s=s.replace(anchor,extra+anchor,1)
for x,ch in [('01','P'),('02','R')]:
 old=f"dispatch_{x}:\n\tROT ('{ch}' << 1) R_ROT\n\tOUT ?- R_OUT\n\tR_MOVED\n\tMOVED next_char_rearm\n"
 new=f'''dispatch_{x}:
marker_{x}_loop:
\tR_MOVED
\tR_MARK_FLAG
\tMOVED marker_{x}_rot
}}{{
marker_{x}_return:
\tR_ROT R_MOVED
\tMARK5 marker_{x}_five
\tMOVED marker_{x}_loop
}}{{
marker_{x}_five:
\tMARK2 marker_{x}_done
\tMOVED marker_{x}_loop
}}{{
marker_{x}_done:
\tOUT ?- R_OUT
\tMOVED next_char_rearm
'''
 assert s.count(old)==1;s=s.replace(old,new)
mut=s.replace('\tMARK5 marker_01_five\n','\tMOVED marker_01_done\n',1);assert mut!=s
for name,body in [('marker_loop4',s),('marker_mutant',mut)]:
 hell=out/(name+'.hell');hell.write_text(body,encoding='utf8');subprocess.run([str(ROOT/'third_party/lmao/lmao'),'-d','-o',str(out/(name+'.mb')),str(hell)],check=True)
