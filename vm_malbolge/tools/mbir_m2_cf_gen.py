#!/usr/bin/env python3
"""Stored-program control-flow probe.

11-byte MBIR image. The decisive bytes (prog_0, prog_1, prog_4, prog_6,
prog_7, prog_8) are stored from stdin. The other five positions are read
and ignored so the layout stays aligned. Each stored byte uses its own
scratch cell, left dirty. Opcode in prog_0 is classified by decrement:

  0x0C JUMP  -> emit prog_6 (the immediate after the skipped HALT)
  0x01       -> prog_1 == 0 emits prog_8 (JZ taken);
                prog_1 == 1 emits prog_7 (JZ not taken / JNZ fall-through)
  0x0E CALL  -> emit prog_8 then prog_4 (callee, then the byte after return)

Scope is these shapes. Not a general PC and not a call stack deeper than one.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELL_PATH = ROOT / "vm_malbolge/src/mbir_m2_cf.hell"
MB_PATH = ROOT / "vm_malbolge/src/mbir_m2_cf.mb"
N = 11

DECREMENT_HEAD = r"""
decrement_value:
	NO_MORE_CARRY_FLAG nomorecarrykilled_2 R_NO_MORE_CARRY_FLAG
nomorecarrykilled_2:
	R_MOVED
	ROT C1 R_ROT
	R_FLAG_DEC_TMP3
	MOVED crazy_tmp

return_from_tmp_3:
	R_CRAZY
value_load_loop:
	ROT C2 R_ROT
jmp_into_loop_from_behind:
	R_MOVED
	R_FLAG_DEC_VAL8
	MOVED crazy_value

return_from_value_8:
	R_CRAZY R_MOVED
	LOOP2 value_loaded
	MOVED value_load_loop

value_loaded:
	LOOP2_2 jump_back_to_behind
	R_FLAG_DEC_TMP4
	MOVED crazy_tmp

return_from_tmp_4:
	R_CRAZY R_MOVED
	R_FLAG_DEC_CARRY2
	MOVED crazy_carry

return_from_carry_2:
	R_CRAZY R_MOVED
	MOVED jmp_into_loop_from_behind

jump_back_to_behind:
	R_FLAG_DEC_CARRY2
	MOVED exec_carry

return_from_carry_was_not_set_2:
	R_NO_MORE_CARRY_FLAG
return_from_carry_was_set_2:
	R_MOVED
	R_FLAG_DEC_VAL9
	MOVED rot_value

return_from_value_9:
	R_MOVED R_ROT
	LOOP5 exit_inner_decrement_loop
	NO_MORE_CARRY_FLAG restore_no_more_carry_flag_and_rotate_value_2 R_NO_MORE_CARRY_FLAG
	MOVED decrement_value

exit_inner_decrement_loop:
	LOOP2_3 exit_decrement_loop
	NO_MORE_CARRY_FLAG restore_no_more_carry_flag_and_rotate_value_2 R_NO_MORE_CARRY_FLAG
	MOVED decrement_value

restore_no_more_carry_flag_and_rotate_value_2:
	R_NO_MORE_CARRY_FLAG
	MOVED return_from_carry_was_set_2

