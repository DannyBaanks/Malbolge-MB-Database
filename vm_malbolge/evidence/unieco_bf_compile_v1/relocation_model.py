#!/usr/bin/env python3
"""Test a hypothesized relocation of the reference runtime from a captured state.

This is a model-level experiment: the host seeds the state. It is NOT a
Malbolge bootstrap, not the old relocated candidate, and proves no loader path.
"""
import importlib.util
import json
import pathlib

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
spec = importlib.util.spec_from_file_location('compose', ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
se = m.SE
image = (ROOT/'vm_malbolge/evidence/unieco_strict_relocation_v1/reference_cat_functional.mb').read_bytes()
N = 59049
SHIFT = 94 * 300
LO, HI = 7614, 7971

def fresh():
    mem = list(image) + [0]*(N-len(image))
    for i in range(len(image), N):
        mem[i] = se.crazy(mem[i-1],mem[i-2])
    return mem

def step(mem, state, stream):
    a,c,d,pos = state
    if not 33 <= mem[c] <= 126:
        return state, None, None, 'NONPRINT'
    op = (mem[c]+c)%94
    out = None
    if op == 4:
        c = mem[d]
    elif op == 5:
        out = a%256
    elif op == 23:
        a = stream[pos] if pos < len(stream) else 59048
        pos += pos < len(stream)
    elif op == 39:
        mem[d] = se.rot(mem[d]); a = mem[d]
    elif op == 40:
        d = mem[d]
    elif op == 62:
        mem[d] = se.crazy(a,mem[d]); a = mem[d]
    elif op == 81:
        return (a,c,d,pos),op,out,'HALTED'
    if 33 <= mem[c] <= 126:mem[c] = se.encrypt(mem[c])
    return (a,(c+1)%N,(d+1)%N,pos),op,out,None

mem = fresh(); state = (0,0,0,0)
for n in range(20000):
    a,c,d,pos = state
    if (mem[c]+c)%94 == 23:
        break
    state,op,out,status = step(mem,state,b'')
    if status or out is not None:raise AssertionError('unexpected preamble I/O or stop')
else:raise AssertionError('first input not reached')
snapshot = mem.copy(); entry = state
stream = bytes(range(256)) + b'\x00\xff'
# Profile reference jump-pointer cells over this finite stream, including EOF.
trace_mem = snapshot.copy(); s = entry; pointers = set(); reference_ops = []; reference_out = bytearray()
for n in range(200000):
    a,c,d,pos = s
    if (trace_mem[c]+c)%94 == 4 and LO <= trace_mem[d] <= HI:
        pointers.add(d)
    s,op,out,status = step(trace_mem,s,stream)
    reference_ops.append(op)
    if out is not None:reference_out.append(out)
    if status:break
else:status='MAX_STEPS'
assert status == 'HALTED' and bytes(reference_out) == stream
# Relocate the code range by a multiple of 94; rewrite observed jump pointer
# initial values only. No host updates are made after the experiment starts.
relocated = snapshot.copy()
for i in range(LO,HI+1):relocated[i+SHIFT] = snapshot[i]
rewrites = []
for d in sorted(pointers):
    before = relocated[d]
    if LO <= before <= HI:
        relocated[d] += SHIFT
        rewrites.append({'cell': d, 'old': before, 'new': relocated[d]})
rstate = (entry[0],entry[1]+SHIFT,entry[2],entry[3])
output = bytearray(); first_mismatch = None
for n,expected_op in enumerate(reference_ops,1):
    before = rstate
    rstate,op,out,rstatus = step(relocated,rstate,stream)
    if out is not None:output.append(out)
    if op != expected_op:
        first_mismatch = {'step_after_first_in':n,'expected_opcode':expected_op,'actual_opcode':op,
                          'registers_before':list(before),'status':rstatus}
        break
    if rstatus:break
else:rstatus='MAX_STEPS'
result = {'shift':SHIFT,'code_range':[LO,HI], 'input_bytes':len(stream),
          'entry_original':list(entry),'entry_relocated':[entry[0],entry[1]+SHIFT,entry[2],entry[3]],
          'reference_halted':status=='HALTED','reference_output_exact':bytes(reference_out)==stream,
          'profiled_jump_pointer_cells':sorted(pointers),'initial_pointer_rewrites':rewrites,
          'relocated_status':rstatus,'relocated_output_bytes':len(output),
          'relocated_output_exact':bytes(output)==stream,'first_opcode_mismatch':first_mismatch,
          'scope':'host-seeded snapshot model; finite stream; no native bootstrap or old-candidate composition'}
(P/'relocation_model.results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
