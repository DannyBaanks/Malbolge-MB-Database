#!/usr/bin/env python3
"""Generator for Milestone A04 acceptance gate:
One-deep Malbolge stack fetch loop for PUSH_CONST (0x01 <operand>),
OUT_BYTE (0x10), and HALT (0x00).

Acceptance gate vectors:
- 01 41 10 00 -> output "A" (0x41), status HALTED
- 01 42 10 00 -> output "B" (0x42), status HALTED
- 00          -> output "" (empty), status HALTED
- 01 41 00    -> output "" (empty), status HALTED
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE_SOURCE = ROOT / "vm_malbolge/src/byte_push_const_dispatch_cell_probe.hell"
DEFAULT_OUT = ROOT / "vm_malbolge/src/mbir_a04_gate.hell"


def generate() -> str:
    source = PROBE_SOURCE.read_text(encoding="utf-8")

    # 1. Update subroutine exit to restore ALL subroutine flags symmetrically
    old_dec_exit = (
        "\tSUBROUTINE_FLAG1 return_from_decrement_value_1 R_SUBROUTINE_FLAG1\n"
        "\tSUBROUTINE_FLAG2 return_from_decrement_value_2 R_SUBROUTINE_FLAG2\n"
        "\tSUBROUTINE_FLAG3 return_from_decrement_value_3"
    )
    new_dec_exit = (
        "\tSUBROUTINE_FLAG1 return_from_decrement_value_1 R_SUBROUTINE_FLAG1\n"
        "\tSUBROUTINE_FLAG2 return_from_decrement_value_2 R_SUBROUTINE_FLAG2\n"
        "\tSUBROUTINE_FLAG3 return_from_decrement_value_3 R_SUBROUTINE_FLAG3"
    )
    source = source.replace(old_dec_exit, new_dec_exit)

    # 2. Append reset flags to value and value_C1
    old_v = (
        "value:\n"
        "\tC1\n"
        "\tFLAG2 return_from_value_2 R_FLAG2\n"
        "\tFLAG6 return_from_value_6 R_FLAG6\n"
        "\tFLAG7 return_from_value_7 R_FLAG7\n"
        "\tFLAG8 return_from_value_8 R_FLAG8\n"
        "\tFLAG9 return_from_value_9"
    )
    new_v = (
        "value:\n"
        "\tC1\n"
        "\tFLAG2 return_from_value_2 R_FLAG2\n"
        "\tFLAG6 return_from_value_6 R_FLAG6\n"
        "\tFLAG7 return_from_value_7 R_FLAG7\n"
        "\tFLAG8 return_from_value_8 R_FLAG8\n"
        "\tFLAG9 return_from_value_9 R_FLAG9\n"
        "\tRESET_FLAG1 ret_rst_val_1 R_RESET_FLAG1\n"
        "\tRESET_FLAG2 ret_rst_val_2 R_RESET_FLAG2\n"
        "\tRESET_FLAG3 ret_rst_val_3"
    )

    old_c1 = (
        "value_C1:\n"
        "\tC1\n"
        "\tFLAG2 return_from_value_C1_2"
    )
    new_c1 = (
        "value_C1:\n"
        "\tC1\n"
        "\tFLAG2 return_from_value_C1_2 R_FLAG2\n"
        "\tRESET_FLAG4 ret_rst_val_c1_4 R_RESET_FLAG4\n"
        "\tRESET_FLAG5 ret_rst_val_c1_5 R_RESET_FLAG5\n"
        "\tRESET_FLAG6 ret_rst_val_c1_6"
    )
    source = source.replace(old_v, new_v).replace(old_c1, new_c1)

    # Remove unused save_tmp and save_B definitions from .DATA
    old_saves = (
        "crazy_save_tmp:\n"
        "\tU_CRAZY save_tmp\n"
        "save_tmp:\n"
        "\tC1\n"
        "\tFLAG10 return_from_save_tmp_10 R_FLAG10\n"
        "\n"
        "crazy_save_B:\n"
        "\tU_CRAZY save_B\n"
        "save_B:\n"
        "\tC1\n"
        "\tFLAG10 return_from_save_B_10 R_FLAG10\n"
        "\tFLAG11 return_from_save_B_11 R_FLAG11\n"
        "\tFLAG12 return_from_save_B_12 R_FLAG12\n"
    )
    source = source.replace(old_saves, "")

    # Add FLAG3 to execution_not_jumped_to_carry for carry reset
    old_exec_carry = (
        "execution_not_jumped_to_carry:\n"
        "\tFLAG1 return_from_carry_1 R_FLAG1\n"
        "\tFLAG2 return_from_carry_2 R_FLAG2"
    )
    new_exec_carry = (
        "execution_not_jumped_to_carry:\n"
        "\tFLAG1 return_from_carry_1 R_FLAG1\n"
        "\tFLAG2 return_from_carry_2 R_FLAG2\n"
        "\tFLAG3 return_from_carry_reset R_FLAG3"
    )
    source = source.replace(old_exec_carry, new_exec_carry)

    # Add RESET_FLAG1..6 to .CODE
    reset_flags = "".join(f"RESET_FLAG{i}:\n\tNop/MovD\n\tJmp\n\n" for i in range(1, 7))
    source = source.replace(".CODE\n", ".CODE\n" + reset_flags, 1)

    # At the end of one-time init: jump to next_opcode symmetrically
    old_init_end = (
        "return_from_stack_top_1:\n"
        "\tR_CRAZY R_MOVED\n"
        "\tCOUNTER2_1 do_crzy_stack_top\n"
        "\n"
        "\t// now we prepared tmp1, tmp2, tmp3, tmp4 AND stack_top.\n"
        "\t// so we can read in a character now.\n"
        "\tIN ?- R_IN"
    )
    new_init_end = (
        "return_from_stack_top_1:\n"
        "\tR_CRAZY R_MOVED\n"
        "\tCOUNTER2_1 do_crzy_stack_top\n"
        "\tMOVED next_opcode\n"
        "}{\n"
        "next_opcode:\n"
        "\tR_MOVED\n"
        "\tIN ?- R_IN"
    )
    source = source.replace(old_init_end, new_init_end)

    # Bypass save_tmp and save_B in opcode fetch
    old_save_chain = (
        "return_from_value_2:\n"
        "\tR_CRAZY R_MOVED\n"
        "\t// save value(=B)->save_B via save_tmp. A ends = B.\n"
        "\tR_FLAG10\n"
        "\tMOVED crazy_save_tmp\n"
        "}{\n"
        "return_from_save_tmp_10:\n"
        "\tR_CRAZY R_MOVED\n"
        "\tR_FLAG10\n"
        "\tMOVED crazy_save_B\n"
        "}{\n"
        "return_from_save_B_10:\n"
        "\tR_CRAZY R_MOVED\n"
        "\t// EOF test: inc overflows IFF B=C2.\n"
        "\tR_SUBROUTINE_FLAG1\n"
        "\tMOVED increment_value"
    )
    new_save_chain = (
        "return_from_value_2:\n"
        "\tR_CRAZY R_MOVED\n"
        "\t// EOF test: inc overflows IFF B=C2.\n"
        "\tR_SUBROUTINE_FLAG1\n"
        "\tMOVED increment_value"
    )
    source = source.replace(old_save_chain, new_save_chain)

    # In dispatch_01: after operand store into stack_top, jump to reset_and_loop
    store_end = "return_from_stack_top_2:\n\tR_CRAZY R_MOVED\n"
    store_idx = source.find(store_end)
    assert store_idx != -1

    recover_and_halt = source[store_idx + len(store_end):source.find("dispatch_fallback:")]
    source = (
        source[:store_idx + len(store_end)]
        + "\tMOVED reset_and_loop\n}{\n"
        + source[source.find("dispatch_fallback:"):]
    )

    # In dispatch_fallback (OUT_BYTE handler): recover stack_top, emit OUT, jump to reset_and_loop
    old_fallback = (
        "dispatch_fallback:\n"
        "\tROT C2 R_ROT\n"
        "\tR_FLAG11\n"
        "\tMOVED crazy_save_B\n"
        "}{\n"
        "return_from_save_B_11:\n"
        "\tR_CRAZY R_MOVED\n"
        "\tROT C2 R_ROT\n"
        "\tR_FLAG12\n"
        "\tMOVED crazy_save_B\n"
        "}{\n"
        "return_from_save_B_12:\n"
        "\tR_CRAZY R_MOVED\n"
        "\tOUT ?- R_OUT\n"
        "\tHALT\n"
        "}{"
    )
    new_fallback_body = recover_and_halt.replace("\tHALT\n}{\n", "\tMOVED reset_and_loop\n}{\n")
    new_fallback = "dispatch_fallback:\n" + new_fallback_body
    source = source.replace(old_fallback, new_fallback)

    # Shared reset_and_loop block: resets value, value_C1, and carry, then jumps to next_opcode
    reset_block = """
