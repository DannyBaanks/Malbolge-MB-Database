#!/usr/bin/env python3
"""Frente 3: ¿puede el cargador evaluar una expresion de profundidad 3?

La pila actual (mbir_m2_loader) tiene dos ranuras (stack_scratch, stack_top) mas
cuatro celdas scratch/prog. Los vectores demostrados son de profundidad 1: un
PUSH, un OUT.

Experimento: medir si una cadena con TRES push seguidos y un OUT produce el
valor correcto del más profundo (LIFO), y si una expresión aritmética encadenada
de tres operandos evalúa. Si el clasificador de flags se satura, el resultado
será un eco del operando o silencio — y eso localiza el muro.

Uso: python3 stack_depth_probe.py [imagen.mb]
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LMAO = REPO / "third_party/lmao/lmao"
BASE = REPO / "vm_malbolge/src/mbir_m2_loader.hell"
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402

RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

VECTORS = [
    # (etiqueta, hex MBIR, salida esperada segun LIFO de profundidad N)
    ("profundidad 1: push A, out", "01411000", "41"),
    ("profundidad 2: push A push B, out, out", "01410142021000", "4241"),
    ("profundidad 3: push 1 2 3, out, out, out", "01010102010310101000", "030201"),
    ("profundidad 4: push 1 2 3 4, out x4", "01010102010301041010101000", "04030201"),
    ("profundidad 5: push 1 2 3 4 5, out x5", "010101020103010401051010101000", "0504030201"),
]


def run_oracle(mb, sb, max_steps=600000):
    src = open(mb, encoding="latin-1").read()
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=sb.decode("latin-1"))
    return text.encode("latin-1"), steps, status


def run_runner(mb, sb, max_steps=600000):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("binary", nargs="?", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_m2_loader.mb")
    args = ap.parse_args()
    mb = args.binary
    if not mb.exists():
        print(f"imagen no encontrada: {mb}")
        return 1
    print(f"imagen: {mb} ({mb.stat().st_size} bytes)")
    print(f"{'vector':46s} {'in':34s} {'esperado':12s} {'oraculo':12s} {'runner':12s}")
    for label, hexin, want in VECTORS:
        sb = bytes.fromhex(hexin)
        oout, osteps, ostatus = run_oracle(mb, sb)
        rout = run_runner(mb, sb)
        ok = (oout.hex() == want) and (rout.hex() == want)
        print(f"{label:46s} {hexin:34s} {want:12s} "
              f"{oout.hex() or '(vacio)':12s} {rout.hex() or '(vacio)':12s} "
              f"{'PASS' if ok else 'FALLO'}  pasos={osteps}")

    # Recuento: ¿hasta que profundidad sobrevive el LIFO?
    print("\n=== barrido de profundidad ===")
    for n in range(1, 6):
        pushes = "".join(f"01{i + 1:02x}" for i in range(n))
        outs = "10" * n
        hexin = f"{pushes}{outs}00"
        want = "".join(f"{i + 1:02x}" for i in reversed(range(n)))
        sb = bytes.fromhex(hexin)
        oout, osteps, _ = run_oracle(mb, sb)
        rout = run_runner(mb, sb)
        ok = (oout.hex() == want) and (rout.hex() == want)
        print(f"  profundidad {n}: esperado {want:12s} oraculo={oout.hex() or '(vacio)':12s} "
              f"runner={rout.hex() or '(vacio)':12s} {'PASS' if ok else 'FALLO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
