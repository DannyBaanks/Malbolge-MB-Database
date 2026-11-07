#!/usr/bin/env python3
"""Rebuild the journal adaptation and mutants in a new directory."""
import argparse,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'vm_malbolge/evidence/epoch_selector_store_v1/combined_pruned.hell'
ap=argparse.ArgumentParser();ap.add_argument('output_dir',type=Path);out=ap.parse_args().output_dir;out.mkdir(parents=True,exist_ok=False)
s=BASE.read_text(encoding='utf8');s=s.replace('.CODE\n','.CODE\nEPOCH_PHASE:\n\tNop/MovD\n\tJmp\n\n',1)
a='''ret_compose_read2:
\tR_CRAZY R_MOVED
\tOUT ?- R_OUT
\tMOVED next_char_rearm
''';b='''ret_compose_read2:
\tR_CRAZY R_MOVED
\tEPOCH_PHASE epoch_even
\tMOVED epoch_odd
}{
epoch_even:
\tOUT ?- R_OUT
\tMOVED next_char_rearm
}{
epoch_odd:
\tR_MOVED
\tOUT ?- R_OUT
\tMOVED next_char_rearm
''';assert s.count(a)==1;s=s.replace(a,b,1)
flags=''
for x in ('J_SAVE','J_RESET1','J_RESET2','J_ROT','J_RESTORE'):flags+=f'{x}:\n\tNop/MovD\n\tJmp\n\n'
s=s.replace('.CODE\n','.CODE\n'+flags,1)
a='\tC_READ2 ret_compose_read2 R_C_READ2\n';assert s.count(a)==1;s=s.replace(a,a+'\tJ_RESET1 ret_j_reset1 R_J_RESET1\n\tJ_RESET2 ret_j_reset2 R_J_RESET2\n\tJ_RESTORE ret_j_restore R_J_RESTORE\n',1)
a='{\nnext_char_rearm:';assert s.count(a)==1
j='''epoch_journal_rot:
\tU_ROT epoch_journal
epoch_journal_crazy:
\tU_CRAZY epoch_journal
epoch_journal:
\tC1
\tINIT_FLAG ret_init_epoch_journal R_INIT_FLAG
\tJ_SAVE ret_j_save R_J_SAVE
\tJ_ROT ret_j_rot R_J_ROT

''';s=s.replace(a,j+a,1)
a='\tINIT_COUNT init_compose_slot\n\t// IN B;';b='''\tINIT_COUNT init_compose_slot
init_epoch_journal:
\tR_INIT_FLAG
\tMOVED epoch_journal_crazy
}{
ret_init_epoch_journal:
\tR_CRAZY R_MOVED
\tINIT_COUNT init_epoch_journal
\t// IN B;''';assert s.count(a)==1;s=s.replace(a,b,1)
a='''ret_compose_store:
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
\tEPOCH_PHASE epoch_even
''';b='''ret_compose_store:
\tR_CRAZY R_MOVED
\tR_J_SAVE
\tMOVED epoch_journal_crazy
}{
ret_j_save:
\tR_CRAZY R_MOVED
\tROT C1 R_ROT
\tR_J_RESET1
\tMOVED compose_slot_crazy
}{
ret_j_reset1:
\tR_CRAZY R_MOVED
\tR_J_RESET2
\tMOVED compose_slot_crazy
}{
ret_j_reset2:
\tR_CRAZY R_MOVED
\tMOVED epoch_journal_loop
}{
epoch_journal_loop:
\tR_MOVED
\tR_J_ROT
\tMOVED epoch_journal_rot
}{
ret_j_rot:
\tR_ROT R_MOVED
\tMARK5 epoch_j_five
\tMOVED epoch_journal_loop
}{
epoch_j_five:
\tMARK2 epoch_j_done
\tMOVED epoch_journal_loop
}{
epoch_j_done:
\tR_J_RESTORE
\tMOVED compose_slot_crazy
}{
ret_j_restore:
\tR_CRAZY R_MOVED
\tEPOCH_PHASE epoch_even
''';assert s.count(a)==1;s=s.replace(a,b,1)
for n in ('C_READ1','C_READ2'):s=s.replace(f'{n}:\n\tNop/MovD\n\tJmp\n\n','',1)
for n,k in [('C_READ1','ret_compose_read1'),('C_READ2','ret_compose_read2')]:s=s.replace(f'\t{n} {k} R_{n}\n','',1)
a='''epoch_j_done:
\tR_J_RESTORE
\tMOVED compose_slot_crazy
}{
ret_j_restore:
\tR_CRAZY R_MOVED
\tEPOCH_PHASE epoch_even
\tMOVED epoch_odd
}{
epoch_even:
\tOUT ?- R_OUT
\tMOVED next_char_rearm
}{
epoch_odd:
\tR_MOVED
\tOUT ?- R_OUT
\tMOVED next_char_rearm
''';b='''epoch_j_done:
\tEPOCH_PHASE epoch_even
\tMOVED epoch_odd
}{
epoch_even:
\tR_J_RESTORE
\tMOVED compose_slot_crazy
}{
epoch_odd:
\tR_MOVED
\tR_J_RESTORE
\tMOVED compose_slot_crazy
}{
ret_j_restore:
\tR_CRAZY R_MOVED
\tOUT ?- R_OUT
\tMOVED next_char_rearm
''';assert s.count(a)==1;s=s.replace(a,b,1)
a='ret_compose_store:\n\tR_CRAZY R_MOVED\n\tR_J_SAVE\n';b='ret_compose_store:\n\tR_CRAZY R_MOVED\n\tROT C0 R_ROT\n\tR_J_SAVE\n';assert s.count(a)==1;mut_j=s.replace(a,b,1)
a='epoch_j_done:\n\tEPOCH_PHASE epoch_even';b='epoch_j_done:\n\tROT C0 R_ROT\n\tEPOCH_PHASE epoch_even';assert s.count(a)==1;mut_r=s.replace(a,b,1)
a='\tEPOCH_PHASE epoch_even\n\tMOVED epoch_odd\n}{\nepoch_even:\n\tR_J_RESTORE';b='\tMOVED epoch_even\n\tMOVED epoch_odd\n}{\nepoch_even:\n\tR_MOVED\n\tR_J_RESTORE';assert s.count(a)==1;mut_p=s.replace(a,b,1)
for name,body in [('journal',s),('mutant_journal',mut_j),('mutant_restore',mut_r),('mutant_phase',mut_p)]:
 p=out/(name+'.hell');p.write_text(body,encoding='utf8');subprocess.run([str(ROOT/'third_party/lmao/lmao'),'-d','-o',str(out/(name+'.mb')),str(p)],check=True)
