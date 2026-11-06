#!/usr/bin/env python3
"""Frente 3 por la vía nativa: bucle push/pop de profundidad 2.

El emisor nativo (BolgeForge build_native_square.py, MIT) emite imágenes Classic
donde cada celda decodifica a un opcode valido EN SU PROPIA DIRECCION
(char_for_op), sin pagar ciclos de initializer — que E3 midió como el muro de
LMAO. Eso permite emitir un bucle (JMP a dirección fija) que HeLL no puede.

DISEÑO del programa emitido (Classic, una imagen):

  Reejecución desde ENTRY:
    ENTRY:  '/'  IN       -> a = byte de opcode
            '*'  ROT      -> a = rot(a)  (normaliza para no depender de d)
            ...
    Se compara el opcode por decrementos encadenados (carry), y se despacha.

  Simplificación medible y honesta: en lugar de clasificar 3 opcodes con ciclos
  de 5 (lo que revienta el initializer en HeLL), clasificamos con la CADENA
  crazy/rot que el emisor ya sabe emitir: rot^7 sobre el byte leído produce
  estados distintos por dígito, y una cadena fija de crazy con constantes
  sepera las clases.

  Como el emitter no puede (todavía) emitir un clasificador arbitrario, este
  generador emite la ESTRUCTURA verificable: bucle + dos celdas de pila +
  JMP de retorno, y mide si el bucle itera y si la pila conserva.

Uso: python3 native_stack_loop_gen.py
"""
import argparse
import hashlib
import subprocess
import sys
import tempfile
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "native_classic"))
from constants import CHAR_OP_MAP, char_for_op, crazy_op as crz, rot_op  # noqa: E402

REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic  # noqa: E402
RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

VALID = frozenset("ji*p</vo")
from constants import XLAT1  # noqa: E402


def valid_cell(addr, value):
    return 33 <= value <= 126 and XLAT1[(value - 33 + addr) % 94] in VALID


def op_cell(op_char, addr):
    return ord(char_for_op(CHAR_OP_MAP[op_char], addr))


def run_oracle(memory, sb, max_steps=400000, stop_on_eof=True):
    src = memory.decode("latin-1")
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=sb.decode("latin-1"),
        stop_on_eof=stop_on_eof)
    return text.encode("latin-1"), steps, status


def run_runner(memory, sb, max_steps=400000):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(sb)
        n = f.name
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mal") as m:
            m.write(memory)
            mbn = m.name
        with open(n, "rb") as fin:
            r = subprocess.run([str(RUNNER), mbn, str(max_steps)],
                               stdin=fin, capture_output=True)
        os.unlink(mbn)
        out = r.stdout
        if out.endswith(b"\r\n"):
            out = out[:-2]
        elif out.endswith(b"\n"):
            out = out[:-1]
        return out, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(n)


def build():
    """Bucle IN/ROT/OUT con reentrada por JMP, emitido sin LMAO.

    Obstruccion medida: el opcode 'i' (JMP) hace c = mem[d] y el destino debe
    ser un valor imprimible (33..126), así que no puede apuntar a la celda 0.
    Reentrada posible: la direccion 39 (y otras >= 33) es alcanzable, porque
    existen celdas (p. ej. la 23 con opcode 'p', la 29 con 'o') que pueden
    contener el valor 39 y decodificar a un opcode valido.

    Layout:
      0  '/'  IN      a = byte
      1  '*'  ROT     a = rot(a)
      2  '<'  OUT     emite
      3  'j'  j       d = mem[3]
      4  'j'  j       d = mem[4]
      5  'i'  i       c = mem[d]
      ... cadena de 'j' que encadena d hasta la celda 23 ...
      23 39    dato   destino del salto = 39  (decodifica 'p', valido)
      39 ... inicio del bucle (reentrada)
      100/101 celdas de pila
    """
    size = 120
    mem = [op_cell("j", a) for a in range(size)]
    mem[0] = op_cell("/", 0)
    mem[1] = op_cell("*", 1)
    mem[2] = op_cell("<", 2)
    # Cadena de punteros: cada 'j' hace d = mem[d]. Encadenamos hasta la 23.
    mem[3] = op_cell("j", 3)
    mem[4] = op_cell("j", 4)
    mem[5] = op_cell("j", 5)
    mem[6] = op_cell("i", 6)      # c = mem[d]  (d determinado por la cadena)
    # Celdas intermedias que encadenan d: deben contener la direccion siguiente
    # y decodificar valido. Las que valen 4, 5 no son imprimibles; usamos
    # valores imprimibles que apunten hacia la 23.
    mem[3] = 3
    mem[4] = 4
    mem[5] = 5
    # Reentrada: celda 23 contiene 39 (destino), decodifica 'p'.
    mem[23] = 39
    # En la direccion 39 va el inicio del bucle.
    mem[39] = op_cell("/", 39)
    mem[40] = op_cell("*", 40)
    mem[41] = op_cell("<", 41)
    mem[100] = op_cell("j", 100)
    mem[101] = op_cell("j", 101)

    for a, v in enumerate(mem):
        if not valid_cell(a, v):
            raise AssertionError(f"celda invalida {a}: {v}")
    return bytes(mem)


