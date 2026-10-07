#!/usr/bin/env python3
"""Generate the A04 PUSH_CONST operand storage probe from the proven cell probe.

The probe assumes the first input byte is opcode 0x01. It consumes that byte,
then runs the existing cell_stack_top input/store/recover path on the operand.
There is no opcode classifier or later OUT_BYTE dispatch in this probe.
"""
from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "vm_malbolge/src/cell_stack_top.hell"
DEFAULT_OUT = ROOT / "vm_malbolge/src/byte_push_const_cell_probe.hell"

ANCHOR = (
    "\t// now we prepared tmp1, tmp2, tmp3, tmp4 AND stack_top.\n"
    "\t// so we can read in a character now.\n"
    "\tIN ?- R_IN\n"
)
REPLACEMENT = (
    "\t// A04 probe assumption: the next byte is opcode 0x01 (PUSH_CONST).\n"
    "\tIN ?- R_IN\n"
    "\t// The existing verified path stores and recovers the operand byte.\n"
    "\tIN ?- R_IN\n"
)


def generate(base_source: str) -> str:
    if base_source.count(ANCHOR) != 1:
        raise ValueError("cell_stack_top source anchor changed; update this generator")
    return base_source.replace(ANCHOR, REPLACEMENT, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    source = generate(BASE.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(source, encoding="utf-8", newline="")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
