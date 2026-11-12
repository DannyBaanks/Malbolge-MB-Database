#!/usr/bin/env python3
"""Validate one-byte native runtime, compiler state and a real echo control."""
import hashlib,importlib.util,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);se=m.SE;N=59049
image=(P/'increment_oneshot.mb').read_bytes();target={int(k):v for k,v in json.loads((P/'oneshot_targets.json').read_text()).items()};sha=lambda b:hashlib.sha256(b).hexdigest();OL=ROOT.parent/'Malbolge-PureEpoch/build/olmstead'
mem=list(image)+[0]*(N-len(image))
for i in range(len(image),N):mem[i]=se.crazy(mem[i-1],mem[i-2])
a=c=d=0
for step in range(1,100000):
 if not 33<=mem[c]<=126:raise AssertionError('nonprint before input')
 op=(mem[c]+c)%94
 if op==23:break
 if op==4:c=mem[d]
 elif op==5:raise AssertionError('output before input')
 elif op==39:mem[d]=se.rot(mem[d]);a=mem[d]
 elif op==40:d=mem[d]
 elif op==62:mem[d]=se.crazy(a,mem[d]);a=mem[d]
 elif op==81:raise AssertionError('halt before input')
 if 33<=mem[c]<=126:mem[c]=se.encrypt(mem[c])
 c=(c+1)%N;d=(d+1)%N
else:raise AssertionError('no IN')
mismatch=[{'address':i,'expected':v,'actual':mem[i]} for i,v in target.items() if mem[i]!=v]
installation={'first_input_step':step,'pc':c,'d':d,'target_cells':len(target),'mismatches':mismatch,
              'ok':c==40000 and d==50000 and not mismatch}
records={}
for b in range(256):
 r=subprocess.run([str(OL),str(P/'increment_oneshot.mb')],input=bytes([b]),capture_output=True,timeout=10)
 records[str(b)]={'rc':r.returncode,'stdout_hex':r.stdout.hex(),'stderr_hex':r.stderr.hex(),
                  'ok':r.returncode==0 and r.stdout==bytes([(b+1)%256])}
 if not records[str(b)]['ok']:raise AssertionError(f'byte {b}')
controls={}
for b in [0,1,127,254,255]:
 r=subprocess.run([str(OL),str(P/'increment_control_echo.mb')],input=bytes([b]),capture_output=True,timeout=10)
 controls[str(b)]={'rc':r.returncode,'stdout_hex':r.stdout.hex(),'is_echo':r.returncode==0 and r.stdout==bytes([b]),
                   'detected':r.stdout!=bytes([(b+1)%256])}
scratch={}
for b in [0,1,127,254,255]:
 r=se.run(image,max_steps=100000,stdin=bytes([b]));scratch[str(b)]={'status':r['status'],'steps':r['steps'],'stdout_hex':r['out'].hex(),
        'ok':r['status']=='HALTED' and r['out']==bytes([(b+1)%256])}
# A second byte is intentionally not consumed: the construction is one-shot.
r=subprocess.run([str(OL),str(P/'increment_oneshot.mb')],input=b'\x00\xff',capture_output=True,timeout=10)
multibyte={'input_hex':'00ff','rc':r.returncode,'stdout_hex':r.stdout.hex(),'expected_stream_hex':'0100',
           'stream_goal_met':r.returncode==0 and r.stdout==b'\x01\x00'}
report={'image_sha256':sha(image),'image_bytes':len(image),'valid_loader_cells':all((v+i)%94 in m.VALID for i,v in enumerate(image)),
        'installation':installation,'native_single_byte_cases':records,'echo_table_controls':controls,'scratch':scratch,
        'multibyte_negative':multibyte,'scope':'one input byte per execution; not EOF-safe streaming'}
(P/'oneshot_verify.results.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
summary={'installation_ok':installation['ok'],'native_cases':len(records),'native_all_equal':all(x['ok'] for x in records.values()),
         'controls_detected':all(x['detected'] and x['is_echo'] for x in controls.values()),
         'scratch_pass':all(x['ok'] for x in scratch.values()),'multi_byte_goal_met':multibyte['stream_goal_met']}
print(json.dumps(summary,indent=2));assert all([summary['installation_ok'],summary['native_all_equal'],summary['controls_detected'],summary['scratch_pass']]) and not summary['multi_byte_goal_met']
