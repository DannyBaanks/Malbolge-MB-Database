#!/usr/bin/env python3
"""Compare a restricted binary BF fragment, Python, and strict Malbolge."""
import hashlib,importlib.util,json,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]; PURE=ROOT.parent/'Malbolge-PureEpoch';ISYCO=ROOT.parent.parent/'ISyCo'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
bf=load('bf_fragment',P/'bf_fragment.py');assembly=load('assembly_bf',ISYCO/'workspace/assembly/brainfuck/brainfuck_interpreter.py'); boss=load('boss2',PURE/'tools/boss2_brainfuck.py')
program=(P/'echo4.bf').read_text().strip(); image=(P/'echo4.mb').read_bytes();control=(P/'ctrl_no_first_out.mb').read_bytes();olm=PURE/'build/olmstead';sha=lambda x:hashlib.sha256(x).hexdigest()
assert bf.compile_fragment(program)==image
vectors=[bytes([i,(i+1)%256,(i*73)%256,255-i]) for i in range(256)]
results={'gate_commit':'c6b6dc8','bf_gates_commit':'2a3d983','formula':'33+((op-pos-33)%94)','bf_program':program,'source_ascii':image.decode('ascii'),'source_sha256':sha(image),'full_vectors':[],'short_cases':{},'assembly_cases':{},'compiler_rejections':{},'boss2_rejections':{}}
inputs=bytearray();py_outputs=bytearray();bf_outputs=bytearray();mb_outputs=bytearray()
for i,v in enumerate(vectors):
 py=subprocess.run([sys.executable,'-I',str(P/'reference.py')],input=v,capture_output=True,timeout=5)
 mb=subprocess.run([str(olm),str(P/'echo4.mb')],input=v,capture_output=True,timeout=5)
 bout=bf.execute(program,v); inputs.extend(v);py_outputs.extend(py.stdout);bf_outputs.extend(bout);mb_outputs.extend(mb.stdout)
 results['full_vectors'].append({'i':i,'input_hex':v.hex(),'python_hex':py.stdout.hex(),'bf_hex':bout.hex(),'olmstead_hex':mb.stdout.hex(),'python_rc':py.returncode,'olmstead_rc':mb.returncode,'olmstead_stderr_hex':mb.stderr.hex(),'equal':py.returncode==mb.returncode==0 and not py.stderr and not mb.stderr and py.stdout==bout==mb.stdout==v})
for label,v in [('empty',b''),('one',b'A'),('two',b'Ab'),('three',b'Ab9'),('four',b'Ab9!'),('five',b'Ab9!?')]:
 py=subprocess.run([sys.executable,'-I',str(P/'reference.py')],input=v,capture_output=True,timeout=5)
 mb=subprocess.run([str(olm),str(P/'echo4.mb')],input=v,capture_output=True,timeout=5)
 expected=bf.execute(program,v)
 results['short_cases'][label]={'input_hex':v.hex(),'python_hex':py.stdout.hex(),'bf_hex':expected.hex(),'olmstead_hex':mb.stdout.hex(),'python_rc':py.returncode,'olmstead_rc':mb.returncode,'all_equal':py.stdout==expected==mb.stdout,'olmstead_stderr_hex':mb.stderr.hex()}
for label,v in [('empty',''),('ascii','Ab9!'),('embedded_nul','\x00A'),('short','Ab9')]:
 out,steps,status=assembly.run(program,stdin_data=v);actual=out.encode('latin1');assumed=bf.execute(program,v.encode('utf8'))
 results['assembly_cases'][label]={'input_utf8_hex':v.encode('utf8').hex(),'output_hex':actual.hex(),'steps':steps,'status':status,'matches_fragment':actual==assumed}
for source in ('',',','.',',,','+','[.,]',',.,'):
 try:bf.compile_fragment(source);r='ACCEPTED'
 except ValueError as e:r=type(e).__name__+': '+str(e)
 results['compiler_rejections'][source]=r
for source in (',.','[.,]','+[-].'):
 try:boss.build_boss2_brainfuck(source);r='ACCEPTED'
 except NotImplementedError as e:r=type(e).__name__+': '+str(e)
 results['boss2_rejections'][source]=r
r=subprocess.run([str(olm),str(P/'ctrl_no_first_out.mb')],input=b'Ab9!',capture_output=True,timeout=5)
results['control']={'output_hex':r.stdout.hex(),'rc':r.returncode,'stderr_hex':r.stderr.hex(),'expected_hex':b'Ab9!'.hex(),'fails_equivalence':r.returncode==0 and r.stdout!=b'Ab9!'}
for name,data in [('full_inputs.raw',inputs),('full_python.raw',py_outputs),('full_bf.raw',bf_outputs),('full_olmstead.raw',mb_outputs)]: (P/name).write_bytes(data)
results['summary']={'all_full_equal':all(x['equal'] for x in results['full_vectors']),'assembly_fragment_agree':all(x['matches_fragment'] for x in results['assembly_cases'].values()),'short_eof_all_equal':all(x['all_equal'] for k,x in results['short_cases'].items() if k in ('empty','one','two','three')),'control_fails':results['control']['fails_equivalence'],'boss2_unsupported_rejected':all(x.startswith('NotImplementedError') for x in results['boss2_rejections'].values()),'limited_compiler_rejections':all(x.startswith('ValueError') for x in results['compiler_rejections'].values()),'binary_data_sha':{'input':sha(inputs),'python':sha(py_outputs),'bf':sha(bf_outputs),'olmstead':sha(mb_outputs)}}
(P/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'summary':results['summary'],'short_cases':results['short_cases'],'assembly_cases':results['assembly_cases'],'control':results['control'],'boss2_rejections':results['boss2_rejections']},indent=2))
