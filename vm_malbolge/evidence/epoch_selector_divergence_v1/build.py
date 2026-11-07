#!/usr/bin/env python3
"""Regenerate attempted fixes and C traces in a NEW directory."""
import argparse,gzip,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'vm_malbolge/evidence/epoch_selector_rearm_v0/rearmed2.hell';ENGINE=ROOT.parent/'Malbolge-Engine/src';PURE=ROOT.parent/'Malbolge-PureEpoch'
a=argparse.ArgumentParser();a.add_argument('output_dir',type=Path);p=a.parse_args();p.output_dir.mkdir(parents=True,exist_ok=False);out=p.output_dir
s=BASE.read_text(encoding='utf8');anchor='\tOUT ?- R_OUT\n\tMOVED next_char_rearm\n';assert s.count(anchor)==18
fix1=s.replace(anchor,'\tOUT ?- R_OUT\n\tR_NO_MORE_CARRY_FLAG\n\tMOVED next_char_rearm\n');fix2=s
for x in ('01','02'):
 old=f'dispatch_{x}:\n\tROT ';new=f'dispatch_{x}:\n\tNO_MORE_CARRY_FLAG cleaned_{x} R_NO_MORE_CARRY_FLAG\ncleaned_{x}:\n\tROT ';assert fix2.count(old)==1;fix2=fix2.replace(old,new)
for name,body in [('reset_carry',fix1),('conditional_flag',fix2)]:
 (out/(name+'.hell')).write_text(body,encoding='utf8');subprocess.run([str(ROOT/'third_party/lmao/lmao'),'-d','-o',str(out/(name+'.mb')),str(out/(name+'.hell'))],check=True)
vm=(ENGINE/'vm.c').read_text();vm=vm.replace('#include <string.h>','#include <string.h>\n#include <stdio.h>');anchor='        uint32_t ins = mem_get(c);';assert vm.count(anchor)==1
vm=vm.replace(anchor,anchor+'\n        fprintf(stderr, "TRACE %llu %u %u %u %u %zu\\n", (unsigned long long)executed,a,c,d,ins,input_pos);',1)
(out/'vm_instrumented.c').write_text(vm);(out/'vm.h').write_bytes((ENGINE/'vm.h').read_bytes());(out/'malbolge.c').write_bytes((ENGINE/'malbolge.c').read_bytes())
subprocess.run(['gcc','-O2','-o',str(out/'runner_trace'),str(out/'vm_instrumented.c'),str(out/'malbolge.c')],check=True)
source=ROOT/'vm_malbolge/evidence/epoch_selector_rearm_v0/rearmed2.mb';data=b'\x01\x02\x01'
r=subprocess.run([str(out/'runner_trace'),str(source),'300000'],input=data,capture_output=True,check=True);(out/'runner_trace.stdout').write_bytes(r.stdout);(out/'runner_trace.stderr.gz').write_bytes(gzip.compress(r.stderr,mtime=0))
r=subprocess.run([str(PURE/'build/trace_ref'),str(source),'60000',str(out/'trace_c.jsonl'),str(out/'final_c.bin')],input=data,capture_output=True);(out/'trace_c.stdout').write_bytes(r.stdout);(out/'trace_c.stderr').write_bytes(r.stderr);print('trace_ref exit',r.returncode,'expected 3 for STALL')