exit_decrement_loop:
"""


def flag(name: str) -> str:
    return f"{name}:\n\tNop/MovD\n\tJmp\n\n"


def dec_chain(prefix: str, first_sf: int, steps: int, routes: dict[int, str]) -> str:
    parts = []
    for k in range(1, steps + 1):
        dest = routes.get(k, "halt_now")
        cont = "halt_now" if k == steps else f"{prefix}_c{k}"
        parts.append(
            f"ret_{prefix}_{k}:\n"
            f"\tNO_MORE_CARRY_FLAG {cont}\n"
            f"\tMOVED {dest}\n"
            "}{"
        )
        if k != steps:
            parts.append(
                f"{cont}:\n"
                f"\tR_SF{first_sf + k}\n"
                "\tMOVED decrement_value\n"
                "}{"
            )
    return "\n".join(parts)


def generate() -> str:
    # Bytes the vectors actually branch on. The other positions are consumed
    # from stdin and ignored, so the 11-byte shape stays aligned.
    store_at = (0, 1, 4, 6, 7, 8)
    names = [f"SF{i}" for i in range(1, 18)]
    names += [
        "FLAG_SCR",
        "FLAG_STORE",
        "FLAG_VR1",
        "FLAG_VR2",
        "FLAG_VR3",
        "FLAG_READ_A",
        "FLAG_READ_B",
        "FLAG_CP1_C",
        "FLAG_CP1_V",
        "FLAG_CP3_C",
        "FLAG_CP3_V",
        "FLAG_PATH_CALL",
        "FLAG_DEC_TMP3",
        "FLAG_DEC_TMP4",
        "FLAG_DEC_VAL8",
        "FLAG_DEC_VAL9",
        "FLAG_DEC_CARRY2",
    ]
    code = "".join(flag(n) for n in names)

    scratch_blocks = []
    prog_blocks = []
    for i in store_at:
        scratch_blocks.append(
            "\n".join(
                [
                    f"scratch_{i}_crazy:",
                    f"\tU_CRAZY scratch_{i}",
                    f"scratch_{i}:",
                    "\tC1",
                    f"\tFLAG_SCR ret_scr_{i} R_FLAG_SCR",
                ]
            )
        )
        prog_blocks.append(
            "\n".join(
                [
                    f"prog_{i}_crazy:",
                    f"\tU_CRAZY prog_{i}",
                    f"prog_{i}:",
                    "\tC1",
                    f"\tFLAG_STORE ret_p{i} R_FLAG_STORE",
                    f"\tFLAG_READ_A ret_p{i}_a R_FLAG_READ_A",
                    f"\tFLAG_READ_B ret_p{i}_b R_FLAG_READ_B",
                ]
            )
        )

    # One scratch per stored byte, each left dirty. The next load falls
    # through after the store, so there is no NEXT ladder and no reset.
    load_lines = ["{", "ENTRY:"]
    for i in range(N):
        load_lines.append("\tIN ?- R_IN")
        if i not in store_at:
            continue
        load_lines.extend(
            [
                "\tR_FLAG_SCR",
                f"\tMOVED scratch_{i}_crazy",
                "}{",
                f"ret_scr_{i}:",
                "\tR_CRAZY R_MOVED",
                "\tR_FLAG_STORE",
                f"\tMOVED prog_{i}_crazy",
                "}{",
                f"ret_p{i}:",
                "\tR_CRAZY R_MOVED",
            ]
        )
    load_lines.append("start_dispatch:")
    load_text = "\n".join(load_lines)

    op_chain = dec_chain("op", 1, 15, {1: "halt_now", 2: "family_01", 13: "do_jmp", 15: "do_call"})
    jz_chain = dec_chain("jz", 16, 2, {1: "out_taken", 2: "out_not"})
    ladder = "\n".join(
        [f"\tSF{i} ret_op_{i} R_SF{i}" for i in range(1, 16)]
        + [f"\tSF{15 + i} ret_jz_{i} R_SF{15 + i}" for i in range(1, 3)]
    )

    value_ops = "\n".join(
        [
            "\tFLAG_VR1 ret_vr1 R_FLAG_VR1",
            "\tFLAG_VR2 ret_vr2 R_FLAG_VR2",
            "\tFLAG_VR3 ret_vr3 R_FLAG_VR3",
            "\tFLAG_CP1_V ret_cp1_v R_FLAG_CP1_V",
            "\tFLAG_CP3_V ret_cp3_v R_FLAG_CP3_V",
            "\tFLAG_DEC_VAL8 return_from_value_8 R_FLAG_DEC_VAL8",
            "\tFLAG_DEC_VAL9 return_from_value_9",
        ]
    )
    c1_ops = "\n".join(
        [
            "\tFLAG_VR1 ret_vrc1 R_FLAG_VR1",
            "\tFLAG_VR2 ret_vrc2 R_FLAG_VR2",
            "\tFLAG_VR3 ret_vrc3 R_FLAG_VR3",
            "\tFLAG_CP1_C ret_cp1_c R_FLAG_CP1_C",
            "\tFLAG_CP3_C ret_cp3_c R_FLAG_CP3_C",
        ]
    )

    return f"""/* mbir_m2_cf.hell — JUMP / JZ / CALL from a stored 11-byte program. */
.CODE
MOVED:
	MovD/Nop
	Jmp

ROT:
	Rot/Nop
	Jmp

IN:
	In/Nop
	Jmp

OUT:
	Out/Nop
	Jmp

CRAZY:
	Opr/Nop
	Jmp

HALT:
	Hlt

NOP:
	Jmp

LOOP2:
	Nop/MovD
	Jmp

LOOP2_2:
	Nop/MovD
	Jmp

LOOP2_3:
	Nop/MovD
	Jmp

LOOP5:
	Nop/Nop/Nop/Nop/MovD
	Jmp

NO_MORE_CARRY_FLAG:
	Nop/MovD
	Jmp

@C21 CARRY:
	RNop
	RNop
	Jmp

{code}
.DATA
crazy_value:
	U_CRAZY value
rot_value:
	U_ROT value
value:
	C1
{value_ops}

crazy_value_C1:
	U_CRAZY value_C1
value_C1:
	C1
{c1_ops}

crazy_tmp:
	U_CRAZY tmp
tmp:
	C0
	FLAG_DEC_TMP3 return_from_tmp_3 R_FLAG_DEC_TMP3
	FLAG_DEC_TMP4 return_from_tmp_4

crazy_carry:
	U_CRAZY carry
exec_carry:
	R_MOVED
carry:
	CARRY
	U_NOP execution_not_jumped_to_carry
	U_NOP carry_was_not_set U_NOP carry_was_set
carry_was_set:
	MOVED return_carry_was_set
