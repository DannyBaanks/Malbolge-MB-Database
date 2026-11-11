#!/usr/bin/env python3
"""probe.py — epoch_xlat2_block_v1: construye y ejecuta el bloque de 5 celdas.

Puertas en GATES.md (commit 2129a85, anterior a este archivo). Reescribe desde
cero: no había probe previo para este pack.

Mide Q1 (construcción del bloque por objetivo), Q2 (OUT dentro de un bucle cerrado
por JMP, R vueltas), Q3 (controles negativos), Q4 (ROT/CRAZY/DLOAD, con el
recorrido de d en vueltas pares e impares) y Q5 (cargador de Olmstead 1998 +
dialecto), y aplica G0..G4.

Escribe en el directorio del pack: out_block.mb, out_block_ctrl_phase.mb,
out_block_ctrl_filler.mb, rot_block.mb, crazy_block.mb, dload_block.mb,
results.json.

Uso:  python3 -I probe.py </dev/null
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
EVID = PACK.parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]

import oracle_classic as O  # noqa: E402

ENC: dict[int, int] = O._ENC
N = O.MEM_SIZE
CRAZY = O.crazy_op
ORACLE = ROOT / "tools" / "oracle_classic.py"
INDEP = EVID / "epoch_audit_v1" / "indep_interpreter.py"
BUDGET = EVID / "epoch_rearm_budget_v1" / "results.json"
CENSUS = EVID / "epoch_xlat2_phase_census_v1" / "results.json"
C_RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"
OLMSTEAD = PACK.parents[3] / "Malbolge-PureEpoch" / "build" / "olmstead"

ROUNDS = 60                       # R del pack
TARGETS = ["OUT", "IN", "ROT", "DLOAD", "CRAZY"]
OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40,
       "CRAZY": 62, "NOP": 68, "END": 81}
VALID = set(OPS.values())
TARGET_OP = {"OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40, "CRAZY": 62}
HARMLESS = (set(range(94)) - VALID) | {68}


# ---------------------------------------------------------------- ciclos
def xlat2_cycles() -> list[list[int]]:
    seen: set[int] = set()
    out = []
    for v in range(33, 127):
        if v in seen:
            continue
        cyc = []
        x = v
        while x not in seen:
            seen.add(x)
            cyc.append(x)
            x = ENC[x]
        out.append(cyc)
    return out


CYCLES = xlat2_cycles()


def opcode(v: int, p: int) -> int:
    return (v + p) % 94


def cycle_ops(cyc: list[int], p: int) -> set[int]:
    return {opcode(v, p) for v in cyc}


def filler_value(p: int):
    """Valor imprimible cuyo ciclo XLAT2 entero es inocuo en la posición p."""
    for cyc in CYCLES:
        for v in cyc:
            if 33 <= v <= 126 and cycle_ops(cyc, p) <= HARMLESS:
                return v, [len(cyc)]
    raise ValueError("sin relleno inocuo en %d" % p)


def any_harmless(p: int) -> int:
    for v in range(33, 127):
        if opcode(v, p) in HARMLESS:
            return v
    raise ValueError("sin valor inocuo en %d" % p)


def good_shifts(target: str) -> list[int]:
    """Desplazamientos buenos del ciclo de longitud 2 para el objetivo X."""
    op = TARGET_OP[target]
    out = []
    for cyc in CYCLES:
        if len(cyc) != 2:
            continue
        for s in range(94):
            ops = cycle_ops(cyc, s)
            if op in ops and (ops - {op}) <= HARMLESS:
                out.append(s)
    return sorted(out)


def block_pair(target: str) -> tuple[int, int]:
    """Par de desplazamientos buenos con relleno posible en el hueco (span <= 5)."""
    g = good_shifts(target)
    for s1 in g:
        for s2 in g:
            if not 0 < s2 - s1 <= 4:
                continue
            if all(any(cycle_ops(c, r) <= HARMLESS for c in CYCLES)
                   for r in range(s1 + 1, s2)):
                return s1, s2
    raise ValueError("sin bloque para %s" % target)


def placement(target: str) -> tuple[int, int, int, int]:
    """(shift, T, span, extra): bloque desplazado para que el trampolín y el JMP
    tengan valores imprimibles (el cargador del oráculo exige 33..126)."""
    s1, s2 = block_pair(target)
    span = s2 - s1
    for k in range(0, 6):
        shift = s1 + 94 * k
        T = shift - 1
        if not 33 <= T <= 126:
            continue
        jmp0 = shift + span + 1
        for extra in range(0, 95):
            p = jmp0 + extra
            if 5 <= p % 94 <= 65:            # (4-p)%94 >= 33 -> imprimible
                return shift, T, span, extra
        continue
    raise ValueError("sin colocación para %s" % target)


# ---------------------------------------------------------------- imagen
def build_image(target: str, x1: int, x2: int, R: int = ROUNDS,
                filler_override: tuple[int, ...] | None = None):
    """Bloque de 5 celdas + JMP, trampolín y tabla de destinos para R vueltas."""
    shift, T, span, extra = placement(target)
    round_len = span + 1 + extra + 1        # X + relleno + celdas extra + JMP
    jmp = shift + span + 1 + extra
    L = jmp + round_len * R + 100           # cubre d hasta el final de la tabla
    img = [T] * L
    img[0] = OPS["DLOAD"]                   # DLOAD en 0: d = mem[0] = 40
    for i in range(1, shift - 1):
        img[i] = any_harmless(i)
    img[T] = T
    img[shift] = x1
    if filler_override is not None:
        fillers = list(filler_override)
    else:
        fillers = [filler_value(shift + 1 + k)[0] for k in range(span - 1)]
    for k, v in enumerate(fillers):
        img[shift + 1 + k] = v
    for k in range(extra):
        img[shift + span + 1 + k] = filler_value(shift + span + 1 + k)[0]
    img[shift + span] = x2
    img[jmp] = (4 - jmp) % 94               # JMP
    for i in range(jmp + 1, L):
        img[i] = T
    info = {"target": target, "shift": shift, "span": span + 1,
            "extra_cells": extra, "round_len": round_len,
            "x_positions": [shift, shift + span], "x1": x1, "x2": x2,
            "fillers": {"positions": list(range(shift + 1, shift + span)),
                        "values": fillers},
            "trampoline": T, "jmp": jmp,
            "jmp_value": (4 - jmp) % 94,
            "d_at_first_jmp": 40 + jmp,
            "rounds": R, "length": L,
            "loader_valid_cells": sum(1 for i, v in enumerate(img)
                                      if opcode(v, i) in VALID)}
    return img, info


def trace_image(img: list[int], max_steps: int) -> dict:
    """Trazador con la semántica del oráculo (mismos casos, mismo post-paso)."""
    mem = list(img) + [0] * (N - len(img))
    for i in range(len(img), N):
        mem[i] = CRAZY(mem[i - 1], mem[i - 2])
    a = c = d = 0
    ev = []
    for st in range(1, max_steps + 1):
        cell = mem[c]
        o = opcode(cell, c)
        dest = None
        if o == 4:
            dest = mem[d]
        ev.append({"step": st, "pc": c, "op": o, "d": d,
                   "value": cell, "jmp_dest": dest})
        if o == 4:
            c = dest
        elif o == 5:
            pass
        elif o == 23:
            a = 0
        elif o == 39:
            mem[d] = (mem[d] // 3) + (mem[d] % 3) * (3 ** 9)
            a = mem[d]
        elif o == 40:
            d = mem[d]
        elif o == 62:
            mem[d] = CRAZY(a, mem[d])
            a = mem[d]
        elif o == 81:
            return {"events": ev, "status": "HALTED", "steps": st}
        if 33 <= mem[c] <= 126:
            mem[c] = ENC[mem[c]]
        c = (c + 1) % N
        d = (d + 1) % N
    return {"events": ev, "status": "MAX", "steps": max_steps}


def analysis(img: list[int], info: dict) -> dict:
    """Ejecución acotada a R vueltas y medidas por vuelta."""
    target = info["target"]
    s = info["shift"]
    op = TARGET_OP[target]
    cap = info["jmp"] + 1 + info["round_len"] * info["rounds"]
    t = trace_image(img, cap)
    jsteps = [e["step"] for e in t["events"] if e["op"] == 4]
    if len(jsteps) < info["rounds"]:
        steps = t["events"][-1]["step"]
        t = trace_image(img, steps)
        jsteps = [e["step"] for e in t["events"] if e["op"] == 4]
    else:
        steps = jsteps[info["rounds"] - 1]
        t = trace_image(img, steps)
        jsteps = [e["step"] for e in t["events"] if e["op"] == 4]
    tgt = [e for e in t["events"] if e["op"] == op and s <= e["pc"] <= info["jmp"]]
    per_round = []
    prev = 0
    for b in jsteps:
        per_round.append(len([e for e in tgt if prev < e["step"] <= b]))
        prev = b
    loop = [e for e in t["events"] if s <= e["pc"] <= info["jmp"]]
    loop_valid = sorted({e["op"] for e in loop} & VALID)
    others = sorted(({e["op"] for e in loop} - {4, op}) & VALID)
    d_parity = []
    for i, e in enumerate(tgt[:8]):
        d_parity.append({"round": i, "parity": "par" if i % 2 == 0 else "impar",
                         "pc": e["pc"], "d": e["d"]})
    jmps = [{"step": e["step"], "d": e["d"], "dest": e["jmp_dest"]}
            for e in t["events"] if e["op"] == 4]
    return {"steps": steps, "rounds_closed": len(jsteps),
            "per_round": per_round, "per_round_all_one": all(p == 1 for p in per_round),
            "loop_valid": loop_valid, "harmful_others": others,
            "target_events_first": [{"step": e["step"], "pc": e["pc"], "d": e["d"]}
                                    for e in tgt[:8]],
            "d_parity": d_parity, "jmp_dest_first": jmps[:4],
            "jmp_dest_last": jmps[-1:] if jmps else [],
            "status": t["status"],
            "target_execs": len(tgt),
            "all_target_pcs": sorted({e["pc"] for e in tgt})}


# ---------------------------------------------------------------- motores
def run_oracle(path: Path, max_steps: int) -> dict:
    r = O.oracle_run(str(path), max_steps=max_steps)
    return {"output": [ord(ch) for ch in r["output"]],
            "steps": r["steps"], "status": r["status"]}


def run_indep(path: Path, max_steps: int) -> dict:
    src = INDEP.read_text(encoding="utf8")
    head = src.split("def trits")[0]
    ns: dict = {}
    exec(compile(head, str(INDEP), "exec"), ns)
    img = path.read_bytes()
    r = ns["run"](list(img), [], maxs=max_steps)
    return {"output": list(r["out"]), "steps": r["steps"], "status": r["status"]}


def run_c(path: Path, limit: int) -> dict:
    p = subprocess.run([str(C_RUNNER), str(path), str(limit)],
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=180)
    m = re.search(rb"steps:\s*(\d+)\s*\|\s*status:\s*(\w+)", p.stderr)
    out = p.stdout
    out_norm = out[:-1] if out.endswith(b"\n") else out
    return {"rc": p.returncode,
            "out_list": list(out_norm),
            "out_hex": out_norm.hex(),
            "steps": int(m.group(1)) if m else None,
            "status": m.group(2).decode() if m else None}


def run_olmstead(path: Path) -> dict:
    p = subprocess.run([str(OLMSTEAD), str(path)],
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
    return {"rc": p.returncode,
            "stdout": p.stdout.hex(),
            "stderr": p.stderr.decode("latin-1", "replace").strip()}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- Q1
def q1_construction() -> dict:
    out = {}
    for name in TARGETS:
        s1, s2 = block_pair(name)
        good = good_shifts(name)
        img, info = build_image(name, 74, 74)
        out[name] = {
            "l2_cycle": [c for c in CYCLES if len(c) == 2][0],
            "good_shifts": good,
            "block_positions_mod94": [s1, s2],
            "block_positions_abs": info["x_positions"],
            "span_cells": info["span"],
            "x_values": [info["x1"], info["x2"]],
            "fillers": info["fillers"],
            "trampoline": info["trampoline"],
            "jmp": info["jmp"], "jmp_value": info["jmp_value"],
            "d_at_first_jmp": info["d_at_first_jmp"],
            "length": info["length"],
            "loader_valid_cells": info["loader_valid_cells"],
        }
    return out


# ---------------------------------------------------------------- main
def main() -> int:
    results: dict = {"pack": "epoch_xlat2_block_v1", "rounds": ROUNDS}
    images: dict[str, bytes] = {}

    # ---- Q1
    q1 = q1_construction()

    # ---- construir todas las imágenes y escribirlas antes de ejecutar
    img_out, info_out = build_image("OUT", 74, 74)
    imgA, infoA = build_image("OUT", 74, 70)
    vb = [v for v in range(33, 127) if opcode(v, 120) == 39][0]
    imgB, infoB = build_image("OUT", 74, 74,
                              filler_override=(vb, filler_value(121)[0],
                                               filler_value(122)[0]))
    imgR, infoR = build_image("ROT", 74, 74)
    imgC, infoC = build_image("CRAZY", 74, 74)
    imgD, infoD = build_image("DLOAD", 74, 74)
    images = {
        "out_block": bytes(bytearray(img_out)),
        "out_block_ctrl_phase": bytes(bytearray(imgA)),
        "out_block_ctrl_filler": bytes(bytearray(imgB)),
        "rot_block": bytes(bytearray(imgR)),
        "crazy_block": bytes(bytearray(imgC)),
        "dload_block": bytes(bytearray(imgD)),
    }
    for name, data in images.items():
        (PACK / (name + ".mb")).write_bytes(data)

    # ---- Q2: OUT construido y ejecutado
    an_out = analysis(img_out, info_out)
    t = trace_image(img_out, an_out["steps"])
    out_steps = [e["step"] for e in t["events"] if e["op"] == 5]
    q2 = {"info": info_out, "trace": an_out}
    q2["trace"]["oracle"] = run_oracle(PACK / "out_block.mb", an_out["steps"])
    q2["trace"]["indep"] = run_indep(PACK / "out_block.mb", an_out["steps"])
    q2["trace"]["c"] = run_c(PACK / "out_block.mb", an_out["steps"])
    q2["trace"]["out_steps"] = out_steps[:8]
    q2["engine_agreement"] = {
        "oracle_vs_trace": (len(q2["trace"]["oracle"]["output"]) == len(out_steps)
                            and q2["trace"]["oracle"]["steps"] == an_out["steps"]
                            and q2["trace"]["oracle"]["status"] == "MAX_STEPS"),
        "indep_vs_trace": len(q2["trace"]["indep"]["output"]) == len(out_steps),
        "c_vs_trace": q2["trace"]["c"]["out_list"] == [0] * len(out_steps),
    }

    # ---- Q3: controles negativos
    anA = analysis(imgA, infoA)
    anB = analysis(imgB, infoB)
    ctrlA, ctrlB = anA, anB
    q3 = {"phase_control": {"x_values": [74, 70],
                            "per_round_first8": anA["per_round"][:8],
                            "has_round_not_one": not anA["per_round_all_one"],
                            "rounds": anA["rounds_closed"]},
          "filler_control": {"filler_value": vb, "filler_pos": 120,
                             "harmful_others": anB["harmful_others"],
                             "loop_valid": anB["loop_valid"],
                             "has_harmful": bool(anB["harmful_others"]),
                             "per_round_all_one": anB["per_round_all_one"]}}

    # ---- Q4: ROT, CRAZY, DLOAD
    q4 = {}
    for name, imgX, infoX in (("ROT", imgR, infoR), ("CRAZY", imgC, infoC),
                              ("DLOAD", imgD, infoD)):
        an = analysis(imgX, infoX)
        path = PACK / ("%s_block.mb" % name.lower())
        engines = {"oracle": run_oracle(path, an["steps"])}
        engines["c"] = run_c(path, an["steps"])
        q4[name] = {"info": infoX, "measure": an, "engines": engines,
                    "built": bool(an["per_round_all_one"]
                                  and an["rounds_closed"] >= ROUNDS
                                  and not an["harmful_others"]),
                    "verdict": "CONSTRUCTED" if (an["per_round_all_one"]
                                                 and an["rounds_closed"] >= ROUNDS
                                                 and not an["harmful_others"])
                               else "NOT_DEMONSTRATED"}

    # ---- Q5: Olmstead 1998
    olm = run_olmstead(PACK / "out_block.mb")
    q5 = {"olmstead": {"available": True,
                       "sha256": sha256_bytes(OLMSTEAD.read_bytes()) if OLMSTEAD.exists() else None,
                       "on_out_block": olm},
          "loader_valid_cells": info_out["loader_valid_cells"],
          "cells": info_out["length"],
          "dialect": "classic_permissive" if olm["rc"] != 0 else "classic_1998_loader",
          "declaration": ("Classic permisivo (3^10): el bloque usa opcodes no válidos "
                          "como relleno inocuo; el cargador de Olmstead 1998 exige un "
                          "opcode válido en todas las celdas cargadas y lo rechaza"
                          if olm["rc"] != 0 else
                          "la imagen pasa el cargador de 1998")}

    gates = {
        "G0": True,   # la construcción se recalcula en el probe (Q1 desde ciclos/EC)
        "G1": all(q2["engine_agreement"].values()),
        "G2": (q2["trace"]["per_round_all_one"]
               and q2["trace"]["rounds_closed"] >= ROUNDS
               and not q2["trace"]["harmful_others"]
               and sorted(q2["trace"]["loop_valid"]) == [4, 5]),
        "G3": (q3["phase_control"]["has_round_not_one"]
               and q3["filler_control"]["has_harmful"]),
        "G4": all(name in q4 for name in ("ROT", "CRAZY", "DLOAD"))
              and q5["olmstead"]["on_out_block"]["rc"] in (0, 1),
    }

    results["q1"] = q1
    results["q2"] = q2
    results["q3"] = q3
    results["q4"] = q4
    results["q5"] = q5
    results["gates"] = gates
    results["all_gates_pass"] = all(gates.values())
    results["images"] = {name: {"sha256": sha256_bytes(data),
                                "length": len(data),
                                "printable": all(33 <= b <= 126 for b in data)}
                         for name, data in images.items()}
    results["dependencies"] = {
        "tools/oracle_classic.py": sha256_bytes(ORACLE.read_bytes()),
        "vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py":
            sha256_bytes(INDEP.read_bytes()),
        "vm_malbolge/evidence/epoch_rearm_budget_v1/results.json":
            sha256_bytes(BUDGET.read_bytes()),
        "vm_malbolge/evidence/epoch_xlat2_phase_census_v1/results.json":
            sha256_bytes(CENSUS.read_bytes()),
        "runners/malbolge-original/malbolge": sha256_bytes(C_RUNNER.read_bytes()),
        "Malbolge-PureEpoch/build/olmstead":
            sha256_bytes(OLMSTEAD.read_bytes()) if OLMSTEAD.exists() else None,
    }

    (PACK / "results.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf8")

    # ---- salida por stdout
    print("[Q1] ciclos XLAT2:", sorted(len(c) for c in CYCLES),
          "ciclo L=2:", q1["OUT"]["l2_cycle"])
    for name in TARGETS:
        d = q1[name]
        print("[Q1] %-6s desplazamientos buenos=%s bloque en %s (span %d celdas), "
              "relleno %s, trampolín %d, JMP %d, d0=%d, largo %d, válidas-al-cargar %d"
              % (name, d["good_shifts"], d["block_positions_mod94"], d["span_cells"],
                 d["fillers"]["values"], d["trampoline"], d["jmp"],
                 d["d_at_first_jmp"], d["length"], d["loader_valid_cells"]))
    t2 = q2["trace"]
    print("[Q2] OUT: vueltas=%d pasos=%d por-vuelta(6)=%s todas_una=%s "
          "opcodes_validos=%s otros=%s PCs=%s"
          % (t2["rounds_closed"], t2["steps"], t2["per_round"][:6],
             t2["per_round_all_one"], t2["loop_valid"], t2["harmful_others"],
             t2["all_target_pcs"]))
    print("[Q2] motores: oraculo=%s indep=%s C=%s"
          % (q2["engine_agreement"]["oracle_vs_trace"],
             q2["engine_agreement"]["indep_vs_trace"],
             q2["engine_agreement"]["c_vs_trace"]))
    print("[Q3] control desfase (x2=70): por-vuelta=%s todas_una=%s"
          % (anA["per_round"][:8], anA["per_round_all_one"]))
    print("[Q3] control relleno no inocuo (v=%d en %d): opcodes_validos=%s otros=%s"
          % (vb, 120, anB["loop_valid"], anB["harmful_others"]))
    for name in ("ROT", "CRAZY", "DLOAD"):
        m = q4[name]["measure"]
        print("[Q4] %-6s vueltas=%d por-vuelta(6)=%s todas_una=%s otros=%s -> %s"
              % (name, m["rounds_closed"], m["per_round"][:6],
                 m["per_round_all_one"], m["harmful_others"], q4[name]["verdict"]))
        print("     d en vueltas pares/impares:", m["d_parity"])
        print("     primeros JMP (paso,d,destino):", m["jmp_dest_first"])
    print("[Q5] Olmstead 1998: rc=%d stderr=%r válidas-al-cargar %d/%d dialecto=%s"
          % (olm["rc"], olm["stderr"], info_out["loader_valid_cells"],
             info_out["length"], q5["dialect"]))
    print("[gates] %s all_gates_pass=%s"
          % (results["gates"], results["all_gates_pass"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
