#!/usr/bin/env python3
"""Generator for Milestone A05b: 2-Slot LIFO Malbolge Stack Fetch Loop.

Implements a true 2-slot Last-In-First-Out (LIFO) stack machine in pure Malbolge:
- SLOT0_FLAG and SLOT1_FLAG track stack depth dynamically (0 -> 1 -> 2 -> 1 -> 0).
- Slots 0 and 1 each possess isolated scratch and storage cells (`stack_top`, `stack_top_1`).
- Multi-cycle execution is sustained indefinitely via the universal 3-crazy reset
  formula (crz(C0, crz(C2, crz(C1, X))) == C1 for all 59,049 words), multiplexing
  shared flags `RESET_FLAG1..3` across all data cells.

Verified test vectors:
- 01 41 10 00                   -> "A" (41), status HALTED
- 01 42 10 00                   -> "B" (42), status HALTED
- 00                            -> "" (empty), status HALTED
- 01 41 00                      -> "" (empty), status HALTED
- 01 41 10 01 42 10 00          -> "AB" (4142), status HALTED
- 01 41 01 42 10 10 00          -> "BA" (4241, true LIFO inversion), status HALTED
- 01 41 01 42 10 00             -> "B" (42, top of stack after 2 pushes), status HALTED
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE_SOURCE = ROOT / "vm_malbolge/src/byte_push_const_dispatch_cell_probe.hell"
DEFAULT_OUT = ROOT / "vm_malbolge/src/mbir_a05_lifo.hell"


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
        "\tRESET_FLAG1 ret_rst_val_c1_1 R_RESET_FLAG1\n"
        "\tRESET_FLAG2 ret_rst_val_c1_2 R_RESET_FLAG2\n"
        "\tRESET_FLAG3 ret_rst_val_c1_3"
    )
    source = source.replace(old_v, new_v).replace(old_c1, new_c1)

    # 3. Remove unused save_tmp and save_B definitions from .DATA
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

    # 4. Add FLAG3 to execution_not_jumped_to_carry for carry reset
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

    # 5. Add SLOT0_FLAG, SLOT1_FLAG and 3 shared RESET_FLAGs to .CODE
    code_flags = (
        "SLOT0_FLAG:\n\tNop/MovD\n\tJmp\n\n"
        "SLOT1_FLAG:\n\tNop/MovD\n\tJmp\n\n"
        + "".join(f"RESET_FLAG{i}:\n\tNop/MovD\n\tJmp\n\n" for i in range(1, 4))
    )
    source = source.replace(".CODE\n", ".CODE\n" + code_flags, 1)

    # 6. Eliminate unused tmp1..tmp4 variables in .DATA
    start_vars = source.find("tmp1_crazy:")
    end_vars = source.find("stack_scratch_crazy:")
    assert start_vars != -1 and end_vars != -1
    source = source[:start_vars] + source[end_vars:]

    # 7. In ENTRY: eliminate do_crzy_tmp1..4, start directly with do_crzy_stack_scratch
    idx_entry = source.find("ENTRY:")
    idx_scratch = source.find("do_crzy_stack_scratch:")
    assert idx_entry != -1 and idx_scratch != -1
    source = source[:idx_entry] + "ENTRY:\n\tROT C1 R_ROT\n" + source[idx_scratch:]

    # 8. Add initialization of stack_scratch_1 and stack_top_1 in ENTRY:
    old_init_end = (
        "return_from_stack_top_1:\n"
        "\tR_CRAZY R_MOVED\n"
        "\tCOUNTER2_1 do_crzy_stack_top\n"
        "\n"
        "\t// now we prepared tmp1, tmp2, tmp3, tmp4 AND stack_top.\n"
        "\t// so we can read in a character now.\n"
        "\tIN ?- R_IN"
    )
    new_init_end = """return_from_stack_top_1:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_crzy_stack_top

