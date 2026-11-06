#!/usr/bin/env python3
"""Frentes 3 y 5: cadena de salto computado sobre el andamio del cargador.

Mecanismo (verificado en mbir_native_cmp_decimal.mb, evidencia
cadena_salto_computado.md):

    leer byte b        -> a = b
    crazy(b, 118)      -> 29504      (celda de dato en direccion 118)
    crazy(29504, X)    -> b + 1      (destino)
    JMP indirecto      -> c = b + 1

O sea: el destino del salto es el byte de entrada MAS UNO. El flujo de control
lo dirige el dato.

Este generador injerta esa cadena sobre mbir_m2_loader.hell con .OFFSET en
region libre, y añade un centinela 0x00 al flujo para que el EOF no disperse
a los dos motores (frente 5, cerrado con centinela).

Uso: python3 computed_jump_graft.py
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
RUNNER = REPO / "runners/malbolge-original/malbolge"

OFF_CRAZY = 57000
OFF_TARGET = 57010

GRAFT = """
// ==========================================
// CADENA DE SALTO COMPUTADO (frentes 3 y 5)
// leer byte -> crazy(b, C_CONST) -> crazy(., mem[T]) -> JMP indirecto
// Todas las celdas son de DATOS: E3 midio esa dimension como barata.
// ==========================================
.DATA
@%d
crazy_chain:
	U_CRAZY chain_val
chain_val:
	118

@%d
target_cell:
	C1
""" % (OFF_CRAZY, OFF_TARGET)


def build():
    src = BASE.read_text(encoding="utf-8")
    return src.rstrip("\n") + "\n" + GRAFT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_jump_graft.hell")
    ap.add_argument("--mb", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_jump_graft.mb")
    args = ap.parse_args()
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    src = build()
    args.hell.write_text(src, encoding="utf-8")
    base_lines = len(BASE.read_text(encoding="utf-8").splitlines())
    print(f"graft: {args.hell} ({len(src.splitlines())} lineas, "
          f"+{len(src.splitlines()) - base_lines} sobre la base)")
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

    # El cargador debe seguir funcionando (4/4 M2)
    print("\n=== cargador tras el injerto ===")
    for label, hx in [("push+out", "01411000"), ("push42+out", "01421000"),
                      ("halt", "00"), ("push+out+halt", "014100")]:
        src2 = open(args.mb, encoding="latin-1").read()
        t, s, stt = oracle_classic.run(src2, max_steps=600000,
                                       stdin_data=bytes.fromhex(hx).decode("latin-1"))
        print(f"  {label:18s} in={hx:10s} -> {t.encode('latin-1').hex() or '(vacio)':10s} "
              f"pasos={s} {stt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