carry_was_not_set:
	MOVED return_carry_was_not_set
execution_not_jumped_to_carry:
	FLAG_DEC_CARRY2 return_from_carry_2 R_FLAG_DEC_CARRY2
return_carry_was_set:
	FLAG_DEC_CARRY2 return_from_carry_was_set_2 R_FLAG_DEC_CARRY2
return_carry_was_not_set:
	FLAG_DEC_CARRY2 return_from_carry_was_not_set_2

{chr(10)+chr(10).join(scratch_blocks)}

{chr(10)+chr(10).join(prog_blocks)}

{load_text}
	ROT C2 R_ROT
	R_FLAG_READ_A
	MOVED prog_0_crazy
}}{{
ret_p0_a:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_B
	MOVED prog_0_crazy
}}{{
ret_p0_b:
	R_CRAZY R_MOVED
	R_FLAG_CP1_C
	MOVED crazy_value_C1
}}{{
ret_cp1_c:
	R_CRAZY R_MOVED
	R_FLAG_CP1_V
	MOVED crazy_value
}}{{
ret_cp1_v:
	R_CRAZY R_MOVED
	R_SF1
	MOVED decrement_value
}}{{
{op_chain}
family_01:
	R_MOVED
	MOVED reset_values
}}{{
do_jmp:
	R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_A
	MOVED prog_6_crazy
}}{{
do_call:
	R_MOVED
	R_FLAG_PATH_CALL
	ROT C2 R_ROT
	R_FLAG_READ_A
	MOVED prog_8_crazy
}}{{
reset_values:
	R_MOVED
	ROT C1 R_ROT
	R_FLAG_VR1
	MOVED crazy_value
}}{{
ret_vr1:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_VR2
	MOVED crazy_value
}}{{
ret_vr2:
	R_CRAZY R_MOVED
	ROT C0 R_ROT
	R_FLAG_VR3
	MOVED crazy_value
}}{{
ret_vr3:
	R_CRAZY R_MOVED
	ROT C1 R_ROT
	R_FLAG_VR1
	MOVED crazy_value_C1
}}{{
ret_vrc1:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_VR2
	MOVED crazy_value_C1
}}{{
ret_vrc2:
	R_CRAZY R_MOVED
	ROT C0 R_ROT
	R_FLAG_VR3
	MOVED crazy_value_C1
}}{{
ret_vrc3:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_A
	MOVED prog_1_crazy
}}{{
ret_p1_a:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_B
	MOVED prog_1_crazy
}}{{
ret_p1_b:
	R_CRAZY R_MOVED
	R_FLAG_CP3_C
	MOVED crazy_value_C1
}}{{
ret_cp3_c:
	R_CRAZY R_MOVED
	R_FLAG_CP3_V
	MOVED crazy_value
}}{{
ret_cp3_v:
	R_CRAZY R_MOVED
	R_SF16
	MOVED decrement_value
}}{{
{jz_chain}
out_taken:
	R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_A
	MOVED prog_8_crazy
}}{{
out_not:
	R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_A
	MOVED prog_7_crazy
}}{{
ret_p6_a:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_B
	MOVED prog_6_crazy
}}{{
ret_p6_b:
	R_CRAZY R_MOVED
	OUT ?- R_OUT
	HALT
}}{{
ret_p7_a:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_B
	MOVED prog_7_crazy
}}{{
ret_p7_b:
	R_CRAZY R_MOVED
	OUT ?- R_OUT
	HALT
}}{{
ret_p8_a:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_B
	MOVED prog_8_crazy
}}{{
ret_p8_b:
	R_CRAZY R_MOVED
	OUT ?- R_OUT
	FLAG_PATH_CALL out_caller
	HALT
}}{{
out_caller:
	ROT C2 R_ROT
	R_FLAG_READ_A
	MOVED prog_4_crazy
}}{{
ret_p4_a:
	R_CRAZY R_MOVED
	ROT C2 R_ROT
	R_FLAG_READ_B
	MOVED prog_4_crazy
}}{{
ret_p4_b:
	R_CRAZY R_MOVED
	OUT ?- R_OUT
	HALT
}}{{
halt_now:
	HALT
}}{{
{DECREMENT_HEAD}{ladder}
}}
"""


def build() -> None:
    text = generate()
    # prog blocks separated so each cell is its own block
    text = text.replace("prog_", "\nprog_", 1)  # no, don't do this
    HELL_PATH.write_text(generate(), encoding="utf-8")
    lmao = ROOT / "third_party/lmao/lmao"
    res = subprocess.run(
        [str(lmao), "-d", "-o", str(MB_PATH), str(HELL_PATH)],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(res.stdout)
    sys.stderr.write(res.stderr)
    if res.returncode != 0:
        sys.exit(res.returncode or 1)
    size = MB_PATH.stat().st_size
    print(f"Built {MB_PATH} ({size} bytes, limit=59049, headroom={59049 - size})")


if __name__ == "__main__":
    build()