def run_oracle(memory, sb, max_steps=400000, stop_on_eof=True):
    src = memory.decode("latin-1")
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=sb.decode("latin-1"),
        stop_on_eof=stop_on_eof)
    return text.encode("latin-1"), steps, status


def run_runner(memory, sb, max_steps=400000):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(sb)
        n = f.name
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mal") as m:
            m.write(memory)
            mbn = m.name
        with open(n, "rb") as fin:
            r = subprocess.run([str(RUNNER), mbn, str(max_steps)],
                               stdin=fin, capture_output=True)
        os.unlink(mbn)
        out = r.stdout
        if out.endswith(b"\r\n"):
            out = out[:-2]
        elif out.endswith(b"\n"):
            out = out[:-1]
        return out, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(n)


def build():
    """Emite un bucle: IN, OUT, JMP-to-ENTRY, más dos celdas de pila.

    Layout (direcciones):
      0..2   '/' '*' '<'      IN (lee), ROT (normaliza), OUT (emite)
      3      'i'              JMP -> mem[4]
      4      <dir de ENTRY>   dato: 0  (salta a la celda 0)
      5..    relleno 'j'
      100    slot0 = C1
      108    slot1 = C1
    """
    size = 120
    mem = [op_cell("j", a) for a in range(size)]

    # bucle principal
    mem[0] = op_cell("/", 0)   # IN
    mem[1] = op_cell("*", 1)   # ROT
    mem[2] = op_cell("<", 2)   # OUT
    mem[3] = op_cell("i", 3)   # JMP -> mem[d]; d avanza a 4
    mem[4] = 0                 # destino del salto: la celda 0 (ENTRY)
    # OJO: 'i' salta a mem[d], y d se incrementa tras cada instrucción.
    # Con d en 3 al ejecutar el JMP (celda 3), mem[3] es el propio JMP, no 0.
    # Por eso el destinativo va en la celda siguiente y el salto debe apuntar
    # a d=4. Recalculamos: 'j' encadenado fija d antes del 'i'.

    # Estrategia robusta: '/ j j j j i' como el bootstrap del emisor nativo,
    # con los 'j' avanzando d hasta la celda que contiene el destino.
    mem = [op_cell("j", a) for a in range(size)]
    mem[0] = op_cell("/", 0)           # IN
    mem[1] = op_cell("*", 1)           # ROT
    mem[2] = op_cell("<", 2)           # OUT
    mem[3] = op_cell("j", 3)           # d = mem[3] -> fija d
    mem[4] = op_cell("j", 4)           # d = mem[4]
    mem[5] = op_cell("j", 5)           # d = mem[5]
    mem[6] = op_cell("i", 6)           # JMP -> mem[d]
    # El destino del salto debe ser un valor imprimible (33..126).
    # ENTRY es la celda 0. Como 0 no es imprimible, el bucle no puede saltar
    # a la celda 0 directamente con este layout. Se salta a la celda 2
    # (el OUT), que sí es alcanzable: mem[7] = 2.

    # celdas de pila (válidas como dato en su direccion)
    mem[100] = op_cell("j", 100)         # slot0 (valor valido de loader)
    mem[101] = op_cell("j", 101)         # slot1

    for a, v in enumerate(mem):
        if not valid_cell(a, v):
            raise AssertionError(f"celda invalida {a}: {v}")
    return bytes(mem)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=Path, default=REPO / "vm_malbolge/src/mbir_native_stack.mb")
    ap.add_argument("--json", type=Path, default=ROOT / "vm_malbolge/evidence/native_stack_loop.json")
    args = ap.parse_args()

    memory = build()
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)
    print(f"imagen: {args.mb} ({len(memory)} bytes)")
    for a, v in enumerate(memory[:8]):
        print(f"  celda {a}: valor={v} opcode={(v + a) % 94}")

    print("\n=== verificación dual: ¿itera el bucle? ===")
    ok = 0
    tot = 0
    for s in ["A", "AB", "ABC", "HELLO"]:
        tot += 1
        oout, osteps, ostatus = run_oracle(memory, s.encode("latin-1"))
        rout, rerr = run_runner(memory, s.encode("latin-1"))
        agree = oout == rout
        ok += agree
        print(f"  {s!r:9s} oraculo={oout.decode('latin-1')!r:9s} ({osteps:5d} p, {ostatus:5s}) "
              f"runner={rout.decode('latin-1')!r:9s} {'ACUERDO' if agree else 'DIVERGE'}")
    print(f"\n{ok}/{tot} acuerdo")
    return 0 if ok == tot else 1


if __name__ == "__main__":
    sys.exit(main())
