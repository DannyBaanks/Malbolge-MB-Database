#!/usr/bin/env python3
"""Lower a 2-cell Brainfuck tape swap loop (,>,[.<.,>,]) to looping HeLL assembly."""
from __future__ import annotations
import pathlib
import sys
from collections import Counter

# Ternary constants
ONE = 29524
LOW = sum(3**i for i in range(6))
HIGH = ONE - LOW

flags = []
variables = {}
body = []
serial = 0
reg = 0
a_slot = None

def emit(s: str) -> None:
    body.append(s)

def call(var: str, mode: str) -> None:
    global serial
    serial += 1
    f = f'F{len(variables.get(var, [])) + 1}'
    r = f'RET{serial}'
    if f not in flags:
        flags.append(f)
    variables.setdefault(var, []).append((f, r))
    emit(f' R_{f}\n MOVED {var}_{mode}\n}}\n{{\n{r}:\n R_{"CRAZY" if mode=="crazy" else "ROT"} R_MOVED')

def constant(x: int) -> None:
    global a_slot
    a_slot = None
    emit(' ROT ' + {0: 'C0', 1: 'C1', 2: 'C2'}[x] + ' R_ROT')

def clear(v: str) -> None:
    global serial, a_slot
    serial += 1
    loop = f'CLEAR{serial}'
    constant(1)
    emit(loop + ':')
    call(v, 'crazy')
    emit(' COUNTER2 ' + loop)
    a_slot = v

def load(v: str | int) -> None:
    global serial, a_slot
    if isinstance(v, str) and a_slot == v:
        return
    if isinstance(v, int):
        constant(v)
        return
    serial += 1
    loop = f'LOAD{serial}'
    emit(loop + ':')
    constant(2)
    call(v, 'crazy')
    emit(' COUNTER2 ' + loop)
    a_slot = v

def copy(src: str | int, dst: str) -> None:
    global a_slot
    if isinstance(src, int):
        clear(dst)
        constant({0: 1, 1: 0, 2: 2}[src])
        call(dst, 'crazy')
        a_slot = dst
        return
    clear('aux')
    clear(dst)
    load(src)
    call('aux', 'crazy')
    call(dst, 'crazy')
    a_slot = dst

def build_ir():
    global reg
    ir = []
    def gate(a, b):
        nonlocal ir
        global reg
        reg += 1
        dst = f'g{reg}'
        ir.append(('gate', dst, a, b))
        return dst

    def lrot(x, n):
        nonlocal ir
        global reg
        reg += 1
        dst = f'g{reg}'
        ir.append(('rotate', dst, x, (10 - n) % 10))
        return dst

    def eq2or(x, m):
        g = gate(m, x)
        return gate(g, x)

    def andor(x, y, m):
        g1 = gate(2, x)
        g2 = gate(g1, y)
        g3 = gate(m, g2)
        return gate(g3, g3)

    # 1. Read cell0 (BF: , at pointer 0)
    ir.append(('input', 'cell0', None, None))

    # 2. Advance pointer > and read cell1 (BF: , at pointer 1)
    ir.append(('input', 'cell1', None, None))

    # 3. Test EOF on active cell1 (BF: [ loop condition on *ptr)
    p1 = eq2or('cell1', 'highmask')
    for k in (1, 2, 4):
        p1 = andor(p1, lrot(p1, k), 'highmask')
    eof1_1 = gate(p1, 'eofmask1')
    eof1_w = gate(eof1_1, 'eofmask2')
    ir.append(('branch', None, eof1_w, None))

    # 4. Output cell1 (BF: . at pointer 1)
    ir.append(('output', None, 'cell1', None))

    # 5. Retreat pointer < and output cell0 (BF: . at pointer 0)
    ir.append(('output', None, 'cell0', None))

    return ir

