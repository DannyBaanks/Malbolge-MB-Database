#!/usr/bin/env python3
"""Rebuild three attempted selectors in a new directory, never overwrite evidence."""
import argparse, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('output_dir',type=Path);args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
base=(ROOT/'vm_malbolge/src/byte_dispatch18.hell').read_text(encoding='utf8')
a='\tOUT ?- R_OUT\n\tHALT\n';b='\tOUT ?- R_OUT\n\tR_MOVED\n\tMOVED ENTRY\n';assert base.count(a)==18
loop=base.replace(a,b);s=loop.replace('.CODE\n','.CODE\nINIT_FLAG:\n\tNop/MovD\n\tJmp\n\nINIT_COUNT:\n\tMovD/Nop\n\tJmp\n\n',1)
for name in ('value','value_C1','save_tmp','save_B'):
 anchor=name+':\n\tC1\n';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\tINIT_FLAG ret_init_'+name+' R_INIT_FLAG\n',1)
anchor='ENTRY:\n\t// IN B;';assert s.count(anchor)==1
block='ENTRY:\n\tROT C1 R_ROT\n'
for name in ('value','value_C1','save_tmp','save_B'):
 block+=f'init_{name}:\n\tR_INIT_FLAG\n\tMOVED crazy_{name}\n}}{{\nret_init_{name}:\n\tR_CRAZY R_MOVED\n\tINIT_COUNT init_{name}\n'
s=s.replace(anchor,block+'\t// IN B;',1);s2=s.replace('ENTRY:\n\tROT C1 R_ROT','next_char_rearm:\n\tR_MOVED\nENTRY:\n\tROT C1 R_ROT',1);assert s2.count(b)==18;s2=s2.replace(b,'\tOUT ?- R_OUT\n\tMOVED next_char_rearm\n')
for name,src in [('loop',loop),('rearmed',s),('rearmed2',s2)]:
 hell=args.output_dir/(name+'.hell');hell.write_text(src,encoding='utf8');subprocess.run([str(ROOT/'third_party/lmao/lmao'),'-d','-o',str(args.output_dir/(name+'.mb')),str(hell)],check=True)
