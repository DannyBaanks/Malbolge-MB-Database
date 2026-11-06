#!/usr/bin/env python3
"""Generador de mbir_cmp_lt_dec.hell sobre el layout QUE FUNCIONA.

A diferencia del intento anterior (que escribía el .CODE desde cero y
desenrutaba la entrada), este generador toma vm_malbolge/src/mbir_cmp_lt.hell
como base VERBATIM (mismo repo, MIT): conserva su .CODE, su .DATA y su
cableado de entrada, y sustituye SOLO los bloques de codigo de la logica de
comparacion.

Punto clave que hace posible la tecnica 5+2 sin tocar el layout: la imagen base
YA contiene las celdas de ciclo que la tecnica necesita --

  * ciclo de 5: LOOP5 (Nop/Nop/Nop/Nop/MovD), que ademas es el waypoint que el
    camino errante de la entrada recorre;
  * ciclo de 2: cualquier celda de bandera (Nop/MovD), que es exactamente un
    ciclo de 2.

No se añade NINGUNA celda a .CODE ni a .DATA, así que ninguna direccion se
desplaza y el camino errante de la entrada sigue aterrizando donde la imagen
base lo tiene cableado.

Uso: python3 cmp_lt_dec_gen.py
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LMAO = REPO / "third_party/lmao/lmao"
BASE = REPO / "vm_malbolge/src/mbir_cmp_lt.hell"
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402
RUNNER = REPO / "runners/malbolge-original/malbolge"

# Bloques de codigo NUEVOS (solo logica; no declaran celdas).
# La lectura de digitos reusa las celdas existentes: value/value_C1 para el
# clasificador por decrementos, stack_top/stack_top_1 para los operandos, y el
# par LOOP5 (ciclo 5) / una bandera libre (ciclo 2) para la pareja de ciclos.
NEW_CODE = """{
// ==========================================
// E1: comparador de digitos decimales sobre el layout verbatim de
// mbir_cmp_lt.hell. NO se añade ninguna celda: se reusan LOOP5 (ciclo de 5,
// ya presente en la base) y cualquier bandera (Nop/MovD = ciclo de 2).
// El lector reusa next_opcode de la base para leer y copiar a value, y la
// clasificacion reusa las tres ranuras SUBROUTINE_FLAG4/5/6 secuencialmente
// (la base las usa para op2 DESPUES, y cada flag se limpia al consumirse).
// ==========================================
dec_read_digit:
	// la base ya lee un byte y lo copia a value en next_opcode
	R_MOVED
	MOVED next_opcode
}{
ret_dec_c1:
	R_CRAZY R_MOVED
	R_SUBROUTINE_FLAG4
	MOVED decrement_value
}{
ret_dec_d1:
	NO_MORE_CARRY_FLAG dec_ge_1
	MOVED dec_done
}{
dec_ge_1:
	R_SUBROUTINE_FLAG5
	MOVED decrement_value
}{
ret_dec_d2:
	NO_MORE_CARRY_FLAG dec_ge_2
	MOVED dec_done
}{
dec_ge_2:
	R_SUBROUTINE_FLAG6
	MOVED decrement_value
}{
ret_dec_d3:
	MOVED dec_done
}{
dec_done:
	R_MOVED
	MOVED LT_B1
}
"""

# Punto de entrada: en lugar del ENTRY original, leer los dos digitos y luego
# entrar en la maquinaria de comparacion existente.
OLD_ENTRY_MARKER = "ENTRY:\n"
NEW_ENTRY = """ENTRY:
	R_MOVED
	MOVED dec_read_digit
"""


def build():
    src = BASE.read_text(encoding="utf-8")
    # 1. insertar los bloques de codigo nuevos justo antes del bloque ENTRY
    anchor = "{\nENTRY:\n"
    assert src.count(anchor) == 1, "bloque ENTRY no encontrado"
    src = src.replace(anchor, NEW_CODE.rstrip() + "\n" + anchor, 1)
    # 2. sustituir el cuerpo de ENTRY por el nuevo leedor de digitos
    old_entry = """ENTRY:
	MOVED next_opcode
}{
"""
    new_entry = """ENTRY:
	R_MOVED
	MOVED next_opcode
}{
"""
    assert src.count(old_entry) == 1, "cuerpo de ENTRY no encontrado"
    src = src.replace(old_entry, new_entry, 1)
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_cmp_lt_dec.hell")
    ap.add_argument("--mb", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_cmp_lt_dec.mb")
    args = ap.parse_args()
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    src = build()
    args.hell.write_text(src, encoding="utf-8")
    base_lines = len(BASE.read_text(encoding="utf-8").splitlines())
    print(f"generado {args.hell}: {len(src.splitlines())} lineas "
          f"(base verbatim {base_lines}); ninguna celda añadida")
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
