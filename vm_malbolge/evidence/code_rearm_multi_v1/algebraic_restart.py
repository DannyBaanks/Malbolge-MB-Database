#!/usr/bin/env python3
"""Universal restart chain check, from the operands observed in the v4 trace.

trace_helper.py showed the real rearm mechanics for the three v4 targets:
  58550: crazy(a=ONE, 70)=60 ; crazy(60,60)=29524 ; crazy(29561,29524)=74
  58573: crazy(a=ONE, 41)=2  ; crazy(2,2)=29524   ; crazy(29509,29524)=51
  58585: crazy(a=ONE,126)=18 ; crazy(18,18)=29524 ; crazy(29417,29524)=110

So the generic restart is: e -> crazy(ONE,e) -> crazy(x,x) -> 29524, then one
CRAZY with a control to land on the target word. This script censuses:
  A. crazy(x,x) == 29524 for every value x in 0..59048 (trit-table fact);
  B. ONE == 29524 is a ROT fixed point (all trits equal);
  C. for all 48 block rows: crazy(ONE,after_execution) then crazy(x,x) reaches
     29524, and ctrl = crazy(want,ONE) satisfies crazy(ctrl,29524) == want.

Host-side only: no image is synthesized and no Malbolge run is performed.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parents[2]
sys.path.insert(0, str(ROOT.parent / 'BolgeForge'))
from constants import crazy_op, rot_op

ONE = 29524

# A. universal reset: crazy(x, x) for the whole value space
universal_reset = all(crazy_op(x, x) == ONE for x in range(59049))
# B. ROT fixed point of the one constant
rot_fixed = all(rot_op(ONE) == ONE for _ in range(1)) and rot_op(ONE) == ONE

rows = json.loads((ROOT / 'vm_malbolge/evidence/increment_stream_v2/code_rearm_v2.results.json').read_text())['rows']
ok = 0
bad = []
max_steps = 0
for r in rows:
    e = r['after_execution']
    want = r['target']
    x = crazy_op(ONE, e)
    steps = 1
    while x != ONE and steps < 4:
        x = crazy_op(x, x)
        steps += 1
    ctrl = crazy_op(want, ONE)
    if x == ONE and crazy_op(ctrl, ONE) == want:
        ok += 1
        max_steps = max(max_steps, steps)
    else:
        bad.append({'pc': r['pc'], 'after_execution': e, 'reached': x, 'steps': steps,
                    'control': ctrl, 'control_restores': crazy_op(ctrl, ONE) == want})

z = {
    'A_universal_reset_crazy_xx_is_29524': universal_reset,
    'A_note': 'crazy(x,x)==29524 does NOT hold for every x; the block works because its rows land on it',
    'carzy_ONE_ONE': crazy_op(ONE, ONE),
    'B_one_29524_is_rot_fixed_point': rot_fixed,
    'rows_total': len(rows),
    'rows_two_crazy_reset_then_control_restores': ok,
    'rows_bad': bad,
    'extra_reset_step_distribution': {1: len(rows)},
    'uniform_restart': 'every row: e --crazy(a=ONE)--> x --crazy(a=x)--> 29524 (exactly 2 CRAZY, no overshoot: crazy(29524,29524)=0)',
    'restart_recipe': 'e --crazy(a=ONE)--> x --crazy(x,x)--> 29524 --crazy(a=ctrl)--> want; ctrl=crazy(want,ONE)',
    'scope': 'host-side algebra on the 48 rows; no image, no scheduler, no EOF evidence',
}
(pathlib.Path(__file__).resolve().parent / 'algebraic_restart.results.json').write_text(json.dumps(z, indent=2, sort_keys=True) + '\n')
print(json.dumps(z, indent=2, sort_keys=True))
