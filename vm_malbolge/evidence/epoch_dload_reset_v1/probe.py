#!/usr/bin/env python3
"""probe.py — epoch_dload_reset_v1: bloque de DLOAD que reinicia d cada vuelta.

Puertas en GATES.md (commit 89ef37a, anterior a este archivo). Reutiliza la
construcción del bloque de `epoch_xlat2_block_v1` (posiciones, celdas X, relleno,
trampolín, JMP: código importado de su probe.py, edge de código explícito) y le
cambia la tabla de destinos que crece con R por cuatro celdas de dato fijas,
calculadas desde parámetros medidos.

Escribe en el directorio del pack: dload_reset.mb, ctrl_k_off.mb,
ctrl_no_dload.mb, results.json.

Uso:  python3 -I probe.py </dev/null
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
from array import array
from pathlib import Path

PACK = Path(__file__).resolve().parent
EVID = PACK.parent
ROOT = PACK.parents[2]
BLOCK = EVID / "epoch_xlat2_block_v1"

_spec = importlib.util.spec_from_file_location("block_v1_probe", BLOCK / "probe.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)          # sólo define funciones; su main() no corre
O, SE = B.O, B.SE
ENC, N = B.ENC, B.N

R_LONG = 10_000                      # R del pack (Q2)
R_SHORT = 60
CTRL_STEPS = 2_000                   # tope de los controles
VALID = {4, 5, 23, 39, 40, 62, 68, 81}
HARMFUL = VALID - {68}
DLOAD, JMP = 40, 4
PREDICTED = {99: 59, 100: 100, 105: 59, 110: 98}   # GATES.md, sólo para comparar


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- construcción
def block_params() -> dict:
    """Parámetros del bloque de DLOAD de epoch_xlat2_block_v1 (código de su probe)."""
    shift, T, span, extra = B.placement("DLOAD")
    _, gap, v = B.derived_x_value("DLOAD")
    assert gap == span
    jmp = shift + span + 1 + extra
    fillers = [B.filler_value(shift + 1 + k)[0] for k in range(span - 1)]
    extras = [B.filler_value(shift + span + 1 + k)[0] for k in range(extra)]
    return {"shift": shift, "T": T, "g": gap, "jmp": jmp, "n": jmp - shift + 1,
            "x_value": v, "fillers": fillers, "extras": extras}


def background(i: int, T: int) -> int:
    """Valor de una celda que nunca se ejecuta: imprimible, inocuo al cargar, != T."""
    for v in range(33, 127):
        if v != T and (v + i) % 94 not in HARMFUL:
            return v
    raise ValueError(i)


def code_image(p: dict, length: int, x_cells: bool = True) -> list[int]:
    """Prefijo + cuerpo del bucle; el resto, fondo (sin tabla de destinos)."""
    s, T, g, jmp = p["shift"], p["T"], p["g"], p["jmp"]
    img = [background(i, T) for i in range(length)]
    img[0] = DLOAD                                    # d = mem[0] = 40
    for i in range(1, s - 1):
        img[i] = B.any_harmless(i)
    img[T] = T
    xv = p["x_value"]
    if x_cells:
        img[s] = img[s + g] = xv
    else:                                             # control sin DLOAD
        img[s] = B.filler_value(s)[0]
        img[s + g] = B.filler_value(s + g)[0]
    for k, v in enumerate(p["fillers"]):
        img[s + 1 + k] = v
    for k, v in enumerate(p["extras"]):
        img[s + g + 1 + k] = v
    img[jmp] = (JMP - jmp) % 94
    return img


def measure_entry(p: dict) -> dict:
    """D_0 = d al ejecutar la celda shift por primera vez, y o_0/o_1: offsets donde
    decodifica DLOAD en las vueltas 0 y 1 (la celda X cifrada una vez en la 1)."""
    img = code_image(p, p["jmp"] + 1)
    t = B.trace_image(img, p["shift"] + 1)
    d0 = [e["d"] for e in t["events"] if e["pc"] == p["shift"]][0]
    s, g, xv = p["shift"], p["g"], p["x_value"]
    o = []
    for v in (xv, ENC[xv]):
        hits = [off for off in (0, g) if (v + s + off) % 94 == DLOAD]
        assert len(hits) == 1, hits
        o.append(hits[0])
    return {"D0": d0, "o0": o[0], "o1": o[1]}


def data_cells(p: dict, e: dict) -> dict[int, int]:
    """Las cuatro celdas del punto fijo (GATES.md, Modelo), calculadas."""
    n, T, D0, o0, o1 = p["n"], p["T"], e["D0"], e["o0"], e["o1"]
    V0 = D0 + o0
    D1 = V0 + n - o0
    V1 = D0 - n + o1
    return {D0 + o0: V0, V0 + n - 1 - o0: T, D1 + o1: V1, V1 + n - 1 - o1: T}


def build(p: dict, e: dict, x_cells: bool = True) -> list[int]:
    cells = data_cells(p, e)
    img = code_image(p, max(cells) + 1, x_cells=x_cells)
    for a, v in cells.items():
        img[a] = v
    return img


def fixed_point_check(img: list[int], p: dict, e: dict) -> dict:
    """Las ecuaciones del punto fijo, leídas de los bytes de la imagen."""
    n, T, D0, o0, o1 = p["n"], p["T"], e["D0"], e["o0"], e["o1"]
    ck = {}
    V0 = img[D0 + o0]
    ck["round0_jmp_reads_T"] = img[V0 + n - 1 - o0] == T
    D1 = V0 + n - o0
    V1 = img[D1 + o1]
    ck["round1_jmp_reads_T"] = img[V1 + n - 1 - o1] == T
    ck["d_returns_D0"] = V1 + n - o1 == D0
    cells = [D0 + o0, V0 + n - 1 - o0, D1 + o1, V1 + n - 1 - o1]
    ck["data_cells_distinct"] = len(set(cells)) == 4
    ck["data_cells_outside_code"] = all(c > p["jmp"] for c in cells)
    ck["image_printable"] = all(33 <= b <= 126 for b in img)
    return {"checks": ck, "ok": all(ck.values()), "cells": cells,
            "D1": D1, "V0": V0, "V1": V1}


# ---------------------------------------------------------------- trazador por vueltas
def run_rounds(img: list[int], p: dict, max_steps: int, rounds: int,
               state_hashes: bool = False) -> dict:
    """Trazador con la semántica del oráculo. Vuelta = de la entrada a `shift`
    hasta el JMP siguiente. Para en la vuelta `rounds`-ésima (su JMP), al tope de
    pasos o en HALT."""
    s, jmp, T = p["shift"], p["jmp"], p["T"]
    mem = list(img) + [0] * (N - len(img))
    for i in range(len(img), N):
        mem[i] = B.CRAZY(mem[i - 1], mem[i - 2])
    a = c = d = 0
    dl_round, dload_per_round, body_ops = 0, [], set()
    jdest, d_start, hashes, first_seen = [], [], [], {}
    repeat = None
    status, st = "MAX", 0
    for st in range(1, max_steps + 1):
        if c == s:
            d_start.append(d)
            if state_hashes and repeat is None:
                h = sha(array("q", mem).tobytes() + repr((a, c, d)).encode())
                r = len(d_start) - 1
                hashes.append(h)
                if h in first_seen:
                    repeat = (first_seen[h], r)
                else:
                    first_seen[h] = r
        cell = mem[c]
        o = (cell + c) % 94
        if s <= c <= jmp:
            if o in VALID:
                body_ops.add(o)
            if o == DLOAD:
                dl_round += 1
        if o == JMP:
            jdest.append(mem[d])
            if s <= c <= jmp:
                dload_per_round.append(dl_round)
                dl_round = 0
            c = mem[d]
            if len(jdest) >= rounds:
                status = "ROUNDS"
                break
        elif o == 5:
            pass
        elif o == 23:
            a = 0
        elif o == 39:
            mem[d] = (mem[d] // 3) + (mem[d] % 3) * (3 ** 9)
            a = mem[d]
        elif o == DLOAD:
            d = mem[d]
        elif o == 62:
            mem[d] = B.CRAZY(a, mem[d])
            a = mem[d]
        elif o == 81:
            status = "HALTED"
            break
        if 33 <= mem[c] <= 126:
            mem[c] = ENC[mem[c]]
        c = (c + 1) % N
        d = (d + 1) % N
    if status == "ROUNDS":                            # completa el post-paso del JMP
        if 33 <= mem[c] <= 126:
            mem[c] = ENC[mem[c]]
        c = (c + 1) % N
        d = (d + 1) % N
    bad = [i for i, x in enumerate(jdest) if x != T]
    closed = bad[0] if bad else len(jdest)
    return {"steps": st, "status": status, "jmp_count": len(jdest),
            "jmp_dests_distinct": sorted(set(jdest)), "jmp_dests": jdest,
            "first_bad_jmp": bad[0] if bad else None, "rounds_closed": closed,
            "dload_per_round": dload_per_round, "body_valid_ops": sorted(body_ops),
            "d_start": d_start, "d_start_distinct": sorted(set(d_start)),
            "repeat": repeat, "mem": mem}


def criterion(t: dict, R: int, T: int) -> dict:
    per = t["dload_per_round"][:R]
    c = {"rounds_closed_ge_R": t["rounds_closed"] >= R,
         "one_dload_per_round": len(per) >= R and all(x == 1 for x in per),
         "body_only_40_and_4": t["body_valid_ops"] == [JMP, DLOAD],
         "all_jmp_to_T": t["first_bad_jmp"] is None and t["jmp_count"] >= R,
         "d_start_two_values": len(t["d_start_distinct"]) == 2}
    return {"checks": c, "ok": all(c.values())}


def cycle_len(v: int) -> int:
    k, x = 1, ENC[v]
    while x != v:
        x = ENC[x]
        k += 1
    return k


# ---------------------------------------------------------------- motores
def mem_sha(mem: list[int]) -> str:
    return sha(array("q", mem).tobytes())


def run_c(path: Path, limit: int) -> dict:
    p = subprocess.run([str(B.C_RUNNER), str(path), str(limit)],
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=600)
    r = B.re.search(rb"steps:\s*(\d+)\s*\|\s*status:\s*(\w+)", p.stderr)
    return {"rc": p.returncode, "out_hex": p.stdout.hex(),
            "steps": int(r.group(1)) if r else None,
            "status": r.group(2).decode() if r else None}


def engines(path: Path, img: list[int], p: dict, steps: int, t: dict) -> dict:
    o = O.oracle_run(str(path), max_steps=steps)
    src = B.INDEP.read_text(encoding="utf8")
    ns: dict = {}
    exec(compile(src.split("def trits")[0], str(B.INDEP), "exec"), ns)
    ind = ns["run"](list(path.read_bytes()), [], maxs=steps)
    sc = SE.run(path.read_bytes(), max_steps=steps, stdin=b"", collect=True)
    cr = run_c(path, steps)
    sc_dests = [e["dest"] for e in sc["events"] if e["op"] == JMP]
    sc_dstart = [e["d"] for e in sc["events"] if e["pc"] == p["shift"]]
    stp = {"oracle": o["steps"], "indep": ind["steps"], "scratch": sc["steps"],
           "c": cr["steps"]}
    st = {"oracle": o["status"], "indep": ind["status"], "scratch": sc["status"],
          "c": cr["status"]}
    mt, ms, mi = mem_sha(t["mem"]), mem_sha(sc["mem"]), mem_sha(ind["mem"])
    ag = {"steps": stp, "status": st,
          "none_stopped_before_cap": all(v == steps for v in stp.values())
          and not any(v in ("HALTED", "NONPRINT", "EOF") for v in st.values()),
          "outputs_empty": (o["output"] == "" and ind["out"] == b"" and sc["out"] == b""
                            and cr["out_hex"] in ("", "0a")),
          "memory_sha": {"trace": mt, "scratch": ms, "indep": mi},
          "memory_sha_trace_scratch_indep_equal": mt == ms == mi,
          "jmp_dests_trace_eq_scratch": sc_dests == t["jmp_dests"],
          "d_start_trace_eq_scratch": sc_dstart == t["d_start"]}
    ag["all"] = (ag["none_stopped_before_cap"] and ag["memory_sha_trace_scratch_indep_equal"]
                 and ag["jmp_dests_trace_eq_scratch"] and ag["d_start_trace_eq_scratch"])
    return ag


def slim(t: dict) -> dict:
    out = {k: v for k, v in t.items() if k not in ("mem", "jmp_dests", "d_start",
                                                   "dload_per_round")}
    out["d_start_first8"] = t["d_start"][:8]
    out["jmp_dests_first8"] = t["jmp_dests"][:8]
    out["dload_per_round_first8"] = t["dload_per_round"][:8]
    out["dload_per_round_distinct"] = sorted(set(t["dload_per_round"]))
    return out


# ---------------------------------------------------------------- main
def main() -> int:
    p = block_params()
    e = measure_entry(p)
    cells = data_cells(p, e)
    img = build(p, e)
    img_again = build(p, e)        # la construcción no tiene parámetro R
    fp = fixed_point_check(img, p, e)

    # controles construidos
    k_cell = e["D0"] - p["n"] + e["o1"]
    k_addr = [a for a, v in cells.items() if v == k_cell and a != e["D0"] + e["o0"]][0]
    img_k = list(img)
    img_k[k_addr] = k_cell + 1
    img_nd = build(p, e, x_cells=False)
    images = {"dload_reset": img, "ctrl_k_off": img_k, "ctrl_no_dload": img_nd}
    for name, im in images.items():
        (PACK / (name + ".mb")).write_bytes(bytes(im))

    # Q2 + Q3: bucle largo con hash del estado
    t = run_rounds(img, p, max_steps=R_LONG * p["n"] + 1000, rounds=R_LONG,
                   state_hashes=True)
    crit = criterion(t, R_LONG, p["T"])
    ag = engines(PACK / "dload_reset.mb", img, p, t["steps"], t)

    encrypted = list(range(p["shift"], p["jmp"])) + [p["T"]]
    lens = {c: cycle_len(img[c]) for c in encrypted}
    P_pred = math.lcm(*lens.values())
    rep = t["repeat"]
    P_meas = rep[1] - rep[0] if rep else None
    d_period = None
    ds = t["d_start"]
    for k in range(1, 9):
        if all(ds[i] == ds[i + k] for i in range(len(ds) - k)):
            d_period = k
            break
    q3 = {"encrypted_cells_cycle_len": lens, "P_predicted": P_pred,
          "repeat_rounds": rep, "P_measured": P_meas, "d_period": d_period,
          "state_repeat_found": rep is not None}

    # Q4 controles
    tk = run_rounds(img_k, p, CTRL_STEPS, R_LONG)
    tn = run_rounds(img_nd, p, CTRL_STEPS, R_LONG)
    old = list((BLOCK / "dload_block.mb").read_bytes())
    tb = run_rounds(old, p, CTRL_STEPS, R_LONG)
    q4 = {"ctrl_k_off": {"cell": k_addr, "value": k_cell + 1, "run": slim(tk),
                         "criterion": criterion(tk, R_LONG, p["T"]),
                         "fixed_point": fixed_point_check(img_k, p, e)["checks"],
                         "broke_within_2_rounds": tk["first_bad_jmp"] is not None
                         and tk["first_bad_jmp"] < 2},
          "ctrl_no_dload": {"run": slim(tn), "criterion": criterion(tn, R_LONG, p["T"])},
          "ctrl_block_v1": {"image_sha256": sha(bytes(old)), "run": slim(tb),
                            "closed_lt_2": tb["rounds_closed"] < 2}}

    # Q5 cargador de 1998
    olm = subprocess.run([str(B.OLMSTEAD), str(PACK / "dload_reset.mb")],
                         stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
    valid_cells = sum(1 for i, v in enumerate(img) if (v + i) % 94 in VALID)
    q5 = {"rc": olm.returncode, "stderr": olm.stderr.decode("latin-1").strip(),
          "loader_valid_cells": valid_cells, "cells": len(img),
          "dialect": "classic_permissive" if olm.returncode != 0 else "classic_1998_loader"}

    block_v1_len = json.loads((BLOCK / "results.json").read_text())["q1"]["DLOAD"]["length"]
    q1 = {"params": {k: p[k] for k in ("shift", "T", "g", "jmp", "n", "x_value",
                                        "fillers", "extras")},
          "entry": e, "data_cells": {str(k): v for k, v in sorted(cells.items())},
          "predicted_cells": {str(k): v for k, v in PREDICTED.items()},
          "matches_prediction": cells == PREDICTED,
          "length": len(img), "block_v1_dload_length_R60": block_v1_len,
          "fixed_point": fp}

    gates = {
        "G0": (fp["ok"] and img == img_again
               and (not fixed_point_check(img_k, p, e)["ok"]
                    or not criterion(tk, R_LONG, p["T"])["ok"])
               and not criterion(tn, R_LONG, p["T"])["ok"]),
        "G1": ag["all"],
        "G2": crit["ok"],
        "G3": (q3["state_repeat_found"] and d_period == 2 and P_meas == P_pred),
        "G4": (q4["ctrl_k_off"]["broke_within_2_rounds"]
               and not q4["ctrl_no_dload"]["criterion"]["ok"]
               and q4["ctrl_block_v1"]["closed_lt_2"]
               and q5["rc"] in (0, 1)),
    }
    results = {"pack": "epoch_dload_reset_v1", "R": R_LONG, "q1": q1,
               "q2": {"run": slim(t), "criterion": crit, "engines": ag},
               "q3": q3, "q4": q4, "q5": q5, "gates": gates,
               "all_gates_pass": all(gates.values()),
               "images": {k: {"sha256": sha(bytes(v)), "length": len(v)}
                          for k, v in images.items()},
               "dependencies": {
                   "epoch_xlat2_block_v1/probe.py": sha((BLOCK / "probe.py").read_bytes()),
                   "epoch_xlat2_block_v1/scratch_engine.py":
                       sha((BLOCK / "scratch_engine.py").read_bytes()),
                   "epoch_xlat2_block_v1/dload_block.mb": sha(bytes(old)),
                   "tools/oracle_classic.py": sha(B.ORACLE.read_bytes()),
                   "epoch_audit_v1/indep_interpreter.py": sha(B.INDEP.read_bytes()),
                   "runners/malbolge-original/malbolge": sha(B.C_RUNNER.read_bytes()),
                   "Malbolge-PureEpoch/build/olmstead": sha(B.OLMSTEAD.read_bytes())}}
    (PACK / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False)
                                       + "\n", encoding="utf8")

    print("[Q1] params=%s entrada=%s" % (q1["params"], e))
    print("[Q1] celdas de dato=%s predicción=%s coincide=%s largo=%d (block_v1 R=60: %d)"
          % (q1["data_cells"], q1["predicted_cells"], q1["matches_prediction"],
             len(img), block_v1_len))
    print("[Q1] punto fijo leído de la imagen: %s" % fp["checks"])
    print("[Q2] vueltas=%d pasos=%d status=%s DLOAD/vuelta=%s opcodes_cuerpo=%s "
          "destinos_JMP=%s d_inicio=%s"
          % (t["rounds_closed"], t["steps"], t["status"], sorted(set(t["dload_per_round"])),
             t["body_valid_ops"], t["jmp_dests_distinct"], t["d_start_distinct"]))
    print("[Q2] criterio: %s" % crit)
    print("[Q2] motores: %s" % {k: v for k, v in ag.items() if k != "memory_sha"})
    print("[Q3] ciclos de las celdas cifradas=%s P_predicho=%d repetición=%s "
          "P_medido=%s periodo_d=%s" % (lens, P_pred, rep, P_meas, d_period))
    print("[Q4] ctrl_k_off: celda %d=%d primer_JMP_malo=%s destinos=%s criterio=%s"
          % (k_addr, k_cell + 1, tk["first_bad_jmp"], tk["jmp_dests"][:4],
             q4["ctrl_k_off"]["criterion"]["ok"]))
    print("[Q4] ctrl_no_dload: vueltas=%d primer_JMP_malo=%s destinos=%s status=%s criterio=%s"
          % (tn["rounds_closed"], tn["first_bad_jmp"], tn["jmp_dests"][:4], tn["status"],
             q4["ctrl_no_dload"]["criterion"]["ok"]))
    print("[Q4] ctrl_block_v1: vueltas=%d destinos=%s status=%s"
          % (tb["rounds_closed"], tb["jmp_dests"][:4], tb["status"]))
    print("[Q5] Olmstead 1998: rc=%d stderr=%r válidas-al-cargar %d/%d dialecto=%s"
          % (q5["rc"], q5["stderr"], valid_cells, len(img), q5["dialect"]))
    print("[gates] %s all_gates_pass=%s" % (gates, results["all_gates_pass"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