reset_and_loop:
\tR_MOVED
\tROT C1 R_ROT
\tR_RESET_FLAG1
\tMOVED crazy_value
}{
ret_rst_val_1:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_RESET_FLAG2
\tMOVED crazy_value
}{
ret_rst_val_2:
\tR_CRAZY R_MOVED
\tROT C0 R_ROT
\tR_RESET_FLAG3
\tMOVED crazy_value
}{
ret_rst_val_3:
\tR_CRAZY R_MOVED
\tROT C1 R_ROT
\tR_RESET_FLAG4
\tMOVED crazy_value_C1
}{
ret_rst_val_c1_4:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_RESET_FLAG5
\tMOVED crazy_value_C1
}{
ret_rst_val_c1_5:
\tR_CRAZY R_MOVED
\tROT C0 R_ROT
\tR_RESET_FLAG6
\tMOVED crazy_value_C1
}{
ret_rst_val_c1_6:
\tR_CRAZY R_MOVED
\tROT 3 R_ROT
\tR_FLAG3
\tMOVED crazy_carry
}{
return_from_carry_reset:
\tR_CRAZY R_MOVED
\tMOVED next_opcode
}{
"""
    old_inc2 = "return_from_increment_value_2:\n\tHALT\n}{\n"
    source = source.replace(old_inc2, old_inc2 + reset_block)

    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    content = generate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(content, encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
