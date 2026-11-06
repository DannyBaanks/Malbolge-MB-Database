#!/usr/bin/env python3
"""Generador de la imagen UNIFICADA: stored-program loader + ADD/SUB + CMP_EQ.

Parte de vm_malbolge/src/mbir_m2_alu.hell, que YA carga un programa de 7 bytes
en RAM y ejecuta ADD/SUB (8/8), y le añade el opcode CMP_EQ (0x04):

  1. Dos flags nuevos (OPCODE_PHASE, CMP_MODE). Medido: mbir_m2_alu.hell admite
     2 flags + 4 celdas (56.007 B, margen 3.042); 3 flags ya fallan.
  2. La clasificación del opcode pasa de 3 a 5 decrementos. Al ser la fase del
     opcode la PRIMERA, y limpiarse cada flag al consumirse, se reusan las
     ranuras SUBROUTINE_FLAG4/5 (que luego usa op2) sin colisión: el bloque de
     salida se bifurca por OPCODE_PHASE.
  3. CMP_EQ reutiliza la clasificación existente de op1/op2 (FLAG_OP2_IS_1/2/3 y
     los carries de decremento de op1) y los bloques de salida res_is_0/res_is_1.

Uso: python3 unified_gen.py [--hell out.hell] [--mb out.mb]
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE / "native_classic"))
LMAO = REPO / "third_party/lmao/lmao"
BASE = REPO / "vm_malbolge/src/mbir_m2_alu.hell"
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402
RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

NEW_FLAGS = """OPCODE_PHASE:
\tNop/MovD
\tJmp

CMP_MODE:
\tNop/MovD
\tJmp

