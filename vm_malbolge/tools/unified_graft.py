#!/usr/bin/env python3
"""Frente 2: injertar la primitiva de despacho del emisor nativo sobre el
andamio del cargador (mbir_m2_loader.hell), con .OFFSET en región libre.

Hipótesis: el andamio del cargador tiene 18.740 B de margen y admite 512 celdas
de datos y 8 flags de código (loader_budget_probe.json). La primitiva de
despacho del emisor nativo NO gasta flags de código — solo celdas de datos,
que E3 midió como la dimensión barata (64 celdas caben).

Conflicto real: ambos mecanismos quieren la celda 0. Se resuelve con .OFFSET,
que coloca el bloque del emisor en una región libre del andamio.

Uso: python3 unified_graft.py
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LMAO = REPO / "third_party/lmao/lmao"
BASE = REPO / "vm_malbolge/src/mbir_m2_loader.hell"


GRAFT = """
// ==========================================
// PRIMITIVA DE DESPACHO DEL EMISOR NATIVO
// (injertada con .OFFSET en region libre del andamio del cargador)
// Todas las celdas son de DATOS: E3 midio esa dimension como barata.
// ==========================================
.DATA
@57000
crazy_const:
	U_CRAZY const_val
const_val:
	85

crazy_boot:
	U_ROT boot_val
boot_val:
	84

target_cell:
	C1

"""



def build():
    src = BASE.read_text(encoding="utf-8")
    return src.rstrip("\n") + "\n" + GRAFT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_unified_graft.hell")
    ap.add_argument("--mb", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_unified_graft.mb")
    args = ap.parse_args()
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    src = build()
    args.hell.write_text(src, encoding="utf-8")
    base_lines = len(BASE.read_text(encoding="utf-8").splitlines())
    print(f"graft escrito: {args.hell}")
    print(f"  base: {base_lines} lineas; total: {len(src.splitlines())} "
          f"(+{len(src.splitlines()) - base_lines})")
    res = subprocess.run([str(LMAO), "-d", "-o", str(args.mb), str(args.hell)],
                         capture_output=True, text=True)
    if res.returncode != 0 or not args.mb.exists():
        print("LMAO RECHAZO:")
        for line in (res.stdout + res.stderr).splitlines():
            if line.strip() and not line.startswith("This is LMAO"):
                print("   ", line)
        return 1
    size = args.mb.stat().st_size
    print(f"LMAO OK: {args.mb}")
    print(f"  tamaño: {size} bytes; margen: {59049 - size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
