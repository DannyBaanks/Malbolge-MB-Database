#!/usr/bin/env py
"""mbir_dispatch_gen.py — HeLL generator: N-way byte-VALUE opcode dispatch.

Generates a single-byte, one-shot dispatch program:
    read one opcode byte B -> classify into N handlers (+ echo fallback) -> HALT.

Handler semantics (skeleton only, NOT the full MBIR VM):
     0x00  -> HALT, no output
     other listed opcodes -> emit one marker byte, HALT
     unlisted non-zero   -> echo B verbatim, HALT

With --push-const-out, the 0x01 handler instead consumes one following input
byte and emits it. This is a partial PUSH_CONST/OUT_BYTE probe, not a stack or
fetch-loop implementation.

Architecture (proven in byte_dispatch2.hell): digital_root idioms — ENTRY
double-crazy copy, increment-overflow EOF test, decrement-until-overflow value
discrimination, one carry pad. Decrement exit uses M+1 sites with a trailing
R_SUBROUTINE_FLAGn restore on every non-last site.

Usage:
    py vm_malbolge/tools/mbir_dispatch_gen.py --opcodes 00010203 -o out.hell
    (pairs of hex chars = handler opcodes; first MUST be 00 = HALT)
"""
import argparse

MARKERS = {
    0x01: "P", 0x02: "R", 0x03: "U", 0x04: "L", 0x05: "S",
    0x06: "A", 0x07: "B", 0x08: "M", 0x09: "E", 0x0A: "T",
    0x0B: "G", 0x0C: "J", 0x0D: "F", 0x0E: "C", 0x0F: "V",
    0x10: "O", 0x11: "I",
}


def _code(n_sites):
    flags = "\n".join(
        "SUBROUTINE_FLAG%d:\n\tNop/MovD\n\tJmp\n" % i for i in range(1, n_sites + 1)
    )
    return ".CODE\n" + flags + """
FLAG1:
\tNop/MovD
\tJmp

FLAG2:
\tNop/MovD
\tJmp

FLAG3:
\tNop/MovD
\tJmp

FLAG4:
\tNop/MovD
\tJmp

FLAG5:
\tNop/MovD
\tJmp

FLAG6:
\tNop/MovD
\tJmp

FLAG7:
\tNop/MovD
\tJmp

FLAG8:
\tNop/MovD
\tJmp

FLAG9:
\tNop/MovD
\tJmp

FLAG10:
\tNop/MovD
\tJmp

FLAG11:
\tNop/MovD
\tJmp

FLAG12:
\tNop/MovD
\tJmp

LOOP2:
\tNop/MovD
\tJmp

LOOP2_2:
\tNop/MovD
\tJmp

LOOP2_3:
\tNop/MovD
\tJmp

LOOP5:
\tNop/Nop/Nop/Nop/MovD
\tJmp

NO_MORE_CARRY_FLAG:
\tNop/MovD
\tJmp

MOVED:
\tMovD/Nop
\tJmp

CRAZY:
\tOpr/Nop
\tJmp

ROT:
\tRot/Nop
\tJmp

HALT:
\tHlt

OUT:
\tOut/Nop
\tJmp

IN:
\tIn/Nop
\tJmp

NOP:
\tJmp

@C21 CARRY:
\tRNop
\tRNop
\tJmp
"""