"""

# --- 1. armar OPCODE_PHASE antes del primer decremento del opcode -----------
OLD_ARM = """ret_opcode_val:
\tR_CRAZY R_MOVED
\t// Opcode is 0x02 or 0x03.
\t// Dec 1:
\tR_SUBROUTINE_FLAG1
\tMOVED decrement_value
}{
"""
NEW_ARM = """ret_opcode_val:
\tR_CRAZY R_MOVED
\t// Unified image: opcode is 0x02 (ADD), 0x03 (SUB) or 0x04 (CMP_EQ).
\t// Armar la fase de opcode: la salida de decrement_value se bifurca por ella.
\tR_OPCODE_PHASE
\t// Dec 1:
\tR_SUBROUTINE_FLAG1
\tMOVED decrement_value
}{
"""

# --- 2. clasificacion del opcode extendida a 5 decrementos ------------------
OLD_TAIL = """ret_opcode_dec3:
\tNO_MORE_CARRY_FLAG opcode_is_sub
\tMOVED alu_pop_op2
}{
opcode_is_sub:
\tR_SUB_FLAG
\tMOVED alu_pop_op2
\t?
}{
"""
NEW_TAIL = """ret_opcode_dec3:
\t// sin carry -> el opcode es >= 3, seguir decrementando
\tNO_MORE_CARRY_FLAG opcode_ge_4
\tMOVED opcode_is_add
}{
opcode_is_add:
\tR_OPCODE_PHASE
\tMOVED alu_pop_op2
}{
opcode_ge_4:
\tR_SUBROUTINE_FLAG4
\tMOVED decrement_value
}{
ret_opcode_dec4:
\t// sin carry -> >= 4; carry -> el opcode era 3 (SUB)
\tNO_MORE_CARRY_FLAG opcode_ge_5
\tMOVED opcode_is_sub
}{
opcode_is_sub:
\tR_SUB_FLAG
\tR_OPCODE_PHASE
\tMOVED alu_pop_op2
}{
opcode_ge_5:
\tR_SUBROUTINE_FLAG5
\tMOVED decrement_value
}{
ret_opcode_dec5:
\t// sin carry -> >= 5 (no soportado); carry -> el opcode era 4 (CMP_EQ)
\tNO_MORE_CARRY_FLAG opcode_unsupported
\tMOVED opcode_is_cmp_eq
}{
opcode_is_cmp_eq:
\tR_CMP_MODE
\tR_OPCODE_PHASE
\tMOVED alu_pop_op2
}{
opcode_unsupported:
\tR_OPCODE_PHASE
\tHALT
}{
"""

# --- 3. bloque de salida bifurcado por OPCODE_PHASE -------------------------
OLD_EXIT = """exit_decrement_loop:
\tSUBROUTINE_FLAG1 ret_opcode_dec1 R_SUBROUTINE_FLAG1
\tSUBROUTINE_FLAG2 ret_opcode_dec2 R_SUBROUTINE_FLAG2
\tSUBROUTINE_FLAG3 ret_opcode_dec3 R_SUBROUTINE_FLAG3
\tSUBROUTINE_FLAG4 ret_op2_dec1 R_SUBROUTINE_FLAG4
\tSUBROUTINE_FLAG5 ret_op2_dec2 R_SUBROUTINE_FLAG5
\tSUBROUTINE_FLAG6 ret_op2_dec3 R_SUBROUTINE_FLAG6
\tSUBROUTINE_FLAG7 ret_op1_dec1 R_SUBROUTINE_FLAG7
\tSUBROUTINE_FLAG8 ret_op1_dec2 R_SUBROUTINE_FLAG8
\tSUBROUTINE_FLAG9 ret_op1_dec3 R_SUBROUTINE_FLAG9
}
"""
NEW_EXIT = """exit_decrement_loop:
\t// Durante la fase del opcode las ranuras 4 y 5 significan dec4/dec5 del
\t// opcode; despues significan dec1/dec2 de op2. La bandera de fase decide.
\tOPCODE_PHASE exit_decrement_loop_opcode
\tSUBROUTINE_FLAG1 ret_opcode_dec1 R_SUBROUTINE_FLAG1
\tSUBROUTINE_FLAG2 ret_opcode_dec2 R_SUBROUTINE_FLAG2
\tSUBROUTINE_FLAG3 ret_opcode_dec3 R_SUBROUTINE_FLAG3
\tSUBROUTINE_FLAG4 ret_op2_dec1 R_SUBROUTINE_FLAG4
\tSUBROUTINE_FLAG5 ret_op2_dec2 R_SUBROUTINE_FLAG5
\tSUBROUTINE_FLAG6 ret_op2_dec3 R_SUBROUTINE_FLAG6
\tSUBROUTINE_FLAG7 ret_op1_dec1 R_SUBROUTINE_FLAG7
\tSUBROUTINE_FLAG8 ret_op1_dec2 R_SUBROUTINE_FLAG8
\tSUBROUTINE_FLAG9 ret_op1_dec3 R_SUBROUTINE_FLAG9
}{
exit_decrement_loop_opcode:
\tSUBROUTINE_FLAG1 ret_opcode_dec1 R_SUBROUTINE_FLAG1
\tSUBROUTINE_FLAG2 ret_opcode_dec2 R_SUBROUTINE_FLAG2
\tSUBROUTINE_FLAG3 ret_opcode_dec3 R_SUBROUTINE_FLAG3
\tSUBROUTINE_FLAG4 ret_opcode_dec4 R_SUBROUTINE_FLAG4
\tSUBROUTINE_FLAG5 ret_opcode_dec5 R_SUBROUTINE_FLAG5
}
"""

# --- 4. ramas CMP_MODE en la cola de clasificacion de op1 -------------------
OLD_OP1_D1 = """ret_op1_dec1:
\tNO_MORE_CARRY_FLAG op1_dec1_continue
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
"""
NEW_OP1_D1 = """ret_op1_dec1:
\tNO_MORE_CARRY_FLAG op1_dec1_continue
\tCMP_MODE cmp_op1_is_0 R_CMP_MODE
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
"""
OLD_OP1_D2 = """ret_op1_dec2:
\tNO_MORE_CARRY_FLAG op1_dec2_continue
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
"""
NEW_OP1_D2 = """ret_op1_dec2:
\tNO_MORE_CARRY_FLAG op1_dec2_continue
\tCMP_MODE cmp_op1_is_1 R_CMP_MODE
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
"""
OLD_OP1_D3 = """ret_op1_dec3:
\tNO_MORE_CARRY_FLAG op1_is_4
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
"""
NEW_OP1_D3 = """ret_op1_dec3:
\tNO_MORE_CARRY_FLAG op1_is_4
\tCMP_MODE cmp_op1_is_2 R_CMP_MODE
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
"""
OLD_OP1_4 = """op1_is_4:
\tSUB_FLAG res_is_2_direct R_SUB_FLAG
\tMOVED res_is_7
}{
"""
NEW_OP1_4 = """op1_is_4:
\tCMP_MODE cmp_op1_ge_3 R_CMP_MODE
\tSUB_FLAG res_is_2_direct R_SUB_FLAG
\tMOVED res_is_7
}{
"""

# --- 5. bloques de resultado de CMP_EQ --------------------------------------
CMP_BLOCKS = """
// ==========================================
// CMP_EQ: igualdad exacta sobre el dominio que la clasificacion distingue
// ({0,1,2} exactos; >=3 colapsa en una sola clase)
// ==========================================
cmp_op1_is_0:
\t// op1 == 0: igual solo si op2 == 0 (ninguna bandera de op2 activa)
\tFLAG_OP2_IS_1 cmp_not_equal R_FLAG_OP2_IS_1
\tFLAG_OP2_IS_2 cmp_not_equal R_FLAG_OP2_IS_2
\tFLAG_OP2_IS_3 cmp_not_equal R_FLAG_OP2_IS_3
\tMOVED cmp_equal
}{
cmp_op1_is_1:
\tFLAG_OP2_IS_1 cmp_equal R_FLAG_OP2_IS_1
\tMOVED cmp_not_equal
}{
cmp_op1_is_2:
\tFLAG_OP2_IS_2 cmp_equal R_FLAG_OP2_IS_2
\tMOVED cmp_not_equal
}{
cmp_op1_ge_3:
\t// op1 >= 3: igual solo si op2 tambien es >= 3 (exacto salvo 3 vs 4+)
\tFLAG_OP2_IS_3 cmp_equal R_FLAG_OP2_IS_3
\tMOVED cmp_not_equal
}{
cmp_equal:
\tMOVED res_is_1
}{
cmp_not_equal:
\tMOVED res_is_0
}{
"""

ANCHOR_FLAGS = "SUBROUTINE_FLAG9:\n\tNop/MovD\n\tJmp\n"
ANCHOR_CMP = "store_result_and_out:\n"


def patch(src):
    n = 0
    for old, new in [(OLD_ARM, NEW_ARM), (OLD_TAIL, NEW_TAIL), (OLD_EXIT, NEW_EXIT),
                     (OLD_OP1_D1, NEW_OP1_D1), (OLD_OP1_D2, NEW_OP1_D2),
                     (OLD_OP1_D3, NEW_OP1_D3), (OLD_OP1_4, NEW_OP1_4)]:
        assert src.count(old) == 1, f"anclaje no unico ({src.count(old)}): {old[:40]!r}"
        src = src.replace(old, new, 1)
        n += 1
    assert src.count(ANCHOR_FLAGS) == 1
    src = src.replace(ANCHOR_FLAGS, ANCHOR_FLAGS + "\n" + NEW_FLAGS, 1)
    n += 1
    assert src.count(ANCHOR_CMP) == 1
    src = src.replace(ANCHOR_CMP, CMP_BLOCKS + ANCHOR_CMP, 1)
    n += 1
    return src, n


def run_oracle(mb, stdin_bytes, max_steps=600000):
    src = open(mb, encoding="latin-1").read()
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=stdin_bytes.decode("latin-1"))
    return text.encode("latin-1"), steps, status


def run_runner(mb, stdin_bytes, max_steps=600000):
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(stdin_bytes)
        name = f.name
    try:
        with open(name, "rb") as fin:
            r = subprocess.run([str(RUNNER), str(mb), str(max_steps)],
                               stdin=fin, capture_output=True)
        out = r.stdout
        if out.endswith(b"\r\n"):
            out = out[:-2]
        elif out.endswith(b"\n"):
            out = out[:-1]
        return out, r.stderr
    finally:
        os.unlink(name)


VECTORS = [
    ("ADD 2+3", "01020103021000", "05"),
    ("ADD 4+3", "01040103021000", "07"),
    ("ADD 1+1", "01010101021000", "02"),
    ("ADD 2+0", "01020100021000", "02"),
    ("SUB 4-2", "01040102031000", "02"),
    ("SUB 2-2", "01020102031000", "00"),
    ("SUB 2-1", "01020101031000", "01"),
    ("SUB 2-0", "01020100031000", "02"),
    ("CMP_EQ 2==2", "01020102041000", "01"),
    ("CMP_EQ 2==1", "01020101041000", "00"),
    ("CMP_EQ 2==0", "01020100041000", "00"),
    ("CMP_EQ 4==2", "01040102041000", "00"),
    ("CMP_EQ 0==0", "01000100041000", "01"),
    ("CMP_EQ 1==2", "01010102041000", "00"),
    ("CMP_EQ 4==4", "01040104041000", "01"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_unified.hell")
    ap.add_argument("--mb", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_unified.mb")
    args = ap.parse_args()

    src = BASE.read_text(encoding="utf-8")
    src, n = patch(src)
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    args.hell.write_text(src, encoding="utf-8")
    print(f"parche aplicado: {n} regiones modificadas -> {args.hell}")

    res = subprocess.run([str(LMAO), "-d", "-o", str(args.mb), str(args.hell)],
                         capture_output=True, text=True)
    if res.returncode != 0 or not args.mb.exists():
        print("LMAO RECHAZO la imagen unificada:")
        for line in (res.stdout + res.stderr).splitlines():
            if line.strip():
                print("   ", line)
        return 1
    size = args.mb.stat().st_size
    print(f"LMAO OK: {args.mb} ({size} bytes, margen {59049 - size})")

    cases = []
    for name, hexin, want in VECTORS:
        sb = bytes.fromhex(hexin)
        oout, osteps, ostatus = run_oracle(args.mb, sb)
        rout, rerr = run_runner(args.mb, sb)
        ok = (oout.hex() == want) and (rout.hex() == want)
        cases.append({"name": name, "input_hex": hexin, "expected": want,
                      "oracle": oout.hex(), "runner": rout.hex(),
                      "oracle_steps": osteps, "oracle_status": ostatus,
                      "verdict": "PASS" if ok else "FAIL"})
        print(f"  {name:14s} in={hexin:16s} exp={want} oracle={oout.hex():>4} "
              f"runner={rout.hex():>4} pasos={osteps:6d} "
              f"{'PASS' if ok else 'FAIL'}")
    ok = sum(1 for c in cases if c["verdict"] == "PASS")
    print(f"\n{ok}/{len(cases)} PASS en los dos motores")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
