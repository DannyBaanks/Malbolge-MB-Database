#!/usr/bin/env python3
"""build.py — epoch_resolver_word_v1: resolvedor de épocas con payload de 10 trits.

A diferencia de `epoch_algebra_v3` (máscara imprimible `121`, que sólo cubre
7776/59049 palabras), aquí la máscara es `29524` fabricada en runtime, así que la
escritura exacta vale para **cualquier palabra de 10 trits**, incluido un payload
con trits 2 en posiciones altas — justo lo que `121` no puede escribir.

Celdas (zona de dato 41..126):

    S   = 41   fuente de 29524 (no se consume: es invariante bajo ROT)
    PW  = 44   scratch de la petición (29524 -> swap(b))
    A   = 45   scratch de escritura del payload (29524 -> swap(V))
    P   = 46   celda del payload (29524 -> V)
    R.. = 48.. celdas de rotación, una por máscara (54 = 2000_3)
    SH  = 61   celda de salto estática (T-1) para la variante verificable en C
    T   = 100  celda de época: escrito el payload y ejecutado
    W   = 75   puntero de petición (29524 -> b exacto)
    T+1 = 101  sucesor: 74, que decodifica END en 101

La petición es UN byte de stdin: `b = T - 1`.  El payload `V` se construye en
memoria: parte de 29524 y añade un trit 2 por posición con la máscara
`rot^r(54)`; el construido aquí lleva 2s en las posiciones 1, 3 y 5 (la posición
5 ya sale del alcance de la máscara 121).

Al final el JMP aterriza en `T`, donde el payload decodifica OUT y emite
`V % 256`.  Hay dos variantes:

  * `resolver_word`         — salto con destino conocido en compilación (celda
                              SH = T-1): verificable en los tres motores.
  * `resolver_word_dynamic` — salto por el puntero escrito en runtime (el
                              mecanismo de `epoch_algebra_v3`).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from plan import DATA_HI, OPS, Planner, PlanError, enc

S = 41            # fuente de 29524
PW = 44           # scratch de la petición
A = 45            # scratch de escritura del payload
P = 46            # celda del payload
R = 48            # primeras celdas de rotación (48, 49, 50)
SH = 61           # celda de salto estática
T = 100           # celda de época (escrita y ejecutada)
W = 75            # puntero de petición
SUCC = T + 1      # 101: valor 74 -> decodifica END
NO_TRIT2 = 36     # 1100_3
ROT_SRC = 54      # 2000_3

# posiciones donde el payload lleva un trit 2 y las rotaciones que lo ponen ahí
# (rot^r(54) tiene el 2 en la posición (3-r) mod 10; r=0 se sustituye por 10
# porque la identidad no ejecuta ninguna instrucción y no carga `a`)
TWOS = ((1, 2), (3, 10), (5, 8))
REQUEST = T - 1
V = 29524 + sum(3 ** p for p, _ in TWOS)


def _trits(v: int) -> str:
    return "".join(str((v // 3 ** i) % 3) for i in range(9, -1, -1))


def _plan(mutant: str, static_jump: bool):
    twos = ((1, 2), (3, 0)) if mutant == "mutant_wrong_payload" else TWOS
    rot_cells = [R + i for i in range(len(twos))]
    p = Planner()
    p.seed_free(S, NO_TRIT2)
    p.seed_free(PW, NO_TRIT2)
    p.seed_free(A, NO_TRIT2)
    p.seed_free(P, NO_TRIT2)
    p.seed_free(W, NO_TRIT2)
    p.seed_free(T, 121 if mutant == "mutant_mask_121" else NO_TRIT2)
    p.seed_free(SUCC, 74)
    for _c in rot_cells:
        p.seed_free(_c, ROT_SRC)
    if static_jump:
        p.seed_free(SH, T - 1)

    # ---------- fase 0: bootstrap de S (a arranca en 0) ----------
    p.seed_free(0, 40)                   # 40 decodifica DLOAD en 0 -> d = 41
    p._emit("DLOAD", S)
    p.d = S
    p.crazy(S)                           # S = crazy(0, 36) = 29524 ; a = 29524

    # ---------- salto de zona: el código no cabe en 0..39 ----------
    p.park()
    p.zone_jump()

    # ---------- fase 1: fábrica de máscaras ----------
    for cell in (W, PW, A, P) + (() if mutant == "mutant_mask_121" else (T,)):
        p.ensure_d(cell)
        p.crazy(cell)                    # a=29524 -> celda = 0, a = 0
        p.ensure_d(cell)
        p.crazy(cell)                    # a=0 -> celda = 29524, a = 29524

    # ---------- fase 2: petición (un byte de stdin) ----------
    p.inn()                              # a = b
    p.ensure_d(PW)
    p.crazy(PW)                          # PW = swap(b), a = swap(b)
    p.ensure_d(W)
    p.crazy(W)                           # W = b exacto (el puntero), a = b

    # ---------- fase 3: construcción del payload ----------
    for (pos, rots), rc in zip(twos, rot_cells):
        p.ensure_d(rc)
        for _ in range(rots or 10):
            p.rot(rc)                    # a = rot^r(54): un 2 en la posición pos
            p.ensure_d(rc)
        p.ensure_d(P)
        p.crazy(P)                       # P gana el trit 2 ; a = P

    # ---------- fase 4: escritura exacta en la época ----------
    p.ensure_d(A)
    p.crazy(A)                           # A = swap(V), a = swap(V)
    p.ensure_d(T)
    p.crazy(T)                           # T = V EXACTO, a = V

    # ---------- fase 5: salto a la época ----------
    if static_jump:
        p.ensure_d(SH)
        p.jmp()                          # c = T-1 -> pc = T
    else:
        p.ensure_d(W)                    # DLOAD lee mem[SUCC] = 74 -> d = W
        p.jmp()                          # c = mem[W] = b -> pc = b+1 = T
    return p


def build(mutant: str = "", static_jump: bool = True) -> dict:
    p = _plan(mutant, static_jump)
    payload = (29524 + sum(3 ** q for q, _ in TWOS)
               if mutant != "mutant_wrong_payload" else 29524 + 3 + 27)
    data = p.to_bytes()
    meta = {
        "mutant": mutant or None,
        "static_jump": static_jump,
        "request_byte": REQUEST,
        "epoch_cell": T,
        "successor": SUCC,
        "pointer_cell": W,
        "payload": payload,
        "payload_trits": [int(x) for x in _trits(payload)],
        "twos_positions": [pos for pos, _ in
                           (((1, 0), (3, 0)) if mutant == "mutant_wrong_payload"
                            else TWOS)],
        "expected_out": payload % 256,
        "opcode_at_epoch": (payload + T) % 94,
        "opcode_at_successor": (74 + SUCC) % 94,
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "printable": all(33 <= b <= 126 for b in data),
        "plan": p.summary(),
    }
    return {"data": data, "meta": meta, "plan": p}


def build_all() -> dict:
    return {
        "resolver_word": build("", static_jump=True),
        "resolver_word_dynamic": build("", static_jump=False),
        "mutant_mask_121": build("mutant_mask_121", static_jump=True),
        "mutant_wrong_payload": build("mutant_wrong_payload", static_jump=True),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for name, r in build_all().items():
        (out / (name + ".mb")).write_bytes(r["data"])
        index[name] = r["meta"]
        print(f"{name:24s} len={r['meta']['length']} "
              f"salto={'estático' if r['meta']['static_jump'] else 'dinámico'} "
              f"payload={r['meta']['payload']} OUT={r['meta']['expected_out']} "
              f"imprimible={r['meta']['printable']}")
    (out / "labels.json").write_text(json.dumps(
        {"S": S, "PW": PW, "A": A, "P": P, "R": R, "SH": SH, "T": T, "W": W,
         "SUCC": SUCC, "request": REQUEST, "payload": V,
         "twos": [q for q, _ in TWOS], "no_trit2_seed": NO_TRIT2,
         "rot_src": ROT_SRC}, indent=2) + "\n", encoding="utf8")
    (out / "build_index.json").write_text(json.dumps(index, indent=2) + "\n",
                                          encoding="utf8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