DATA_CELLS = """
.DATA
crazy_value:
\tU_CRAZY value
rot_value:
\tU_ROT value
value:
\tC1
\tFLAG2 return_from_value_2 R_FLAG2
\tFLAG6 return_from_value_6 R_FLAG6
\tFLAG7 return_from_value_7 R_FLAG7
\tFLAG8 return_from_value_8 R_FLAG8
\tFLAG9 return_from_value_9

crazy_value_C1:
\tU_CRAZY value_C1
rot_value_C1:
\tU_ROT value_C1
value_C1:
\tC1
\tFLAG2 return_from_value_C1_2

crazy_save_tmp:
\tU_CRAZY save_tmp
save_tmp:
\tC1
\tFLAG10 return_from_save_tmp_10 R_FLAG10

crazy_save_B:
\tU_CRAZY save_B
save_B:
\tC1
\tFLAG10 return_from_save_B_10 R_FLAG10
\tFLAG11 return_from_save_B_11 R_FLAG11
\tFLAG12 return_from_save_B_12 R_FLAG12

crazy_tmp:
\tU_CRAZY tmp
tmp:
\tC0
\tFLAG1 return_from_tmp_1 R_FLAG1
\tFLAG2 return_from_tmp_2 R_FLAG2
\tFLAG3 return_from_tmp_3 R_FLAG3
\tFLAG4 return_from_tmp_4

crazy_carry:
\tU_CRAZY carry
exec_carry:
\tR_MOVED
carry:
\tCARRY
\tU_NOP execution_not_jumped_to_carry
\tU_NOP carry_was_not_set U_NOP carry_was_set
carry_was_set:
\tMOVED return_carry_was_set
carry_was_not_set:
\tMOVED return_carry_was_not_set
execution_not_jumped_to_carry:
\tFLAG1 return_from_carry_1 R_FLAG1
\tFLAG2 return_from_carry_2 R_FLAG2
return_carry_was_set:
\tFLAG1 return_from_carry_was_set_1 R_FLAG1
\tFLAG2 return_from_carry_was_set_2 R_FLAG2
return_carry_was_not_set:
\tFLAG1 return_from_carry_was_not_set_1 R_FLAG1
\tFLAG2 return_from_carry_was_not_set_2
"""

ENTRY_FRONT = """{
ENTRY:
\t// IN B; value=B via value_C1 (ENTRY idiom). A ends = B.
\tIN ?- R_IN
\tR_FLAG2
\tMOVED crazy_value_C1
}{
return_from_value_C1_2:
\tR_CRAZY R_MOVED
\tR_FLAG2
\tMOVED crazy_value
}{
return_from_value_2:
\tR_CRAZY R_MOVED
\t// save value(=B)->save_B via save_tmp. A ends = B.
\tR_FLAG10
\tMOVED crazy_save_tmp
}{
return_from_save_tmp_10:
\tR_CRAZY R_MOVED
\tR_FLAG10
\tMOVED crazy_save_B
}{
return_from_save_B_10:
\tR_CRAZY R_MOVED
\t// EOF test: inc overflows IFF B=C2.
\tR_SUBROUTINE_FLAG1
\tMOVED increment_value
}{
return_from_increment_value_1:
\tNO_MORE_CARRY_FLAG got_byte
\tMOVED got_eof
}{
got_eof:
\tHALT
}{
got_byte:
\t// value=B+1. dec(site1) -> B.
\tR_SUBROUTINE_FLAG1
\tMOVED decrement_value
}{
return_from_decrement_value_1:
\t// value=B.
"""

FALLBACK = """dispatch_fallback:
\tROT C2 R_ROT
\tR_FLAG11
\tMOVED crazy_save_B
}{
return_from_save_B_11:
\tR_CRAZY R_MOVED
\tROT C2 R_ROT
\tR_FLAG12
\tMOVED crazy_save_B
}{
return_from_save_B_12:
\tR_CRAZY R_MOVED
\tOUT ?- R_OUT
\tHALT
}{
return_from_increment_value_2:
\tHALT
}{"""

