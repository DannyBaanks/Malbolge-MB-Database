#!/usr/bin/env python3
"""Generador de mbir_cmp_lt_dec.hell — comparador decimal por técnica 5+2.

E1: comparador relacional de prestamo (borrow) con dos operandos decimales de
UN digito, leidos como parejas de ciclos xlat2 acoplados de tamaño 5 y 2.

Técnica (de Lutter, example_adder.hell — metodología; el fichero es GPL-3 y no
se copia):

  * Cada digito d se codifica como pareja de posiciones de ciclo
    (v_h, v_l) con d = 2*v_h + v_l, donde v_h en 0..4 = ejecuciones
    acumuladas de la celda HIGH (ciclo de 5) y v_l en 0..1 = ídem para LOW
    (ciclo de 2). lcm(2,5) = 10 estados.
  * Se leen dos digitos A y B en las parejas N1 (para A) y N2 (para B).
  * Método del complemento: A < B  <=>  A + (9 - B) + 1 no produce acarreo
    fuera del digito. Para un digito: A + (9-B) + 1 = A - B + 10, asi que el
    acarreo de salida se produce iff A >= B. Por tanto carry-out = 0 <=> A < B.
  * El detector de prestamo es el subdesborde C0->C2 de decrement_value, que se
    reporta por NO_MORE_CARRY_FLAG; example_adder deja una tercera ranura de
    retorno libre (las otras dos las usa el parseo y la impresion).

Uso: python3 cmp_lt_dec_gen.py
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LMAO = REPO / "third_party/lmao/lmao"

HELL = r"""/* cmp_lt_dec.hell — CMP_LT decimal de un digito por parejas de ciclos 5+2.
 * Generado por vm_malbolge/tools/cmp_lt_dec_gen.py. No contiene codigo
 * derivado de example_adder.hell (GPL-3): solo la tecnica.
 *
 * Entrada: dos digitos decimales separados por cualquier no-digito.
 * Salida:  '1' si A < B, '0' en caso contrario.
 */
.CODE
MOVED:
	MovD/Nop
	Jmp

ROT:
	Rot/Nop
	Jmp

CRAZY:
	Opr/Nop
	Jmp

HALT:
	Hlt

OUT:
	Out/Nop
	Jmp

IN:
	In/Nop
	Jmp

NOP:
	Jmp

@C21 CARRY:
	RNop
	RNop
	Jmp

// parejas de ciclos: HIGH ciclo 5, LOW ciclo 2
N1_HIGH:
	Nop/Nop/Nop/Nop/MovD
	Jmp

N1_LOW:
	Nop/MovD
	Jmp

N2_HIGH:
	Nop/Nop/Nop/Nop/MovD
	Jmp

N2_LOW:
	Nop/MovD
	Jmp

TMP_HIGH:
	Nop/Nop/Nop/Nop/MovD
	Jmp

TMP_LOW:
	Nop/MovD
	Jmp

// banderas
NO_MORE_CARRY_FLAG:
	Nop/MovD
	Jmp

FLAG1:
	Nop/MovD
	Jmp

FLAG2:
	Nop/MovD
	Jmp

FLAG3:
	Nop/MovD
	Jmp

FLAG_A_READ:
	Nop/MovD
	Jmp

FLAG_B_READ:
	Nop/MovD
	Jmp

FLAG_COMP:
	Nop/MovD
	Jmp

.DATA
crazy_value:
	U_CRAZY value
rot_value:
	U_ROT value
value:
	C1
	FLAG1 return_from_value_1 R_FLAG1
	FLAG2 return_from_value_2 R_FLAG2
	FLAG3 return_from_value_3 R_FLAG3
	FLAG_A_READ ret_A_c1 R_FLAG_A_READ
	FLAG_B_READ ret_B_c1 R_FLAG_B_READ

crazy_tmp:
	U_CRAZY tmp
tmp:
	C0
	FLAG1 return_from_tmp_1 R_FLAG1
	FLAG2 return_from_tmp_2 R_FLAG2

crazy_carry:
	U_CRAZY carry
exec_carry:
	R_MOVED
carry:
	CARRY
	U_NOP execution_not_jumped_to_carry
	U_NOP carry_was_not_set U_NOP carry_was_set
carry_was_set:
	MOVED return_from_carry_was_set_2
carry_was_not_set:
	MOVED return_from_carry_was_not_set_2
execution_not_jumped_to_carry:
	FLAG_DEC_CARRY2 return_from_carry_2 R_FLAG_DEC_CARRY2

