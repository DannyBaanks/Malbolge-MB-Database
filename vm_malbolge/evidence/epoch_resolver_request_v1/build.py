#!/usr/bin/env python3
"""build.py — epoch_resolver_request_v1: el payload de 10 trits lo elige la petición.

En `epoch_resolver_word_v1` el payload era fijo: la máscara `29524` yanked en
runtime permitía escribir cualquier palabra de 10 trits, pero el *qué* se escribe
lo fijaba el programa. Aquí la petición lleva los dígitos de control y el
programa construye el payload desde ellos.

## Por qué la petición lleva dígitos de control y no los 10 trits

La operación `crazy` es ternaria a nivel de trit: `TBL[celda][ctrl]`, con

    celda=0: ctrl 0->1, 1->0, 2->0
    celda=1: ctrl 0->1, 1->0, 2->2
    celda=2: ctrl 0->2, 1->2, 2->1

Para construir una palabra desde cero el acumulador debe mantener el invariante
`{1,2}` (entonces `ctrl=0` es no-op: 1->1, 2->2) y cada posición se pone a 2 con
un `ctrl=2` en esa posición. Es decir: hace falta un **dígito de control por
posición**, y ese dígito sólo puede ser 0 o 2.

¿Se puede derivar ese dígito del trit pedido? Sería el mapa `0->0, 1->2, 2->0`
(ó `0->0, 1->2, 2->2`). El semigrupo de composiciones de `crazy` sobre un trit
tiene **15 mapas** (enumerados exhaustivamente: `g0=(1,0,0)`, `g1=(1,0,2)`,
`g2=(2,2,1)`), y **ninguno** es uno de esos dos: el mapa alcanzable más cercano
es `(0,0,2)`. Por tanto, con esta álgebra el trit de la petición **no** puede
producir el dígito de control: la interfaz honesta es la que lleva los dígitos.

Nótese que el mapa que sí aparece, `(0,0,2)`, es exactamente el que hace falta
para la fase final: `ctrl=2` donde el trit es 2.

## Descomposición del payload

Con `P` y `M` ambas en `{1,2}^10` (invariante `{1,2}`) el payload vale

    V = crazy(M, P)                      (ctrl = M, celda = P)

y por trit:

    V=0 -> (P=1, M=1)      V=1 -> (P=2, M=2)      V=2 -> (P=1, M=2)

de modo que

    P = 29524 + Σ_{p: trit_p(V)=1} 3^p        (2 donde el trit es 1)
    M = 29524 + Σ_{p: trit_p(V)≠0} 3^p        (2 donde el trit no es 0)

Verificado **exhaustivamente sobre las 59049 palabras**: 0 discrepancias.

## Protocolo de la petición (20 bytes)

    bytes 0..9    : 2 si el trit p del payload es 1, si no 0   -> control de P
    bytes 10..19  : 2 si el trit p del payload no es 0, si no 0 -> control de M

Cada byte se lee con `IN` y se escribe en el acumulador con `crazy`; el
acumulador gira una vez entre escrituras (`ROT`), de modo que la ventana de
escritura avanza de posición en posición sinDestroyir lo ya escrito (el marco se
restaura con un `ROT` final, que además deja `a` = la palabra restaurada).

## Celdas (zona de dato 41..126)

    S   = 41   fuente de 29524 (crazy(0,36))
    P   = 44   palabra de control P (29524 -> ...)
    45  = 43   celda de salto hacia P
    M   = 46   palabra de control M (29524 -> ...)
    47  = 45   celda de salto hacia M
    A   = 48   scratch de la escritura exacta
    SH  = 61   celda de salto estática (T-1)
    T   = 100  celda de época: escrito el payload y ejecutado
    T+1 = 101  sucesor: 74 -> decodifica END
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from plan import Planner, PlanError

S = 41            # fuente de 29524
P = 44            # palabra de control P
M = 46            # palabra de control M
A = 48            # scratch de escritura exacta
SH = 61           # celda de salto estática
T = 100           # celda de época
SUCC = T + 1      # 101: 74 -> END
NO_TRIT2 = 36     # 1100_3

# Payloads de prueba: todos ≡ 93 (mod 94) para que el opcode en T sea OUT.
PAYLOADS = {
    "payload_v93": 93,
    "payload_v187": 187,
    "payload_v281": 281,
    "payload_v29797": 29797,
}


def trits(v: int) -> list[int]:
    return [(v // 3 ** i) % 3 for i in range(10)]


def request_for(v: int) -> bytes:
    """Los 20 dígitos de control que producen el payload `v`."""
    t = trits(v)
    ctrl_p = [2 if x == 1 else 0 for x in t]
    ctrl_m = [2 if x != 0 else 0 for x in t]
    return bytes(ctrl_p + ctrl_m)


def expected_p(v: int) -> int:
    return 29524 + sum(3 ** p for p, x in enumerate(trits(v)) if x == 1)


def expected_m(v: int) -> int:
    return 29524 + sum(3 ** p for p, x in enumerate(trits(v)) if x != 0)


def _plan():
    p = Planner()
    p.seed_free(S, NO_TRIT2)
    p.seed_free(P, NO_TRIT2)
    p.seed_free(M, NO_TRIT2)
    p.seed_free(A, NO_TRIT2)
    p.seed_free(T, NO_TRIT2)
    p.seed_free(SUCC, 74)
    p.seed_free(SH, T - 1)
    p.seed_free(P + 1, P - 1)      # 45 -> 43 : salto de vuelta a P
    p.seed_free(M + 1, M - 1)      # 47 -> 45 : salto de vuelta a M

    # ---------- fase 0: bootstrap de S (a arranca en 0) ----------
    p.seed_free(0, 40)             # 40 decodifica DLOAD en 0 -> d = 41
    p._emit("DLOAD", S)
    p.d = S
    p.crazy(S)                     # S = crazy(0, 36) = 29524 ; a = 29524

    # ---------- salto de zona ----------
    p.park()
    p.zone_jump()

    # ---------- fase 1: fábrica de máscaras ----------
    for cell in (P, M, A, T):
        p.ensure_d(cell)
        p.crazy(cell)              # a=29524 -> celda = 0, a = 0
        p.ensure_d(cell)
        p.crazy(cell)              # a=0 -> celda = 29524, a = 29524

    # ---------- fase 2: el payload elegido por la petición ----------
    # Se construye P (10 dígitos de control) y luego M (10 dígitos).
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

    # ---------- fase 3: V = crazy(M, P) ----------
    p.ensure_d(P)
    p.crazy(P)                      # P = V exacto ; a = V

    # ---------- fase 4: escritura exacta en la época ----------
    p.ensure_d(A)
    p.crazy(A)                      # A = swap(V), a = swap(V)
    p.ensure_d(T)
    p.crazy(T)                      # T = V EXACTO, a = V

    # ---------- fase 5: salto a la época ----------
    p.ensure_d(SH)
    p.jmp()                         # c = T-1 -> pc = T
    return p


def build() -> dict:
    p = _plan()
    data = p.to_bytes()
    meta = {
        "epoch_cell": T,
        "successor": SUCC,
        "pointer_cell": None,
        "request_bytes": 20,
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "printable": all(33 <= b <= 126 for b in data),
        "plan": p.summary(),
    }
    return {"data": data, "meta": meta, "plan": p}


def build_all() -> dict:
    """Una imagen por payload; la imagen es la misma, lo que cambia es la petición."""
    base = build()
    out = {}
    for name, v in PAYLOADS.items():
        meta = dict(base["meta"])
        meta.update({
            "payload": v,
            "expected_p": expected_p(v),
            "expected_m": expected_m(v),
            "expected_out": v % 256,
            "opcode_at_epoch": (v + T) % 94,
            "request_hex": request_for(v).hex(),
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
    # una sola imagen: la petición es lo que selecciona el payload
    data = built["payload_v93"]["data"]
    (out / "resolver_request.mb").write_bytes(data)
    for name, r in built.items():
        index[name] = r["meta"]
        print("%-18s payload=%6d P=%6d M=%6d OUT=%#04x opcode=%2d "
              "peticion=%s" % (
                  name, r["meta"]["payload"], r["meta"]["expected_p"],
                  r["meta"]["expected_m"], r["meta"]["expected_out"],
                  r["meta"]["opcode_at_epoch"], r["meta"]["request_hex"]))
    (out / "build_index.json").write_text(json.dumps(index, indent=2) + "\n",
                                          encoding="utf8")
    (out / "labels.json").write_text(json.dumps(
        {"S": S, "P": P, "M": M, "A": A, "SH": SH, "T": T, "SUCC": SUCC,
         "no_trit2_seed": NO_TRIT2, "request_bytes": 20,
         "payloads": PAYLOADS}, indent=2) + "\n", encoding="utf8")
    print("imagen=%s len=%d sha256=%s" % (
        "resolver_request.mb", len(data),
        hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
