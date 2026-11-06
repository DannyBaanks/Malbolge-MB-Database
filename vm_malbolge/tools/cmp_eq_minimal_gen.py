#!/usr/bin/env python3
"""Parche MÍNIMO de CMP_EQ sobre mbir_m2_alu.hell (dominio {0,1,2}).

Ruta más barata que permite la evidencia: NO añadir un cuarto/quinto decremento
de opcode con su propio bloque de salida, ni una bandera de fase general. En su
lugar:

  1. UN decremento extra (dec4) que reusa SUBROUTINE_FLAG4 -- ranura que durante
     la fase del opcode está libre, porque op2 la usa después y cada flag se
     limpia al consumirse.
  2. La salida por FLAG4 se redirige a una compuerta de DOS líneas que prueba la
     bandera CMP_GATE (armada solo para ese decremento) y, si no está armada,
     ejecuta el código original de ret_op2_dec1. No es un segundo bloque de
     salida: son dos líneas.
  3. La selección de resultado reusa las clasificaciones EXISTES de op1 y op2
     (FLAG_OP2_IS_1/2/3 y los carries de decremento de op1). Como el dominio se
     restringe a {0,1,2}, esas clasificaciones son exactas y la igualdad se
     decide con una sola prueba por clase de op1.
  4. Dos flags nuevos en total (CMP_GATE, CMP_RESULT). La sonda de presupuesto
     midió que 2 flags + 4 celdas ensamblan (56.007 B, margen 3.042).

Uso: python3 cmp_eq_minimal_gen.py
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LMAO = REPO / "third_party/lmao/lmao"
BASE = REPO / "vm_malbolge/src/mbir_m2_alu.hell"
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402
RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

NEW_FLAGS = """CMP_GATE:
\tNop/MovD
\tJmp

CMP_RESULT:
\tNop/MovD
\tJmp

"""

ANCHOR_FLAGS = "SUBROUTINE_FLAG9:\n\tNop/MovD\n\tJmp\n"

OLD_CLASS = """ret_opcode_dec3:
\tNO_MORE_CARRY_FLAG opcode_is_sub
\tMOVED alu_pop_op2
}{
opcode_is_sub:
\tR_SUB_FLAG
\tMOVED alu_pop_op2
\t?
}{
"""
NEW_CLASS = """ret_opcode_dec3:
\tNO_MORE_CARRY_FLAG opcode_ge_4
\tMOVED alu_pop_op2
}{
opcode_is_sub:
\tR_SUB_FLAG
\tMOVED alu_pop_op2
\t?
}{
opcode_ge_4:
\t// sin carry tras dec3 => el opcode es >= 3. Un decremento mas distingue
\t// 0x03 (carry) de 0x04 (sin carry => CMP_EQ). Reusa SUBROUTINE_FLAG4, que
\t// la fase de op2 usara despues: cada flag se limpia al consumirse.
\tR_CMP_GATE
\tR_SUBROUTINE_FLAG4
\tMOVED decrement_value
}{
opcode_is_cmp_eq:
\tR_CMP_RESULT
\tMOVED alu_pop_op2
}{
"""

OLD_EXIT_LINE = "\tSUBROUTINE_FLAG4 ret_op2_dec1 R_SUBROUTINE_FLAG4\n"
NEW_EXIT_LINE = "\tSUBROUTINE_FLAG4 ret_dec_gate R_SUBROUTINE_FLAG4\n"

GATE_BLOCK = """ret_dec_gate:
\tCMP_GATE opcode_is_cmp_eq R_CMP_GATE
\tNO_MORE_CARRY_FLAG op2_nonzero
\tMOVED op2_is_0
}{
"""

OLD_OP1 = {
    "d1": """ret_op1_dec1:
\tNO_MORE_CARRY_FLAG op1_dec1_continue
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
""",
    "d2": """ret_op1_dec2:
\tNO_MORE_CARRY_FLAG op1_dec2_continue
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
""",
    "d3": """ret_op1_dec3:
\tNO_MORE_CARRY_FLAG op1_is_4
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
""",
    "i4": """op1_is_4:
\tSUB_FLAG res_is_2_direct R_SUB_FLAG
\tMOVED res_is_7
}{
""",
}
NEW_OP1 = {
    "d1": """ret_op1_dec1:
\tNO_MORE_CARRY_FLAG op1_dec1_continue
\tCMP_RESULT cmp_op1_is_0 R_CMP_RESULT
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
""",
    "d2": """ret_op1_dec2:
\tNO_MORE_CARRY_FLAG op1_dec2_continue
\tCMP_RESULT cmp_op1_is_1 R_CMP_RESULT
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
""",
    "d3": """ret_op1_dec3:
\tNO_MORE_CARRY_FLAG op1_is_4
\tCMP_RESULT cmp_op1_is_2 R_CMP_RESULT
\tSUB_FLAG check_sub_results R_SUB_FLAG
\tMOVED check_add_results
}{
""",
    "i4": """op1_is_4:
\tCMP_RESULT cmp_op1_ge_3 R_CMP_RESULT
\tSUB_FLAG res_is_2_direct R_SUB_FLAG
\tMOVED res_is_7
}{
""",
}

CMP_BLOCKS = """cmp_op1_is_0:
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
\t// op1 >= 3: igual solo si op2 tambien es >= 3
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

ANCHOR_CMP = "store_result_and_out:\n"


def patch(src):
    n = 0
    assert src.count(OLD_CLASS) == 1, "clasificacion del opcode no encontrada"
    src = src.replace(OLD_CLASS, NEW_CLASS, 1)
    n += 1
    assert src.count(OLD_EXIT_LINE) == 1, "linea FLAG4 del exit no encontrada"
    src = src.replace(OLD_EXIT_LINE, NEW_EXIT_LINE, 1)
    n += 1
    anchor = "exit_decrement_loop:\n"
    assert src.count(anchor) == 1
    src = src.replace(anchor, GATE_BLOCK + anchor, 1)
    n += 1
    for k in ("d1", "d2", "d3", "i4"):
        assert src.count(OLD_OP1[k]) == 1, f"bloque op1 {k} no encontrado"
        src = src.replace(OLD_OP1[k], NEW_OP1[k], 1)
        n += 1
    assert src.count(ANCHOR_FLAGS) == 1
    src = src.replace(ANCHOR_FLAGS, ANCHOR_FLAGS + "\n" + NEW_FLAGS, 1)
    n += 1
    assert src.count(ANCHOR_CMP) == 1
    src = src.replace(ANCHOR_CMP, CMP_BLOCKS + ANCHOR_CMP, 1)
    n += 1
    return src, n


def run_oracle(mb, sb, max_steps=600000):
    src = open(mb, encoding="latin-1").read()
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=sb.decode("latin-1"))
    return text.encode("latin-1"), steps, status


