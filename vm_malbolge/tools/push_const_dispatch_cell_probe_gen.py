#!/usr/bin/env python3
"""Generate a one-shot PUSH_CONST dispatch + cell-roundtrip probe.

The program classifies the first input byte as 0x00 or 0x01. HALT emits
nothing. The 0x01 handler reads the operand, stores and recovers it through
the established dedicated-cell route, then emits it as an observation.

This is not a multi-instruction MBIR VM: it does not run a later OUT_BYTE
dispatch, loop over a bytecode stream, or validate a truncated operand.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "vm_malbolge/tools"
sys.path.insert(0, str(TOOLS))

import mbir_dispatch_gen  # noqa: E402

BASE = ROOT / "vm_malbolge/src/cell_stack_top.hell"
DEFAULT_OUT = ROOT / "vm_malbolge/src/byte_push_const_dispatch_cell_probe.hell"
LATER_FETCH_OUT = ROOT / "vm_malbolge/src/byte_push_const_later_fetch_probe.hell"


def _private_flags(source: str) -> str:
    """Give the operand-cell routine independent return-phase cells."""
    source = re.sub(r"\bR_FLAG(\d+)\b", r"R_PUSH_FLAG\1", source)
    return re.sub(r"\bFLAG(\d+)\b", r"PUSH_FLAG\1", source)


def generate(base_source: str | None = None, read_later_byte: bool = False) -> str:
    base = BASE.read_text(encoding="utf-8") if base_source is None else base_source
    source = mbir_dispatch_gen.generate([0x00, 0x01])

    # The dispatcher's arithmetic loop counters and the cell route's
    # initialization counters have different return cycles.
    loops = base[base.index("COUNTER2_1:"):base.index(".OFFSET C21")]
    flags = "".join(
        f"PUSH_FLAG{i}:\n\tNop/MovD\n\tJmp\n\n" for i in range(1, 13)
    )
    source = source.replace(".CODE\n", ".CODE\n" + loops + "\n" + flags, 1)

    data_start = base.index(".DATA\n") + len(".DATA\n")
    data_end = base.index("\n{\nnext_char:")
    data = _private_flags(base[data_start:data_end])

    init_start = base.index("ENTRY:\n") + len("ENTRY:\n")
    first_read = base.index("\tIN ?- R_IN\n", init_start)
    init = _private_flags(base[init_start:first_read])

    operand_start = first_read + len("\tIN ?- R_IN\n")
    output = base.rindex("\tOUT ?- R_OUT")
    route = base[operand_start:output]

    # After storing the byte into tmp1..tmp4, bypass the original EOF probe.
    # EOF-on-operand handling is outside this valid-stream probe; this avoids
    # colliding with the dispatcher's own C21 carry landing region.
    restore_anchor = (
        "return_from_tmp4_2:\n"
        "\t// crazy tmp4 has been executed\n"
        "\t// restore xlat2 cycles\n"
        "\tR_CRAZY R_MOVED\n"
    )
    if route.count(restore_anchor) != 1:
        raise ValueError("cell-store anchor changed; update the generator")
    route = route.replace(
        restore_anchor, restore_anchor + "\tMOVED NO_EOF_READ\n", 1
    )
    route = _private_flags(route)

    if source.count("\n{\nENTRY:") != 1:
        raise ValueError("dispatch ENTRY anchor changed; update the generator")
    source = source.replace("\n{\nENTRY:", "\n" + data + "\n{\nENTRY:", 1)
    if source.count("\tIN ?- R_IN\n") < 1:
        raise ValueError("dispatch input anchor missing")
    source = source.replace("\tIN ?- R_IN\n", init + "\tIN ?- R_IN\n", 1)

    old_handler = (
        "dispatch_01:\n"
        "\tROT ('P' << 1) R_ROT\n"
        "\tOUT ?- R_OUT\n"
        "\tHALT"
    )
    new_handler = (
        "dispatch_01:\n"
        "\tIN ?- R_IN\n"
        "\tR_MOVED\n"  # dispatch self-encrypted MOVED; restore before cell route
        + route
        + "\tOUT ?- R_OUT\n\tHALT"
    )
    if source.count(old_handler) != 1:
        raise ValueError("PUSH_CONST handler anchor changed; update the generator")
    source = source.replace(old_handler, new_handler, 1)
    if read_later_byte:
        anchor = (
            "NO_EOF_READ:\n"
            "\t// thats it: no EOF has been read, so we will print out the character we read."
        )
        replacement = (
            "NO_EOF_READ:\n"
            "\t// Preserve the cell value across one later bytecode fetch.\n"
            "\tR_MOVED\n"
            "\tIN ?- R_IN\n"
            "\tR_MOVED\n"
            "\t// thats it: no EOF has been read, so we will print out the character we read."
        )
        if source.count(anchor) != 1:
            raise ValueError("later-fetch anchor changed; update the generator")
        source = source.replace(anchor, replacement, 1)
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--read-next-byte", action="store_true",
        help="consume one later byte before recovering/emitting the cell value",
    )
    args = parser.parse_args()
    if args.read_next_byte and args.out == DEFAULT_OUT:
        args.out = LATER_FETCH_OUT
    result = generate(read_later_byte=args.read_next_byte)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(result, encoding="utf-8", newline="")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
