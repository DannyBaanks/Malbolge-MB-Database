#!/usr/bin/env python3
"""crypto/machine_hell.py — emisor HeLL de la maquina cifradora/descifradora.

Bifurcacion de vm_malbolge/tools/increment_bf/build_hell.py (misma tuberia:
netlist de gates crazy/rot -> HeLL con slots, COUNTER, rama EOF). Diseno de
especializacion finita (como classic_compiler_v0 del repo):

  - Maquina straight-line: (IN, suma/resta con KS_i, OUT) x N + HALT.
    Sin estado ni bucle: el keystream vive como constantes .DATA por posicion,
    insertadas por el generador que posee la clave. La imagen .mb ES el
    portador de la clave (modelo elegido: cifrador/descifrador privados).
  - Netlist aritmetico = kit verificado en adder_full.py (D/G/P/DS/B/Q +
    ripple de 9 pasos + D final), compuesto aqui como IR de gates.
  - Autoverificacion simbolica: el emisor evalua el netlist sobre el dominio
    (input 0..255 + EOF 59048; KS constante por posicion) y ASSERTO que la
    respuesta de cada posicion es exactamente (data+ks)%256 (cipher) o
    (data-ks)%256 (decipher), antes de escribir el HeLL.
  - Rama EOF por posicion: entrada truncada -> HALT limpio, no basura.

Uso: build_machine(ks_bytes, mode, out_hell)  # mode 'cipher' | 'decipher'
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from adder_full import get_gadgets  # noqa: E402

ONE = 29524
TWO = 59048
LOW = sum(3 ** i for i in range(6))
HIGH = ONE - LOW
TBL = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
C256_WORD = 256


def crazy(x, y):
    out, p = 0, 1
    for _ in range(10):
        out += TBL[(y // p) % 3][(x // p) % 3] * p
        p *= 3
    return out % 59049


def rot(x):
    return x // 3 + (x % 3) * 19683


def left(x, n):
    for _ in range((10 - n) % 10):
        x = rot(x)
    return x


_FNS, _N_TABLES, _FOUND = get_gadgets()
GD, GG, GP, GDS, GB, GQ = (_FNS[n] for n in ("D", "G", "P", "DS", "B", "Q"))



def bool_and(x, y):
    g1 = crazy(TWO, x)
    g2 = crazy(y, y)
    g3 = crazy(g1, g2)
    return crazy(g3, y)


def bool_or(x, y):
    g1 = crazy(TWO, y)
    g2 = crazy(x, g1)
    return crazy(g2, g1)


def ripple(g, p, steps=9):
    c = g
    for _ in range(steps):
        c = bool_or(g, bool_and(left(c, 1), p))
    return left(c, 1)


def kit_add(x, y):
    return GD(GD(x, y), ripple(GG(x, y), GP(x, y)))


def kit_sub(x, y):
    return GDS(GDS(x, y), ripple(GB(x, y), GQ(x, y)))


def kit_sub256(x, y):
    return kit_sub(kit_add(x, 256), y)


# ---------------- gadgets desde las expresiones VERIFICADAS (sin transcripcion) ----------------
def parse_gadget_expr(expr):
    """AST de crazy(...) con hojas x, y, 0, ONE, TWO -> arbol de tuplas."""
    tokens = expr.replace("(", " ( ").replace(")", " ) ").replace(",", " , ").split()
    tokens = [t for t in tokens if t != "crazy"]
    pos = [0]

    def take():
        t = tokens[pos[0]]
        pos[0] += 1
        return t

    def parse():
        t = take()
        if t == "(":
            a = parse()
            assert take() == ","
            b = parse()
            assert take() == ")"
            return ("gate", a, b)
        if t in ("x", "y", "0", "ONE", "TWO"):
            return ("leaf", t)
        raise ValueError(t)

    return parse()


_LEAF_MAP = {"0": 0, "ONE": 1, "TWO": 2}


def emit_gadget(em, ast, xvar, yvar):
    kind = ast[0]
    if kind == "leaf":
        name = ast[1]
        if name == "x":
            return xvar
        if name == "y":
            return yvar
        return _LEAF_MAP[name]
    return em.gate(emit_gadget(em, ast[1], xvar, yvar), emit_gadget(em, ast[2], xvar, yvar))


_GADGETS = {n: parse_gadget_expr(_FOUND[n]) for n in ("D", "G", "P", "DS", "B", "Q")}


class Emitter:
    def __init__(self):
        self.ir = []
        self.reg = 0
        self.pos_branch = []  # (indice_ir, var_eofword) por posicion
        self.pos_start = []   # indices de ir donde arranca cada posicion

    def gate(self, a, b):
        self.reg += 1
        dst = f"g{self.reg}"
        self.ir.append(("gate", dst, a, b))
        return dst

    def lrot(self, x, n):
        self.reg += 1
        dst = f"g{self.reg}"
        self.ir.append(("rotate", dst, x, (10 - n) % 10))
        return dst

    def bor(self, x, y):
        g1 = self.gate(2, y)
        g2 = self.gate(x, g1)
        return self.gate(g2, g1)

    def band(self, x, y):
        g1 = self.gate(2, x)
        g2 = self.gate(y, y)
        g3 = self.gate(g1, g2)
        return self.gate(g3, y)

    def D(self, x, y):
        return emit_gadget(self, _GADGETS["D"], x, y)

    def G(self, x, y):
        return emit_gadget(self, _GADGETS["G"], x, y)

    def P(self, x, y):
        return emit_gadget(self, _GADGETS["P"], x, y)

    def DS(self, x, y):
        return emit_gadget(self, _GADGETS["DS"], x, y)

    def B(self, x, y):
        return emit_gadget(self, _GADGETS["B"], x, y)

    def Q(self, x, y):
        return emit_gadget(self, _GADGETS["Q"], x, y)

    def ripple(self, g, p, steps=9):
        c = g
        for _ in range(steps):
            c = self.bor(g, self.band(self.lrot(c, 1), p))
        return self.lrot(c, 1)

    def add(self, x, y):
        return self.D(self.D(x, y), self.ripple(self.G(x, y), self.P(x, y)))

    def sub(self, x, y):
        return self.DS(self.DS(x, y), self.ripple(self.B(x, y), self.Q(x, y)))

    def sub256(self, x, y):
        return self.sub(self.add(x, "C256"), y)

    def eof_analysis(self):
        p = self.gate(self.gate("highmask", "input"), "input")
        for k in (1, 2, 4):
            inner = self.gate(2, p)
            lr = self.lrot(p, k)
            g2 = self.gate(inner, lr)
            g3 = self.gate("highmask", g2)
            p = self.gate(g3, g3)
        eof_first = self.gate(p, "eofmask1")
        return self.gate(eof_first, "eofmask2")


def _broadcast(v, n):
    return [v] * n if not isinstance(v, list) else v


def eval_ir(ir, initial):
    """Evaluacion elemento a elemento sobre el dominio (listas)."""
    n = next(len(v) for v in initial.values() if isinstance(v, list))
    vals = {k: _broadcast(v, n) for k, v in initial.items() if not isinstance(v, list)}
    vals.update({k: v for k, v in initial.items() if isinstance(v, list)})
    for op in ir:
        if op[0] == "branch":
            continue
        _, dst, a, b = op
        wa = _broadcast(a * ONE, n) if isinstance(a, int) else vals[a]
        if op[0] == "gate":
            wb = _broadcast(b * ONE, n) if isinstance(b, int) else vals[b]
            vals[dst] = [crazy(x, y) for x, y in zip(wa, wb)]
        else:
            out = []
            for x in wa:
                for _ in range(b % 10):
                    x = rot(x)
                out.append(x)
            vals[dst] = out
    return vals


def build_machine(ks_bytes, mode, out_hell, verbose=True):
    assert mode in ("cipher", "decipher")
    n = len(ks_bytes)
    em = Emitter()
    answers = []
    for i, ks in enumerate(ks_bytes):
        em.pos_start.append(len(em.ir))
        eofw = em.eof_analysis()
        em.ir.append(("branch", None, eofw, None))
        em.pos_branch.append((len(em.ir) - 1, eofw))
        if mode == "cipher":
            answers.append(em.add("input", f"ks{i}"))
        else:
            answers.append(em.sub256("input", f"ks{i}"))

    # ---- autoverificacion simbolica ----
    initial = {
        "input": list(range(256)) + [59048],
        "highmask": HIGH,
        "lowmask": LOW,
        "eofmask1": 58680,
        "eofmask2": 29528,
        "C256": C256_WORD,
    }
    for i, ks in enumerate(ks_bytes):
        initial[f"ks{i}"] = ks
    final = eval_ir(em.ir, initial)
    for i, (ks, ans) in enumerate(zip(ks_bytes, answers)):
        for x in range(256):
            expect = (x + ks) % 256 if mode == "cipher" else (x - ks) % 256
            got = final[ans][x] % 256
            if got != expect:
                raise SystemExit(f"verificacion simbolica: pos={i} x={x} ks={ks} got={got} exp={expect}")
    if verbose:
        print(f"verificacion simbolica OK: {len(em.ir)} ops, {n} posiciones, modo={mode}")

    # ---- valores por variable + uses + physical ----
    variables = {}

    def call(var, mode_):
        pass  # se define abajo (necesita emit)

    return em, answers, n, initial, final


# ---------------- emision HeLL (porte de la maquinaria de build_hell.py) ----------------
STATE = {}


def emit(s):
    STATE["body"].append(s)


def call(var, mode):
    serial = STATE["serial"] + 1
    STATE["serial"] = serial
    f = f"F{len(STATE['variables'].get(var, [])) + 1}"
    r = f"RET{serial}"
    if f not in STATE["flags"]:
        STATE["flags"].append(f)
    STATE["variables"].setdefault(var, []).append((f, r))
    emit(f" R_{f}\n MOVED {var}_{mode}\n}}\n{{\n{r}:\n R_{"CRAZY" if mode == "crazy" else "ROT"} R_MOVED")


def constant(x):
    STATE["a_slot"] = None
    emit(" ROT " + {0: "C0", 1: "C1", 2: "C2"}[x] + " R_ROT")


def clear(v):
    serial = STATE["serial"] + 1
    STATE["serial"] = serial
    loop = f"CLEAR{serial}"
    constant(1)
    emit(loop + ":")
    call(v, "crazy")
    emit(" COUNTER2 " + loop)
    STATE["a_slot"] = v


def load(v):
    if isinstance(v, str) and STATE["a_slot"] == v:
        return
    if isinstance(v, int):
        constant(v)
        return
    serial = STATE["serial"] + 1
    STATE["serial"] = serial
    loop = f"LOAD{serial}"
    emit(loop + ":")
    constant(2)
    call(v, "crazy")
    emit(" COUNTER2 " + loop)
    STATE["a_slot"] = v


def copy(src, dst):
    STATE["a_slot"] = None
    if isinstance(src, int):
        clear(dst)
        constant({0: 1, 1: 0, 2: 2}[src])
        call(dst, "crazy")
        STATE["a_slot"] = dst
        return
    clear("aux")
    clear(dst)
    load(src)
    call("aux", "crazy")
    call(dst, "crazy")
    STATE["a_slot"] = dst


def emit_hell(em, answers, n, initial, final, out_path):
    STATE.clear()
    STATE.update({"flags": [], "variables": {}, "body": [], "serial": 0, "a_slot": None})

    dom = final  # vals por variable (listas) sobre el dominio
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
    for ans in answers:
        uses[ans] += 1

    ks_vars = {f"ks{i}" for i in range(n)}
    PROTECTED = {"lowmask", "highmask", "eofmask1", "eofmask2", "input", "C256"} | ks_vars
    physical = {"input": "input", "lowmask": "lowmask", "highmask": "highmask",
                "eofmask1": "eofmask1", "eofmask2": "eofmask2", "C256": "C256"}
    for i in range(n):
        physical[f"ks{i}"] = f"ks{i}"
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

    # ramas EOF por posicion: (indice_ir, var_eofword)
    branch_at = {ix: i for i, (ix, _w) in enumerate(em.pos_branch)}
    eof_slot_of_pos = {}
    pos_end = {}
    for i in range(n):
        # ultima op de la posicion = el gate de respuesta
        pos_end[i] = em.pos_start[i + 1] - 1 if i + 1 < n else len(em.ir) - 1

    emit(" START:\n R_MOVED\nENTRY:")
    clear("aux")
    clear("input")
    for mv, cv in [("eofmask1", "ctrlmask1"), ("eofmask2", "ctrlmask2")]:
        clear(mv)
        load(cv)
        call(mv, "crazy")

    for i in range(n):
        if i > 0:
            clear("aux")
            clear("input")
        emit(" IN ?- R_IN")
        call("aux", "crazy")
        call("input", "crazy")
        STATE["a_slot"] = "input"
        for ix in range(em.pos_start[i], pos_end[i] + 1):
            kind, dst, a, b = em.ir[ix]
            emit(f"TRACE{i}_{ix}:")
            pa = physical[a] if isinstance(a, str) else a
            if kind == "branch":
                consume(a)
                eof_slot = pa
                eof_slot_of_pos[i] = eof_slot
                emit(f" MOVED {eof_slot}\n}}\n{{\nEOF_CONTINUE_{i}:\n R_MOVED")
                # NO liberar el slot: su celda DATA lleva la cadena EOF
                continue
            if kind == "gate":
                pb = physical[b] if isinstance(b, str) else b
                consume(a)
                consume(b)
                reuse = isinstance(b, str) and uses[b] == 0 and b not in PROTECTED
                slot = pb if reuse else allocate()
                if not reuse:
                    if isinstance(pb, str) and boolean_operands[ix]:
                        clear(slot)
                        load(pb)
                        call(slot, "crazy")
                        STATE["a_slot"] = slot
                    else:
                        copy(pb, slot)
                load(pa)
                call(slot, "crazy")
                STATE["a_slot"] = slot
                release(a, slot)
                if not reuse:
                    release(b, slot)
            else:
                consume(a)
                reuse = isinstance(a, str) and uses[a] == 0 and a not in PROTECTED
                slot = pa if reuse else allocate()
                if not reuse:
                    copy(pa, slot)
                if b in (5, 6, 9):
                    serial = STATE["serial"] + 1
                    STATE["serial"] = serial
                    loop = f"RLOOP{serial}"
                    end = f"REND{serial}"
                    emit(f" R_MOVED\n{loop}:\n R_MOVED")
                    call(slot, "rot")
                    emit(f" COUNTER{b} {end}\n MOVED {loop}\n}}\n{{\n{end}:")
                elif b == 8:
                    serial = STATE["serial"] + 1
                    STATE["serial"] = serial
                    loop = f"RLOOP{serial}"
                    end = f"RHALF{serial}"
                    prep = f"RPREP{serial}"
                    emit(f"{prep}:\n R_MOVED\n{loop}:\n R_MOVED")
                    call(slot, "rot")
                    emit(f" COUNTER4 {end}\n MOVED {loop}\n}}\n{{\n{end}:\n COUNTER2 {prep}")
                else:
                    for _ in range(b):
                        call(slot, "rot")
                STATE["a_slot"] = slot
                release(a, slot)
            physical[dst] = slot
        # OUT de la respuesta de la posicion
        load(physical[answers[i]])
        emit(" OUT ?- R_OUT")

    emit(" MOVED HALT")

    # ---------- head ----------
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

    # ---------- DATA ----------
    data = "\n.DATA\n"
    for var, calls in STATE["variables"].items():
        data += "\n{\n" + f"{var}_crazy: U_CRAZY {var}\n"
        if any(var + "_rot" in line for line in STATE["body"]):
            data += f"{var}_rot: U_ROT {var}\n"
        val = None
        if var == "lowmask":
            val = LOW
        elif var == "highmask":
            val = HIGH
        elif var == "ctrlmask1":
            val = 58324
        elif var == "ctrlmask2":
            val = 8
        elif var == "C256":
            val = 256
        elif var.startswith("ks") and var[2:].isdigit():
            val = initial[var]
        else:
            val = "C1"
        data += f"{var}: {val}\n"
        for pos, slot in eof_slot_of_pos.items():
            if slot == var:
                data += (f" U_NOP EOF_SKIP_{pos}\n U_NOP EOF_STOP_{pos}\n U_NOP EOF_NOT_{pos}\n"
                         f"EOF_STOP_{pos}: HALT\nEOF_NOT_{pos}: R_MOVED\n MOVED EOF_CONTINUE_{pos}\nEOF_SKIP_{pos}:\n")
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
        "positions": n,
        "flags": len(STATE["flags"]),
        "variables": len(STATE["variables"]),
        "nextslot": STATE["nextslot"],
        "source_bytes": len(source),
        "source_sha256": __import__("hashlib").sha256(source.encode()).hexdigest(),
    }
    return meta


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ks", required=True, help="bytes del keystream en hex, p.ej. 2a3f")
    ap.add_argument("--mode", choices=["cipher", "decipher"], default="cipher")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ks = bytes.fromhex(args.ks)
    em, answers, n, initial, final = build_machine(ks, args.mode, args.out)
    meta = emit_hell(em, answers, n, initial, final, args.out)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