INCREMENT_SUB = """increment_value:
\tR_MOVED
\t// kill NO_MORE_CARRY_FLAG
\tNO_MORE_CARRY_FLAG nomorecarrykilled R_NO_MORE_CARRY_FLAG
nomorecarrykilled:
\t// We have to set tmp to C0. It won't contain any trit that is 2, so we can just crazy C1 into tmp.
set_tmp_to_C0:
\tROT C1 R_ROT
\tR_FLAG1 // set return flag
\tMOVED crazy_tmp // crazy C1 into tmp variable to set it to C0

return_from_tmp_1:
\tR_CRAZY
\tROT C2 R_ROT // load C2 to A register
\t// now we have to execute the command sequence
\t//   OPR value
\t//   OPR tmp
\t//   OPR carry
\t// twice.
crazy_loop_increment_value:
\t//the following sequence must be executed twice; label for loop
\tR_MOVED
\tR_FLAG6 // set return flag
\tMOVED crazy_value // crazy A register into tmp variable

return_from_value_6:
\tR_MOVED R_CRAZY
\tR_FLAG2 // set return flag
\tMOVED crazy_tmp // crazy into tmp variable

return_from_tmp_2:
\tR_CRAZY R_MOVED
\tR_FLAG1 // set return flag
\tMOVED crazy_carry // crazy into carry variable

return_from_carry_1:
\tR_CRAZY R_MOVED
\t// check loop condition
\tLOOP2 leave_crazy_loop_increment_value
\tMOVED crazy_loop_increment_value

leave_crazy_loop_increment_value:
\tR_FLAG1
\tMOVED exec_carry

return_from_carry_was_not_set_1:
\tR_NO_MORE_CARRY_FLAG
return_from_carry_was_set_1:
\tR_MOVED
\t// rotate string_ptr until it has been rotated 10 times.
\t// after rotating go to increment or rotate again corresponding to the NO_MORE_CARRY_FLAG
\tR_FLAG7 // set return flag
\tMOVED rot_value // rot string_ptr

return_from_value_7:
\tR_MOVED R_ROT
\t// exit loop after 5 times
\tLOOP5 exit_inner_increment_loop
\tNO_MORE_CARRY_FLAG restore_no_more_carry_flag_and_rotate_value R_NO_MORE_CARRY_FLAG
\tMOVED increment_value

exit_inner_increment_loop:
\t// exit loop after 2 times
\tLOOP2_2 exit_increment_loop
\tNO_MORE_CARRY_FLAG restore_no_more_carry_flag_and_rotate_value R_NO_MORE_CARRY_FLAG
\tMOVED increment_value

restore_no_more_carry_flag_and_rotate_value:
\tR_NO_MORE_CARRY_FLAG
\tMOVED return_from_carry_was_set_1

exit_increment_loop:
\tSUBROUTINE_FLAG1 return_from_increment_value_1 R_SUBROUTINE_FLAG1
\tSUBROUTINE_FLAG2 return_from_increment_value_2
}
"""

DECREMENT_HEADER = """{
decrement_value:
\t// kill NO_MORE_CARRY_FLAG
\tNO_MORE_CARRY_FLAG nomorecarrykilled_2 R_NO_MORE_CARRY_FLAG
nomorecarrykilled_2:
\t// We have to set tmp to C0. It won't contain any trit that is 2, so we can just crazy C1 into tmp.
\tR_MOVED
\tROT C1 R_ROT
\tR_FLAG3 // set return flag
\tMOVED crazy_tmp // crazy C1 into tmp variable to set it to C0

return_from_tmp_3:
\tR_CRAZY
value_load_loop:
\tROT C2 R_ROT
jmp_into_loop_from_behind:
\tR_MOVED
\tR_FLAG8
\tMOVED crazy_value

return_from_value_8:
\tR_CRAZY R_MOVED
\tLOOP2 value_loaded
\tMOVED value_load_loop

value_loaded:
\tLOOP2_2 jump_back_to_behind
\tR_FLAG4 // set return flag
\tMOVED crazy_tmp

return_from_tmp_4:
\tR_CRAZY R_MOVED
\tR_FLAG2 // set return flag
\tMOVED crazy_carry

return_from_carry_2:
\tR_CRAZY R_MOVED
\tMOVED jmp_into_loop_from_behind

jump_back_to_behind:
\tR_FLAG2
\tMOVED exec_carry

return_from_carry_was_not_set_2:
\tR_NO_MORE_CARRY_FLAG
return_from_carry_was_set_2:
\tR_MOVED
\t// rotate string_ptr until it has been rotated 10 times.
\t// after rotating go to increment or rotate again corresponding to the NO_MORE_CARRY_FLAG
\tR_FLAG9 // set return flag
\tMOVED rot_value // rot string_ptr

return_from_value_9:
\tR_MOVED R_ROT
\t// exit loop after 5 times
\tLOOP5 exit_inner_decrement_loop
\tNO_MORE_CARRY_FLAG restore_no_more_carry_flag_and_rotate_value_2 R_NO_MORE_CARRY_FLAG
\tMOVED decrement_value

exit_inner_decrement_loop:
\t// exit loop after 2 times
\tLOOP2_3 exit_decrement_loop
\tNO_MORE_CARRY_FLAG restore_no_more_carry_flag_and_rotate_value_2 R_NO_MORE_CARRY_FLAG
\tMOVED decrement_value

restore_no_more_carry_flag_and_rotate_value_2:
\tR_NO_MORE_CARRY_FLAG
\tMOVED return_from_carry_was_set_2

exit_decrement_loop:
"""