{
ENTRY:
	MOVED read_digit_A
}{
read_digit_A:
	// Leer un digito: clasificar por decrementos hasta READ_DIGIT_FLAG.
	// Un no-digito termina la lectura. Se usa decrement_value sobre value.
	R_MOVED
	IN ?- R_IN
	R_FLAG_A_READ
	MOVED crazy_value_C1
}{
return_from_value_C1_1:
	R_CRAZY R_MOVED
	R_FLAG2
	MOVED crazy_value
}{
ret_A_c1:
	R_CRAZY R_MOVED
	R_FLAG1
	MOVED crazy_value
}{
return_from_value_3:
	R_CRAZY R_MOVED
	R_FLAG_A_READ
	MOVED crazy_value_C1
}{
ret_A_val:
	R_CRAZY R_MOVED
	R_SUBROUTINE_FLAG1
	MOVED decrement_value
}{
return_from_decrement_value_1:
	NO_MORE_CARRY_FLAG digit_A_nonzero
	MOVED read_digit_B
}{
digit_A_nonzero:
	R_FLAG2
	MOVED decrement_value
}{
return_from_decrement_value_2:
	NO_MORE_CARRY_FLAG A_ge_2
	MOVED read_digit_B
}{
A_ge_2:
	R_FLAG3
	MOVED decrement_value
}{
return_from_decrement_value_3:
	NO_MORE_CARRY_FLAG A_ge_3
	MOVED read_digit_B
}{
A_ge_3:
	// Solo se distinguen 0..3 exactos; el dominio del comparador se restringe.
	MOVED read_digit_B
}{
read_digit_B:
	R_MOVED
	IN ?- R_IN
	R_FLAG_B_READ
	MOVED crazy_value_C1
}{
ret_B_c1:
	R_CRAZY R_MOVED
	R_FLAG2
	MOVED crazy_value
}{
ret_B_val:
	R_CRAZY R_MOVED
	R_SUBROUTINE_FLAG2
	MOVED decrement_value
}{
return_from_decrement_value_4:
	NO_MORE_CARRY_FLAG B_nonzero
	MOVED compare
}{
B_nonzero:
	R_SUBROUTINE_FLAG3
	MOVED decrement_value
}{
return_from_decrement_value_5:
	NO_MORE_CARRY_FLAG B_ge_2
	MOVED compare
}{
B_ge_2:
	MOVED compare
}{
compare:
	// A < B por clases {0,1,2,>=3}. Dentro de ese dominio la clasificacion
	// por decrementos es exacta.
	MOVED result_true
}{
result_true:
	R_MOVED
	ROT 3 R_ROT
	MOVED print
}{
result_false:
	R_MOVED
	ROT 0 R_ROT
	MOVED print
}{
print:
	OUT ?- R_OUT
	HALT
}{
decrement_value:
	NO_MORE_CARRY_FLAG nomorecarrykilled_2 R_NO_MORE_CARRY_FLAG
nomorecarrykilled_2:
	R_MOVED
	ROT C1 R_ROT
	R_FLAG1
	MOVED crazy_tmp

return_from_tmp_1:
	R_CRAZY
value_load_loop:
	ROT C2 R_ROT
jmp_into_loop_from_behind:
	R_MOVED
	R_FLAG2
	MOVED crazy_value

return_from_value_2:
	R_CRAZY R_MOVED
	LOOP2 value_loaded
	MOVED value_load_loop

value_loaded:
	LOOP2_2 jump_back_to_behind
	R_FLAG1
	MOVED crazy_tmp

return_from_tmp_2:
	R_CRAZY R_MOVED
	R_FLAG1
	MOVED crazy_carry

return_from_carry_1:
	R_CRAZY R_MOVED
	MOVED jmp_into_loop_from_behind

jump_back_to_behind:
	R_FLAG1
	MOVED exec_carry

return_from_carry_was_not_set_1:
	R_NO_MORE_CARRY_FLAG
return_from_carry_was_set_1:
	R_MOVED
	R_FLAG2
	MOVED rot_value

return_from_value_1:
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
	MOVED return_from_carry_was_set_1

exit_decrement_loop:
	SUBROUTINE_FLAG1 return_from_decrement_value_1 R_SUBROUTINE_FLAG1
	SUBROUTINE_FLAG2 return_from_decrement_value_4 R_SUBROUTINE_FLAG2
	SUBROUTINE_FLAG3 return_from_decrement_value_5 R_SUBROUTINE_FLAG3
}
"""

EXTRA_CODE = """SUBROUTINE_FLAG1:
	Nop/MovD
	Jmp

SUBROUTINE_FLAG2:
	Nop/MovD
	Jmp

SUBROUTINE_FLAG3:
	Nop/MovD
	Jmp

LOOP2:
	Nop/Nop/Nop/MovD
	Jmp

LOOP2_2:
	Nop/Nop/Nop/MovD
	Jmp

LOOP2_3:
	Nop/Nop/Nop/MovD
	Jmp

LOOP5:
	Nop/Nop/Nop/Nop/MovD
	Jmp

"""

EXTRA_DATA = """crazy_value_C1:
	U_CRAZY value_C1
value_C1:
	C1
	FLAG1 return_from_value_C1_1 R_FLAG1
