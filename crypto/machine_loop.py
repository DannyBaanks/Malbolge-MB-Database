#!/usr/bin/env python3
"""crypto/machine_loop.py — MAQUINA LOOP (M6): cifra/descifra un stream dentro
de Malbolge Classic, con el keystream derivado en la propia VM.

Estructura (cipher):

    LOOP_HEAD:
      IN input                    ; rama EOF ya tuneada -> HALT
      input = ADD(input, ks)      ; netlist completo verificado (kit)
      OUT input                   ; emite (input+ks) % 256 (OUT trunca a 8 bits)
      ks = crazy(ks, c)           ; avance in-place (idioma del repo)
      c  = crazy(c, ONE)          ; c alterna (involucion, sin colisiones)
      MOVED LOOP_HEAD

decipher: mismo con SUB y offset 256 ((x+256-ks)%256 exacto por OUT).

Uso: build_loop_machine(mode, seed_ks, seed_c, out_hell) -> meta
Autoverificacion simbolica sobre el dominio antes de emitir.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import machine_hell as MH  # noqa: E402
from machine_hell import Emitter, eval_ir  # noqa: E402

ONE = MH.ONE


def build_loop_machine(mode, seed_ks, seed_c, out_path, verbose=True):
    assert mode in ("cipher", "decipher")
    em = Emitter()
    # --- rama EOF sobre input (receta/mascaras de la maquina de referencia) ---
    eofw = em.eof_analysis()
    em.ir.append(("branch", None, eofw, None))
    branch_at = len(em.ir) - 1
    # --- netlist aritmetico de una vuelta ---
    if mode == "cipher":
        answer = em.add("input", "ks")
    else:
        answer = em.sub256("input", "ks")

    # --- autoverificacion simbolica (dominio: input 0..255 + EOF; ks/c fijos) ---
    initial = {
        "input": list(range(256)) + [59048],
        "highmask": HIGH_,
        "lowmask": LOW_,
        "eofmask1": 58680,
        "eofmask2": 29528,
        "ks": seed_ks,
        "C256": 256,
    }
    final = eval_ir(em.ir, initial)
    for x in range(256):
        expect = (x + seed_ks) % 256 if mode == "cipher" else (x - seed_ks) % 256
        if final[answer][x] % 256 != expect:
            raise SystemExit(f"verificacion simbolica: x={x} ks={seed_ks} mode={mode}")
    if verbose:
        print(f"verificacion simbolica OK: {len(em.ir)} ops, mode={mode}, ks_seed={seed_ks}")

    STATE = MH.STATE
    STATE.clear()
    STATE.update({"flags": [], "variables": {}, "body": [], "serial": 0, "a_slot": None})

    dom = final
    n_dom = len(initial["input"])

    def words(v):
        return [v * ONE] * n_dom if isinstance(v, int) else dom[v]

    def boolean_words(ws):
        return all(all((x // (3 ** i)) % 3 != 2 for i in range(10)) for x in ws)

    boolean_operands = {}
    for ix, op in enumerate(em.ir):
        if op[0] == "branch":
            continue
        boolean_operands[ix] = boolean_words(words(op[2])) if not isinstance(op[2], int) else True

    uses = Counter()
    for kind, dst, a, b in em.ir:
        if isinstance(a, str):
            uses[a] += 1
        if kind == "gate" and isinstance(b, str):
            uses[b] += 1
    uses[answer] += 1

    ks_c = {"ks", "c"}
    PROTECTED = {"lowmask", "highmask", "eofmask1", "eofmask2", "input", "C256"} | ks_c
    physical = {"input": "input", "lowmask": "lowmask", "highmask": "highmask",
                "eofmask1": "eofmask1", "eofmask2": "eofmask2", "C256": "C256",
                "ks": "ks", "c": "c"}
    free = []
    STATE["nextslot"] = 0

    def allocate():
        if free:
            return free.pop()
        STATE["nextslot"] += 1
        return f"t{STATE['nextslot']}"

    def consume(x):
        if isinstance(x, str):
            uses[x] -= 1

    def release(x, keep):
        if isinstance(x, str) and uses[x] == 0 and x not in PROTECTED:
            slot = physical[x]
            if slot != keep and slot not in free:
                free.append(slot)

    # ---------------- cuerpo ----------------
    MH.emit(" START:\n R_MOVED\nENTRY:")
    MH.clear("aux")
    MH.clear("input")
    for mv, cv in [("eofmask1", "ctrlmask1"), ("eofmask2", "ctrlmask2")]:
        MH.clear(mv)
        MH.load(cv)
        MH.call(mv, "crazy")
    MH.emit("LOOP_HEAD:")
    MH.clear("aux")
    MH.clear("input")
    MH.emit(" IN ?- R_IN")
    MH.call("aux", "crazy")
    MH.call("input", "crazy")
    STATE["a_slot"] = "input"

    for ix, (kind, dst, a, b) in enumerate(em.ir):
        MH.emit(f"TRACE{ix}:")
        pa = physical[a] if isinstance(a, str) else a
        if kind == "branch":
            consume(a)
            eof_slot = pa
            MH.emit(f" MOVED {eof_slot}\n}}\n{{\nEOF_CONTINUE:\n R_MOVED")
            continue  # el slot eof no se libera: su DATA lleva la cadena
        if kind == "gate":
            pb = physical[b] if isinstance(b, str) else b
            consume(a)
            consume(b)
            reuse = isinstance(b, str) and uses[b] == 0 and b not in PROTECTED
            slot = pb if reuse else allocate()
            if not reuse:
                if isinstance(pb, str) and boolean_operands[ix]:
                    MH.clear(slot)
                    MH.load(pb)
                    MH.call(slot, "crazy")
                    STATE["a_slot"] = slot
                else:
                    MH.copy(pb, slot)
            MH.load(pa)
            MH.call(slot, "crazy")
            STATE["a_slot"] = slot
            release(a, slot)
            if not reuse:
                release(b, slot)
        else:  # rotate
            consume(a)
            reuse = isinstance(a, str) and uses[a] == 0 and a not in PROTECTED
            slot = pa if reuse else allocate()
            if not reuse:
                MH.copy(pa, slot)
            if b in (5, 6, 9):
                serial = STATE["serial"] + 1
                STATE["serial"] = serial
                loop, end = f"RLOOP{serial}", f"REND{serial}"
                MH.emit(f" R_MOVED\n{loop}:\n R_MOVED")
                MH.call(slot, "rot")
                MH.emit(f" COUNTER{b} {end}\n MOVED {loop}\n}}\n{{\n{end}:")
            elif b == 8:
                serial = STATE["serial"] + 1
                STATE["serial"] = serial
                loop, end, prep = f"RLOOP{serial}", f"RHALF{serial}", f"RPREP{serial}"
                MH.emit(f"{prep}:\n R_MOVED\n{loop}:\n R_MOVED")
                MH.call(slot, "rot")
                MH.emit(f" COUNTER4 {end}\n MOVED {loop}\n}}\n{{\n{end}:\n COUNTER2 {prep}")
            else:
                for _ in range(b):
                    MH.call(slot, "rot")
            STATE["a_slot"] = slot
            release(a, slot)
        physical[dst] = slot

    # salida de la vuelta
    MH.load(physical[answer])
    MH.emit(" OUT ?- R_OUT")

    # avance del keystream, in-place (mismo idioma que la init de mascaras)
    MH.load("c")
    MH.call("ks", "crazy")          # mem[ks] = crazy(A=c, mem[ks])
    MH.constant(1)
    MH.call("c", "crazy")           # mem[c] = crazy(A=ONE, mem[c])

    # loop-back
    MH.emit(" MOVED LOOP_HEAD")

    # ---------------- head / DATA (porte de la plantilla) ----------------
    head = """.CODE