def generate(opcodes, push_const_out=False):
    M = len(opcodes)               # handlers, incl 0x00 HALT
    n_sites = M + 1                # undo + M discriminators
    code = _code(n_sites)

    # --- discriminator chain (value arrives at B via return_from_decrement_value_1) ---
    # site k (k = 2..M+1) decrements; overflow iff B == opcode (k-2).
    chain = []
    for k in range(2, n_sites + 1):
        t = k - 2  # opcode value under test
        chain.append(
            "\t// dec(site%d): value=B-%d (overflow IFF B==0x%02x).\n"
            "\tR_SUBROUTINE_FLAG%d\n\tMOVED decrement_value\n}{\n"
            "return_from_decrement_value_%d:\n"
            % (k, k - 1, t, k, k)
        )
        if t == M - 1:
            chain.append("\tNO_MORE_CARRY_FLAG dispatch_fallback\n\tMOVED dispatch_%02x\n}{\n" % t)
        else:
            chain.append("\tNO_MORE_CARRY_FLAG disc_%d\n\tMOVED dispatch_%02x\n}{\ndisc_%d:\n" % (t + 1, t, t + 1))
    pipeline = "".join(chain)

    # --- handler bodies ---
    handlers = ["dispatch_00:\n\tHALT\n}{\n"]
    for op in opcodes[1:]:
        if push_const_out and op == 0x01:
            # Partial semantic probe: 0x01 consumes its u8 operand and emits it.
            # This is not a stack or fetch-loop implementation.
            handlers.append("dispatch_%02x:\n\tIN ?- R_IN\n\tOUT ?- R_OUT\n\tHALT\n}{\n" % op)
        else:
            m = MARKERS.get(op, "X")
            handlers.append("dispatch_%02x:\n\tROT ('%s' << 1) R_ROT\n\tOUT ?- R_OUT\n\tHALT\n}{\n" % (op, m))

    # --- decrement exit (M+1 sites, trailing R on non-last) ---
    lines = []
    for i in range(1, n_sites + 1):
        if i < n_sites:
            lines.append("\tSUBROUTINE_FLAG%d return_from_decrement_value_%d R_SUBROUTINE_FLAG%d" % (i, i, i))
        else:
            lines.append("\tSUBROUTINE_FLAG%d return_from_decrement_value_%d" % (i, i))
    decrement = DECREMENT_HEADER + "\n".join(lines) + "\n}\n"

    header = ("/* byte_dispatch%d.hell — %d-way byte-VALUE dispatch (GENERATED by "
              "vm_malbolge/tools/mbir_dispatch_gen.py).\n"
              " * Opcodes: %s\n"
              " * 0x00 -> HALT (no output); other listed opcodes -> marker byte; "
              "else -> echo. One-shot byte classifier, NOT the MBIR VM.\n */\n" % (
                  M, M, " ".join("%02x" % o for o in opcodes)))

    return (header + code + DATA_CELLS + ENTRY_FRONT + pipeline +
            "".join(handlers) + FALLBACK + "\n" + INCREMENT_SUB + decrement)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opcodes", default="00010203",
                    help="pairs of hex chars = handler opcodes (first MUST be 00)")
    ap.add_argument("--push-const-out", action="store_true",
                    help="make 0x01 consume one operand and emit it (partial probe)")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()
    s = a.opcodes.strip()
    assert len(s) % 2 == 0, "opcodes must be pairs of hex chars"
    opcodes = [int(s[i:i+2], 16) for i in range(0, len(s), 2)]
    assert opcodes == sorted(set(opcodes)), "opcodes must be ascending + unique"
    assert opcodes[0] == 0x00, "first opcode must be 0x00 (HALT)"
    text = generate(opcodes, push_const_out=a.push_const_out)
    out = a.out or ("byte_dispatch%d.hell" % len(opcodes))
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("wrote %s (%d opcodes, %d sites)" % (out, len(opcodes), len(opcodes) + 1))


if __name__ == "__main__":
    main()
