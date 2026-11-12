#!/usr/bin/env python3
"""Feasibility checks for a self-sustaining rearm loop (host-side only).

Three questions the loop design depends on:

1. Restoration involution: for a value v planted as target, the chain is
   ctrl = crazy(v, ONE) ; restore = crazy(ctrl, 29524). Is
   crazy(crazy(v,ONE),ONE) == v for every v? (Decides whether ANY cell value,
   not just the 48 code words, can be restored by the uniform chain.)

2. Reset universality: a code cell after one execution holds enc(want), a
   printable char. Does e -> crazy(ONE,e) -> crazy(x,x) == 29524 for every
   printable e? (The 48 rows all reset; this generalises.)

3. Orbit clock: can an unrestored code cell give N-1 harmless opcodes and then
   HALT? At a fixed pc each orbit element decodes to a distinct opcode, so the
   pure-NOP clock is only possible for N<=2; we count the (pc, cycle) pairs
   where the 'o' char and the 'v' char share an xlat2 cycle.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parents[2]
sys.path.insert(0, str(ROOT.parent / 'BolgeForge'))
from constants import crazy_op, rot_op, XLAT1, XLAT2

ONE = 29524
MEM = 59049

def opcode(cell, pc):
    return XLAT1[(cell + pc) % 94]

# 1. involution over the whole value space
inv_ok = sum(1 for v in range(MEM) if crazy_op(crazy_op(v, ONE), ONE) == v)
inv_counter = [v for v in range(MEM) if crazy_op(crazy_op(v, ONE), ONE) != v][:8]

# 2. reset for every printable e
enc = lambda ch: ord(XLAT2[ch - 33])
printable = list(range(33, 127))
reset_ok = []
reset_bad = []
for e in printable:
    x = crazy_op(ONE, e)
    if crazy_op(x, x) == ONE:
        reset_ok.append(e)
    else:
        reset_bad.append(e)

# 3. xlat2 cycles and the N<=2 orbit clock
cycles = []
seen = set()
for v in printable:
    if v in seen:
        continue
    cyc = []
    x = v
    while x not in seen:
        seen.add(x); cyc.append(x); x = enc(x)
    cycles.append(cyc)
clock = []
for p in range(94):
    o_char = 33 + ((XLAT1.index('o') - p) % 94)
    v_char = 33 + ((XLAT1.index('v') - p) % 94)
    same = next((c for c in cycles if o_char in c and v_char in c), None)
    if same:
        clock.append({'pc_mod94': p, 'o_char': o_char, 'v_char': v_char,
                      'cycle_len': len(same), 'o_position': same.index(o_char),
                      'v_position': same.index(v_char),
                      'o_before_v': same.index(o_char) < same.index(v_char)})

z = {
    'involution_pairs_over_59049': {'ok': inv_ok, 'bad_count': MEM - inv_ok, 'bad_examples': inv_counter},
    'reset_printable_e': {'ok': len(reset_ok), 'bad': reset_bad},
    'xlat2_cycles': {'count': len(cycles), 'lengths': sorted({len(c) for c in cycles}),
                     'longest': max(len(c) for c in cycles)},
    'orbit_clock_pure_nop': {'possible_pairs': len(clock), 'o_before_v': sum(1 for c in clock if c['o_before_v']),
                             'detail': clock[:6],
                             'note': 'N<=2 only without controlled-dangerous opcodes; N>=3 needs choreographed d/a at the clock cell'},
    'scope': 'host-side feasibility for the two-restorer loop design; no image synthesized',
}
(pathlib.Path(__file__).resolve().parent / 'loop_feasibility.results.json').write_text(json.dumps(z, indent=2, sort_keys=True) + '\n')
print(json.dumps(z, indent=2, sort_keys=True))
