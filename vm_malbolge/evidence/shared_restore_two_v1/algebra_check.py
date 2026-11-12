#!/usr/bin/env python3
"""Host-side algebra for rearming clock+constant after shared_restore_one_v1."""
import importlib.util, json, pathlib
P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
s = importlib.util.spec_from_file_location(
    'compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
se = m.SE
ONE = 29524
CLOCK_PC = 58303


def encrypt_chain(v0, n=6):
    v = v0
    out = []
    for _ in range(n):
        op = (v + CLOCK_PC) % 94
        out.append({'value': v, 'opcode': op})
        v = se.encrypt(v)
    return out


def crazy_restore(e, want):
    x = se.crazy(ONE, e)
    mid = se.crazy(x, x)
    ctrl = se.crazy(want, ONE)
    got = se.crazy(ctrl, mid)
    return {
        'e': e,
        'want': want,
        'x': x,
        'mid': mid,
        'ctrl': ctrl,
        'got': got,
        'ok': got == want,
        'ctrl_roundtrip': se.crazy(ctrl, ONE) == want,
    }


def nine_rots(v0, n=9):
    v = v0
    for _ in range(n):
        v = se.rot(v)
    return v


clock_chain = encrypt_chain(117)
assert [row['opcode'] for row in clock_chain[:4]] == [46, 40, 49, 81]
assert clock_chain[3]['value'] == 58

clock = crazy_restore(58, 117)
constant_crazy = crazy_restore(40, 120)
constant_rots = nine_rots(40)
assert clock['ok'] and constant_crazy['ok'] and constant_rots == 120

# No printable (pc≡23) start yields two MOVD before HALT without IN/OUT.
movd_double = []
for v0 in range(33, 127):
    v = v0
    ops = []
    bad = False
    for _ in range(12):
        if not 33 <= v <= 126:
            bad = True
            break
        op = (v + CLOCK_PC) % 94
        ops.append(op)
        if op == 81:
            break
        if op in (5, 23):
            bad = True
            break
        v = se.encrypt(v)
    if bad or not ops or ops[-1] != 81:
        continue
    if ops.count(40) >= 2:
        movd_double.append({'v0': v0, 'ops': ops})

z = {
    'base': 'shared_restore_one_v1@4172c2e',
    'clock_pc': CLOCK_PC,
    'clock_orbit_from_117': clock_chain,
    'clock_rearm': clock,
    'constant_rearm_crazy': constant_crazy,
    'constant_rearm_nine_rots': {'from': 40, 'to': constant_rots, 'ok': constant_rots == 120},
    'double_movd_before_halt_at_clock_pc': movd_double,
    'implication': (
        'call1 cannot share one xlat2 orbit for two MOVD dispatch phases; '
        'must rearm clock (58→117) and constant (40→120), and divert the '
        'fourth return through cell T+3=57103 away from CLOCK before HALT'
    ),
    'divert_cell': {'address': 57103, 'call1_value': 58302, 'role': 'JMP target before CLOCK'},
}
(P / 'algebra_check.results.json').write_text(json.dumps(z, indent=2) + '\n')
print(json.dumps(z, indent=2))
