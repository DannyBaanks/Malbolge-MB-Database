#!/usr/bin/env python3
"""Frente 5: reconstruir el probe de loop del lexer (P6) y reproducir la
divergencia oraculo-vs-runner documentada en python/P6_STATUS.md.

El experimento original (2026-10-10) vivia en /tmp y se perdió. Se reconstruye:
byte_dispatch18.hell con cada cola `OUT ?- R_OUT / HALT` reemplazada por
`OUT ?- R_OUT / R_MOVED / MOVED ENTRY`, de modo que tras emitir el marcador
vuelva al clasificador y lea un segundo byte.

Despues se mide, en el MISMO binario, la salida del oraculo Python y del
runner C nativo con stdin '01' y '01 02', y se comprueba si la divergencia
documentada (runner '50' vs oraculo '50dadadadada3939') se reproduce.

Uso: python3 lex_loop_probe.py
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
BASE = REPO / "vm_malbolge/src/byte_dispatch18.hell"
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402

RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

OLD_TAIL = "\tOUT ?- R_OUT\n\tHALT\n"
NEW_TAIL = "\tOUT ?- R_OUT\n\tR_MOVED\n\tMOVED ENTRY\n"


def build():
    src = BASE.read_text(encoding="utf-8")
    n = src.count(OLD_TAIL)
    return src.replace(OLD_TAIL, NEW_TAIL), n


def run_oracle(mb, sb, max_steps=300000):
    src = open(mb, encoding="latin-1").read()
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=sb.decode("latin-1"))
    return text.encode("latin-1"), steps, status


def run_runner(mb, sb, max_steps=300000):
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
        return out, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hell", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_lex_loop.hell")
    ap.add_argument("--mb", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_lex_loop.mb")
    args = ap.parse_args()
    src, n = build()
    args.hell.parent.mkdir(parents=True, exist_ok=True)
    args.hell.write_text(src, encoding="utf-8")
    print(f"probe reconstruido: {args.hell} ({len(src.splitlines())} lineas, "
          f"{n} colas reemplazadas)")
    res = subprocess.run([str(LMAO), "-d", "-o", str(args.mb), str(args.hell)],
                         capture_output=True, text=True)
    if res.returncode != 0 or not args.mb.exists():
        print("LMAO RECHAZO:")
        for line in (res.stdout + res.stderr).splitlines():
            if line.strip() and not line.startswith("This is LMAO"):
                print("   ", line)
        return 1
    print(f"LMAO OK: {args.mb} ({args.mb.stat().st_size} bytes)")

    print(f"\n{'stdin':10s} {'oraculo':22s} {'pasos':>8s} | {'runner':22s} | acuerdo")
    divergences = 0
    for stream in ["01", "01 02", "02", "01 02 03"]:
        sb = stream.encode("latin-1")
        oout, osteps, ostatus = run_oracle(args.mb, sb)
        rout, rerr = run_runner(args.mb, sb)
        agree = oout == rout
        divergences += (not agree)
        print(f"{stream:10s} {oout.hex() or '(vacio)':22s} {osteps:8d} | "
              f"{rout.hex() or '(vacio)':22s} | {'SI' if agree else 'NO'}")
    print(f"\ndivergencias: {divergences}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
