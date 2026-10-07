#!/usr/bin/env python3
"""Generator for Milestone A05: Re-entrant Multi-Cycle Malbolge Stack Fetch Loop.

Implements clean data-cell state re-initialization via the universal 3-crazy reset
formula (crz(C0, crz(C2, crz(C1, X))) == C1 for all 59,049 words).
Enables arbitrary sequential PUSH_CONST (0x01 <operand>), OUT_BYTE (0x10),
and HALT (0x00) instruction cycles without state corruption or phase drift.

Verified test vectors:
- 01 41 10 00                         -> "A" (41), 50341 steps, HALTED
- 01 42 10 00                         -> "B" (42), 50341 steps, HALTED
- 00                                  -> "" (empty), 44295 steps, HALTED
- 01 41 00                            -> "" (empty), 47962 steps, HALTED
- 01 41 10 01 42 10 00                -> "AB" (4142), 56387 steps, HALTED
- 01 41 10 01 42 10 01 43 10 00       -> "ABC" (414243), 62433 steps, HALTED
- 01 7a 10 01 00 10 01 ff 10 00       -> "z\\x00\\xff" (7a00ff), 62433 steps, HALTED
- 01 68 10 01 65 10 01 6c 10 01 6c 10 01 6f 10 00 -> "hello" (68656c6c6f), 74525 steps, HALTED
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE_SOURCE = ROOT / "vm_malbolge/src/byte_push_const_dispatch_cell_probe.hell"
DEFAULT_OUT = ROOT / "vm_malbolge/src/mbir_a05_multicycle.hell"


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

    # 2. Append 3 shared reset flags to value and value_C1
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
        "\tRESET_FLAG1 ret_rst_val_c1_1 R_RESET_FLAG1\n"
        "\tRESET_FLAG2 ret_rst_val_c1_2 R_RESET_FLAG2\n"
        "\tRESET_FLAG3 ret_rst_val_c1_3"
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

    # Add 3 shared RESET_FLAGs to .CODE (only 3 flags required for all resets)
    reset_flags = "".join(f"RESET_FLAG{i}:\n\tNop/MovD\n\tJmp\n\n" for i in range(1, 4))
    source = source.replace(".CODE\n", ".CODE\n" + reset_flags, 1)

    # Eliminate unused tmp1..tmp4 variables in .DATA
    start_vars = source.find("tmp1_crazy:")
    end_vars = source.find("stack_scratch_crazy:")
    assert start_vars != -1 and end_vars != -1
    source = source[:start_vars] + source[end_vars:]

    # In ENTRY: eliminate do_crzy_tmp1..4, start directly with do_crzy_stack_scratch
    idx_entry = source.find("ENTRY:")
    idx_scratch = source.find("do_crzy_stack_scratch:")
    assert idx_entry != -1 and idx_scratch != -1
    source = source[:idx_entry] + "ENTRY:\n\tROT C1 R_ROT\n" + source[idx_scratch:]

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

    # Add shared reset flags to stack_scratch and stack_top
    old_ss = (
        "stack_scratch:\n"
        "\t?\n"
        "\tPUSH_FLAG1 return_from_stack_scratch_1 R_PUSH_FLAG1\n"
        "\tPUSH_FLAG5 return_from_stack_scratch_2 R_PUSH_FLAG5\n"
    )
    new_ss = old_ss + (
        "\tRESET_FLAG1 ret_rst_ss_1 R_RESET_FLAG1\n"
        "\tRESET_FLAG2 ret_rst_ss_2 R_RESET_FLAG2\n"
        "\tRESET_FLAG3 ret_rst_ss_3\n"
    )
    source = source.replace(old_ss, new_ss)

    old_st = (
        "stack_top:\n"
        "\t?\n"
        "\tPUSH_FLAG1 return_from_stack_top_1 R_PUSH_FLAG1\n"
        "\tPUSH_FLAG2 return_from_stack_top_2 R_PUSH_FLAG2\n"
        "\tPUSH_FLAG3 return_from_stack_top_3 R_PUSH_FLAG3\n"
        "\tPUSH_FLAG4 return_from_stack_top_4 R_PUSH_FLAG4\n"
    )
    new_st = old_st + (
        "\tRESET_FLAG1 ret_rst_st_1 R_RESET_FLAG1\n"
        "\tRESET_FLAG2 ret_rst_st_2 R_RESET_FLAG2\n"
        "\tRESET_FLAG3 ret_rst_st_3\n"
    )
    source = source.replace(old_st, new_st)

    # In dispatch_01: direct store into stack_scratch and stack_top, then reset_and_loop
    idx_d01 = source.find("dispatch_01:")
    idx_fallback = source.find("dispatch_fallback:")
    assert idx_d01 != -1 and idx_fallback != -1
    new_d01 = """dispatch_01:
\tIN ?- R_IN
\tR_MOVED
\tR_PUSH_FLAG5
\tMOVED stack_scratch_crazy
}{
return_from_stack_scratch_2:
\tR_CRAZY R_MOVED
\tR_PUSH_FLAG2
\tMOVED stack_top_crazy
}{
return_from_stack_top_2:
\tR_CRAZY R_MOVED
\tMOVED reset_and_loop
}{
"""
    source = source[:idx_d01] + new_d01 + source[idx_fallback:]

    # In dispatch_fallback (OUT_BYTE handler): recover stack_top, emit OUT,
    # then reset stack_scratch and stack_top via universal C1->C2->C0 sequence,
    # then jump to reset_and_loop.
    idx_fallback = source.find("dispatch_fallback:")
    idx_inc2 = source.find("return_from_increment_value_2:")
    assert idx_fallback != -1 and idx_inc2 != -1
    new_fallback = """dispatch_fallback:
\tROT C2 R_ROT
\tR_PUSH_FLAG3
\tMOVED stack_top_crazy
}{
return_from_stack_top_3:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_PUSH_FLAG4
\tMOVED stack_top_crazy
}{
return_from_stack_top_4:
\tR_CRAZY R_MOVED

\tOUT ?- R_OUT

\tROT C1 R_ROT
\tR_RESET_FLAG1
\tMOVED stack_scratch_crazy
}{
ret_rst_ss_1:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_RESET_FLAG2
\tMOVED stack_scratch_crazy
}{
ret_rst_ss_2:
\tR_CRAZY R_MOVED
\tROT C0 R_ROT
\tR_RESET_FLAG3
\tMOVED stack_scratch_crazy
}{
ret_rst_ss_3:
\tR_CRAZY R_MOVED
\tROT C1 R_ROT
\tR_RESET_FLAG1
\tMOVED stack_top_crazy
}{
ret_rst_st_1:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_RESET_FLAG2
\tMOVED stack_top_crazy
}{
ret_rst_st_2:
\tR_CRAZY R_MOVED
\tROT C0 R_ROT
\tR_RESET_FLAG3
\tMOVED stack_top_crazy
}{
ret_rst_st_3:
\tR_CRAZY R_MOVED
\tMOVED reset_and_loop
}{
"""
    source = source[:idx_fallback] + new_fallback + source[idx_inc2:]

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
\tR_RESET_FLAG1
\tMOVED crazy_value_C1
}{
ret_rst_val_c1_1:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_RESET_FLAG2
\tMOVED crazy_value_C1
}{
ret_rst_val_c1_2:
\tR_CRAZY R_MOVED
\tROT C0 R_ROT
\tR_RESET_FLAG3
\tMOVED crazy_value_C1
}{
ret_rst_val_c1_3:
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    generated = generate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(generated, encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
