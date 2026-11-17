#!/usr/bin/env python3
"""Scratch probe for four sequential callers of one shared operation site."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import os
import subprocess
import sys

PACK = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(os.environ.get('MALBOLGE_MB_DATABASE_ROOT', str(PACK.parents[2]))).resolve()
BF = pathlib.Path(os.environ.get('BOLGEFORGE_ROOT', str(REPO.parent / 'BolgeForge'))).resolve()
CB = pathlib.Path(os.environ.get('CLASESBOLGE_MALBOLGE', str(REPO.parent.parent / 'clasesbolge/tools/malbolge.py'))).resolve()
OLM = pathlib.Path(os.environ.get('OLMSTEAD_BIN', str(REPO.parent / 'Malbolge-PureEpoch/build/olmstead'))).resolve()
sys.path.insert(0, str(BF))
from constants import XLAT1, XLAT2  # noqa: E402
from tools.resynthesize import synthesize_preamble_ops  # noqa: E402

spec_cb = importlib.util.spec_from_file_location('cb', CB)
cb = importlib.util.module_from_spec(spec_cb)
spec_cb.loader.exec_module(cb)

spec_se = importlib.util.spec_from_file_location(
    'se', REPO / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
)
se_mod = importlib.util.module_from_spec(spec_se)
spec_se.loader.exec_module(se_mod)
SE = se_mod.SE

OP_JMP, OP_OUT, OP_MOVD, OP_MIX, OP_HALT = 4, 5, 40, 62, 81
EFFECTS = {4, 5, 23, 39, 40, 62, 81}
VALID = set('ji*p</vo')
SOURCE_LEN = 39932
HANDOFF = 40000
BLOCK_START = 38000
BODY_START = 15000
MEM_SIZE = 59049
INIT_VALUE = 12345


def encode(op: int, pc: int) -> int:
    return 33 + ((op - pc - 33) % 94)


def phase_word(pc: int, op: int) -> int:
    for word in (74, 70):
        if (word + pc) % 94 == op and (ord(XLAT2[word - 33]) + pc) % 94 not in EFFECTS:
            return word
    raise ValueError((pc, op))


class Shared4:
    def __init__(self):
        self.code: dict[int, int] = {}
        self.values: dict[int, int] = {}
        self.code_cursor = BLOCK_START
        self.data_cursor = HANDOFF + 2

        self.call_order = tuple(os.environ.get('G5B_CALL_ORDER', 'rr,ll,rl,lr').split(','))
        if len(self.call_order) != 4 or set(self.call_order) != {'ll', 'lr', 'rl', 'rr'}:
            raise ValueError(f'G5B_CALL_ORDER must permute ll,lr,rl,rr: {self.call_order}')
        self.cont = {
            leaf: BODY_START + i * 4
            for i, leaf in enumerate(self.call_order)
        }
        for i, leaf in enumerate(self.call_order):
            pc = self.cont[leaf]
            self.code[pc] = encode(OP_OUT, pc)
            self.code[pc + 1] = encode(
                OP_HALT if i == len(self.call_order) - 1 else OP_JMP,
                pc + 1,
            )

        self.wrapper = self.make_tick(OP_MOVD, 60)
        self.shared_op = self.make_tick(OP_MIX, 82)
        self.f_root = self.make_flag()
        self.f_left = self.make_flag()
        self.f_right = self.make_flag()
        self.align = self.make_tick(OP_MOVD, 60)
        self.call_wrappers = {self.call_order[0]: self.wrapper}
        for leaf in self.call_order[1:]:
            self.call_wrappers[leaf] = self.make_tick(OP_MOVD, 60)

        base = self.reserve_data(14)
        self.d_addr = base + 4
        self.put(self.d_addr - 2, self.align)
        self.put(self.d_addr - 1, self.shared_op - 1)
        self.put(self.d_addr, INIT_VALUE)

        self.build_router()
        self.build_callers()

    def put(self, addr: int, value: int) -> None:
        old = self.values.get(addr)
        if old is not None and old != value:
            raise ValueError(f'data collision at {addr}: {old} != {value}')
        self.values[addr] = value

    def alloc_code(self, residue: int) -> int:
        while (self.code_cursor % 94 != residue
               or self.code_cursor in self.code
               or self.code_cursor + 1 in self.code):
            self.code_cursor += 1
        pc = self.code_cursor
        self.code_cursor += 2
        return pc

    def make_tick(self, op: int, residue: int) -> int:
        pc = self.alloc_code(residue)
        self.code[pc] = phase_word(pc, op)
        self.code[pc + 1] = encode(OP_JMP, pc + 1)
        return pc

    def make_flag(self) -> int:
        pc = self.alloc_code(60)
        self.code[pc] = 74
        self.code[pc + 1] = encode(OP_JMP, pc + 1)
        return pc

    def alloc_data_block(self, vals: list[int]) -> int:
        base = self.reserve_data(len(vals))
        for i, value in enumerate(vals):
            self.put(base + i, value)
        return base

    def reserve_data(self, count: int) -> int:
        base = self.data_cursor
        self.data_cursor += count
        return base

    def build_router(self) -> None:
        d, c = self.d_addr, self.shared_op
        p_right = self.reserve_data(9)
        self.put(p_right + 1, self.f_root - 1)
        self.put(p_right + 3, self.f_right - 1)
        self.put(p_right + 5, self.cont['rl'] - 1)
        p_left = self.reserve_data(7)
        self.put(p_left + 1, self.f_left - 1)
        self.put(p_left + 3, self.cont['lr'] - 1)
        p_right_right = self.reserve_data(7)
        self.put(p_right_right + 1, self.f_right - 1)
        self.put(p_right_right + 3, self.cont['rr'] - 1)
        self.put(p_right + 4, p_right_right)

        self.put(d + 1, c)                 # shared op rearm
        self.put(d + 2, self.f_root - 1)  # enter root selector
        self.put(d + 3, p_right)          # root MOVD branch
        self.put(d + 4, self.f_left - 1)  # root NOP branch
        self.put(d + 5, p_left)           # left MOVD branch
        self.put(d + 6, self.cont['ll'] - 1)  # left NOP branch
        self.after_route = {
            'll': d + 7,
            'lr': p_left + 4,
            'rl': p_right + 6,
            'rr': p_right_right + 4,
        }

    def build_callers(self) -> None:
        toggles = {
            'll': [self.f_root, self.f_left],
            'lr': [self.f_root],
            'rl': [self.f_right],
            'rr': [],
        }
        frames = {}
        for leaf in self.call_order:
            frame = self.reserve_data(len(toggles[leaf]) + 2)
            frames[leaf] = frame
            targets = [*toggles[leaf], self.align - 1]
            for i, target in enumerate(targets):
                self.put(frame + i, target)
            # The align MOVD reads this after the final selected flag and
            # loads d=d_addr-2, then its paired JMP returns through d_addr-1.
            self.put(frame + len(toggles[leaf]) + 1, self.d_addr - 3)

        first = self.call_order[0]
        self.put(HANDOFF, self.call_wrappers[first] - 1)
        self.put(HANDOFF + 1, frames[first] - 1)

        for prev_leaf, next_leaf in zip(self.call_order, self.call_order[1:]):
            d_after_return = self.after_route[prev_leaf]
            # The leaf emits one byte, then this JMP enters the next caller's
            # wrapper. The wrapper MOVD reads its next per-call frame pointer.
            self.put(d_after_return + 1, self.call_wrappers[next_leaf] - 1)
            self.put(d_after_return + 2, frames[next_leaf] - 1)

    def assemble(self) -> bytes:
        raw = (BF / 'reference/malbolge_org/cat.mal').read_bytes()
        template = [v for v in raw if 33 <= v <= 126]
        if len(template) + 94 * 325 != SOURCE_LEN:
            raise ValueError('template length changed')

        clean = template + [33] * (SOURCE_LEN - len(template))
        ops = synthesize_preamble_ops(
            clean, self.values, HANDOFF, 9003, 0,
            template_clean=template, boot='original',
        )
        preamble_end = 99 + len(ops)
        if preamble_end >= min(self.code):
            raise ValueError(f'preamble overlaps code: {preamble_end}')

        prog = bytearray(template[:99])
        prog.extend(33 + ((XLAT1.index(ch) - i) % 94) for i, ch in enumerate(ops, 99))
        while len(prog) < SOURCE_LEN - 2:
            prog.append(33 + ((XLAT1.index('o') - len(prog)) % 94))
        prog.extend(template[-2:])
        for pc, word in self.code.items():
            prog[pc] = word

        if len(prog) != SOURCE_LEN:
            raise ValueError('bad image length')
        if not all(XLAT1[(word - 33 + pc) % 94] in VALID
                   for pc, word in enumerate(prog)):
            raise ValueError('loader check failed')
        for pc, word in self.code.items():
            if not 33 <= word <= 126:
                raise ValueError((pc, word))
        return bytes(prog)


def trace(image: bytes, plan: Shared4) -> dict:
    mem = list(image) + [0] * (MEM_SIZE - len(image))
    for i in range(len(image), MEM_SIZE):
        mem[i] = SE.crazy(mem[i - 1], mem[i - 2])
    tails = [*(pc + 1 for pc in plan.call_wrappers.values()), plan.align + 1,
             plan.shared_op + 1,
             plan.f_root + 1, plan.f_left + 1, plan.f_right + 1]
    tails_before = {pc: mem[pc] for pc in tails}
    flags = [plan.f_root, plan.f_left, plan.f_right]
    out = []
    cont_visits = []
    states_at_cont = []
    shared_calls = []
    a = c = d = 0
    status = 'limit'

    for steps in range(1, 2_000_000):
        if c in plan.cont.values() and c not in cont_visits:
            cont_visits.append(c)
            states_at_cont.append({
                'pc': c,
                'flags': [mem[pc] for pc in flags],
                'shared_op': mem[plan.shared_op],
            })
        shared_before = None
        if c == plan.shared_op:
            shared_before = {'a_before': a, 'd': d, 'value_before': mem[d]}
        if not 33 <= mem[c] <= 126:
            status = 'frozen'
            break
        op = (mem[c] + c) % 94
        if op == OP_JMP:
            c = mem[d]
        elif op == OP_OUT:
            out.append(a % 256)
        elif op == 23:
            a = 59048
        elif op == 39:
            a = mem[d] = SE.rot(mem[d])
        elif op == OP_MOVD:
            d = mem[d]
        elif op == OP_MIX:
            a = mem[d] = SE.crazy(a, mem[d])
        elif op == OP_HALT:
            status = 'halt'
            break
        if shared_before is not None:
            shared_calls.append({
                **shared_before,
                'a_after': a,
                'value_after': mem[shared_before['d']],
            })
        if 33 <= mem[c] <= 126:
            mem[c] = SE.encrypt(mem[c])
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE

    return {
        'status': status,
        'steps': steps,
        'output': bytes(out),
        'cont_visits': cont_visits,
        'states_at_cont': states_at_cont,
        'shared_calls': shared_calls,
        'tails_unchanged': all(mem[pc] == tails_before[pc] for pc in tails),
    }


def run_sequential(image_path: pathlib.Path) -> dict:
    plan = Shared4()
    image = plan.assemble()
    image_path = image_path.resolve()
    image_path.parent.mkdir(parents=True, exist_ok=True)
    if image_path.exists():
        raise FileExistsError(image_path)
    image_path.write_bytes(image)

    local = trace(image, plan)
    if local['status'] != 'halt':
        debug = dict(local)
        debug['output'] = local['output'].hex()
        raise RuntimeError(f'local trace failed: {json.dumps(debug)}')

    native = subprocess.run([str(OLM), str(image_path)], input=b'', capture_output=True, timeout=20)
    independent = cb.execute(image, b'', max_steps=2_000_000)
    image_path.with_suffix(image_path.suffix + '.native.stdout.raw').write_bytes(native.stdout)
    image_path.with_suffix(image_path.suffix + '.native.stderr.raw').write_bytes(native.stderr)
    expected_calls = []
    for call in local['shared_calls']:
        expected_value = SE.crazy(call['a_before'], call['value_before'])
        assert call['a_after'] == expected_value
        assert call['value_after'] == expected_value
        expected_calls.append(expected_value)
    expected = bytes(value % 256 for value in expected_calls)
    assert expected_calls == [12130, 21990, 7534, 21990], expected_calls
    assert expected.hex() == '62e66ee6', expected.hex()
    targets = [plan.cont[leaf] for leaf in plan.call_order]

    assert len(local['shared_calls']) == 4, local['shared_calls']
    assert all(call['d'] == plan.d_addr for call in local['shared_calls'])
    assert native.returncode == 0, (native.returncode, native.stderr.hex())
    assert native.stdout == expected, (native.stdout.hex(), expected.hex())
    assert independent.status == 'end' and independent.output == expected
    assert local['status'] == 'halt' and local['output'] == expected
    assert local['cont_visits'] == targets, (local['cont_visits'], targets)
    assert all(state['flags'] == [74, 74, 74] and state['shared_op'] == 74
               for state in local['states_at_cont']), local['states_at_cont']
    assert local['tails_unchanged']

    return {
        'call_order': list(plan.call_order),
        'shared_op_address': plan.shared_op,
        'variable_address': plan.d_addr,
        'continuation_visits': local['cont_visits'],
        'output_hex': native.stdout.hex(),
        'output_length': len(native.stdout),
        'shared_calls': local['shared_calls'],
        'native_rc': native.returncode,
        'independent_status': independent.status,
        'local_trace_status': local['status'],
        'local_trace_steps': local['steps'],
        'states_at_cont': local['states_at_cont'],
        'tails_unchanged': local['tails_unchanged'],
        'image_sha256': hashlib.sha256(image).hexdigest(),
    }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('uso: python3 probe.py <positive.mb>')
    result = run_sequential(pathlib.Path(sys.argv[1]))
    print(json.dumps({
        'run': result,
        'all_four_sequential_calls_match': True,
        'scope': f"order {','.join(result['call_order'])}; one variable and one shared opcode site",
    }, indent=2))
