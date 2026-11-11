#!/usr/bin/env python3
"""probe.py — epoch_rearm_budget_v1: presupuesto de re-armar el resolvedor de épocas.

Puertas en GATES.md (commit 4a5b0b0, anterior a este archivo). No construye el bucle:
mide, desde la traza, qué cuesta devolver la memoria al estado de la imagen.
Uso:  python3 -I probe.py      (escribe results.json; exit 0 si G0..G3 pasan)
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math

from pathlib import Path

PACK = Path(__file__).resolve().parent
EVID = PACK.parent
IMG_PATH = EVID / "epoch_resolver_epoch_select_v1" / "resolver_epoch.mb"
INDEP = EVID / "epoch_audit_v1" / "indep_interpreter.py"

N = 3 ** 10
O = ((1, 0, 0), (1, 0, 2), (2, 2, 1))          # O[trit de memoria][trit de a]
X2 = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X"
      "~xDl}REokN:#?G\"i@")
ENC = {33 + i: ord(ch) for i, ch in enumerate(X2)}
MASK = 29524
SEEDED_HOP_MAX = 127          # DLOAD con valor imprimible deja d <= 126 + 1
INSTANCES = ((100, 93), (100, 281), (100, 29797), (106, 275), (106, 29791),
             (112, 269), (112, 29785))
CONTROL_EPOCH_BYTE = 50


def crz(a: int, m: int) -> int:
    r, p = 0, 1
    for _ in range(10):
        r += O[m % 3][a % 3] * p
        a //= 3
        m //= 3
        p *= 3
    return r


def rot(v: int) -> int:
    return v // 3 + (v % 3) * 19683


def trits(v: int) -> list[int]:
    return [(v // 3 ** i) % 3 for i in range(10)]


def swap01(v: int) -> int:
    return sum((1 if t == 0 else 0 if t == 1 else 2) * 3 ** i for i, t in enumerate(trits(v)))


def request(epoch_byte: int, payload: int) -> bytes:
    t = trits(payload)
    return bytes([epoch_byte] + [2 if x == 1 else 0 for x in t] + [2 if x != 0 else 0 for x in t])


def trace(img: bytes, inp: bytes, max_steps: int = 20000) -> dict:
    mem = list(img) + [0] * (N - len(img))
    for i in range(len(img), N):
        mem[i] = crz(mem[i - 1], mem[i - 2])
    mem0 = list(mem)
    a = c = d = 0
    ip = 0
    out: list[int] = []
    pcs: list[int] = []
    status = "MAX_STEPS"
    for _ in range(max_steps):
        pcs.append(c)
        op = (mem[c] + c) % 94
        if op == 4:
            c = mem[d]
        elif op == 5:
            out.append(a % 256)
        elif op == 23:
            if ip >= len(inp):
                status = "EOF"
                break
            a = inp[ip]
            ip += 1
        elif op == 39:
            mem[d] = rot(mem[d])
            a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = crz(a, mem[d])
            a = mem[d]
        elif op == 81:
            status = "HALTED"
            break
        if 33 <= mem[c] <= 126:
            mem[c] = ENC[mem[c]]
        c = (c + 1) % N
        d = (d + 1) % N
    return {"mem0": mem0, "mem": mem, "pcs": pcs, "out": bytes(out),
            "steps": len(pcs), "status": status}


def load_cost_table() -> dict[int, tuple]:
    """Coste mínimo (en instrucciones de carga) de dejar cada palabra en `a`.

    ROT^i de una celda sembrada p (i = 1..10)            -> coste i, 0 celdas consumidas
    ROT^i de p, luego CRAZY contra q rotada j (j = 0..9)  -> coste i + j + 1, 1 consumida
    """
    best: dict[int, tuple] = {}
    orbit = {}
    for p in range(33, 127):
        x, seq = p, []
        for _ in range(10):
            x = rot(x)
            seq.append(x)
        orbit[p] = seq                      # seq[i-1] = rot^i(p)
    for p, seq in orbit.items():
        for i, x in enumerate(seq, start=1):
            if x not in best or i < best[x][0]:
                best[x] = (i, "rot", p, i, None, None, 0)
    ys = []
    for q in range(33, 127):
        y = q
        for j in range(10):
            ys.append((y, q, j))
            y = rot(y)
    for p, seq in orbit.items():
        for i, x in enumerate(seq, start=1):
            for y, q, j in ys:
                w = crz(x, y)
                cost = i + j + 1
                if w not in best or cost < best[w][0]:
                    best[w] = (cost, "rot+crazy", p, i, q, j, 1)
    return best


def ctrl_set(orig: int, dirty: int) -> list[int]:
    opts = []
    for vo, wd in zip(trits(orig), trits(dirty)):
        cand = [a for a in range(3) if O[wd][a] == vo]
        if not cand:
            return []
        opts.append(cand)
    return [sum(x * 3 ** i for i, x in enumerate(t)) for t in itertools.product(*opts)]


def restore_plan(orig: int, dirty: int, table: dict) -> dict:
    via_a = None
    for ctrl in ctrl_set(orig, dirty):
        if ctrl in table:
            cost = table[ctrl][0] + 1                       # carga + CRAZY de restore
            if via_a is None or cost < via_a["cost"]:
                via_a = {"cost": cost, "ctrl": ctrl, "aux_consumed": table[ctrl][6]}
    via_b = None
    sw = swap01(orig)
    if MASK in table and sw in table:
        # carga 29524, CRAZY (-> extract2), CRAZY (-> 29524), carga swap01, CRAZY (-> orig)
        cost = table[MASK][0] + 2 + table[sw][0] + 1
        via_b = {"cost": cost, "aux_consumed": table[MASK][6] + table[sw][6]}
    choice = min((x for x in (via_a, via_b) if x), key=lambda x: x["cost"], default=None)
    return {"via_a": via_a, "via_b": via_b,
            "best": None if choice is None else ("A" if choice is via_a else "B"),
            "cost": None if choice is None else choice["cost"],
            "aux_consumed": None if choice is None else choice["aux_consumed"]}


def xlat2_cycles() -> dict[int, int]:
    length = {}
    for v in range(33, 127):
        x, k = ENC[v], 1
        while x != v:
            x = ENC[x]
            k += 1
        length[v] = k
    return length


def budget(tr: dict, table: dict) -> dict:
    mem0, mem = tr["mem0"], tr["mem"]
    body = sorted(set(tr["pcs"]))
    dirty = [i for i in range(N) if mem0[i] != mem[i]]
    plans = {i: restore_plan(mem0[i], mem[i], table) for i in dirty}
    unrestorable = [i for i, p in plans.items() if p["best"] is None]
    load_restore = sum(p["cost"] for p in plans.values() if p["cost"] is not None)
    aux = sum(p["aux_consumed"] for p in plans.values() if p["aux_consumed"] is not None)
    high = [i for i in dirty if i > SEEDED_HOP_MAX]
    addr = 0
    for t in high:                      # cota inferior por celda: caminar d o escribir un puntero
        walk = t - SEEDED_HOP_MAX
        ptr = table[t - 1][0] + 2 if (t - 1) in table else None
        addr += walk if ptr is None else min(walk, ptr)
    restorer = load_restore + addr      # instrucciones, cota inferior (sin rutado bajo 127)
    return {"body_cells": len(body), "body_min": body[0], "body_max": body[-1],
            "body_repeated_executions": tr["steps"] - len(body),
            "dirty_cells": len(dirty),
            "dirty_code": sum(1 for i in dirty if i in set(body)),
            "dirty_data": sum(1 for i in dirty if i not in set(body)),
            "via_a": sum(1 for p in plans.values() if p["best"] == "A"),
            "via_b": sum(1 for p in plans.values() if p["best"] == "B"),
            "unrestorable": unrestorable,
            "load_and_restore_instr": load_restore,
            "aux_cells_consumed": aux,
            "dirty_above_127": len(high),
            "addressing_lower_bound_instr": addr,
            "restorer_lower_bound_instr": restorer,
            "per_cell_cost_min": min((p["cost"] for p in plans.values() if p["cost"]), default=None),
            "per_cell_cost_max": max((p["cost"] for p in plans.values() if p["cost"]), default=None)}


def verdict(b: dict) -> str:
    if b["unrestorable"]:
        return "BLOCKED(RESTORE)"
    if b["restorer_lower_bound_instr"] + b["aux_cells_consumed"] > N:
        return "BLOCKED(MEMORY)"
    if b["addressing_lower_bound_instr"] > N:
        return "BLOCKED(ADDRESSING)"
    if b["restorer_lower_bound_instr"] >= b["body_cells"]:
        return "BLOCKED(REGRESS)"
    return "FEASIBLE_BUDGET"


def main() -> int:
    img = IMG_PATH.read_bytes()
    ns: dict = {}
    exec(INDEP.read_text().split("img=open")[0], ns)        # intérprete independiente
    results: dict = {"image_sha256": hashlib.sha256(img).hexdigest(), "image_len": len(img)}

    # G0
    g0 = []
    for t, v in INSTANCES:
        req = request(t - 1, v)
        mine = trace(img, req)
        ind = ns["run"](img, req, maxs=20000)
        g0.append({"epoch": t, "payload": v, "out": mine["out"].hex(), "steps": mine["steps"],
                   "status": mine["status"], "agree": (mine["out"], mine["steps"], mine["status"])
                   == (ind["out"], ind["steps"], ind["status"])})
    results["g0"] = g0
    g0_ok = all(r["agree"] for r in g0)
    print("[G0] trazador vs intérprete independiente: %d/%d coinciden" % (sum(r["agree"] for r in g0), len(g0)))

    table = load_cost_table()
    results["reachable_words"] = len(table)
    print("[tabla] palabras alcanzables (ROT o ROT+CRAZY): %d de %d" % (len(table), N))

    # Q1..Q5 por instancia
    per = {}
    for t, v in INSTANCES:
        b = budget(trace(img, request(t - 1, v)), table)
        b["verdict"] = verdict(b)
        per["e%d_p%d" % (t, v)] = b
    results["instances"] = per
    for k, b in per.items():
        print("[Q] %-12s cuerpo=%d sucias=%d (código %d, dato %d) A=%d B=%d sin_vía=%d "
              "carga+restore=%d aux=%d >127=%d direcc>=%d restaurador>=%d coste/celda=%s..%s -> %s"
              % (k, b["body_cells"], b["dirty_cells"], b["dirty_code"], b["dirty_data"],
                 b["via_a"], b["via_b"], len(b["unrestorable"]), b["load_and_restore_instr"],
                 b["aux_cells_consumed"], b["dirty_above_127"], b["addressing_lower_bound_instr"],
                 b["restorer_lower_bound_instr"], b["per_cell_cost_min"], b["per_cell_cost_max"],
                 b["verdict"]))

    # Q6
    cyc = xlat2_cycles()
    lengths = sorted(set(cyc.values()))
    tr = trace(img, request(99, 29797))
    body_vals = [tr["mem0"][i] for i in sorted(set(tr["pcs"]))]
    body_len = [cyc[v] for v in body_vals]
    lcm = 1
    for x in body_len:
        lcm = lcm * x // math.gcd(lcm, x)
    results["q6"] = {"xlat2_cycle_lengths": lengths,
                     "cycle_census": {str(L): sum(1 for v in cyc.values() if v == L) for L in lengths},
                     "body_cycle_lengths": sorted(set(body_len)), "body_lcm": lcm}
    print("[Q6] ciclos de XLAT2: longitudes=%s censo=%s; cuerpo: longitudes=%s mcm=%d"
          % (lengths, results["q6"]["cycle_census"], sorted(set(body_len)), lcm))

    # G3 control
    ctl = budget(trace(img, request(CONTROL_EPOCH_BYTE, 29797)), table)
    results["g3_control_b50"] = ctl
    print("[G3] control b=%d: cuerpo=%d sucias=%d restaurador>=%d (fuera del veredicto)"
          % (CONTROL_EPOCH_BYTE, ctl["body_cells"], ctl["dirty_cells"], ctl["restorer_lower_bound_instr"]))

    verdicts = sorted({b["verdict"] for b in per.values()})
    results["g2_verdicts"] = verdicts
    results["gates"] = {"G0": g0_ok, "G2_single_verdict_per_instance": all(
        b["verdict"] for b in per.values()), "G3": ctl["dirty_cells"] > 0}
    ok = all(results["gates"].values())
    results["all_gates_pass"] = ok
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf8")
    print("[G2] veredictos: %s" % verdicts)
    print("[verdict] all_gates_pass=%s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
