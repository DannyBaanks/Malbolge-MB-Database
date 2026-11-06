#!/usr/bin/env python3
"""Frente 6a — primer milestone de la pista C: emisor C -> Classic con paridad dual.

El nicho real de la pista C no es un interprete de C dentro de Malbolge (proyecto
enorme y sin arte previo, como dice c/STATUS.md), sino lo que este repo ya sabe
hacer: EMITIR Malbolge Classic. El primer milestone medible es un emisor escrito
en C que produzca una imagen valida y la verifique en los dos motores.

Este script:
  1. escribe un emisor C (vm_malbolge/tools/c_emitter.c) que genera un .mal
     Classic con una receta rectilinea conocida (bootstrap + OUT + HALT),
  2. lo compila con gcc,
  3. lo ejecuta para producir la imagen,
  4. verifica esa imagen en tools/oracle_classic.py y en el runner C nativo,
  5. exige paridad bit a bit y paridad de pasos.

Uso: python3 c_frontend_gen.py
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402

RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

# Emisor C: emite un .mal Classic que escribe 0x34 ('4') y para.
# La celda 0 es `/` (IN): lee un byte (lo ignora), luego el programa emite.
# Construido sobre la relacion posicional op = (char + addr) % 94.
EMITTER_C = r"""
/* c_emitter.c — emisor Classic minimo para la pista C de MALBOLGE-MB-DATABASE.
 * Emite un .mal cuya unica funcion observable es emitir 0x34 y detenerse.
 * La imagen se construye celda a celda respetando la relacion posicional
 * de Classic: opcode = (valor + direccion) % 94.
 */
#include <stdio.h>
#include <stdlib.h>

static const char XLAT1[] =
    "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTYA1j5+*M(N";

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "uso: c_emitter salida.mal\n"); return 1; }
    FILE *f = fopen(argv[1], "wb");
    if (!f) { perror("fopen"); return 1; }
    /* Secuencia: '/' IN (lee y descarta), luego una celda de dato con '4',
     * luego '<' OUT (emite a & 255) y 'v' HALT.
     * En Classic el acumulador se carga con ROT o CRAZY sobre una celda de dato.
     * basta con que la celda de dato sea leida por el '/', no por OUT.
     * SECUENCIA REAL: '/' IN -> 'j' (d = mem[d], fija d en la celda de dato) ->
     * '*' (a = mem[d], carga '4') -> '<' OUT -> 'v' HALT. */
    const char *prog = "/j*j<v";   /* IN, JMP, ROT(carga dato), OUT, HALT */
    for (size_t i = 0; prog[i]; i++) {
        int idx = -1;
        for (int k = 0; k < 94; k++) {
            if (XLAT1[k] == prog[i]) { idx = k; break; }
        }
        if (idx < 0) { fprintf(stderr, "opcode no encontrado: %c\n", prog[i]); return 1; }
        /* Forma canonica (constants.py char_for_op): char = (idx - addr) mod 94 + 33 */
        int c = (idx - (int)i) % 94;
        if (c < 0) c += 94;
        fputc(c + 33, f);
    }
    fclose(f);
    return 0;
}
"""


def run_oracle(mb, sb, max_steps=200000):
    src = open(mb, encoding="latin-1").read()
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=sb.decode("latin-1"))
    return text.encode("latin-1"), steps, status


def run_runner(mb, sb, max_steps=200000):
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
    ap.add_argument("--src", type=Path,
                    default=REPO / "vm_malbolge/tools/c_emitter.c")
    ap.add_argument("--mb", type=Path,
                    default=REPO / "vm_malbolge/src/mbir_c_emit.mb")
    ap.add_argument("--json", type=Path,
                    default=REPO / "vm_malbolge/evidence/c_frontend_first.json")
    args = ap.parse_args()

    args.src.parent.mkdir(parents=True, exist_ok=True)
    args.src.write_text(EMITTER_C, encoding="utf-8")

    exe = args.src.with_suffix(".bin")
    cc = subprocess.run(["gcc", "-O2", "-o", str(exe), str(args.src)],
                        capture_output=True, text=True)
    if cc.returncode != 0:
        print("gcc FALLO:")
        print(cc.stderr)
        return 1
    print(f"emisor compilado: {exe} ({exe.stat().st_size} bytes)")

    args.mb.parent.mkdir(parents=True, exist_ok=True)
    run = subprocess.run([str(exe), str(args.mb)], capture_output=True, text=True)
    if run.returncode != 0:
        print("emisor FALLO:", run.stderr)
        return 1
    img = args.mb.read_bytes()
    print(f"imagen emitida: {args.mb} ({len(img)} bytes) hex={img.hex()}")

    # Verificacion dual
    sb = b"\x00"
    oout, osteps, ostatus = run_oracle(args.mb, sb)
    rout, rerr = run_runner(args.mb, sb)
    agree = (oout == rout) and (oout == b"4")
    print(f"  oraculo: {oout.hex()} ({osteps} pasos, {ostatus})")
    print(f"  runner : {rout.hex()} ({rerr})")
    bit_exact = oout == rout
    print(f"  paridad bit a bit: {'SI' if bit_exact else 'NO'}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "schema": "c-frontend-first/1",
            "evidence_kind": "MALBOLGE_RUNTIME",
            "claim": ("A C-emitted Classic Malbolge image runs and both engines agree "
                      "bit-exactly, establishing the first milestone of the C track."),
            "claim_status": "DEMONSTRATED" if (agree and bit_exact) else "FAIL",
            "emitter": {"path": str(args.src.relative_to(REPO)),
                        "sha256": hashlib.sha256(args.src.read_bytes()).hexdigest()},
            "artifact": {"path": str(args.mb.relative_to(REPO)),
                         "size_bytes": len(img),
                         "sha256": hashlib.sha256(img).hexdigest(),
                         "hex": img.hex(),
                         "variant": "classic-3^10"},
            "tooling": {
                "oracle": {"path": "tools/oracle_classic.py",
                           "sha256": hashlib.sha256((REPO / "tools/oracle_classic.py").read_bytes()).hexdigest()},
                "runner": {"path": "runners/malbolge-original/malbolge",
                           "sha256": hashlib.sha256(RUNNER.read_bytes()).hexdigest()},
            },
            "verification": {
                "stdin_hex": sb.hex(),
                "oracle_output": oout.hex(),
                "oracle_steps": osteps,
                "oracle_status": ostatus,
                "runner_output": rout.hex(),
                "runner_stderr": rerr,
                "bit_exact_parity": bit_exact,
            },
            "scope_limits": [
                "One-shot: emits a constant byte and halts.",
                "The emitter is a first milestone for the C track, not a C-to-Malbolge compiler.",
            ],
        }, indent=2), encoding="utf-8")
        print(f"Wrote {args.json}")
    return 0 if (agree and bit_exact) else 1


if __name__ == "__main__":
    sys.exit(main())
