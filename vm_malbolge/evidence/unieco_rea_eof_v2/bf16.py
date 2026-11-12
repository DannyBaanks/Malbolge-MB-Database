#!/usr/bin/env python3
"""BF interpreter: unsigned 16-bit wrapping cells and configurable EOF value."""
import argparse
import sys
from pathlib import Path


def run(source, data, eof=65535, limit=1000000):
    program = ''.join(ch for ch in source if ch in '><+-.,[]')
    stack, jumps = [], {}
    for i, ch in enumerate(program):
        if ch == '[':
            stack.append(i)
        elif ch == ']':
            if not stack:
                raise ValueError('unmatched ]')
            j = stack.pop()
            jumps[i] = j
            jumps[j] = i
    if stack:
        raise ValueError('unmatched [')
    tape = [0] * 30000
    pc = pointer = pos = steps = 0
    output = bytearray()
    while pc < len(program):
        if steps >= limit:
            return bytes(output), 'MAX_STEPS', steps, pos
        op = program[pc]
        steps += 1
        if op == '>':
            pointer += 1
            if pointer == len(tape):
                raise ValueError('tape overflow')
        elif op == '<':
            pointer -= 1
            if pointer < 0:
                raise ValueError('tape underflow')
        elif op == '+':
            tape[pointer] = (tape[pointer] + 1) & 65535
        elif op == '-':
            tape[pointer] = (tape[pointer] - 1) & 65535
        elif op == ',':
            if pos < len(data):
                tape[pointer] = data[pos]
                pos += 1
            else:
                tape[pointer] = eof
        elif op == '.':
            output.append(tape[pointer] & 255)
        elif op == '[' and tape[pointer] == 0:
            pc = jumps[pc]
        elif op == ']' and tape[pointer] != 0:
            pc = jumps[pc]
        pc += 1
    return bytes(output), 'HALTED', steps, pos


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('source', type=Path)
    ap.add_argument('--eof', type=int, default=65535)
    ap.add_argument('--limit', type=int, default=1000000)
    args = ap.parse_args()
    out, status, steps, consumed = run(args.source.read_text(), sys.stdin.buffer.read(), args.eof, args.limit)
    sys.stdout.buffer.write(out)
    print(f'status={status} steps={steps} consumed={consumed}', file=sys.stderr)
    raise SystemExit(0 if status == 'HALTED' else 2)
