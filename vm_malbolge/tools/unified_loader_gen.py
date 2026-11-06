#!/usr/bin/env python3
"""Generador de la imagen UNIFICADA sobre el andamio del CARGADOR.

Ruta especificada: parchear vm_malbolge/src/mbir_m2_loader.hell (40.309 B,
18.740 B de margen, admite 512 celdas de datos y 8 flags de código nuevos)
reusando su fase de carga, su subrutina decrement_value y su maquinaria de
carry, y añadiendo despacho para ADD (0x02), SUB (0x03), CMP_EQ (0x04) y
CMP_LT (0x05).

Ventaja estructural de este andamio frente al de mbir_m2_alu.hell: el cargador
solo usa decrement_value en las dos comprobaciones de HALT (byte 0 y byte 2),
que TERMINAN antes de mi despacho. Después, las ranuras de retorno
SUBROUTINE_FLAG1/2 quedan libres y el bloque exit_decrement_loop solo tiene dos
entradas, así que puedo extenderlo sin colisión con ninguna fase aritmética.

Extensión de la carga: el cargador lee 4 bytes (prog_0..3). Añado prog_4, prog_5
y prog_6 reusando secuencialmente DOS flags de almacén (FLAG_S4/FLAG_P4), porque
cada flag se limpia al consumirse y las cargas son secuenciales.

Uso: python3 unified_loader_gen.py
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LMAO = REPO / "third_party/lmao/lmao"
BASE = REPO / "vm_malbolge/src/mbir_m2_loader.hell"
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402
RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

# --- flags nuevos (el cargador solo declara SUBROUTINE_FLAG1/2/3) ------------
NEW_FLAGS = """SUBROUTINE_FLAG4:
\tNop/MovD
\tJmp

SUBROUTINE_FLAG5:
\tNop/MovD
\tJmp

OPCODE_C1:
\tNop/MovD
\tJmp

OPCODE_VAL:
\tNop/MovD
\tJmp

FLAG_P3_R1:
\tNop/MovD
\tJmp

FLAG_OP2_IS_1:
\tNop/MovD
\tJmp

FLAG_OP2_IS_2:
\tNop/MovD
\tJmp

FLAG_OP2_IS_3:
\tNop/MovD
\tJmp

SUB_FLAG:
\tNop/MovD
\tJmp

CMP_MODE:
\tNop/MovD
\tJmp

CMP_LT_MODE:
\tNop/MovD
\tJmp

"""

# --- celdas de datos nuevas --------------------------------------------------
NEW_CELLS = """scratch_4_crazy:
\tU_CRAZY scratch_4
scratch_4:
\tC1
\tFLAG_INIT ret_s4_init R_FLAG_INIT
\tFLAG_S3_STORE ret_s4_store R_FLAG_S3_STORE

prog_4_crazy:
\tU_CRAZY prog_4
prog_4:
\tC1
\tFLAG_INIT ret_p4_init R_FLAG_INIT
\tFLAG_P3_STORE ret_p4_store R_FLAG_P3_STORE

scratch_5_crazy:
\tU_CRAZY scratch_5
scratch_5:
\tC1
\tFLAG_INIT ret_s5_init R_FLAG_INIT
\tFLAG_S3_STORE ret_s5_store R_FLAG_S3_STORE

prog_5_crazy:
\tU_CRAZY prog_5
prog_5:
\tC1
\tFLAG_INIT ret_p5_init R_FLAG_INIT
\tFLAG_P3_STORE ret_p5_store R_FLAG_P3_STORE

scratch_6_crazy:
\tU_CRAZY scratch_6
scratch_6:
\tC1
\tFLAG_INIT ret_s6_init R_FLAG_INIT
\tFLAG_S3_STORE ret_s6_store R_FLAG_S3_STORE

prog_6_crazy:
\tU_CRAZY prog_6
prog_6:
\tC1
\tFLAG_INIT ret_p6_init R_FLAG_INIT
\tFLAG_P3_STORE ret_p6_store R_FLAG_P3_STORE

"""

ANCHOR_FLAGS = "SUBROUTINE_FLAG3:\n\tNop/MovD\n\tJmp\n"

# --- init de las celdas nuevas (enganchado tras do_init_st) -----------------
OLD_INIT = """ret_st_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_st

\tMOVED load_prog_0
"""
NEW_INIT = """ret_st_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_st

