#!/usr/bin/env python3
"""Compile one validated BF cat idiom by selecting an authenticated template.

This intentionally supports only the exact BF operation sequence ,+[-.,+],
with 16-bit wrapping cells and EOF=65535. It is a template compiler, not a
BF virtual machine, and does not reproduce BF tape state inside Malbolge.
"""
import argparse
import hashlib
from pathlib import Path

EXPECTED = {
    '0d298645bcabd8c832c6bbad0769124828a8805bb46cc4644e35added50334f1',
    'c7b0aef98363242607c1fb13aa964fd412da057bcea04105f7e9b8559e986d13',
}
OPS = frozenset('><+-.,[]')


def compile_cat(source: str, template: bytes, cell_bits: int, eof: int) -> bytes:
    operations = ''.join(ch for ch in source if ch in OPS)
    if operations != ',+[-.,+]':
        raise ValueError('unsupported Brainfuck program; expected ,+[-.,+]')
    if cell_bits != 16 or eof != 65535:
        raise ValueError('cat idiom requires 16-bit wrapping cells and EOF 65535')
    if hashlib.sha256(template).hexdigest() not in EXPECTED:
        raise ValueError('Malbolge reference template SHA-256 mismatch')
    return template


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('--template', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--cell-bits', type=int, default=16)
    ap.add_argument('--eof', type=int, default=65535)
    args = ap.parse_args()
    try:
        artifact = compile_cat(args.source.read_text(), args.template.read_bytes(), args.cell_bits, args.eof)
        with args.output.open('xb') as output:
            output.write(artifact)
    except (OSError, ValueError) as exc:
        ap.exit(1, f'compilation failed: {exc}\n')
    print(f'compiled bytes={len(artifact)} sha256={hashlib.sha256(artifact).hexdigest()}')


if __name__ == '__main__':
    main()