do_crzy_ss1:
\tR_PUSH_FLAG1
\tMOVED stack_scratch_1_crazy
}{
return_from_ss1_1:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_crzy_ss1

do_crzy_st1:
\tR_PUSH_FLAG1
\tMOVED stack_top_1_crazy
}{
return_from_st1_1:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_crzy_st1

\tMOVED next_opcode
}{
next_opcode:
\tR_MOVED
\tIN ?- R_IN"""
    source = source.replace(old_init_end, new_init_end)

    # 9. Bypass save_tmp and save_B in opcode fetch
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

    # 10. Add shared reset flags to stack_scratch and stack_top (slot 0)
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

    # 11. Add stack_scratch_1 and stack_top_1 (slot 1) to .DATA
    slot1_vars = """
stack_scratch_1_crazy:
\tU_CRAZY stack_scratch_1
stack_scratch_1:
\t?
\tPUSH_FLAG1 return_from_ss1_1 R_PUSH_FLAG1
\tPUSH_FLAG5 return_from_ss1_2 R_PUSH_FLAG5
\tRESET_FLAG1 ret_rst_ss1_1 R_RESET_FLAG1
\tRESET_FLAG2 ret_rst_ss1_2 R_RESET_FLAG2
\tRESET_FLAG3 ret_rst_ss1_3

stack_top_1_crazy:
\tU_CRAZY stack_top_1
stack_top_1:
\t?
\tPUSH_FLAG1 return_from_st1_1 R_PUSH_FLAG1
\tPUSH_FLAG2 return_from_st1_2 R_PUSH_FLAG2
\tPUSH_FLAG3 return_from_st1_3 R_PUSH_FLAG3
\tPUSH_FLAG4 return_from_st1_4 R_PUSH_FLAG4
\tRESET_FLAG1 ret_rst_st1_1 R_RESET_FLAG1
\tRESET_FLAG2 ret_rst_st1_2 R_RESET_FLAG2
\tRESET_FLAG3 ret_rst_st1_3
"""
    source = source.replace("stack_top_crazy:", slot1_vars + "\nstack_top_crazy:")

    # 12. In dispatch_01: implement 2-slot LIFO push logic
    # When SLOT0_FLAG is Nop: falls through to push slot 0 (SLOT0_FLAG becomes MovD).
    # When SLOT0_FLAG is MovD: jumps to push_slot_1 (SLOT0_FLAG becomes Nop).
    #   In push_slot_1: R_SLOT0_FLAG restores it to MovD, R_SLOT1_FLAG sets SLOT1_FLAG to MovD!
    idx_d01 = source.find("dispatch_01:")
    idx_fallback = source.find("dispatch_fallback:")
    assert idx_d01 != -1 and idx_fallback != -1
    new_d01 = """dispatch_01:
\tIN ?- R_IN
\tR_MOVED
\tSLOT0_FLAG push_slot_1
\t// Slot 0 (depth 0 -> 1):
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
push_slot_1:
\t// Slot 1 (depth 1 -> 2):
\tR_SLOT0_FLAG
\tR_SLOT1_FLAG
\tR_PUSH_FLAG5
\tMOVED stack_scratch_1_crazy
}{
return_from_ss1_2:
\tR_CRAZY R_MOVED
\tR_PUSH_FLAG2
\tMOVED stack_top_1_crazy
}{
return_from_st1_2:
\tR_CRAZY R_MOVED
\tMOVED reset_and_loop
}{
"""
    source = source[:idx_d01] + new_d01 + source[idx_fallback:]

    # 13. In dispatch_fallback (OUT_BYTE handler): implement 2-slot LIFO pop logic
    # When SLOT1_FLAG is MovD: jumps to pop_slot_1 (SLOT1_FLAG becomes Nop).
    # When SLOT1_FLAG is Nop: falls through to pop slot 0 (SLOT1_FLAG becomes MovD, restored to Nop).
    # In pop_slot_0: R_SLOT0_FLAG restores SLOT0_FLAG to Nop.
    idx_fallback = source.find("dispatch_fallback:")
    idx_inc2 = source.find("return_from_increment_value_2:")
    assert idx_fallback != -1 and idx_inc2 != -1
    new_fallback = """dispatch_fallback:
\tSLOT1_FLAG pop_slot_1
\t// Fall-through: Slot 1 empty, pop Slot 0
\tR_SLOT1_FLAG
\tR_SLOT0_FLAG
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

\t// Reset slot 0 to C1:
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
pop_slot_1:
\t// Pop Slot 1:
\tROT C2 R_ROT
\tR_PUSH_FLAG3
\tMOVED stack_top_1_crazy
}{
return_from_st1_3:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_PUSH_FLAG4
\tMOVED stack_top_1_crazy
}{
return_from_st1_4:
\tR_CRAZY R_MOVED

\tOUT ?- R_OUT

\t// Reset slot 1 to C1:
\tROT C1 R_ROT
\tR_RESET_FLAG1
\tMOVED stack_scratch_1_crazy
}{
ret_rst_ss1_1:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_RESET_FLAG2
\tMOVED stack_scratch_1_crazy
}{
ret_rst_ss1_2:
\tR_CRAZY R_MOVED
\tROT C0 R_ROT
\tR_RESET_FLAG3
\tMOVED stack_scratch_1_crazy
}{
ret_rst_ss1_3:
\tR_CRAZY R_MOVED
\tROT C1 R_ROT
\tR_RESET_FLAG1
\tMOVED stack_top_1_crazy
}{
ret_rst_st1_1:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_RESET_FLAG2
\tMOVED stack_top_1_crazy
}{
ret_rst_st1_2:
\tR_CRAZY R_MOVED
\tROT C0 R_ROT
\tR_RESET_FLAG3
\tMOVED stack_top_1_crazy
}{
ret_rst_st1_3:
\tR_CRAZY R_MOVED
\tMOVED reset_and_loop
}{
"""
    source = source[:idx_fallback] + new_fallback + source[idx_inc2:]

    # 14. Shared reset_and_loop block: resets value, value_C1, and carry, then jumps to next_opcode
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