do_init_s4:
\tR_FLAG_INIT
\tMOVED scratch_4_crazy
}{
ret_s4_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_s4

do_init_p4:
\tR_FLAG_INIT
\tMOVED prog_4_crazy
}{
ret_p4_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_p4

do_init_s5:
\tR_FLAG_INIT
\tMOVED scratch_5_crazy
}{
ret_s5_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_s5

do_init_p5:
\tR_FLAG_INIT
\tMOVED prog_5_crazy
}{
ret_p5_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_p5

do_init_s6:
\tR_FLAG_INIT
\tMOVED scratch_6_crazy
}{
ret_s6_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_s6

do_init_p6:
\tR_FLAG_INIT
\tMOVED prog_6_crazy
}{
ret_p6_init:
\tR_CRAZY R_MOVED
\tCOUNTER2_1 do_init_p6

\tMOVED load_prog_0
"""

# --- carga: extender tras load_prog_3 ---------------------------------------
OLD_TAIL = """ret_p3_store:
\tR_CRAZY R_MOVED
\tMOVED exec_v1_v2_push
}{
"""
NEW_TAIL = """ret_p3_store:
\tR_CRAZY R_MOVED
\t// byte 4 = opcode (0x02 ADD / 0x03 SUB / 0x04 CMP_EQ / 0x05 CMP_LT)
\tR_FLAG_S3_STORE
\tMOVED scratch_4_crazy
}{
ret_s4_store:
\tR_CRAZY R_MOVED
\tR_FLAG_P3_STORE
\tMOVED prog_4_crazy
}{
ret_p4_store:
\tR_CRAZY R_MOVED
\t// byte 5 y byte 6 (OUT y HALT): reusan secuencialmente los mismos flags
\tR_FLAG_S3_STORE
\tMOVED scratch_5_crazy
}{
ret_s5_store:
\tR_CRAZY R_MOVED
\tR_FLAG_P3_STORE
\tMOVED prog_5_crazy
}{
ret_p5_store:
\tR_CRAZY R_MOVED
\tR_FLAG_S3_STORE
\tMOVED scratch_6_crazy
}{
ret_s6_store:
\tR_CRAZY R_MOVED
\tR_FLAG_P3_STORE
\tMOVED prog_6_crazy
}{
ret_p6_store:
\tR_CRAZY R_MOVED
\t// despachar sobre el opcode: copiarlo a value_C1 y a value.
\t// Se usan flags propios (OPCODE_C1/OPCODE_VAL) con líneas de prueba en
\t// las celdas value_C1 y value, para no colisionar con las comprobaciones
\t// de HALT del cargador.
\tR_OPCODE_C1
\tMOVED crazy_value_C1
}{
ret_opcode_c1:
\tR_CRAZY R_MOVED
\tR_OPCODE_VAL
\tMOVED crazy_value
}{
ret_opcode_val:
\tR_CRAZY R_MOVED
\tR_SUBROUTINE_FLAG1
\tMOVED decrement_value
}{
"""

# --- clasificacion del opcode: 5 decrementos --------------------------------
OLD_CLASS = """return_from_decrement_value_1:
\tNO_MORE_CARRY_FLAG load_prog_1
\tHALT
}{
"""
NEW_CLASS = """dec_op1_check:
\t// (marcador; la clasificacion del opcode continua abajo)
\tHALT
}{
"""

# --- exit_decrement_loop extendido ------------------------------------------
OLD_EXIT = """exit_decrement_loop:
\tSUBROUTINE_FLAG1 return_from_decrement_value_1 R_SUBROUTINE_FLAG1
\tSUBROUTINE_FLAG2 return_from_decrement_value_2 R_SUBROUTINE_FLAG2
}
"""
NEW_EXIT = """exit_decrement_loop:
\tSUBROUTINE_FLAG1 return_from_decrement_value_1 R_SUBROUTINE_FLAG1
\tSUBROUTINE_FLAG2 return_from_decrement_value_2 R_SUBROUTINE_FLAG2
\tSUBROUTINE_FLAG3 ret_opcode_dec3 R_SUBROUTINE_FLAG3
\tSUBROUTINE_FLAG4 ret_opcode_dec4 R_SUBROUTINE_FLAG4
\tSUBROUTINE_FLAG5 ret_opcode_dec5 R_SUBROUTINE_FLAG5
}
"""

# --- bloques de resultado y clasificacion de operandos -----------------------
NEW_CODE = """
// ==========================================
// CLASIFICACION DEL OPCODE (dec 1..5)
// 0x02 -> carry en dec3 | 0x03 -> carry en dec4
// 0x04 -> carry en dec5 | 0x05 -> carry en dec6
// ==========================================
ret_opcode_dec1:
\tR_SUBROUTINE_FLAG2
\tMOVED decrement_value
}{
ret_opcode_dec2:
\tR_SUBROUTINE_FLAG3
\tMOVED decrement_value
}{
ret_opcode_dec3:
\tNO_MORE_CARRY_FLAG opcode_ge_4
\tMOVED opcode_is_add
}{
opcode_is_add:
\tMOVED eval_pop
}{
opcode_ge_4:
\tR_SUBROUTINE_FLAG4
\tMOVED decrement_value
}{
ret_opcode_dec4:
\tNO_MORE_CARRY_FLAG opcode_ge_5
\tMOVED opcode_is_sub
}{
opcode_is_sub:
\tR_SUB_FLAG
\tMOVED eval_pop
}{
opcode_ge_5:
\tR_SUBROUTINE_FLAG5
\tMOVED decrement_value
}{
ret_opcode_dec5:
\tNO_MORE_CARRY_FLAG opcode_ge_6
\tMOVED opcode_is_cmp_eq
}{
opcode_is_cmp_eq:
\tR_CMP_MODE
\tMOVED eval_pop
}{
opcode_ge_6:
\t// 0x05 y superiores: no soportados por esta imagen
\tHALT
}{
"""


EVAL_CODE = """
// ==========================================
// EVALUACION: clasificar op2 (prog_3) y op1 (prog_1), seleccionar resultado
// ==========================================
eval_pop:
\tR_MOVED
\t// recuperar op2 desde prog_3
\tROT C2 R_ROT
\tR_FLAG_P3_R1
\tMOVED prog_3_crazy
}{
ret_op2_c1:
\tR_CRAZY R_MOVED
\tR_FLAG_VAL_C1_LOAD
\tMOVED crazy_value_C1
}{
ret_op2_val_c1:
\tR_CRAZY R_MOVED
\tR_FLAG_VAL_LOAD
\tMOVED crazy_value
}{
ret_op2_val:
\tR_CRAZY R_MOVED
\t// op2: dec1 -> carry significa op2 == 0
\tR_SUBROUTINE_FLAG1
\tMOVED decrement_value
}{
ret_op2_dec1:
\tNO_MORE_CARRY_FLAG op2_nonzero
\tMOVED eval_pop_op1
}{
op2_nonzero:
\tR_SUBROUTINE_FLAG2
\tMOVED decrement_value
}{
ret_op2_dec2:
\tNO_MORE_CARRY_FLAG op2_is_2_or_3
\tR_FLAG_OP2_IS_1
\tMOVED eval_pop_op1
}{
op2_is_2_or_3:
\tR_SUBROUTINE_FLAG3
\tMOVED decrement_value
}{
ret_op2_dec3:
\tNO_MORE_CARRY_FLAG op2_is_3
\tR_FLAG_OP2_IS_2
\tMOVED eval_pop_op1
}{
op2_is_3:
\tR_FLAG_OP2_IS_3
\tMOVED eval_pop_op1
}{
eval_pop_op1:
\tR_MOVED
\t// recuperar op1 desde prog_1
\tROT C2 R_ROT
\tR_FLAG_P1_R1
\tMOVED prog_1_crazy
}{
ret_eval_op1_c1:
\tR_CRAZY R_MOVED
\tR_FLAG_VAL_C1_LOAD
\tMOVED crazy_value_C1
}{
ret_eval_op1_val_c1:
\tR_CRAZY R_MOVED
\tR_FLAG_VAL_LOAD
\tMOVED crazy_value
}{
ret_eval_op1_val:
\tR_CRAZY R_MOVED
\tR_SUBROUTINE_FLAG1
\tMOVED decrement_value
}{
ret_op1_dec1:
\tNO_MORE_CARRY_FLAG op1_dec1_continue
\tMOVED eval_results
}{
op1_dec1_continue:
\tR_SUBROUTINE_FLAG2
\tMOVED decrement_value
}{
ret_op1_dec2:
\tNO_MORE_CARRY_FLAG op1_dec2_continue
\tMOVED eval_results
}{
op1_dec2_continue:
\tR_SUBROUTINE_FLAG3
\tMOVED decrement_value
}{
ret_op1_dec3:
\tNO_MORE_CARRY_FLAG op1_is_4
\tMOVED eval_results
}{
op1_is_4:
\tMOVED eval_results
}{
eval_results:
\t// Seleccion de resultado. CMP_EQ: igualdad de clases exactas.
\tCMP_MODE eval_cmp R_CMP_MODE
\tFLAG_OP2_IS_1 res_is_1 R_FLAG_OP2_IS_1
\tFLAG_OP2_IS_2 res_is_0 R_FLAG_OP2_IS_2
\tMOVED res_is_2
}{
eval_cmp:
\t// op1 == 0: igual solo si ninguna bandera de op2 activa
\tFLAG_OP2_IS_1 cmp_not_equal R_FLAG_OP2_IS_1
\tFLAG_OP2_IS_2 cmp_not_equal R_FLAG_OP2_IS_2
\tFLAG_OP2_IS_3 cmp_not_equal R_FLAG_OP2_IS_3
\tMOVED cmp_equal
}{
res_is_0:
\tR_MOVED
\tROT 0 R_ROT
\tMOVED eval_out
}{
res_is_1:
\tR_MOVED
\tROT 3 R_ROT
\tMOVED eval_out
}{
res_is_2:
\tR_MOVED
\tROT 6 R_ROT
\tMOVED eval_out
}{
cmp_equal:
\tMOVED res_is_1
}{
cmp_not_equal:
\tMOVED res_is_0
}{
eval_out:
\tOUT ?- R_OUT
\tHALT
}{
"""


def patch(src):
    n = 0
    for old, new in [(OLD_TAIL, NEW_TAIL), (OLD_EXIT, NEW_EXIT), (OLD_INIT, NEW_INIT)]:
        assert src.count(old) == 1, f"anclaje no unico: {old[:40]!r}"
        src = src.replace(old, new, 1)
        n += 1
    # líneas de prueba en las celdas value_C1 y value para los flags nuevos
    old_vc1 = """value_C1:
	C1
	FLAG_VAL_C1_LOAD ret_val_c1_load R_FLAG_VAL_C1_LOAD
	FLAG_VAL_C1_DEC3 ret_val_c1_dec3 R_FLAG_VAL_C1_DEC3
"""
    new_vc1 = old_vc1 + "\tOPCODE_C1 ret_opcode_c1 R_OPCODE_C1\n"
    assert src.count(old_vc1) == 1, "value_C1 no encontrada"
    src = src.replace(old_vc1, new_vc1, 1)
    n += 1
    old_v = """value:
	C1
	FLAG_VAL_LOAD ret_val_load R_FLAG_VAL_LOAD
	FLAG_VAL_DEC3 ret_val_dec3 R_FLAG_VAL_DEC3
	FLAG_DEC_VAL8 return_from_value_8 R_FLAG_DEC_VAL8
	FLAG_DEC_VAL9 return_from_value_9
"""
    new_v = old_v + "\tOPCODE_VAL ret_opcode_val R_OPCODE_VAL\n"
    assert src.count(old_v) == 1, "value no encontrada"
    src = src.replace(old_v, new_v, 1)
    n += 1
    old_p3 = """prog_3:
	?
	FLAG_INIT ret_p3_init R_FLAG_INIT
	FLAG_P3_STORE ret_p3_store R_FLAG_P3_STORE
"""
    new_p3 = old_p3 + "\tFLAG_P3_R1 ret_op2_c1 R_FLAG_P3_R1\n"
    assert src.count(old_p3) == 1, "prog_3 no encontrada"
    src = src.replace(old_p3, new_p3, 1)
    n += 1
    assert src.count(ANCHOR_FLAGS) == 1
    src = src.replace(ANCHOR_FLAGS, ANCHOR_FLAGS + "\n" + NEW_FLAGS, 1)
    n += 1
    # celdas nuevas: justo antes del primer bloque de codigo '{'
    lines = src.splitlines(keepends=True)
    idx = next(i for i, ln in enumerate(lines) if ln.strip() == "{")
    src = "".join(lines[:idx]) + NEW_CELLS + "".join(lines[idx:])
    n += 1
    # bloques nuevos: justo antes del bloque exit_decrement_loop
    src = src.replace("exit_decrement_loop:\n", NEW_CODE + EVAL_CODE + "exit_decrement_loop:\n", 1)
    n += 1
    return src, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path, default=REPO / "vm_malbolge/src/mbir_unified_loader.hell")
    ap.add_argument("--mb", type=Path, default=REPO / "vm_malbolge/src/mbir_unified_loader.mb")
    args = ap.parse_args()

    src = BASE.read_text(encoding="utf-8")
    src, n = patch(src)
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    args.hell.write_text(src, encoding="utf-8")
    print(f"parche aplicado: {n} regiones -> {args.hell} "
          f"({len(src.splitlines())} lineas, base {len(BASE.read_text().splitlines())})")

    res = subprocess.run([str(LMAO), "-d", "-o", str(args.mb), str(args.hell)],
                         capture_output=True, text=True)
    if res.returncode != 0 or not args.mb.exists():
        print("LMAO RECHAZO la imagen sobre el andamio del cargador:")
        for line in (res.stdout + res.stderr).splitlines():
            if line.strip() and not line.startswith("This is LMAO"):
                print("   ", line)
        return 1
    size = args.mb.stat().st_size
    print(f"LMAO OK: {args.mb} ({size} bytes, margen {59049 - size})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
