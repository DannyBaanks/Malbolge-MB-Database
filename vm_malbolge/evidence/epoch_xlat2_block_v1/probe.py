#!/usr/bin/env python3
"""probe.py — epoch_xlat2_block_v1: construye y ejecuta el bloque de 5 celdas.

Puertas en GATES.md (commit 2129a85, anterior a este archivo). Reescribe desde
cero: no había probe previo para este pack.

Mide Q1 (construcción del bloque por objetivo), Q2 (OUT dentro de un bucle cerrado
por JMP, R vueltas), Q3 (controles negativos), Q4 (ROT/CRAZY/DLOAD, con el
recorrido de d en vueltas pares e impares) y Q5 (cargador de Olmstead 1998 +
dialecto), y aplica G0..G4.

Motores: oráculo del repo (`tools/oracle_classic.py`), intérprete independiente
(`epoch_audit_v1/indep_interpreter.py`), trazador local con la misma semántica,
runner C (`runners/malbolge-original/malbolge`) y un motor **scratch** escrito
desde la especificación de 1998 con sus propias tablas (`scratch_engine.py`,
validado con el vector conocido `tools/fixtures/hello_world_40.mb`).

Desde la segunda pasada de medición (2026-11-11) el probe además: deriva los
valores de las celdas X en vez de sembrarlos, recalcula la construcción en G0,
comprueba en cada vuelta que el destino del JMP cae en el trampolín, y registra
los bytes de salida del trazador para comparar los cinco motores en bytes.

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
sys.path[:0] = [str(ROOT / "tools"), str(PACK)]

import oracle_classic as O  # noqa: E402
import scratch_engine as SE  # noqa: E402

ENC: dict[int, int] = O._ENC
N = O.MEM_SIZE
CRAZY = O.crazy_op
ORACLE = ROOT / "tools" / "oracle_classic.py"
INDEP = EVID / "epoch_audit_v1" / "indep_interpreter.py"
BUDGET = EVID / "epoch_rearm_budget_v1" / "results.json"
CENSUS = EVID / "epoch_xlat2_phase_census_v1" / "results.json"
C_RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"
OLMSTEAD = PACK.parents[3] / "Malbolge-PureEpoch" / "build" / "olmstead"
HELLO = ROOT / "tools" / "fixtures" / "hello_world_40.mb"

ROUNDS = 60                       # R del pack
TARGETS = ["OUT", "IN", "ROT", "DLOAD", "CRAZY"]
# Declaración de Q4 heredada del VERDICT de 3bbdfb5 (que ya publicaba estas
# mediciones). NO es un pre-registro: se escribió después de la primera medición
# y en el mismo commit que la segunda, así que funciona como check de REGRESIÓN
# (G4 falla si la medición cambia respecto de 3bbdfb5), no como predicción.
DECLARED_Q4 = {"ROT": "CONSTRUCTED", "CRAZY": "CONSTRUCTED",
               "DLOAD": "NOT_DEMONSTRATED"}
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


def phase_alternates(target: str, s: int, span: int, v: int) -> bool:
    """Con valor v en ambas celdas X (posiciones s y s+span), exactamente una
    decodifica el objetivo en la vuelta 0 y los papeles se intercambian tras un
    paso de XLAT2. Tablas propias del motor scratch (independientes del repo)."""
    op = TARGET_OP[target]
    w = SE.encrypt(v)                      # valor de la celda tras un paso XLAT2
    a, b = (v + s) % 94, (v + s + span) % 94
    a1, b1 = (w + s) % 94, (w + s + span) % 94
    if not ((a == op) ^ (b == op)):
        return False
    if not ((a1 == op) ^ (b1 == op)):
        return False
    if (a == op) == (a1 == op):
        return False
    other_ok = all(x == op or x in HARMLESS
                   for x in (a, b, a1, b1))
    return other_ok


def derived_x_value(target: str) -> tuple[int, int, int]:
    """(shift, span, v): valor de las celdas X derivado del ciclo de longitud 2
    para el que el desfase de posiciones da exactamente una operación por vuelta.

    Si hay dos fases posibles, se prefiere la que hace que la PRIMERA celda X
    decodifique el objetivo en la vuelta 0 (en la vuelta 1 lo toma la segunda)."""
    op = TARGET_OP[target]
    s1, s2 = block_pair(target)
    span = s2 - s1
    cands = []
    for cyc in CYCLES:
        if len(cyc) != 2:
            continue
        for v in cyc:
            if 33 <= v <= 126 and phase_alternates(target, s1, span, v):
                cands.append(v)
    if not cands:
        raise ValueError("sin valor X derivado para %s" % target)
    first_phase = [v for v in cands if (v + s1) % 94 == op]
    return s1, span, (first_phase or cands)[0]


# ---------------------------------------------------------------- imagen
def build_image(target: str, x1: int | None = None, x2: int | None = None,
                R: int = ROUNDS,
                filler_override: tuple[int, ...] | None = None):
    """Bloque de 5 celdas + JMP, trampolín y tabla de destinos para R vueltas.

    Si x1/x2 son None se derivan del ciclo de longitud 2 (G0 los recalcula)."""
    if x1 is None or x2 is None:
        _, _, v = derived_x_value(target)
        x1 = x2 = v
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
    out: list[int] = []
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
            out.append(a % 256)
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
            return {"events": ev, "out": out, "status": "HALTED", "steps": st,
                    "mem": mem}
        if 33 <= mem[c] <= 126:
            mem[c] = ENC[mem[c]]
        c = (c + 1) % N
        d = (d + 1) % N
    return {"events": ev, "out": out, "status": "MAX", "steps": max_steps,
            "mem": mem}


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
    jd = [e["jmp_dest"] for e in t["events"] if e["op"] == 4]
    return {"steps": steps, "rounds_closed": len(jsteps),
            "per_round": per_round, "per_round_all_one": all(p == 1 for p in per_round),
            "loop_valid": loop_valid, "harmful_others": others,
            "jmp_count": len(jd),
            "jmp_dests": jd,
            "jmp_dest_all_trampoline": bool(jd) and all(x == info["trampoline"] for x in jd),
            "jmp_dest_distinct": sorted(set(jd)),
            "d_at_first_jmp_measured": jmps[0]["d"] if jmps else None,
            "out_bytes": t["out"],
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


def run_scratch(path: Path, max_steps: int) -> dict:
    """Cuarto motor: motor escrito desde la especificación de 1998, con sus
    propias tablas (scratch_engine.py). Registra además los destinos de cada
    JMP, para contrastarlos con el trazador."""
    img = path.read_bytes()
    r = SE.run(img, max_steps=max_steps, stdin=b"", collect=True)
    jmps = [e["dest"] for e in r["events"] if e["op"] == 4]
    return {"out_list": list(r["out"]), "out_steps": r["steps"],
            "steps": r["steps"],
            "status": r["status"], "jmp_dests": jmps,
            "jmp_count": len(jmps)}


def out_step_profile(path: Path, out_steps: list[int]) -> dict:
    """Paso exacto de cada OUT en cada motor: con tope s-1 la salida tiene i bytes
    y con tope s tiene i+1 (s = paso del i-ésimo OUT según el trazador)."""
    runners = {"oracle": lambda c: run_oracle(path, c)["output"],
               "indep": lambda c: run_indep(path, c)["output"],
               "c": lambda c: run_c(path, c)["out_list"],
               "scratch": lambda c: run_scratch(path, c)["out_list"]}
    engines = {}
    for name, fn in runners.items():
        bad = []
        for i, s in enumerate(out_steps):
            before, at = len(fn(s - 1)), len(fn(s))
            if before != i or at != i + 1:
                bad.append({"out_index": i, "step": s, "len_before": before, "len_at": at})
        engines[name] = {"match": not bad, "mismatches": bad[:5]}
    return {"out_steps": out_steps, "engines": engines,
            "all_match": bool(out_steps) and all(e["match"] for e in engines.values())}


def mem_agreement(path: Path, img: list[int], steps: int) -> dict:
    """sha256 de las 59049 celdas tras `steps` pasos en trazador, scratch e indep."""
    def h(mem: list[int]) -> str:
        return hashlib.sha256(json.dumps(mem, separators=(",", ":")).encode()).hexdigest()
    tr = h(trace_image(img, steps)["mem"])
    sc = h(SE.run(path.read_bytes(), max_steps=steps, stdin=b"")["mem"])
    src = INDEP.read_text(encoding="utf8")
    ns: dict = {}
    exec(compile(src.split("def trits")[0], str(INDEP), "exec"), ns)
    ind = h(ns["run"](list(path.read_bytes()), [], maxs=steps)["mem"])
    return {"trace": tr, "scratch": sc, "indep": ind, "all_equal": tr == sc == ind}


def scratch_vector_check() -> dict:
    """Valida el motor scratch contra el vector conocido del repo:
    tools/fixtures/hello_world_40.mb -> "Hello World!" en 40 pasos.

    Además contrasta sus tablas tecleadas (XLAT2 y matriz crazy) con las del
    oráculo del repo: la independencia del motor es de implementación, no de
    las tablas — las tablas son las de la especificación de 1998."""
    img = HELLO.read_bytes()
    r = SE.run(img, max_steps=100, stdin=b"")
    o = O.oracle_run(str(HELLO), max_steps=100)
    xlat2_same = all(SE.encrypt(v) == O._ENC[v] for v in range(33, 127))
    crazy_same = all(SE.crazy(x, y) == O.crazy_op(x, y)
                      for x in range(0, 300) for y in range(0, 300))
    import random
    rng = random.Random(20261111)
    pairs = [(rng.randrange(N), rng.randrange(N)) for _ in range(100000)]
    crazy_full = all(SE.crazy(x, y) == O.crazy_op(x, y) for x, y in pairs)
    return {"fixture": "tools/fixtures/hello_world_40.mb",
            "scratch": {"steps": r["steps"], "status": r["status"],
                        "output_hex": r["out"].hex()},
            "oracle": {"steps": o["steps"], "status": o["status"],
                       "output": o["output"]},
            "expected": "Hello World!",
            "expected_steps": 40,
            "scratch_ok": r["out"] == b"Hello World!" and r["steps"] == 40,
            "oracle_ok": o["output"] == "Hello World!" and o["steps"] == 40,
            "xlat2_matches_repo": xlat2_same,
            "crazy_matches_repo": crazy_same,
            "crazy_pairs_checked": 300 * 300,
            "crazy_matches_repo_full_range_random": crazy_full,
            "crazy_full_range_pairs": len(pairs), "crazy_full_range_seed": 20261111}


def _scratch_cycles() -> list[list[int]]:
    """Ciclos de XLAT2 calculados con la tabla del motor scratch (no con O._ENC)."""
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
            x = SE.encrypt(x)
        out.append(cyc)
    return out


# Inocuo, tecleado de nuevo desde GATES.md (no se reutiliza HARMLESS/VALID).
G0_HARMFUL = {4, 5, 23, 39, 40, 62, 81}
G0_HARMLESS = set(range(94)) - G0_HARMFUL


def independent_solutions(target: str) -> list[tuple[int, int, int]]:
    """Todas las soluciones (s1 mod 94, hueco, valor X) del bloque para `target`,
    derivadas con código propio y las tablas del motor scratch. No llama a
    good_shifts / block_pair / derived_x_value / filler_value ni usa CYCLES."""
    op = TARGET_OP[target]
    cycs = _scratch_cycles()
    l2 = [c for c in cycs if len(c) == 2]

    def cycle_ok(cyc: list[int], p: int) -> bool:
        return all((w + p) % 94 in G0_HARMLESS for w in cyc)

    sols = []
    for s1 in range(94):
        for gap in range(1, 5):
            s2 = s1 + gap
            if not all(any(cycle_ok(c, r) for c in cycs) for r in range(s1 + 1, s2)):
                continue
            for cyc in l2:
                for v in cyc:
                    w = SE.encrypt(v)
                    ops0 = ((v + s1) % 94, (v + s2) % 94)
                    ops1 = ((w + s1) % 94, (w + s2) % 94)
                    hit0 = tuple(o == op for o in ops0)
                    hit1 = tuple(o == op for o in ops1)
                    if sum(hit0) != 1 or sum(hit1) != 1 or hit0 == hit1:
                        continue
                    if all(o == op or o in G0_HARMLESS for o in ops0 + ops1):
                        sols.append((s1, gap, v))
    return sols


def canonical_solution(target: str, sols: list[tuple[int, int, int]]):
    """La regla declarada: menor s1, luego menor hueco, y la fase en que la
    PRIMERA celda X decodifica el objetivo en la vuelta 0."""
    if not sols:
        return None
    op = TARGET_OP[target]
    s1, gap = min((s, g) for s, g, _ in sols)
    vs = [v for s, g, v in sols if (s, g) == (s1, gap)]
    first = [v for v in vs if (v + s1) % 94 == op]
    return s1, gap, (first or vs)[0]


def check_construction(target: str, img: list[int], info: dict) -> dict:
    """Comprueba la IMAGEN (no `info`) contra la derivación independiente.

    De `info` sólo se toman las coordenadas absolutas (shift, jmp); todo lo demás
    se lee de los bytes de la imagen."""
    sols = independent_solutions(target)
    canon = canonical_solution(target, sols)
    shift, jmp = info["x_positions"][0], info["jmp"]
    T = shift - 1
    L = len(img)
    checks: dict = {}
    checks["solution_exists"] = canon is not None
    if canon is None:
        return {"checks": checks, "ok": False, "canonical": None}
    s1, gap, v = canon
    checks["shift_is_canonical_mod94"] = shift % 94 == s1
    checks["x_cells_hold_canonical_value"] = (img[shift] == v and img[shift + gap] == v)
    checks["image_x_is_a_solution"] = (shift % 94, gap, img[shift]) in sols \
        and img[shift] == img[shift + gap]
    body_other = [p for p in range(shift + 1, jmp) if p != shift + gap]

    def scratch_cycle(val: int) -> list[int]:
        cyc = [val]
        x = SE.encrypt(val)
        while x != val:
            cyc.append(x)
            x = SE.encrypt(x)
        return cyc

    checks["body_cells_printable"] = all(33 <= img[p] <= 126 for p in range(shift, jmp + 1))
    checks["fillers_harmless_whole_cycle"] = all(
        all((w + p) % 94 in G0_HARMLESS for w in scratch_cycle(img[p]))
        for p in body_other)
    checks["jmp_cell_decodes_jmp"] = (img[jmp] + jmp) % 94 == 4
    checks["trampoline_is_shift_minus_1"] = info["trampoline"] == T
    checks["table_points_to_trampoline"] = all(img[i] == T for i in range(jmp + 1, L))
    round_len = jmp - T
    checks["table_covers_R_rounds"] = 40 + jmp + (ROUNDS - 1) * round_len < L
    checks["prefix_harmless_at_load"] = all(
        (img[i] + i) % 94 in G0_HARMLESS for i in range(1, T))
    checks["dload_seed"] = img[0] == 40 and (img[0] + 0) % 94 == 40
    checks["image_printable"] = all(33 <= b <= 126 for b in img)
    return {"checks": checks, "ok": all(checks.values()),
            "canonical": {"s1": s1, "gap": gap, "x_value": v},
            "n_solutions": len(sols)}


def g0_construction_recomputed(built: dict, controls: dict) -> dict:
    """G0 (tercera pasada): cada imagen construida pasa la comprobación
    independiente y cada imagen ROTA a propósito la falla (control de que la
    comprobación puede decir que no). `built` y `controls`: nombre -> (target,
    img, info)."""
    out = {"targets": {}, "controls": {}}
    for name, (target, img, info) in built.items():
        out["targets"][name] = check_construction(target, img, info)
    for name, (target, img, info) in controls.items():
        r = check_construction(target, img, info)
        out["controls"][name] = {"ok": r["ok"],
                                 "failed_checks": sorted(k for k, v in r["checks"].items()
                                                         if not v),
                                 "detected": not r["ok"]}
    out["ok"] = (all(t["ok"] for t in out["targets"].values())
                 and all(c["detected"] for c in out["controls"].values()))
    return out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- Q1
def q1_construction() -> dict:
    out = {}
    for name in TARGETS:
        s1, s2 = block_pair(name)
        good = good_shifts(name)
        img, info = build_image(name)
        out[name] = {
            "l2_cycle": [c for c in CYCLES if len(c) == 2][0],
            "good_shifts": good,
            "block_positions_mod94": [s1, s2],
            "block_positions_abs": info["x_positions"],
            "span_cells": info["span"],
            "x_values": [info["x1"], info["x2"]],
            "x_values_derived": derived_x_value(name)[2],
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

    # ---- vector conocido para el cuarto motor (scratch)
    vector = scratch_vector_check()

    # ---- construir todas las imágenes y escribirlas antes de ejecutar
    img_out, info_out = build_image("OUT")
    # control de desfase: la segunda celda X se siembra en la OTRA fase del
    # ciclo de longitud 2 (valor derivado, no escrito a mano)
    cyc2 = [c for c in CYCLES if len(c) == 2][0]
    v_out = info_out["x1"]
    other_phase = [x for x in cyc2 if x != v_out][0]
    imgA, infoA = build_image("OUT", x1=v_out, x2=other_phase)
    vb = [v for v in range(33, 127)
          if opcode(v, info_out["fillers"]["positions"][0]) == 39][0]
    fb = [filler_value(p)[0] for p in info_out["fillers"]["positions"][1:]]
    imgB, infoB = build_image("OUT", filler_override=(vb,) + tuple(fb))
    imgR, infoR = build_image("ROT")
    imgC, infoC = build_image("CRAZY")
    imgD, infoD = build_image("DLOAD")
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

    # ---- G0: comprobación independiente de la construcción + controles rotos
    built = {t: (t,) + build_image(t) for t in TARGETS}
    mut_table = list(img_out)
    mut_table[info_out["jmp"] + 50] = info_out["trampoline"] + 1
    mut_jmp = list(img_out)
    mut_jmp[info_out["jmp"]] = img_out[info_out["jmp"]] + 1
    mut_seed = list(img_out)
    mut_seed[0] = 41
    g0_controls = {"ctrl_phase": ("OUT", imgA, infoA),
                   "ctrl_filler": ("OUT", imgB, infoB),
                   "mut_table_cell": ("OUT", mut_table, info_out),
                   "mut_jmp_cell": ("OUT", mut_jmp, info_out),
                   "mut_dload_seed": ("OUT", mut_seed, info_out)}
    g0 = g0_construction_recomputed(built, g0_controls)

    # ---- Q2: OUT construido y ejecutado
    an_out = analysis(img_out, info_out)
    q2 = {"info": info_out, "trace": an_out}
    q2["trace"]["oracle"] = run_oracle(PACK / "out_block.mb", an_out["steps"])
    q2["trace"]["indep"] = run_indep(PACK / "out_block.mb", an_out["steps"])
    q2["trace"]["c"] = run_c(PACK / "out_block.mb", an_out["steps"])
    q2["trace"]["scratch"] = run_scratch(PACK / "out_block.mb", an_out["steps"])
    q2["trace"]["out_steps"] = [e["step"] for e in
                                trace_image(img_out, an_out["steps"])["events"]
                                if e["op"] == 5][:8]
    four = [q2["trace"]["oracle"]["output"], q2["trace"]["indep"]["output"],
            q2["trace"]["c"]["out_list"], q2["trace"]["scratch"]["out_list"],
            q2["trace"]["out_bytes"]]
    steps4 = [q2["trace"]["oracle"]["steps"], q2["trace"]["indep"]["steps"],
              q2["trace"]["c"]["steps"], q2["trace"]["scratch"]["out_steps"],
              q2["trace"]["steps"]]
    all_out_steps = [e["step"] for e in
                     trace_image(img_out, an_out["steps"])["events"] if e["op"] == 5]
    profile = out_step_profile(PACK / "out_block.mb", all_out_steps)
    mem_out = mem_agreement(PACK / "out_block.mb", img_out, an_out["steps"])
    q2["out_step_profile"] = profile
    q2["memory_agreement"] = mem_out
    q2["engine_agreement"] = {
        "bytes_all_five_equal": all(x == four[0] for x in four),
        # Con tope común, que los pasos coincidan sólo dice que ningún motor paró
        # antes del tope; la coincidencia de pasos real es out_step_profile.
        "none_stopped_before_cap": all(x == steps4[0] for x in steps4),
        "out_step_profile_all_match": profile["all_match"],
        "memory_sha_trace_scratch_indep_equal": mem_out["all_equal"],
        "oracle_vs_trace_bytes": q2["trace"]["oracle"]["output"] == q2["trace"]["out_bytes"],
        "indep_vs_trace_bytes": q2["trace"]["indep"]["output"] == q2["trace"]["out_bytes"],
        "indep_vs_trace_steps": q2["trace"]["indep"]["steps"] == q2["trace"]["steps"],
        "c_vs_trace_bytes": q2["trace"]["c"]["out_list"] == q2["trace"]["out_bytes"],
        "scratch_vs_trace_bytes": q2["trace"]["scratch"]["out_list"] == q2["trace"]["out_bytes"],
        "scratch_vs_trace_jmp_dests": (q2["trace"]["scratch"]["jmp_dests"]
                                       == q2["trace"]["jmp_dests"]),
    }

    # ---- Q3: controles negativos
    anA = analysis(imgA, infoA)
    anB = analysis(imgB, infoB)
    ctrlA, ctrlB = anA, anB
    q3 = {"phase_control": {"x_values": [infoA["x1"], infoA["x2"]],
                            "per_round_first8": anA["per_round"][:8],
                            "has_round_not_one": not anA["per_round_all_one"],
                            "rounds": anA["rounds_closed"]},
          "filler_control": {"filler_value": vb,
                             "filler_pos": info_out["fillers"]["positions"][0],
                             "harmful_others": anB["harmful_others"],
                             "loop_valid": anB["loop_valid"],
                             "has_harmful_39": anB["harmful_others"] == [39],
                             "per_round_all_one": anB["per_round_all_one"]}}

    # ---- Q4: ROT, CRAZY, DLOAD
    q4 = {}
    for name, imgX, infoX in (("ROT", imgR, infoR), ("CRAZY", imgC, infoC),
                              ("DLOAD", imgD, infoD)):
        an = analysis(imgX, infoX)
        path = PACK / ("%s_block.mb" % name.lower())
        engines = {"oracle": run_oracle(path, an["steps"]),
                   "scratch": run_scratch(path, an["steps"]),
                   "c": run_c(path, an["steps"]),
                   "indep": run_indep(path, an["steps"])}
        halted = {k: v["status"] == "HALTED" for k, v in engines.items()}
        stp = {k: v["steps"] for k, v in engines.items()}
        mem = mem_agreement(path, imgX, an["steps"])
        agreement = {
            "steps": stp, "halted": halted,
            "steps_all_equal": len(set(stp.values())) == 1,
            "halt_status_all_equal": len(set(halted.values())) == 1,
            "trace_halted": an["status"] == "HALTED",
            "memory_sha_trace_scratch_indep_equal": mem["all_equal"],
            "scratch_vs_trace_jmp_dests": engines["scratch"]["jmp_dests"] == an["jmp_dests"],
            "note": ("sin HALT, steps_all_equal sólo dice que nadie paró antes del "
                     "tope; la comparación con contenido es la memoria final y los "
                     "destinos de JMP" if an["status"] != "HALTED" else
                     "HALT natural: los pasos se comparan de verdad"),
        }
        agreement["all"] = (agreement["steps_all_equal"] and agreement["halt_status_all_equal"]
                            and halted["oracle"] == agreement["trace_halted"]
                            and agreement["memory_sha_trace_scratch_indep_equal"]
                            and agreement["scratch_vs_trace_jmp_dests"])
        crit = (an["per_round_all_one"] and an["rounds_closed"] >= ROUNDS
                and not an["harmful_others"] and an["jmp_dest_all_trampoline"])
        measured = "CONSTRUCTED" if crit else "NOT_DEMONSTRATED"
        q4[name] = {"info": infoX, "measure": an, "engines": engines,
                    "engine_agreement": agreement, "memory_agreement": mem,
                    "criterion": {"per_round_all_one": an["per_round_all_one"],
                                  "rounds_ge_R": an["rounds_closed"] >= ROUNDS,
                                  "no_harmful_others": not an["harmful_others"],
                                  "jmp_dest_all_trampoline": an["jmp_dest_all_trampoline"]},
                    "built": bool(crit),
                    "declared": DECLARED_Q4[name],
                    "measured": measured,
                    "declared_matches_measured": DECLARED_Q4[name] == measured,
                    "verdict": measured}

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
        # G0 (tercera pasada): las imágenes pasan la comprobación independiente
        # (código propio + tablas del motor scratch, leyendo los bytes) Y los cinco
        # controles rotos la fallan.
        "G0": g0["ok"],
        # G1: bytes iguales en los cinco motores y paso exacto de cada OUT igual
        # en los cinco (tope s-1 / s), no sólo el mismo tope.
        "G1": (q2["engine_agreement"]["bytes_all_five_equal"]
               and q2["engine_agreement"]["out_step_profile_all_match"]),
        # G2: criterio de Q2 + destino de cada JMP en el trampolín.
        "G2": (q2["trace"]["per_round_all_one"]
               and q2["trace"]["rounds_closed"] >= ROUNDS
               and not q2["trace"]["harmful_others"]
               and sorted(q2["trace"]["loop_valid"]) == [4, 5]
               and q2["trace"]["jmp_dest_all_trampoline"]),
        # G3: los dos controles rompen el criterio por el motivo declarado.
        "G3": (q3["phase_control"]["has_round_not_one"]
               and q3["filler_control"]["has_harmful_39"]),
        # G4: Q4 publica lo pedido y lo declarado coincide con lo medido; Q5
        # publica el resultado del cargador y la declaración de dialecto.
        "G4": (all(name in q4 for name in ("ROT", "CRAZY", "DLOAD"))
               and all(q4[n]["declared_matches_measured"] for n in q4)
               and all(len(q4[n]["measure"]["d_parity"])
                       == min(q4[n]["measure"]["rounds_closed"], 8)
                       for n in q4)
               and all("per_round" in q4[n]["measure"] for n in q4)
               and q5["olmstead"]["on_out_block"]["rc"] in (0, 1)
               and q5["dialect"] == ("classic_permissive" if olm["rc"] != 0
                                     else "classic_1998_loader")),
    }

    results["q1"] = q1
    results["q2"] = q2
    results["q3"] = q3
    results["q4"] = q4
    results["q5"] = q5
    results["gates"] = gates
    # Fuera de las puertas pre-registradas (GATES.md define G1 sobre Q2): acuerdo
    # de motores en Q4 y memoria final en Q2, publicados sin entrar en G0..G4.
    results["extra_checks"] = {
        "q2_memory_sha_trace_scratch_indep_equal": mem_out["all_equal"],
        "q4_engine_agreement_all": {n: q4[n]["engine_agreement"]["all"] for n in q4},
    }
    results["all_gates_pass"] = all(gates.values())
    results["g0_recomputation"] = g0
    results["scratch_vector"] = vector
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
        "tools/fixtures/hello_world_40.mb": sha256_bytes(HELLO.read_bytes()),
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
    print("[Q2] destinos de JMP: %d jumps, todos en el trampolín=%s distintos=%s "
          "(primeros=%s, último=%s)"
          % (t2["jmp_count"], t2["jmp_dest_all_trampoline"],
             t2["jmp_dest_distinct"], t2["jmp_dest_first"], t2["jmp_dest_last"]))
    print("[Q2] d medido en el primer JMP=%s (fórmula 40+jmp=%s)"
          % (t2["d_at_first_jmp_measured"], info_out["d_at_first_jmp"]))
    print("[Q2] motores: %s" % q2["engine_agreement"])
    print("[Q2] vector scratch (hello_world_40): %s" % vector)
    print("[G0] comprobación independiente: %s; controles rotos detectados: %s"
          % ({k: v["ok"] for k, v in g0["targets"].items()},
             {k: (v["detected"], v["failed_checks"]) for k, v in g0["controls"].items()}))
    print("[Q2] paso exacto de cada OUT (%d OUT): %s"
          % (len(profile["out_steps"]), {k: v["match"] for k, v in profile["engines"].items()}))
    print("[Q2] memoria final sha256 (trazador/scratch/indep) iguales=%s" % mem_out["all_equal"])
    print("[Q3] control desfase (x2=%d): por-vuelta=%s todas_una=%s"
          % (infoA["x2"], anA["per_round"][:8], anA["per_round_all_one"]))
    print("[Q3] control relleno no inocuo (v=%d en %d): opcodes_validos=%s otros=%s"
          % (vb, info_out["fillers"]["positions"][0], anB["loop_valid"],
             anB["harmful_others"]))
    for name in ("ROT", "CRAZY", "DLOAD"):
        m = q4[name]["measure"]
        print("[Q4] %-6s vueltas=%d por-vuelta(6)=%s todas_una=%s otros=%s "
              "jmp_al_trampolín=%s declarado=%s medido=%s"
              % (name, m["rounds_closed"], m["per_round"][:6],
                 m["per_round_all_one"], m["harmful_others"],
                 m["jmp_dest_all_trampoline"], q4[name]["declared"],
                 q4[name]["measured"]))
        ag = q4[name]["engine_agreement"]
        print("     motores: pasos=%s halt=%s memoria_igual=%s destinos_scratch=trazador=%s todo=%s"
              % (ag["steps"], ag["halted"], ag["memory_sha_trace_scratch_indep_equal"],
                 ag["scratch_vs_trace_jmp_dests"], ag["all"]))
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
