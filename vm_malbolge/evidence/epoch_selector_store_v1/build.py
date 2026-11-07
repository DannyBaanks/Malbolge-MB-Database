#!/usr/bin/env python3
"""Build selector+exact-store experiment in a new directory; no overwrites."""
import argparse,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'vm_malbolge/evidence/epoch_selector_reusable_v1/marker_loop4.hell'
ap=argparse.ArgumentParser();ap.add_argument('output_dir',type=Path);out=ap.parse_args().output_dir;out.mkdir(parents=True,exist_ok=False)
s=BASE.read_text(encoding='utf8');extra=''
for flag in ('C_SCR','C_STORE','C_READ1','C_READ2'):extra+=f'{flag}:\n\tNop/MovD\n\tJmp\n\n'
s=s.replace('.CODE\n','.CODE\n'+extra,1)
extra='''compose_scratch_crazy:
\tU_CRAZY compose_scratch
compose_scratch:
\tC1
\tINIT_FLAG ret_init_compose_scratch R_INIT_FLAG
\tC_SCR ret_compose_scratch R_C_SCR

compose_slot_crazy:
\tU_CRAZY compose_slot
compose_slot:
\tC1
\tINIT_FLAG ret_init_compose_slot R_INIT_FLAG
\tC_STORE ret_compose_store R_C_STORE
\tC_READ1 ret_compose_read1 R_C_READ1
\tC_READ2 ret_compose_read2 R_C_READ2

'''
a='{\nnext_char_rearm:';assert s.count(a)==1;s=s.replace(a,extra+a,1)
a='\tINIT_COUNT init_save_B\n\t// IN B;';b='''\tINIT_COUNT init_save_B
init_compose_scratch:
\tR_INIT_FLAG
\tMOVED compose_scratch_crazy
}{
ret_init_compose_scratch:
\tR_CRAZY R_MOVED
\tINIT_COUNT init_compose_scratch
init_compose_slot:
\tR_INIT_FLAG
\tMOVED compose_slot_crazy
}{
ret_init_compose_slot:
\tR_CRAZY R_MOVED
\tINIT_COUNT init_compose_slot
\t// IN B;''';assert s.count(a)==1;s=s.replace(a,b)
for x in ('01','02'):
 a=f'marker_{x}_done:\n\tOUT ?- R_OUT\n\tMOVED next_char_rearm\n';b=f'marker_{x}_done:\n\tMOVED compose_entry\n';assert s.count(a)==1;s=s.replace(a,b)
a='}{\ndispatch_03:';assert s.count(a)==1
extra='''}{
compose_entry:
\tR_MOVED
\tR_C_SCR
\tMOVED compose_scratch_crazy
}{
ret_compose_scratch:
\tR_CRAZY R_MOVED
\tR_C_STORE
\tMOVED compose_slot_crazy
}{
ret_compose_store:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_C_READ1
\tMOVED compose_slot_crazy
}{
ret_compose_read1:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_C_READ2
\tMOVED compose_slot_crazy
}{
ret_compose_read2:
\tR_CRAZY R_MOVED
\tOUT ?- R_OUT
\tMOVED next_char_rearm
}{
dispatch_03:''';s=s.replace(a,extra,1)
(out/'combined.hell').write_text(s,encoding='utf8')
# Keep the real failed full assembly output; retry may vary between LMAO builds.
r=subprocess.run([str(ROOT/'third_party/lmao/lmao'),'-d','-o',str(out/'unpruned.mb'),str(out/'combined.hell')],capture_output=True);(out/'unpruned.stdout').write_bytes(r.stdout);(out/'unpruned.stderr').write_bytes(r.stderr);print('unpruned_lmao_exit',r.returncode)
s=s.replace('NO_MORE_CARRY_FLAG disc_3\n\tMOVED dispatch_02','NO_MORE_CARRY_FLAG unsupported\n\tMOVED dispatch_02',1)
a='}{\ndisc_3:';b='}{\ndispatch_00:';i=s.index(a);j=s.index(b,i);s=s[:i]+'}{\nunsupported:\n\tHALT\n'+s[j:]
a='}{\ndispatch_03:';b='}{\nreturn_from_increment_value_2:';i=s.index(a);j=s.index(b,i);s=s[:i]+s[j:]
for n in range(5,20):
 s,k=re.subn(rf'SUBROUTINE_FLAG{n}:\n\tNop/MovD\n\tJmp\n\n','',s);assert k==1,(n,k)
 s,k=re.subn(rf'\tSUBROUTINE_FLAG{n} return_from_decrement_value_{n}(?: R_SUBROUTINE_FLAG{n})?\n','',s);assert k==1,(n,k)
for n in (11,12):s=s.replace(f'\tFLAG{n} return_from_save_B_{n} R_FLAG{n}\n','')
a='ret_compose_store:\n\tR_CRAZY R_MOVED\n\tROT C2 R_ROT';b='ret_compose_store:\n\tR_CRAZY R_MOVED\n\tROT C1 R_ROT';assert s.count(a)==1;mut_read=s.replace(a,b,1)
a='\tMARK5 marker_01_five\n';b='\tMOVED marker_01_done\n';assert s.count(a)==1;mut_rearm=s.replace(a,b,1)
for name,body in [('combined_pruned',s),('mutant_read',mut_read),('mutant_rearm',mut_rearm)]:
 path=out/(name+'.hell');path.write_text(body,encoding='utf8');subprocess.run([str(ROOT/'third_party/lmao/lmao'),'-d','-o',str(out/(name+'.mb')),str(path)],check=True)