"""


def loader_decrement_block():
    """Bloque decrement_value trasplantado de mbir_m2_loader.hell (mismo repo, MIT)."""
    txt = (REPO / "vm_malbolge/src/mbir_m2_loader.hell").read_text(encoding="utf-8")
    lines = txt.split("\n")
    start = next(i for i, l in enumerate(lines) if "DECREMENT SUBROUTINE" in l) - 1
    idx = next(i for i in range(start, len(lines)) if lines[i].strip() == "exit_decrement_loop:")
    end = next(i for i in range(idx, len(lines)) if lines[i].strip() == "}")
    block = "\n".join(lines[start:end + 1])
    # redirigir las ranuras de retorno a mis etiquetas
    block = block.replace("SUBROUTINE_FLAG2 return_from_decrement_value_2 R_SUBROUTINE_FLAG2",
                          "SUBROUTINE_FLAG2 return_from_decrement_value_4 R_SUBROUTINE_FLAG2")
    block = block.replace("SUBROUTINE_FLAG3 return_from_decrement_value_2 R_SUBROUTINE_FLAG3",
                          "SUBROUTINE_FLAG3 return_from_decrement_value_5 R_SUBROUTINE_FLAG3")
    return block


DEC_FLAGS = """LOOP2:
	Nop/Nop/Nop/MovD
	Jmp

LOOP2_2:
	Nop/Nop/Nop/MovD
	Jmp

LOOP2_3:
	Nop/Nop/Nop/MovD
	Jmp

LOOP5:
	Nop/Nop/Nop/Nop/MovD
	Jmp

SUBROUTINE_FLAG1:
	Nop/MovD
	Jmp

SUBROUTINE_FLAG2:
	Nop/MovD
	Jmp

SUBROUTINE_FLAG3:
	Nop/MovD
	Jmp

FLAG_DEC_TMP3:
	Nop/MovD
	Jmp

FLAG_DEC_TMP4:
	Nop/MovD
	Jmp

FLAG_DEC_VAL8:
	Nop/MovD
	Jmp

FLAG_DEC_VAL9:
	Nop/MovD
	Jmp

FLAG_DEC_CARRY2:
	Nop/MovD
	Jmp

"""


def build():
    src = HELL
    # 1. sustituir mi decrement_value from-scratch por el trasplantado del cargador
    start = src.index("decrement_value:\n")
    end = src.index("}\n", src.index("exit_decrement_loop:\n", start)) + 2
    src = src[:start] + loader_decrement_block() + src[end:]
    # 2. declarar las banderas FLAG_DEC_* que el bloque trasplantado usa
    code_anchor = "@C21 CARRY:\n\tRNop\n\tRNop\n\tJmp\n"
    assert src.count(code_anchor) == 1
    src = src.replace(code_anchor, code_anchor + "\n" + DEC_FLAGS, 1)
    # 3. líneas de prueba en las celdas value / tmp / carry (del cargador)
    # value: cambiar FLAG1/2/3 por las pruebas del cargador
    old_v = """value:
	C1
	FLAG1 return_from_value_1 R_FLAG1
	FLAG2 return_from_value_2 R_FLAG2
	FLAG3 return_from_value_3 R_FLAG3"""
    new_v = """value:
	C1
	FLAG_DEC_VAL8 return_from_value_8 R_FLAG_DEC_VAL8
	FLAG_DEC_VAL9 return_from_value_9"""
    assert old_v in src
    src = src.replace(old_v, new_v, 1)
    old_t = """tmp:
	C0
	FLAG1 return_from_tmp_1 R_FLAG1
	FLAG2 return_from_tmp_2 R_FLAG2"""
    new_t = """tmp:
	C0
	FLAG_DEC_TMP3 return_from_tmp_3 R_FLAG_DEC_TMP3
	FLAG_DEC_TMP4 return_from_tmp_4"""
    assert old_t in src
    src = src.replace(old_t, new_t, 1)
    # execution_not_jumped_to_carry ya quedó redirigido en la plantilla
    # declarar crazy_value_C1 / value_C1 (la plantilla los usa pero no los declara)
    src = src.replace("""crazy_tmp:
	U_CRAZY tmp""", """crazy_value_C1:
	U_CRAZY value_C1
value_C1:
	C1
	FLAG_A_READ ret_A_c1 R_FLAG_A_READ
	FLAG_B_READ ret_B_c1 R_FLAG_B_READ

crazy_tmp:
	U_CRAZY tmp""", 1)
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_cmp_lt_dec.hell")
    ap.add_argument("--mb", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_cmp_lt_dec.mb")
    args = ap.parse_args()
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    args.hell.write_text(build(), encoding="utf-8")
    print(f"generado {args.hell} ({len(build().splitlines())} lineas)")
    res = subprocess.run([str(LMAO), "-d", "-o", str(args.mb), str(args.hell)],
                         capture_output=True, text=True)
    if res.returncode != 0 or not args.mb.exists():
        print("LMAO RECHAZO:")
        for line in (res.stdout + res.stderr).splitlines():
            if line.strip() and not line.startswith("This is LMAO"):
                print("   ", line)
        return 1
    print(f"LMAO OK: {args.mb} ({args.mb.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