def generate_hell_source() -> str:
    global a_slot
    ir = build_ir()
    uses = Counter()
    for kind, dst, a, b in ir:
        if isinstance(a, str):
            uses[a] += 1
        if isinstance(b, str):
            uses[b] += 1

    reserved_vars = {'cell0', 'cell1', 'highmask', 'lowmask', 'eofmask1', 'eofmask2'}
    physical = {v: v for v in reserved_vars}
    free = []
    nextslot = 0

    def allocate():
        nonlocal nextslot
        if free:
            return free.pop()
        nextslot += 1
        return f't{nextslot}'

    def consume(x):
        if isinstance(x, str):
            uses[x] -= 1

    def release(x, keep):
        if isinstance(x, str) and uses[x] == 0 and x not in reserved_vars:
            slot = physical[x]
            if slot != keep and slot not in free:
                free.append(slot)

    emit('next_pair:\n R_MOVED\nENTRY:')
    branch_slot = None

    for ix, (kind, dst, a, b) in enumerate(ir):
        emit(f'TRACE{ix}:')
        if kind == 'input':
            target = dst
            consume(target)
            clear('aux')
            clear(target)
            if target == 'cell1':
                for mv, cv in [('eofmask1', 'ctrlmask1'), ('eofmask2', 'ctrlmask2')]:
                    clear(mv)
                    load(cv)
                    call(mv, 'crazy')
            emit(' IN ?- R_IN')
            call('aux', 'crazy')
            call(target, 'crazy')
            a_slot = target
            continue
        if kind == 'output':
            target = a
            consume(target)
            load(target)
            emit(' OUT ?- R_OUT')
            continue
        if kind == 'branch':
            consume(a)
            eof_slot = physical[a]
            branch_slot = eof_slot
            emit(f' MOVED {eof_slot}\n}}\n{{\nCONT_OUTPUT:\n R_MOVED')
            release(a, None)
            continue
        pa = physical[a] if isinstance(a, str) else a
        if kind == 'gate':
            pb = physical[b] if isinstance(b, str) else b
            consume(a)
            consume(b)
            reuse = isinstance(b, str) and uses[b] == 0 and b not in reserved_vars
            slot = pb if reuse else allocate()
            if slot != pb:
                copy(pb, slot)
            load(pa)
            call(slot, 'crazy')
            a_slot = slot
            release(a, slot)
            release(b, slot)
        else:
            consume(a)
            reuse = isinstance(a, str) and uses[a] == 0 and a not in reserved_vars
            slot = pa if reuse else allocate()
            if not reuse:
                copy(pa, slot)
            if b in (5, 6, 9):
                global serial
                serial += 1
                loop = f'RLOOP{serial}'
                end = f'REND{serial}'
                emit(f' R_MOVED\n{loop}:\n R_MOVED')
                call(slot, 'rot')
                emit(f' COUNTER{b} {end}\n MOVED {loop}\n}}\n{{\n{end}:')
            elif b == 8:
                serial += 1
                loop = f'RLOOP{serial}'
                end = f'RHALF{serial}'
                prep = f'RPREP{serial}'
                emit(f'{prep}:\n R_MOVED\n{loop}:\n R_MOVED')
                call(slot, 'rot')
                emit(f' COUNTER4 {end}\n MOVED {loop}\n}}\n{{\n{end}:\n COUNTER2 {prep}')
            else:
                for _ in range(b):
                    call(slot, 'rot')
            a_slot = slot
            release(a, slot)
        physical[dst] = slot

    emit(f'TRACE{len(ir)}:')
    emit(' MOVED next_pair')

    head = '''.CODE
MOVED: MovD/Nop
 Jmp

CRAZY: Opr/Nop
 Jmp

ROT: Rot/Nop
 Jmp

IN: In/Nop
 Jmp

OUT: Out/Nop
 Jmp

NOP: Jmp

HALT: Hlt

@58329
NON_EOF_0: RNop
 RNop
 Jmp

@58338
NON_EOF_1: RNop
 RNop
 Jmp

@58365
NON_EOF_2: RNop
 RNop
 Jmp

@58446
NON_EOF_3: RNop
 RNop
 Jmp

@58689
EOF_CODE: RNop
 Jmp

COUNTER2: MovD/Nop
 Jmp

COUNTER4: Nop/Nop/Nop/MovD
 Jmp

COUNTER5: Nop/Nop/Nop/Nop/MovD
 Jmp

COUNTER6: Nop/Nop/Nop/Nop/Nop/MovD
 Jmp

COUNTER9: Nop/Nop/Nop/Nop/Nop/Nop/Nop/Nop/MovD
 Jmp

'''
    head += '\n'.join(f'{f}: Nop/MovD\n Jmp\n' for f in flags)
    data = '\n.DATA\n'

    for var, calls in variables.items():
        data += '\n{\n' + f'{var}_crazy: U_CRAZY {var}\n'
        if any(var + '_rot' in line for line in body):
            data += f'{var}_rot: U_ROT {var}\n'
        value = HIGH if var == 'highmask' else LOW if var == 'lowmask' else 58324 if var == 'ctrlmask1' else 8 if var == 'ctrlmask2' else 'C1'
        data += f'{var}: {value}\n'
        if var == branch_slot:
            data += ' U_NOP EOF_SKIP\n U_NOP EOF_STOP\n U_NOP EOF_NOT\nEOF_STOP: HALT\nEOF_NOT: R_MOVED\n MOVED CONT_OUTPUT\nEOF_SKIP:\n'
        for f, r in calls:
            data += f' {f} {r} R_{f}\n'
        data += '}\n'

    source = head + data + '\n{\n' + '\n'.join(body) + '\n}\n'
    return source

def main():
    if len(sys.argv) != 2:
        print("Usage: build_hell.py <output.hell>", file=sys.stderr)
        return 1
    out_path = pathlib.Path(sys.argv[1])
    if out_path.exists():
        print(f"Error: destination {out_path} already exists", file=sys.stderr)
        return 2
    source = generate_hell_source()
    out_path.write_text(source, encoding='utf-8')
    print(f"Generated tape HeLL: {out_path} ({len(source)} bytes, flags={len(flags)}, vars={len(variables)})")
    return 0

if __name__ == '__main__':
    sys.exit(main())
