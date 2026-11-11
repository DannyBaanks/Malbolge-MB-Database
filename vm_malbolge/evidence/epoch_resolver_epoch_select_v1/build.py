#!/usr/bin/env python3
"""build.py — epoch_resolver_epoch_select_v1: la petición elige la ÉPOCA y el PAYLOAD.

En `epoch_resolver_request_v1` la petición ya elegía el *qué* se escribe (los 20
dígitos de control del payload de 10 trits) pero el *dónde* seguía fijo: la celda
de época era la celda 100, decidida por el programa. Aquí se compone el mecanismo
de `epoch_algebra_v3` (selección de la celda de época por puntero, en runtime)
con el payload elegido por la petición.

Resultado: **una sola imagen** sirve para cualquier combinación de (época,
payload) que elija la petición. La petición son 21 bytes:

    byte 0       : b, el byte de época. La celda de época es T = b + 1.
    bytes 1..10  : 2 si el trit p del payload es 1, si no 0   -> control de P
    bytes 11..20 : 2 si el trit p del payload no es 0, si no 0 -> control de M

## El puntero: por qué T = b+1

`W` (celda 52) guarda el byte de época `b` **exacto** (intercambio con la máscara
`29524`: `A1 = crazy(b, 29524)` y `W = crazy(swap(b), 29524)`).

Después, un `DLOAD` que lee `mem[W] = b` deja `d = b`, y el incremento automático
de `d` lo lleva a `b+1 = T`: el `CRAZY` siguiente escribe **justo en la celda de
época**. El mismo truco sirve para el salto final: `JMP` lee `mem[d] = mem[W] = b`
y la ejecución continúa en `b+1 = T`.

El puntero se restaura sin ramas por valor: tras el `CRAZY` en `T`, `d = T+1`, y la
celda sucesora `T+1` guarda un valor `v` que cumple dos papeles a la vez:

  1. `(v + T+1) % 94 = 81` -> la celda sucesora decodifica **END** cuando el PC
     llega a ella tras ejecutar el payload.
  2. `v+1` es una celda que contiene `W-1 = 51`, de modo que
     `DLOAD` -> `d = v` -> `d+1 = v+1` -> `DLOAD` -> `d = 51` -> `d+1 = 52 = W`.

La cadena de dos `DLOAD` es idéntica en las tres épocas: sólo cambian los *valores*
de las celdas de dato, nunca las instrucciones.

## Por qué las épocas no comparten residuo (y por qué eso no importa)

En `epoch_algebra_v3` las tres épocas (36, 130, 224) estaban alineadas a 94 y la
celda sucesora valía 44 en las tres: eso exigía `(W-1 + T+1) % 94 = 81`, o sea
`T ≡ 81 - W (mod 94)`, y con la máscara imprimible `121` la época estaba en
{36,130,224}. Aquí la máscara del payload es `29524` (no imprimible), así que la
celda de época hay que fabricarla en runtime y debe quedar en la zona de dato
alcanzable por saltos imprimibles: `34 <= T <= 126`. En ese rango caben varias
épocas **de residuos distintos**, y cada una necesita su propio valor de sucesor
`v ≡ 80 - T (mod 94)`. De ahí la tabla de tres filas de abajo.

## Celdas (zona de dato 41..126)

    S   = 41   fuente de 29524 (crazy(0,36))
    P   = 44   palabra de control P          45 = 43  (salto de vuelta a P)
    M   = 46   palabra de control M          47 = 45  (salto de vuelta a M)
    A1  = 48   scratch del intercambio del byte de época
    A2  = 49   scratch del intercambio del payload
    W   = 52   puntero: guarda b exacto
    55, 65, 75 = 51   celdas que saltan a W (51 = W-1)
    100, 110, 120     celdas de época (máscara 29524 -> payload)
    101 = 74, 111 = 64, 121 = 54   sucesoras: END + trampolín a W

Tabla de épocas:

    T   | b  | sucesora | valor v | celda que salta a W
    --- | --- | -------- | ------- | -------------------
    100 |  99 |      101 |      74 |                 75
    106 | 105 |      107 |      68 |                 69
    112 | 111 |      113 |      62 |                 63

El payload debe descodificar como OUT en la época elegida: `(V + T) % 94 = 5`.
Como `T` varía, **la época y el payload se eligen juntos**: la misma palabra en
otra época decodifica otro opcode (medido en el probe).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from plan import Planner, PlanError

S = 41            # fuente de 29524
P = 44            # palabra de control P
M = 46            # palabra de control M
A1 = 48           # scratch del byte de época
A2 = 49           # scratch del payload
W = 52            # puntero (guarda b exacto)
NO_TRIT2 = 36     # 1100_3

# T -> (b, celda sucesora, valor sucesor, celda que salta a W)
#
# El valor sucesor cumple (v + T+1) % 94 = 81 (END) y v+1 es una celda que
# contiene W-1 = 51 (el trampolín de vuelta a W).  Las celdas sucesoras se
# quedan <= 113 para que el planificador pueda seguir avanzando d tras cada
# época (su margen de rutado está en DATA_HI-8 = 118).
EPOCH_TABLE = {
    100: {"b": 99, "succ_cell": 101, "succ_val": 74, "hop_to_w": 75},
    106: {"b": 105, "succ_cell": 107, "succ_val": 68, "hop_to_w": 69},
    112: {"b": 111, "succ_cell": 113, "succ_val": 62, "hop_to_w": 63},
}
EPOCHS = tuple(sorted(EPOCH_TABLE))

# (nombre, época, payload). Los payloads cumplen (V + T) % 94 = 5 -> OUT.
INSTANCES = (
    ("e100_p93", 100, 93),
    ("e100_p281", 100, 281),
    ("e100_p29797", 100, 29797),
    ("e106_p275", 106, 275),
    ("e106_p29791", 106, 29791),
    ("e112_p269", 112, 269),
    ("e112_p29785", 112, 29785),
)


def trits(v: int) -> list[int]:
    return [(v // 3 ** i) % 3 for i in range(10)]


def control_digits(v: int) -> bytes:
    """Los 20 dígitos de control que producen el payload `v`."""
    t = trits(v)
    ctrl_p = [2 if x == 1 else 0 for x in t]
    ctrl_m = [2 if x != 0 else 0 for x in t]
    return bytes(ctrl_p + ctrl_m)


def request_for(v: int) -> bytes:
    """Los 20 dígitos de control (sin byte de época)."""
    return control_digits(v)


def request_for_epoch(epoch: int, v: int) -> bytes:
    """La petición completa: byte de época + 20 dígitos de control."""
    return bytes([EPOCH_TABLE[epoch]["b"]]) + control_digits(v)


def expected_p(v: int) -> int:
    return 29524 + sum(3 ** p for p, x in enumerate(trits(v)) if x == 1)


def expected_m(v: int) -> int:
    return 29524 + sum(3 ** p for p, x in enumerate(trits(v)) if x != 0)


def _check_epoch_table() -> None:
    """La tabla de épocas cumple sus tres invariantes."""
    for t, row in EPOCH_TABLE.items():
        v = row["succ_val"]
        if (v + t + 1) % 94 != 81:
            raise PlanError("época %d: el sucesor %d no decodifica END" % (t, v))
        if v + 1 != row["hop_to_w"]:
            raise PlanError("época %d: la celda %d no encadena con W" % (t, v + 1))
        if row["b"] != t - 1:
            raise PlanError("época %d: b=%d no es T-1" % (t, row["b"]))


def _plan():
    _check_epoch_table()
    p = Planner()
    # ---------- semillas de la imagen (todas imprimibles) ----------
    p.seed_free(S, NO_TRIT2)
    p.seed_free(P, NO_TRIT2)
    p.seed_free(P + 1, P - 1)      # 45 -> 43 : salto de vuelta a P
    p.seed_free(M, NO_TRIT2)
    p.seed_free(M + 1, M - 1)      # 47 -> 45 : salto de vuelta a M
    p.seed_free(A1, NO_TRIT2)
    p.seed_free(A2, NO_TRIT2)
    p.seed_free(W, NO_TRIT2)
    for t in EPOCHS:
        p.seed_free(t, NO_TRIT2)
        row = EPOCH_TABLE[t]
        p.seed_free(row["succ_cell"], row["succ_val"])
        p.seed_free(row["hop_to_w"], W - 1)   # 55/65/75 -> 51 : trampolín a W

    # ---------- fase 0: bootstrap de S (a arranca en 0) ----------
    p.seed_free(0, 40)             # 40 decodifica DLOAD en 0 -> d = 41
    p._emit("DLOAD", S)
    p.d = S
    p.crazy(S)                     # S = crazy(0, 36) = 29524 ; a = 29524

    # ---------- salto de zona ----------
    p.park()
    p.zone_jump()

    # ---------- fase 1: fábrica de máscaras ----------
    # Las celdas de época también se fabrican aquí: la máscara 29524 no es
    # imprimible, así que no puede sembrarse en la imagen.
    for cell in (P, M, A1, A2, W) + EPOCHS:
        p.ensure_d(cell)
        p.crazy(cell)              # a=29524 -> celda = 0, a = 0
        p.ensure_d(cell)
        p.crazy(cell)              # a=0 -> celda = 29524, a = 29524

    # ---------- fase 2: el byte de época -> W = b (exacto) ----------
    p.ensure_d(A1)
    p.inn()                        # a = b
    p.ensure_d(A1)
    p.crazy(A1)                    # A1 = crazy(b, 29524) = swap(b) ; a = swap(b)
    p.ensure_d(W)
    p.crazy(W)                     # W = crazy(swap(b), 29524) = b ; a = b

    # ---------- fase 3: el payload elegido por la petición ----------
    def build_word(cell: int) -> None:
        p.ensure_d(cell)
        p.inn()                     # primer byte de control
        p.ensure_d(cell)
        p.crazy(cell)               # posición 0, marco 0
        for _ in range(9):
            p.ensure_d(cell)
            p.rot(cell)             # marco += 1
            p.ensure_d(cell)
            p.inn()                 # siguiente byte de control
            p.ensure_d(cell)
            p.crazy(cell)
        p.ensure_d(cell)
        p.rot(cell)                 # restaura el marco (10 rotaciones = identidad)
                                   # y deja a = la palabra restaurada

    build_word(P)
    build_word(M)                   # a = M al salir

    # ---------- fase 4: V = crazy(M, P) ----------
    p.ensure_d(P)
    p.crazy(P)                      # P = V exacto ; a = V

    # ---------- fase 5: A2 = swap(V) ----------
    p.ensure_d(A2)
    p.crazy(A2)                     # A2 = crazy(V, 29524) = swap(V) ; a = swap(V)

    # ---------- fase 6: escritura exacta en la celda de época ELEGIDA ----------
    # El puntero: d = W -> DLOAD lee mem[W] = b -> d = b -> d+1 = b+1 = T.
    t0 = EPOCHS[0]                 # el planificador modela la primera época
    p.ensure_d(W)
    p._emit("DLOAD", t0)            # lee mem[W] = b -> d = b -> d+1 = T
    p.d = t0
    p.crazy(t0)                     # T = crazy(swap(V), 29524) = V EXACTO

    # ---------- fase 7: salto a la celda de época ----------
    # d = T+1; la sucesora guarda v -> d = v -> d+1 = v+1; esa celda guarda
    # W-1 -> d = W-1 -> d+1 = W; el JMP lee mem[W] = b -> pc = b+1 = T.
    row0 = EPOCH_TABLE[t0]
    p._emit("DLOAD", row0["succ_val"])
    p.d = row0["succ_val"] + 1
    p._emit("DLOAD", W)
    p.d = W
    p.jmp()                         # c = mem[W] = b -> pc = b+1 = T
    return p


def build() -> dict:
    p = _plan()
    data = p.to_bytes()
    meta = {
        "epochs": list(EPOCHS),
        "epoch_table": {str(k): v for k, v in EPOCH_TABLE.items()},
        "pointer_cell": W,
        "request_bytes": 21,
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "printable": all(33 <= b <= 126 for b in data),
        "plan": p.summary(),
    }
    return {"data": data, "meta": meta, "plan": p}


def build_all() -> dict:
    """Una imagen para todas las instancias; lo que cambia es la petición."""
    base = build()
    out = {}
    for name, epoch, v in INSTANCES:
        req = request_for_epoch(epoch, v)
        meta = dict(base["meta"])
        meta.update({
            "epoch": epoch,
            "epoch_byte": EPOCH_TABLE[epoch]["b"],
            "payload": v,
            "expected_p": expected_p(v),
            "expected_m": expected_m(v),
            "expected_out": v % 256,
            "opcode_at_epoch": (v + epoch) % 94,
            "payload_printable": 33 <= v <= 126,
            "request_hex": req.hex(),
        })
        out[name] = {"data": base["data"], "meta": meta, "plan": base["plan"]}
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    built = build_all()
    index = {}
    data = built[INSTANCES[0][0]]["data"]
    (out / "resolver_epoch.mb").write_bytes(data)
    for name, r in built.items():
        index[name] = r["meta"]
        print("%-14s epoca=%3d b=%3d payload=%6d P=%6d M=%6d OUT=%#04x "
              "opcode=%2d peticion=%s" % (
                  name, r["meta"]["epoch"], r["meta"]["epoch_byte"],
                  r["meta"]["payload"], r["meta"]["expected_p"],
                  r["meta"]["expected_m"], r["meta"]["expected_out"],
                  r["meta"]["opcode_at_epoch"], r["meta"]["request_hex"]))
    (out / "build_index.json").write_text(json.dumps(index, indent=2) + "\n",
                                          encoding="utf8")
    (out / "labels.json").write_text(json.dumps(
        {"S": S, "P": P, "M": M, "A1": A1, "A2": A2, "W": W,
         "epoch_table": {str(k): v for k, v in EPOCH_TABLE.items()},
         "no_trit2_seed": NO_TRIT2, "request_bytes": 21,
         "instances": {n: {"epoch": e, "payload": v}
                       for n, e, v in INSTANCES}}, indent=2) + "\n", encoding="utf8")
    print("imagen=resolver_epoch.mb len=%d sha256=%s" % (
        len(data), hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