def run_runner(mb, sb, max_steps=600000):
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(sb)
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
        return out
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
    ("CMP_EQ 1==1", "01010101041000", "01"),
    ("CMP_EQ 0==0", "01000100041000", "01"),
    ("CMP_EQ 1==0", "01010100041000", "00"),
    ("CMP_EQ 0==1", "01000101041000", "00"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path, default=REPO / "vm_malbolge/src/mbir_unified_min.hell")
    ap.add_argument("--mb", type=Path, default=REPO / "vm_malbolge/src/mbir_unified_min.mb")
    args = ap.parse_args()

    src = BASE.read_text(encoding="utf-8")
    src, n = patch(src)
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    args.hell.write_text(src, encoding="utf-8")
    print(f"parche mínimo aplicado: {n} regiones -> {args.hell}")

    res = subprocess.run([str(LMAO), "-d", "-o", str(args.mb), str(args.hell)],
                         capture_output=True, text=True)
    if res.returncode != 0 or not args.mb.exists():
        print("LMAO RECHAZO:")
        for line in (res.stdout + res.stderr).splitlines():
            if line.strip() and not line.startswith("This is LMAO"):
                print("   ", line)
        return 1
    size = args.mb.stat().st_size
    print(f"LMAO OK: {args.mb} ({size} bytes, margen {59049 - size})")

    cases = []
    for name, hexin, want in VECTORS:
        sb = bytes.fromhex(hexin)
        oout, osteps, ostatus = run_oracle(args.mb, sb)
        rout = run_runner(args.mb, sb)
        ok = (oout.hex() == want) and (rout.hex() == want)
        cases.append({"name": name, "input_hex": hexin, "expected": want,
                      "oracle": oout.hex(), "runner": rout.hex(),
                      "oracle_steps": osteps,
                      "verdict": "PASS" if ok else "FAIL"})
        print(f"  {name:14s} in={hexin:16s} exp={want} oracle={oout.hex():>4} "
              f"runner={rout.hex():>4} pasos={osteps:6d} {'PASS' if ok else 'FAIL'}")
    ok = sum(1 for c in cases if c["verdict"] == "PASS")
    print(f"\n{ok}/{len(cases)} PASS en los dos motores")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