MOVED: MovD/Nop
 Jmp

CRAZY: Opr/Nop
 Jmp

ROT: Rot/Nop
 Jmp

IN: In/Nop
 Jmp

OUT: Out/Nop
 Jmp

NOP: Jmp

HALT: Hlt

@58329
NON_EOF_0: RNop
 RNop
 Jmp

@58338
NON_EOF_1: RNop
 RNop
 Jmp

@58365
NON_EOF_2: RNop
 RNop
 Jmp

@58446
NON_EOF_3: RNop
 RNop
 Jmp

@58689
EOF_CODE: RNop
 Jmp

COUNTER2: MovD/Nop
 Jmp

COUNTER4: Nop/Nop/Nop/MovD
 Jmp

COUNTER5: Nop/Nop/Nop/Nop/MovD
 Jmp

COUNTER6: Nop/Nop/Nop/Nop/Nop/MovD
 Jmp

COUNTER9: Nop/Nop/Nop/Nop/Nop/Nop/Nop/Nop/MovD
 Jmp

"""
    head += "\n".join(f"{f}: Nop/MovD\n Jmp\n" for f in STATE["flags"])
    data = "\n.DATA\n"
    for var, calls in STATE["variables"].items():
        data += "\n{\n" + f"{var}_crazy: U_CRAZY {var}\n"
        if any(var + "_rot" in line for line in STATE["body"]):
            data += f"{var}_rot: U_ROT {var}\n"
        if var == "lowmask":
            val = MH.LOW
        elif var == "highmask":
            val = MH.HIGH
        elif var == "ctrlmask1":
            val = 58324
        elif var == "ctrlmask2":
            val = 8
        elif var == "C256":
            val = 256
        elif var == "ks":
            val = seed_ks
        elif var == "c":
            val = seed_c
        else:
            val = "C1"
        data += f"{var}: {val}\n"
        if var == eof_slot:
            data += (" U_NOP EOF_SKIP\n U_NOP EOF_STOP\n U_NOP EOF_NOT\n"
                     "EOF_STOP: HALT\nEOF_NOT: R_MOVED\n MOVED EOF_CONTINUE\nEOF_SKIP:\n")
        for f, r in calls:
            data += f" {f} {r} R_{f}\n"
        data += "}\n"

    source = head + data + "\n{\n" + "\n".join(STATE["body"]) + "\n}\n"
    p = pathlib.Path(out_path)
    if p.exists():
        raise FileExistsError(p)
    p.write_text(source, encoding="utf-8", errors="strict")
    meta = {
        "ops": len(em.ir),
        "mode": mode,
        "flags": len(STATE["flags"]),
        "variables": len(STATE["variables"]),
        "nextslot": STATE["nextslot"],
        "source_bytes": len(source),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    if verbose:
        print(json.dumps(meta, indent=2))
    return meta


HIGH_ = MH.HIGH
LOW_ = MH.LOW


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["cipher", "decipher"], default="cipher")
    ap.add_argument("--seed-ks", default="42")
    ap.add_argument("--seed-c", default="15")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    build_loop_machine(args.mode, int(args.seed_ks, 0), int(args.seed_c, 0), args.out)


if __name__ == "__main__":
    main()