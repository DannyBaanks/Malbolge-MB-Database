#!/usr/bin/env python3
"""epoch_mask_native_v1 — imagen Classic Malbolge AUTÓNOMA que construye
29524 (diez trits iguales a 1) y 59048 (diez trits iguales a 2) en runtime,
sin stdin.

Mecanismo (semántica = tools/oracle_classic.py + runner C original):

  * `a` arranca en 0 en Classic Malbolge, y DLOAD no toca `a`. La PRIMERA
    instrucción útil puede ser por tanto un CRAZY con a = 0 sobre una celda
    imprimible sin ningún trit 2:
        crazy(0, v) = 29524  si v no tiene ningún trit 2
    (por trit: crz[0][0] = 1 y crz[1][0] = 1; crz[2][0] = 2, excluido).
  * A partir de ahí, cada ROT sobre la celda P (que arranca en 54, un trit 2
    en la posición 3) deja en `a` la rotación correspondiente, y el CRAZY
    sobre la celda Q acumuladora añade un 2 en esa posición:
        Q_{S+q} = crazy(P_q, Q_S)      (P_q = rot^q(54))
    Diez iteraciones cubren las diez posiciones (rot desplaza el trit hacia
    abajo: 3,2,1,0,9,8,7,6,5,4) y
        29524 + (3^0+...+3^9) = 29524 + 29524 = 59048.

  Recorrido de `d` (avanza +1 por instrucción; DLOAD: d = mem[d], luego d += 1):

    pc 0   DLOAD  d=0  -> d=mem[0]=40            -> d=41
    pc 1   CRAZY  d=41 -> mem[41]=crazy(0,36)=29524 (a=29524) -> d=42
    pc 2   DLOAD  d=42 -> d=mem[42]=39            -> d=40   (= P)
    pc 3   ROT    d=40 -> mem[40]=rot(54)=18 (a=18) -> d=41   (= Q)
    pc 4   CRAZY  d=41 -> mem[41]=crazy(18,29524) -> d=42
    pc 5   DLOAD  d=42 -> 40      (misma celda de reenvío)
    ...   (bloques de 3 instrucciones × 10)
    pc 32  OUT    emite a % 256 = 59048 % 256 = 168
    pc 33  END

  La imagen tiene 43 bytes: 34 de código (0..33) y tres celdas de dato
  (40 = 54, 41 = 36, 42 = 39), todas imprimibles. No hay stdin, no hay bucle
  (los diez bloques están desenrollados), no hay salto.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40,
       "CRAZY": 62, "NOP": 68, "END": 81}

P = 40          # celda de rotación (arranca en 54 = 2000_3)
Q = 41          # celda acumuladora (arranca en 36 = 1100_3, sin trit 2)
H = 42          # celda de reenvío (39 -> d = 40)
BOOT_STRIDE = 40           # mem[0] = 40 -> d = 41
FWD = 39                   # mem[42] = 39 -> d = 40
NO_TRIT2_BOOT = 36         # 1100_3
ROT_SRC = 54               # 2000_3

BLOCKS = 10
BOOT_LEN = 2                       # pc 0, 1
TAIL = 2                           # OUT, END


def enc(addr: int, op: int) -> int:
    return 33 + ((op - 33 - addr) % 94)


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
        return bytes(self.cells.get(a, enc(a, OPS["NOP"]))
                     for a in range(last + 1))


def build(mutant: str = "") -> tuple[bytes, dict]:
    img = Image()
    img.op(0, OPS["DLOAD"])                    # d = mem[0] = 40 -> 41
    img.byte(0, BOOT_STRIDE)                   # 40 decodifica DLOAD en 0 ✓
    img.op(1, OPS["CRAZY"])                    # a = 0 -> mem[Q] = 29524

    boot = NO_TRIT2_BOOT
    src = ROT_SRC
    fwd = FWD
    nblocks = BLOCKS
    if mutant == "mutant_boot_has_trit2":
        boot = 62                              # 2022_3: el bootstrap falla
    if mutant == "mutant_rot_src":
        src = 36                               # 1100_3: sin ningún trit 2 -> no añade 2s
    if mutant == "mutant_forward":
        fwd = 100                              # el reenvío manda d a 101
    if mutant == "mutant_nine_blocks":
        nblocks = BLOCKS - 1
    if mutant == "bootstrap_only":
        nblocks = 0                             # instancia legítima: sólo el bootstrap

    for i in range(nblocks):
        base = BOOT_LEN + 3 * i
        img.op(base + 0, OPS["DLOAD"])         # d = mem[42] = 39 -> 40
        img.op(base + 1, OPS["ROT"])           # mem[40] = rot(mem[40]); a = ese
        img.op(base + 2, OPS["CRAZY"])         # mem[41] = crazy(a, mem[41])
    out_pc = BOOT_LEN + 3 * nblocks
    img.op(out_pc + 0, OPS["OUT"])
    img.op(out_pc + 1, OPS["END"])

    img.byte(P, src)
    img.byte(Q, boot)
    img.byte(H, fwd)

    data = img.to_bytes()
    good = (boot == NO_TRIT2_BOOT and src == ROT_SRC and fwd == FWD)
    full = good and nblocks == BLOCKS
    only_boot = good and nblocks == 0
    meta = {
        "mutant": mutant or None,
        "negative_control": mutant in NEGATIVE,
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "printable": all(33 <= b <= 126 for b in data),
        "p_cell": P, "q_cell": Q, "h_cell": H,
        "boot_value": boot, "rot_src": src, "forward_value": fwd,
        "blocks": nblocks,
        "expected_q": (59048 if full else (29524 if only_boot else None)),
        "expected_out": (168 if full else (84 if only_boot else None)),
    }
    return data, meta


MUTANTS = ("", "bootstrap_only", "mutant_boot_has_trit2", "mutant_rot_src",
           "mutant_forward", "mutant_nine_blocks")

NEGATIVE = {"mutant_boot_has_trit2", "mutant_rot_src", "mutant_forward",
            "mutant_nine_blocks"}

LABELS = {
    "boot_dload": 0, "boot_crazy": 1,
    "p_cell": P, "q_cell": Q, "h_cell": H,
    "out": None, "end": None,
}
for _i in range(BLOCKS):
    LABELS[f"block{_i}_dload"] = BOOT_LEN + 3 * _i
    LABELS[f"block{_i}_rot"] = BOOT_LEN + 3 * _i + 1
    LABELS[f"block{_i}_crazy"] = BOOT_LEN + 3 * _i + 2
LABELS["out"] = BOOT_LEN + 3 * BLOCKS
LABELS["end"] = BOOT_LEN + 3 * BLOCKS + 1


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for m in MUTANTS:
        name = m or "mask_native"
        data, meta = build(m)
        (out / (name + ".mb")).write_bytes(data)
        index[name] = meta
    (out / "labels.json").write_text(
        json.dumps(LABELS, indent=2, sort_keys=True) + "\n", encoding="utf8")
    (out / "build_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf8")
    for name, meta in index.items():
        print(f"{name:24s} len={meta['length']} bloques={meta['blocks']} "
              f"sha256={meta['sha256']} Q_esperada={meta['expected_q']} "
              f"OUT_esperado={meta['expected_out']} imprimible={meta['printable']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
