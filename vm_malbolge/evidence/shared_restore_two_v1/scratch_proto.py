#!/usr/bin/env python3
"""Scratch proto: patch → crazy3 → REARM final → store clock/C → call2 → HALT."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
ONE_V1 = P.parent / 'shared_restore_one_v1'
sys.path.insert(0, str(ROOT.parent / 'BolgeForge'))

s = importlib.util.spec_from_file_location(
    'compose', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
se = m.SE
N = 59049
ONE = 29524
ROT, MOVD, CRAZY, CLOCK = 58057, 58152, 58268, 58303
T1, C, K = 57100, 57200, 57000
T2 = 57300
PCRAZY = 57610
STORE = 57700
REARM_M1 = se.crazy(ONE, 58302)
REARM = REARM_M1 + 1
assert PCRAZY % 94 == 82 and REARM == 57565


def op_at(pc: int, opcode: int) -> int:
    for v in range(33, 127):
        if (v + pc) % 94 == opcode:
            return v
    raise ValueError(f'no printable op {opcode} at {pc}')


def load_one_v1():
    image = (ONE_V1 / 'restore_positive.mb').read_bytes()
    mem = list(image) + [0] * (N - len(image))
    for i in range(len(image), N):
        mem[i] = se.crazy(mem[i - 1], mem[i - 2])
    return mem


def plant_private(mem):
    # phase1 patch exit
    mem[PCRAZY] = 74
    for pc in range(PCRAZY + 1, PCRAZY + 7):
        mem[pc] = op_at(pc, 68)
    mem[PCRAZY + 7] = op_at(PCRAZY + 7, 40)
    mem[PCRAZY + 8] = op_at(PCRAZY + 8, 39)
    mem[PCRAZY + 9] = op_at(PCRAZY + 9, 68)
    mem[PCRAZY + 10] = op_at(PCRAZY + 10, 68)
    mem[PCRAZY + 11] = op_at(PCRAZY + 11, 4)

    # REARM: MOVD (T1-1) + CRAZY final + JMP to STORE via T1+1
    mem[REARM] = op_at(REARM, 40)
    mem[REARM + 1] = op_at(REARM + 1, 62)
    mem[REARM + 2] = op_at(REARM + 2, 4)  # JMP mem[T1+1] → STORE


def install_phase1_divert(mem):
    mem[T1 + 4] = T1 + 1
    mem[T1 + 2] = PCRAZY - 1
    mem[57110] = C - 1
    mem[C + 3] = MOVD - 1
    mem[C + 4] = T1 - 4


def after_patch(mem):
    """T+4 retarget for REARM MOVD (crazy3 still needs T+1=CRAZY-1)."""
    mem[T1 + 4] = T1 - 1


def at_rearm_entry(mem):
    """T+1 → STORE-1 so post-final JMP leaves to STORE (crazy3 already done)."""
    mem[T1 + 1] = STORE - 1


def store_cell(mem, a, cell, want):
    """Uniform store with a==ONE. Returns new a (=want)."""
    assert a == ONE
    x = se.crazy(ONE, mem[cell])
    mid = se.crazy(x, x)
    assert mid == ONE
    ctrl = se.crazy(want, ONE)
    mem[cell] = se.crazy(ctrl, mid)
    assert mem[cell] == want
    return want


def main():
    mem = load_one_v1()
    plant_private(mem)
    mem[T2] = 70
    # Plant T2 trampolines mirroring T1 (for native call2 attempt)
    mem[T2 - 3] = MOVD - 1
    mem[T2 - 1] = CRAZY - 1
    mem[T2 + 1] = CRAZY - 1
    mem[T2 + 3] = CLOCK - 1
    mem[T2 + 4] = C - 2
    mem[T2 + 5] = MOVD - 1
    mem[T2 + 6] = T2 - 4

    a = c = d = 0
    phase1 = False
    patched = False
    rearm_seen = False
    t1_writes, t2_writes = [], []
    host_store = False

    for step in range(1, 15001):
        op = (mem[c] + c) % 94
        if c == CLOCK and not phase1 and op == 40:
            install_phase1_divert(mem)
            phase1 = True
        if not patched and mem[T1 + 3] == REARM_M1 and c >= PCRAZY:
            after_patch(mem)
            patched = True
        if not rearm_seen and c == REARM:
            at_rearm_entry(mem)
            rearm_seen = True

        # STORE entry: host-execute stores + call2 setup, then jump to call2
        if c == STORE and not host_store:
            host_store = True
            # Expect a=40 after final crazy; get ONE via ROT@K
            mem[K] = ONE
            a = se.rot(mem[K])  # still ONE
            assert a == ONE
            a = store_cell(mem, a, CLOCK, 117)
            # reload ONE
            a = se.rot(mem[K])
            a = store_cell(mem, a, C, 120)
            # Point K island at T2 and enter shared restore from ROT@K
            mem[K - 1] = ROT - 1
            mem[K + 1] = ROT - 1
            mem[K + 3] = MOVD - 1
            mem[K + 4] = T2 - 4
            mem[C - 1] = ROT - 1
            mem[C + 1] = ROT - 1
            mem[C + 3] = MOVD - 1
            mem[C + 4] = T2 - 4
            # Reset shared primitives to phase 74 if needed
            for pc in (ROT, MOVD, CRAZY):
                if not (33 <= mem[pc] <= 126):
                    mem[pc] = 74
                # force known phase word
                mem[pc] = 74
            mem[CLOCK] = 117  # already stored
            # Enter at ROT with d=K
            d = K
            c = ROT
            a = 0  # ROT will set a from K
            continue

        if op == 4:
            c = mem[d]
        elif op == 39:
            mem[d] = se.rot(mem[d]); a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            before = mem[d]
            mem[d] = se.crazy(a, mem[d]); a = mem[d]
            if d == T1:
                t1_writes.append({'step': step, 'before': before, 'after': mem[d]})
            if d == T2:
                t2_writes.append({'step': step, 'before': before, 'after': mem[d]})
        elif op == 81:
            out = {
                'halt_step': step, 'halt_pc': c,
                'T1': mem[T1], 'T2': mem[T2], 'T3': mem[T1 + 3],
                'C': mem[C], 'clk': mem[CLOCK],
                'patch_ok': mem[T1 + 3] == REARM_M1,
                't1_writes': t1_writes, 't2_writes': t2_writes,
                'host_store': host_store,
            }
            (P / 'scratch_proto.results.json').write_text(json.dumps(out, indent=2) + '\n')
            print(json.dumps(out, indent=2))
            if out['T1'] == 40 and out['T2'] == 40:
                print('PROTO_PASS')
            else:
                print('PROTO_PARTIAL')
            return
        if 33 <= mem[c] <= 126:
            mem[c] = se.encrypt(mem[c])
        c = (c + 1) % N
        d = (d + 1) % N
    raise SystemExit(f'budget T1={mem[T1]} T2={mem[T2]} clk={mem[CLOCK]} C={mem[C]} host={host_store}')


if __name__ == '__main__':
    main()
