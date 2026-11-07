#!/usr/bin/env python3
"""Emisor de la maquina de N instrucciones con empaquetado exacto.

Corrige el bloqueante declarado en `dispatchN.md`: la ventana de destinos no
limita a N=3. La busqueda de N=3 exigia separacion uniforme 14 entre TODOS los
destinos y usaba colas 3k+1. Con el bloque real de cada manejador

    push: [L, L+5+t]      (IN,NOP,MOVD,CRAZY + t NOP + JMP)
    pop:  [L, L+4+t]      (NOP,MOVD,ROT,OUT + t-1 NOP + JMP)

el empaquetado exacto da dos resultados medidos, ambos con coste de rotacion
CERO:

  * N=4 con el protocolo original (push=0x35, pop=0x41) y colas 1,4,7,10.
  * N=5 con push=0xff / pop=0x35 (bandas adyacentes, ventana total 486 celdas)
    y colas 1,2,5,6,9.

El unico choque de celdas de puntero es t_j = t_i + 2 (celda JMP frente a la
celda de entrada del despacho siguiente), asi que una cola con diferencias 1 y
3 es valida. Evidencia: evidence/dispatch4_pack.json, evidence/dispatch5.json,
evidence/dispatch_pack.md.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]

import dispatchN_gen as D  # noqa: E402
import oracle_classic as oc  # noqa: E402

DEFAULT_PUSH = 255     # 0xff: banda 29160 (t5=1)
DEFAULT_POP = 53       # 0x35: banda 29403
DEFAULT_N = 5
DEFAULT_TAILS = [1, 2, 5, 6, 9]   # sin diferencias 2 => sin choque JMP/puntero
STRIDE = 15


def pairs_for(a: int, b: int):
    """Parejas (destino push, destino pop) realizables con V imprimible."""
    out = {}
    for V in range(33, 127):
        p = (oc.crazy_op(a, V), oc.crazy_op(b, V))
        if p not in out:
            out[p] = V
    return out


def blocks_ok(sel, tails):
    """Los 2N bloques [L, L+5+t] / [L, L+4+t] no se solapan."""
    blocks = []
    for (p, q), t in zip(sel, tails):
        blocks.append((p, p + 5 + t))
        blocks.append((q, q + 4 + t))
    blocks.sort()
    return all(blocks[i][1] < blocks[i + 1][0] for i in range(len(blocks) - 1))


def search(a, b, n, tails):
    """Primer conjunto de n parejas empaquetable con una permutacion de tails."""
    pairs = sorted(pairs_for(a, b))
    perms = list(itertools.permutations(tails))
    found = []

    def rec(i, chosen, used):
        if len(chosen) == n:
            for perm in perms:
                if blocks_ok(chosen, perm):
                    found.append((list(chosen), list(perm)))
                    return True
            return False
        if len(chosen) + (len(pairs) - i) < n:
            return False
        for j in range(i, len(pairs)):
            p = pairs[j]
            # necesario: dos destinos a menos de 6 celdas siempre se solapan
            if any(abs(x - y) < 6 for x in p for u in used for y in u):
                continue
            chosen.append(p)
            used.append(p)
            if rec(j + 1, chosen, used):
                return True
            used.pop()
            chosen.pop()
        return False

    if not rec(0, [], []):
        raise RuntimeError(f"no hay {n} parejas empaquetables")
    return found[0]


def search_layout(Vs, tails):
    """Busca (slotA, Ps) que cierre la coreografia de d con stride fijo."""
    for slotA in range(82, 100):
        for P0 in range(96, 141):
            Ps = [P0 + 5 * k for k in range(len(Vs))]
            try:
                code, data, targets = D.plan(Vs, Ps, slotA, len(Vs), tails,
                                             stride=STRIDE)
            except (ValueError, AssertionError):
                continue
            return slotA, Ps
    raise RuntimeError("no se encontro layout valido")


def cases(P, Q):
    return [
        bytes([P, 0x41, Q, P, 0x42, Q]),
        bytes([P, 0x41, P, 0x42, Q, Q]),
        bytes([Q, P, 0x41, Q, P, 0x42]),
        bytes([P, 0x41, P, 0x42, P, 0x43, P, 0x44, P, 0x45]),
        bytes([P, 0x41, Q, Q]),
        bytes([P, 0x41, P]),
        bytes([Q]),
        b"",
        bytes([P, 0x00, Q, P, 0xFF, Q, Q]),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", type=int, default=DEFAULT_PUSH)
    ap.add_argument("--pop", type=int, default=DEFAULT_POP)
    ap.add_argument("-n", "--n", type=int, default=DEFAULT_N)
    ap.add_argument("--tails", type=str,
                    default=",".join(str(t) for t in DEFAULT_TAILS))
    ap.add_argument("--mb", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_dispatch5.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/dispatch5.json")
    args = ap.parse_args()
    args.mb = args.mb.resolve()
    args.json = args.json.resolve()

    tails = [int(x) for x in args.tails.split(",")]
    if len(tails) != args.n:
        sys.exit(f"--tails necesita {args.n} valores, hay {len(tails)}")
    if any(tails[i] + 2 in tails for i in range(len(tails))):
        sys.exit("las colas no pueden diferir en 2 (choque JMP/puntero)")

    D.OP_PUSH, D.OP_POP = args.push, args.pop
    sel, tails = search(args.push, args.pop, args.n, tails)
    vmap = pairs_for(args.push, args.pop)
    Vs = [vmap[pair] for pair in sel]
    slotA, Ps = search_layout(Vs, tails)

    memory, code, data, targets, nbad = D.build(
        Vs, Ps, slotA, len(Vs), tails, stride=STRIDE)
    v0a = data[slotA]
    print(f"protocolo push=0x{args.push:02x} pop=0x{args.pop:02x} | "
          f"V={Vs} colas={tails}")
    print(f"slotA={slotA} Ps={Ps}")
    for k, (tp, tq) in enumerate(targets):
        print(f"  D{k}: push@{tp} pop@{tq}")
    print(f"imagen: {args.mb} ({len(memory)} bytes, {len(code)} celdas de "
          f"codigo, {len(data)} de dato, {nbad} sin opcode valido)")
    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)

    rows, ok = [], 0
    for sb in cases(args.push, args.pop):
        exp = D.model(sb, v0a, len(Vs))
        oout, osteps, ostatus = D.run_oracle(memory, sb)
        oout_b = oout.encode("latin-1")
        rout, rerr = D.run_runner(memory, sb)
        agree = (oout_b == exp) and (rout == exp)
        ok += agree
        rows.append({"stdin": sb.hex(), "esperado": exp.hex(),
                     "oraculo": oout_b.hex(), "runner_c": rout.hex(),
                     "pasos_oraculo": osteps, "status": ostatus,
                     "stderr_runner": rerr, "acuerdo": agree})
        print(f"  {sb.hex()[:40]:40s} esperado={exp.hex():10s} "
              f"oraculo={oout_b.hex():10s} runner={rout.hex():10s} "
              f"{osteps:6d}p {ostatus:8s} {'OK' if agree else 'FALLO'}")
    print(f"\n{ok}/{len(rows)} casos de acuerdo")

    payload = {
        "imagen": str(args.mb.relative_to(ROOT)),
        "bytes": len(memory),
        "sha256": hashlib.sha256(memory).hexdigest(),
        "n_instrucciones": len(Vs),
        "protocolo": {"push": args.push, "pop": args.pop},
        "parametros": {"Vs": Vs, "colas": tails, "slotA": slotA,
                       "Ps": Ps, "v0a": v0a, "stride": STRIDE,
                       "destinos": [list(t) for t in targets]},
        "bloques_manejador": {
            "push": "5+t celdas desde el destino",
            "pop": "4+t celdas desde el destino",
            "regla_choque": "t_j = t_i + 2 (celda JMP vs celda puntero)",
        },
        "codigo_celdas": len(code),
        "dato_celdas": len(data),
        "dato_no_valido": nbad,
        "casos": rows,
        "veredicto": ("DESPACHO_N_EMPAQUETADO_DEMOSTRADO"
                      if ok == len(rows) else "FALLO"),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"evidencia: {args.json}")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
