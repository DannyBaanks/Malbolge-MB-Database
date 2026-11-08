#!/usr/bin/env python3
"""v3: resolvedor de epocas en runtime (Malbolge Classic, imagen cruda).

Construye la imagen del resolvedor y sus controles negativos.

Mecanismo (semantica = tools/oracle_classic.py y runners/malbolge-original/malbolge):

  La peticion trae DOS bytes por stdin: b (byte de peticion) y V (payload).
  b selecciona la celda de epoca T = b + 1:
      b =  35 -> T =  36   (clase de residuos 36 mod 94)
      b = 129 -> T = 130
      b = 223 -> T = 224
  Las tres celdas de epoca estan separadas por 94 y comparten residuo, de modo que
  el MISMO byte de payload decodifica al MISMO opcode en las tres.

  Escritura EXACTA: crazy(V,121) = crazy(crazy(V,121),121) para todo V de byte
  (121 = 11111_3 -> trits 0..4 en 1; en un byte el trit 5 solo puede ser 0 o 1).
  La doble aplicacion exige que la CELDULA contenga 121 en los dos pasos:
      celda 47 (scratch): 121 -> crazy(b,121)      = b'
      celda 45 (puntero): 121 -> crazy(b',121)     = b      (exacto)
      celda 49 (scratch): 121 -> crazy(V,121)      = V'
      celda T  (epoca):   121 -> crazy(V',121)     = V      (exacto)

  El puntero se restaura sin ramas: tras escribir en T, d = T+1 y la celda T+1
  vale 44 (= W-1); DLOAD sobre ella devuelve d = 45 = W, y el JMP lee mem[45]=b,
  de modo que la ejecucion continua en b+1 = T.

  Secuencia (d avanza +1 por instruccion; DLOAD: d = mem[d], luego d += 1):
    pc 0  DLOAD   d=0  -> d=mem[0]=40            -> d=41
    pc 1  DLOAD   d=41 -> d=mem[41]=44            -> d=45   (W)
    pc 2  IN      d=45 -> a=b                     -> d=46
    pc 3  DLOAD   d=46 -> d=mem[46]=46            -> d=47   (scratch peticion)
    pc 4  CRAZY   d=47 -> mem[47]=crazy(b,121)=b' -> d=48
    pc 5  DLOAD   d=48 -> d=mem[48]=44            -> d=45   (W)
    pc 6  CRAZY   d=45 -> mem[45]=crazy(b',121)=b -> d=46   (puntero exacto)
    pc 7  IN      d=46 -> a=V                     -> d=47
    pc 8  NOP     d=47                            -> d=48
    pc 9  NOP     d=48                            -> d=49   (scratch payload)
    pc10  CRAZY   d=49 -> mem[49]=crazy(V,121)=V' -> d=50
    pc11  DLOAD   d=50 -> d=mem[50]=44            -> d=45   (W)
    pc12  DLOAD   d=45 -> d=mem[45]=b             -> d=b+1  (T)
    pc13  CRAZY   d=T  -> mem[T]=crazy(V',121)=V   -> d=T+1  (payload exacto)
    pc14  DLOAD   d=T+1-> d=mem[T+1]=44           -> d=45   (W)
    pc15  JMP     d=45 -> c=mem[45]=b             -> pc=b+1 (T)
    pc T  OUT     (payload ejecutado: opcode (V+T)%94)
    pc T+1 END    (44 -> opcode (44+T+1)%94 = 81)

  No hay ninguna comparacion por valor: la unica decision es la direccion fisica
  T leida del puntero.

  La imagen se construye byte a byte (no con LMAO) porque el experimento exige
  colocacion ABSOLUTA de las celdas de epoca en 36/130/224 (94 de separacion) y
  de las celdas de mascara en 121 (imprimible, requisito del loader Classic) y
  LMAO coloca celdas de datos mediante un stub de arranque que reescribe d y c.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MEM = 59049
OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40,
       "CRAZY": 62, "NOP": 68, "END": 81}
TRI = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
XLAT2 = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<."
         "TVac`uY*MK'X~xDl}REokN:#?G\"i@")
assert len(XLAT2) == 94
ENC = {33 + i: ord(XLAT2[i]) for i in range(94)}

MASK = 121            # mascara imprimible de doble crazy para payloads de byte
W = 45                # celda del puntero (121 -> b)
W1 = 47               # scratch de la peticion (121 -> b')
S = 49                # scratch del payload (121 -> V')
H41, H46, H48, H50 = 41, 46, 48, 50
E = 36                # base de la clase de residuos (36 mod 94)
EPOCHS = [E, E + 94, E + 188]          # 36, 130, 224
RESET_VAL = W - 1     # 44: valor de las celdas sucesoras (END + puntero DLOAD)

MUTANTS = ("", "mutant_residue", "mutant_journal",
           "mutant_pointer", "mutant_mask", "mutant_target")

LABELS = {
    "boot": 0, "boot_dload": 1, "in_request": 2, "req_ptr": 3, "req_crazy": 4,
    "ptr_ptr": 5, "ptr_crazy": 6, "in_payload": 7, "pad1": 8, "pad2": 9,
    "pay_crazy": 10, "pay_ptr": 11, "target_ptr": 12, "target_crazy": 13,
    "post_ptr": 14, "jump": 15,
    "ptr_cell": W, "req_scratch": W1, "pay_scratch": S,
    "helper41": H41, "helper46": H46, "helper48": H48, "helper50": H50,
}
for _i, _e in enumerate(EPOCHS):
    LABELS[f"epoch{_i}"] = _e
    LABELS[f"epoch{_i}_succ"] = _e + 1


def crazy_op(x: int, y: int) -> int:
    res = 0
    p = 1
    for _ in range(10):
        res += TRI[y % 3][x % 3] * p
        x //= 3
        y //= 3
        p *= 3
    return res


def enc(addr: int, op: int) -> int:
    """Byte imprimible que decodifica a `op` en `addr`."""
    return 33 + ((op - 33 - addr) % 94)


def opcode(byte: int, addr: int) -> int:
    return (byte + addr) % 94


def rot_op(x: int) -> int:
    return (x // 3) + (x % 3) * 19683


class Image:
    def __init__(self) -> None:
        self.cells: dict[int, int] = {}

    def op(self, addr: int, op: int) -> None:
        self.cells[addr] = enc(addr, op)

    def byte(self, addr: int, value: int) -> None:
        assert 33 <= value <= 126, (addr, value)
        self.cells[addr] = value

    def to_bytes(self) -> bytes:
        last = max(self.cells)
        out = bytearray()
        for a in range(last + 1):
            out.append(self.cells.get(a, enc(a, OPS["NOP"])))
        return bytes(out)


def build(mutant: str = "") -> tuple[bytes, dict]:
    """`mutant` selecciona un control negativo del paso 4."""
    img = Image()

    # --- celdas de datos ---
    img.byte(H41, RESET_VAL)      # 44 -> d = 44 -> d = 45 = W
    img.byte(W, MASK)              # puntero (121 -> b)
    img.byte(H46, H46)             # 46 -> d = 46 -> d = 47 = scratch peticion
    img.byte(W1, MASK)             # scratch peticion (121 -> b')
    img.byte(H48, RESET_VAL)       # 44 -> d = 45 = W
    img.byte(S, MASK)              # scratch payload (121 -> V')
    img.byte(H50, RESET_VAL)       # 44 -> d = 45 = W

    # --- celdas de epoca (mascara inicial) y sucesoras (44 = END y puntero) ---
    epochs = list(EPOCHS)
    if mutant == "mutant_residue":
        epochs = [EPOCHS[0], EPOCHS[1], EPOCHS[2] - 1]     # 223 -> residuo 35
    for idx, ep in enumerate(epochs):
        mask = MASK
        if mutant == "mutant_mask" and idx == 2:
            mask = 122                                     # mascara rota
        img.byte(ep, mask)
        img.byte(ep + 1, RESET_VAL)
    if mutant == "mutant_journal":
        img.byte(S, 122)                                    # scratch corrupto
    if mutant == "mutant_pointer":
        img.byte(W, 122)                                    # puntero corrupto
    if mutant == "mutant_target":
        img.byte(H50, 60)                                   # d -> 61 (otro bloque)

    # --- codigo ---
    img.op(0, OPS["DLOAD"])
    img.op(1, OPS["DLOAD"])
    img.op(2, OPS["IN"])
    img.op(3, OPS["DLOAD"])
    img.op(4, OPS["CRAZY"])
    img.op(5, OPS["DLOAD"])
    img.op(6, OPS["CRAZY"])
    img.op(7, OPS["IN"])
    img.op(8, OPS["NOP"])
    img.op(9, OPS["NOP"])
    img.op(10, OPS["CRAZY"])
    img.op(11, OPS["DLOAD"])
    img.op(12, OPS["DLOAD"])
    img.op(13, OPS["CRAZY"])
    img.op(14, OPS["DLOAD"])
    img.op(15, OPS["JMP"])

    data = img.to_bytes()
    meta = {
        "mutant": mutant or None,
        "epochs": epochs,
        "epoch_residues": [e % 94 for e in epochs],
        "aligned": len({e % 94 for e in epochs}) == 1,
        "request_bytes": {str(e): e - 1 for e in epochs},
        "mask": MASK,
        "pointer_cell": W,
        "scratch_cells": [W1, S],
        "successor_value": RESET_VAL,
        "payload_out_byte": 63,
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    return data, meta


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for mutant in MUTANTS:
        name = mutant or "resolver"
        data, meta = build(mutant)
        (out / (name + ".mb")).write_bytes(data)
        index[name] = meta
    (out / "labels.json").write_text(
        json.dumps(LABELS, indent=2, sort_keys=True) + "\n", encoding="utf8")
    (out / "build_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf8")
    for name, meta in index.items():
        print(f"{name:16s} len={meta['length']} sha256={meta['sha256']} "
              f"epochs={meta['epochs']} residuos={meta['epoch_residues']} "
              f"alineado={meta['aligned']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
