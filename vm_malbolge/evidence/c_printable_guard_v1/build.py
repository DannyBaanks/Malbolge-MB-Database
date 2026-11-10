#!/usr/bin/env python3
"""build.py — c_printable_guard_v1: el runner C se detiene ante celdas no imprimibles.

Causa raíz de la divergencia documentada en `epoch_resolver_word_v1`.  El bucle
del runner C (`runners/malbolge-original/malbolge`, función `vm_run`) hace esto
**antes de decodificar** cada instrucción:

    1cc8  mov  edi,r14d          ; c (pc)
    1ccb  add  rbp,0x1           ; steps += 1
    1ccf  call mem_get           ; eax = mem[c]
    1cd4  lea  edx,[rax-0x21]    ; celda - 33
    1cd7  cmp  edx,0x5d          ; 93
    1cda  ja   1e5e              ; -> status = terminated ; return

Es decir: si la celda señalada por `pc` no está en 33..126, el runner **termina
la ejecución** (mismo destino que el opcode END).  El intérprete canónico no
hace eso: ejecuta cualquier valor decodificando `(mem[c] + c) % 94` y sólo
condiciona el *cifrado posterior* de la celda a que sea imprimible.

Eso explica el síntoma exacto de `epoch_resolver_word_v1`: en el paso 276 el pc
está en `T = 100` y `mem[100] = 29797` (payload de 10 trits).  El oráculo emite
`OUT` y sigue hasta `END` en `T+1`; el C para ahí sin emitir.

Programas de este pack
----------------------
Programas mínimos (44 celdas, todas imprimibles) con una sola forma:

    pc 0     DLOAD   d = mem[0] = 40 -> d = 41
    pc 1     CRAZY   mem[41] = crazy(0, mem[41])          (modo one_crazy)
             o NOP   d pasa de 41 a 42 antes del salto     (modo seed_only)
    pc 2     DLOAD   d = mem[42] = 40 -> d = 41           (sólo two_crazy)
    pc 3     CRAZY   mem[41] = crazy(a, mem[41])          (sólo two_crazy)
    pc 2/4   JMP     c = mem[42] = 40 -> pc = 41
    pc 41    <- aterrizaje: el valor de esta celda es el que se somete a prueba
    pc 42    celda de salto (40)
    pc 43    38 -> (38 + 43) % 94 = 81 = END

El valor de la celda 41 se elige para caer a cada lado del rango imprimible:

    seed_only          41 = semilla (33 o 126: fronteras imprimibles)
    one_crazy          41 = crazy(0, 36) = 29524   (> 126)
    two_crazy          41 = crazy(29524, 29524) = 0 (< 33)

Predicción medible: el runner C debe parar en el paso en que el oráculo entra
por primera vez en una celda no imprimible; con celdas imprimibles debe recorrer
el programa entero y parar en END.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

OPS = {"JMP": 4, "CRAZY": 62, "DLOAD": 40, "NOP": 68, "END": 81}

PIVOT = 41          # celda aterrizada: su valor es el que se prueba
HOP = 42            # celda de salto: 40 -> el JMP aterriza en 41
ENDC = 43           # 38 -> opcode 81 (END) en pc 43
LEN = 44
SEED_NONTWO = 36    # 1100_3: crazy(0, 36) = 29524 (todos los trits a 1)

MODES = {"seed_only": 3, "one_crazy": 3, "two_crazy": 5}

# No existe un control `one_crazy` imprimible: crazy(0, x) mapea los trits de x
# a {1,2} (0->1, 1->1, 2->2), así que su resultado siempre es >= 29524.  Por eso
# las fronteras imprimibles se prueban en modo `seed_only`, que aterriza en la
# misma celda de dato sin pasar por CRAZY.
INSTANCES = {
    "guard_high":        ("one_crazy", SEED_NONTWO),   # 29524 > 126
    "guard_low":         ("two_crazy", SEED_NONTWO),   # 0 < 33
    "control_seed_33":   ("seed_only", 33),            # frontera baja imprimible
    "control_seed_126":  ("seed_only", 126),           # frontera alta imprimible
}


def enc(addr: int, op: int) -> int:
    return 33 + ((op - 33 - addr) % 94)


def pivot_value(mode: str, seed: int) -> int:
    """Valor que queda en la celda 41 cuando el programa aterriza en ella."""
    if mode == "seed_only":
        return seed
    v = oc.crazy_op(0, seed)
    if mode == "one_crazy":
        return v
    return oc.crazy_op(v, v)


def build(mode: str, seed: int) -> bytes:
    if mode not in MODES:
        raise ValueError(mode)
    cells = [enc(a, OPS["NOP"]) for a in range(LEN)]
    cells[0] = enc(0, OPS["DLOAD"])        # == 40: d = mem[0] = 40 -> 41
    if mode == "seed_only":
        cells[1] = enc(1, OPS["NOP"])      # d pasa de 41 a 42 antes del JMP
        cells[2] = enc(2, OPS["JMP"])
    else:
        cells[1] = enc(1, OPS["CRAZY"])
        if mode == "one_crazy":
            cells[2] = enc(2, OPS["JMP"])
        else:
            cells[2] = enc(2, OPS["DLOAD"])   # d = mem[42] = 40 -> 41
            cells[3] = enc(3, OPS["CRAZY"])
            cells[4] = enc(4, OPS["JMP"])
    cells[PIVOT] = seed
    cells[HOP] = PIVOT - 1                  # 40
    cells[ENDC] = (OPS["END"] - ENDC) % 94  # 38
    return bytes(cells)


def build_all() -> dict:
    return {name: build(mode, seed) for name, (mode, seed) in INSTANCES.items()}


def meta_for(name: str) -> dict:
    mode, seed = INSTANCES[name]
    data = build(mode, seed)
    v = pivot_value(mode, seed)
    return {
        "mode": mode,
        "seed_at_pivot": seed,
        "pivot_cell": PIVOT,
        "hop_cell": HOP,
        "end_cell": ENDC,
        "pivot_value": v,
        "pivot_printable": 33 <= v <= 126,
        "opcode_at_pivot": (v + PIVOT) % 94,
        "expected_halt": not (33 <= v <= 126),
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "printable": all(33 <= b <= 126 for b in data),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for name, data in build_all().items():
        (out / (name + ".mb")).write_bytes(data)
        meta = meta_for(name)
        index[name] = meta
        print("%-20s modo=%-10s pivote=%6d imprimible=%-5s opcode=%2d "
              "predice_parada=%s" % (
                  name, meta["mode"], meta["pivot_value"],
                  meta["pivot_printable"], meta["opcode_at_pivot"],
                  meta["expected_halt"]))
    (out / "build_index.json").write_text(json.dumps(index, indent=2) + "\n",
                                          encoding="utf8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
