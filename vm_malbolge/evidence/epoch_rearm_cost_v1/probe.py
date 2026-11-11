#!/usr/bin/env python3
"""probe.py — mide C1..C4 y aplica las puertas G0..G6 de `GATES.md`.

Motores: oráculo del repo (`tools/oracle_classic.py`), trazador propio con las
mismas tablas y runner C original (`runners/malbolge-original/malbolge`).

Mediciones:
  C1  coste de cargar la palabra de control con ROT + un CRAZY de preparación:
      instrucciones, pasos, hops de d, celdas auxiliares leídas/escritas.
      Comparación calculada con la tabla de 34 posiciones de la barrera.
  C2  restore exacto de una celda de código ya ejecutada y re-ejecución, con
      control negativo sin restauración.
  C3  M8 = celdas de código distintas que el cuerpo ejecuta por iteración,
      contado desde la traza (no un literal).
  C4  rearm de las celdas auxiliares: mínimo de CRAZYs por celda (exhaustivo por
      trit), rearm ejecutado de una celda y cota inferior del ciclo. Si el ciclo
      cerrado no se construye: NOT_DEMONSTRATED con la razón.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import deque
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(PACK)]
import oracle_classic as oc  # noqa: E402
import plan as P  # noqa: E402

C_RUNNER = ROOT / "runners/malbolge-original/malbolge"
BARRIER = ROOT / "vm_malbolge/evidence/epoch_rearm_barrier_v1/position_table.json"
MEM = 3 ** 10
PRINTABLE = range(33, 127)
TBL = P.TBL
MAX_STEPS = 1000
FORBIDDEN = "2" + "0" + "0"   # el literal que G5 prohíbe (no aparece escrito)

LINES: list[str] = []


def say(text: str = "") -> None:
    LINES.append(text)
    print(text, flush=True)


# ---------------------------------------------------------------- engines
def trace(data: bytes, max_steps: int = MAX_STEPS) -> dict:
    """Trazador con las tablas del oráculo: registra pc/op/byte y escrituras."""
    mem = oc.load_memory(data.decode("ascii"))
    a = c = d = 0
    out: list[int] = []
    log: list[dict] = []
    writes: list[dict] = []
    status = "MAX_STEPS"
    for step in range(1, max_steps + 1):
        cell = mem[c]
        op = (cell + c) % 94
        rec = {"step": step, "pc": c, "op": op, "byte": cell, "a": a, "d": d}
        jumped = False
        tgt = 0
        if op == 4:
            tgt = mem[d]
            rec["jump_to"] = tgt + 1
            jumped = True
        elif op == 5:
            out.append(a % 256)
            rec["emitted"] = a % 256
        elif op == 39:
            old = mem[d]
            mem[d] = P.rot(old)
            a = mem[d]
            rec["wrote"] = d
            writes.append({"step": step, "addr": d, "old": old, "new": a,
                           "kind": "rot"})
        elif op == 40:
            d = mem[d]
            rec["d_after_read"] = d
        elif op == 62:
            old = mem[d]
            mem[d] = oc.crazy_op(a, old)
            a = mem[d]
            rec["wrote"] = d
            writes.append({"step": step, "addr": d, "old": old, "new": a,
                           "kind": "crazy"})
        elif op == 81:
            status = "HALTED"
            log.append(rec)
            break
        if jumped:
            c = tgt
        if 33 <= mem[c] <= 126:
            old = mem[c]
            mem[c] = oc._ENC[old]
            writes.append({"step": step, "addr": c, "old": old, "new": mem[c],
                           "kind": "enc"})
        c = (c + 1) % MEM
        d = (d + 1) % MEM
        log.append(rec)
    return {"output": bytes(out), "steps": len(log), "status": status,
            "log": log, "writes": writes, "final": {"a": a, "c": c, "d": d}}


def run_c(path: Path) -> dict:
    p = subprocess.run([str(C_RUNNER), str(path), str(MAX_STEPS)],
                       capture_output=True, timeout=120)
    stdout_hex = p.stdout.hex()
    body = stdout_hex[:-2] if stdout_hex.endswith("0a") else stdout_hex
    m = None
    for line in p.stderr.decode("latin-1").splitlines():
        if line.startswith("steps:"):
            m = line
    steps = status = None
    if m:
        parts = m.replace("|", " ").split()
        steps = int(parts[1])
        status = parts[3]
    return {"stdout_hex": stdout_hex, "output_hex": body,
            "steps": steps, "status": status, "returncode": p.returncode}


# ---------------------------------------------------------------- C4 maths
def trits(v: int) -> list[int]:
    return [(v // 3 ** i) % 3 for i in range(10)]


def min_crazys(x: int, y: int) -> int:
    """Mínimo de CRAZYs para llevar x a y (mapas por trit, BFS exhaustivo)."""
    def dist(src: int, dst: int) -> int:
        seen = {src: 0}
        q = deque([src])
        while q:
            u = q.popleft()
            if u == dst:
                return seen[u]
            for ctrl in range(3):
                w = TBL[u][ctrl]
                if w not in seen:
                    seen[w] = seen[u] + 1
                    q.append(w)
        raise AssertionError("trit inalcanzable")

    return max(dist(trits(x)[i], trits(y)[i]) for i in range(10))


def swap01(v: int) -> int:
    return sum((1 if t == 0 else 0 if t == 1 else 2) * 3 ** i
               for i, t in enumerate(trits(v)))


def orbit(v: int) -> list[int]:
    out, x = [], v
    for _ in range(10):
        out.append(x)
        x = P.rot(x)
    return out


# ---------------------------------------------------------------- gates
def main() -> int:
    results: dict = {"dialect": "classic-permissive-3^10",
                     "pack": PACK.name}
    ok = True

    # ---------- G0: integridad y determinismo ----------
    say("[G0] integridad y determinismo")
    built = {}
    integrity = {}
    for name, p, info in P.images():
        data = p.dump()
        path = PACK / (name + ".mb")
        disk = path.read_bytes()
        rebuilt = P.build(name == "restore" or name == "rearm",
                          name == "rearm")[0].dump()
        row = {
            "sha256": hashlib.sha256(disk).hexdigest(),
            "length": len(disk),
            "printable": all(33 <= b <= 126 for b in disk),
            "no_whitespace": not any(chr(b).isspace() for b in disk),
            "matches_rebuild": rebuilt == disk,
            "matches_disk": data == disk,
        }
        integrity[name] = row
        built[name] = disk
        ok = ok and all(row[k] for k in
                        ("printable", "no_whitespace", "matches_rebuild",
                         "matches_disk"))
        say("  %-10s len=%3d sha256=%s printable=%s no_ws=%s rebuild=%s"
            % (name, len(disk), row["sha256"][:16], row["printable"],
               row["no_whitespace"], row["matches_rebuild"]))
    results["integrity"] = integrity

    # ---------- G1: tres motores ----------
    say("[G1] tres motores")
    engines = {}
    for name in ("restore", "no_restore", "rearm"):
        path = PACK / (name + ".mb")
        tr = trace(built[name])
        orc = oc.oracle_run(str(path), MAX_STEPS)
        c = run_c(path)
        oracle_out = orc["output"].encode("latin-1").hex()
        row = {
            "oracle": {"output_hex": oracle_out, "steps": orc["steps"],
                       "status": orc["status"]},
            "tracer": {"output_hex": tr["output"].hex(), "steps": tr["steps"],
                       "status": tr["status"]},
            "c_runner": c,
            "agree": (oracle_out == tr["output"].hex() == c["output_hex"]
                      and orc["steps"] == tr["steps"] == c["steps"]
                      and orc["status"] == tr["status"] == c["status"]),
        }
        engines[name] = row
        ok = ok and row["agree"]
        say("  %-10s oracle=%s/%d/%s tracer=%s/%d/%s c=%s/%s/%s agree=%s"
            % (name, oracle_out, orc["steps"], orc["status"],
               tr["output"].hex(), tr["steps"], tr["status"],
               c["output_hex"], c["steps"], c["status"], row["agree"]))
    results["engines"] = engines

    # ---------- C1: coste de la palabra de control ----------
    say("[C1] carga de la palabra de control (ROT + un CRAZY)")
    tr = trace(built["restore"])
    info = P.build(True, False)[1]
    ctrl = info["ctrl"]
    seg = [r for r in tr["log"] if 46 <= r["pc"] <= 50]
    hops = [r for r in seg if r["op"] == 40]
    reads = sorted({r["d"] for r in hops} |
                   {r["wrote"] for r in seg if "wrote" in r})
    code_cells = {r["pc"] for r in seg}
    aux = sorted(set(reads) - code_cells)
    seg_writes = [w for w in tr["writes"]
                  if seg[0]["step"] <= w["step"] <= seg[-1]["step"]
                  and w["kind"] in ("rot", "crazy")]
    destroyed = sorted({w["addr"] for w in seg_writes})
    table = json.loads(BARRIER.read_text(encoding="utf8"))
    nxt = next((r for r in tr["log"] if r["pc"] == 51), None)
    a_after = nxt["a"] if nxt else None
    c1 = {
        "instructions": len(seg),
        "steps": seg[-1]["step"] - seg[0]["step"] + 1,
        "pcs": [r["pc"] for r in seg],
        "ops": [P.OPNAME.get(r["op"], r["op"]) for r in seg],
        "d_hops": [{"pc": r["pc"], "d": r["d"],
                    "d_after_read": r.get("d_after_read")} for r in hops],
        "aux_cells": aux,
        "aux_cells_read": aux,
        "aux_cells_written": destroyed,
        "aux_writes": seg_writes,
        "a_after_load": a_after,
        "load_ok": (a_after == ctrl
                    and [r["op"] for r in seg] == [40, 40, 39, 40, 62]),
        "ctrl": ctrl,
        "v1": info["v1"],
        "v2": info["v2"],
        "barrier_table_cells": table["cells_with_rearmable_opcodes"],
        "cell_in_barrier_table": str(P.X) in table["position_table"],
        "swap01_v": swap01(P.V),
        "swap01_in_orbit_v": swap01(P.V) in orbit(P.V),
        "orbit_printable": [x for x in orbit(P.V) if 33 <= x <= 126],
    }
    ok = ok and c1["instructions"] == 5 and c1["steps"] == 5 \
        and c1["load_ok"]
    say("  instrucciones=%d pasos=%d hops=%d aux=%s destruidas=%s"
        % (c1["instructions"], c1["steps"], len(hops), aux, destroyed))
    say("  ctrl=%d (v1=%d v2=%d); tabla de la barrera: celda %d en tabla=%s; "
        "swap01(%d)=%d en orbita=%s"
        % (ctrl, info["v1"], info["v2"], P.X, c1["cell_in_barrier_table"],
           P.V, c1["swap01_v"], c1["swap01_in_orbit_v"]))
    results["c1_control_word"] = c1

    # ---------- C2 / G3: restore exacto ----------
    say("[C2] restore exacto y re-ejecución")
    execs = [r for r in tr["log"] if r["pc"] == P.X]
    crazy_x = [w for w in tr["writes"]
               if w["addr"] == P.X and w["kind"] == "crazy"]
    second = execs[1] if len(execs) > 1 else None
    c2 = {
        "x": P.X,
        "executions": len(execs),
        "ops": [r["op"] for r in execs],
        "emitted": [r.get("emitted") for r in execs],
        "second_byte": second["byte"] if second else None,
        "second_op": second["op"] if second else None,
        "crazy_writes": crazy_x,
        "output_hex": tr["output"].hex(),
        "steps": tr["steps"],
        "status": tr["status"],
    }
    ok = ok and (c2["executions"] == 2 and c2["ops"] == [5, 5]
                 and c2["emitted"] == [42, 55]
                 and len(crazy_x) == 1
                 and crazy_x[0]["old"] == oc._ENC[P.V]
                 and crazy_x[0]["new"] == P.V
                 and c2["output_hex"] == "2a37"
                 and c2["status"] == "HALTED")
    say("  ejecuciones=%d ops=%s emitidos=%s segundo_byte=%s crazy_a_X=%s"
        % (c2["executions"], c2["ops"], c2["emitted"], c2["second_byte"],
           [(w["old"], w["new"]) for w in crazy_x]))
    say("  salida=%s pasos=%d estado=%s"
        % (c2["output_hex"], c2["steps"], c2["status"]))
    results["c2_restore"] = c2

    # ---------- G4: control negativo ----------
    say("[C2-neg] control negativo sin restauración")
    trn = trace(built["no_restore"])
    execs_n = [r for r in trn["log"] if r["pc"] == P.X]
    crazy_n = [w for w in trn["writes"]
               if w["addr"] == P.X and w["kind"] == "crazy"]
    second_n = execs_n[1] if len(execs_n) > 1 else None
    neg = {
        "executions": len(execs_n),
        "ops": [r["op"] for r in execs_n],
        "second_byte": second_n["byte"] if second_n else None,
        "second_op": second_n["op"] if second_n else None,
        "crazy_writes": crazy_n,
        "output_hex": trn["output"].hex(),
        "steps": trn["steps"],
        "status": trn["status"],
    }
    ok = ok and (neg["executions"] == 2 and neg["second_op"] != 5
                 and neg["second_byte"] == oc._ENC[P.V]
                 and not crazy_n
                 and neg["output_hex"] == "2a"
                 and neg["status"] == "HALTED")
    say("  ejecuciones=%d ops=%s segundo_byte=%s crazy_a_X=%d salida=%s/%s"
        % (neg["executions"], neg["ops"], neg["second_byte"], len(crazy_n),
           neg["output_hex"], neg["status"]))
    results["c2_negative_control"] = neg

    # ---------- C3 / G5: M8 desde la traza ----------
    say("[C3] M8 medido desde la traza")
    first_x = next(i for i, r in enumerate(tr["log"]) if r["pc"] == P.X)
    body = tr["log"][first_x:]
    body_pcs = sorted({r["pc"] for r in body})
    counts = {pc: sum(1 for r in body if r["pc"] == pc) for pc in body_pcs}
    reexec = sorted(pc for pc in body_pcs if counts[pc] >= 2)
    # conteo independiente: misma definición sobre la ejecución del control
    first_xn = next(i for i, r in enumerate(trn["log"]) if r["pc"] == P.X)
    body_pcs_n = sorted({r["pc"] for r in trn["log"][first_xn:]})
    code_map = sorted(k for k in P.build(True, False)[0].code
                      if P.X <= k <= 55)
    m8 = {
        "m8_body_code_cells": len(body_pcs),
        "body_pcs": body_pcs,
        "executions_per_pc": {str(k): v for k, v in counts.items()},
        "re_executed_pcs": reexec,
        "independent_no_restore_count": len(body_pcs_n),
        "code_map_cells_44_55": code_map,
        "code_map_count": len(code_map),
        "forbidden_literal_present": FORBIDDEN in Path(__file__).read_text(
            encoding="utf8"),
    }
    ok = ok and (m8["m8_body_code_cells"] > 0
                 and m8["m8_body_code_cells"] == m8["independent_no_restore_count"]
                 and m8["m8_body_code_cells"] == m8["code_map_count"]
                 and not m8["forbidden_literal_present"])
    say("  M8=%d celdas=%s re-ejecutadas=%s independiente=%d code_map=%d"
        % (m8["m8_body_code_cells"], body_pcs, reexec,
           m8["independent_no_restore_count"], m8["code_map_count"]))
    results["c3_m8"] = m8

    # ---------- C4 / G6: rearm ----------
    say("[C4] rearm de celdas auxiliares")
    final_write: dict[int, dict] = {}
    for w in tr["writes"]:
        if w["step"] >= tr["log"][first_x]["step"]:
            final_write[w["addr"]] = w
    rearm_cells = []
    for addr in sorted(final_write):
        w = final_write[addr]
        rearm_cells.append({
            "addr": addr,
            "kind": w["kind"],
            "final": w["new"],
            "target": w["old"],
            "min_crazys": min_crazys(w["new"], w["old"]),
        })
    total_crazys = sum(r["min_crazys"] for r in rearm_cells)
    required = [r for r in rearm_cells if r["addr"] != 43]
    total_crazys_req = sum(r["min_crazys"] for r in required)
    # rearm ejecutado: celda 103 en la imagen rearm
    trr = trace(built["rearm"])
    info_r = P.build(True, True)[1]
    w103 = [w for w in trr["writes"]
            if w["addr"] == 103 and w["kind"] == "crazy"]
    rearm_exec = w103[-1] if w103 else None
    seg_r = [r for r in trr["log"] if 56 <= r["pc"] <= 62]
    code_r = {r["pc"] for r in seg_r}
    consumed_r = sorted({w["addr"] for w in trr["writes"]
                         if seg_r[0]["step"] <= w["step"] <= seg_r[-1]["step"]
                         and w["kind"] in ("rot", "crazy")
                         and w["addr"] not in code_r
                         and w["addr"] != 103})
    c4 = {
        "cells_written_by_body": len(rearm_cells),
        "rearm_cells": rearm_cells,
        "total_min_crazys": total_crazys,
        "cells_required_for_loop": len(required),
        "total_min_crazys_required": total_crazys_req,
        "lower_bound_instructions_required": total_crazys_req * len(seg_r),
        "lower_bound_new_aux_cells_required": total_crazys_req * len(consumed_r),
        "note_cell_43": "el JMP de la celda 55 cifra mem[mem[d]] = mem[43] "
                        "(quirk del JMP); esa celda sólo la usa el bootstrap, "
                        "así que la cota conservadora la incluye y la cota "
                        "del bucle la excluye",
        "instructions_per_crazy_measured": len(seg_r),
        "lower_bound_instructions": total_crazys * len(seg_r),
        "new_aux_cells_per_crazy_measured": len(consumed_r),
        "lower_bound_new_aux_cells": total_crazys * len(consumed_r),
        "rearm_executed": {
            "cell": 103,
            "old": rearm_exec["old"] if rearm_exec else None,
            "new": rearm_exec["new"] if rearm_exec else None,
            "target": info_r["v2"],
            "ok": bool(rearm_exec and rearm_exec["new"] == info_r["v2"]),
            "segment_pcs": [r["pc"] for r in seg_r],
            "segment_steps": len(seg_r),
            "aux_cells": consumed_r,
        },
        "rot_fixed_points_printable": [v for v in range(33, 127)
                                       if P.rot(v) == v],
        "cycle_closed": False,
        "cycle_status": "NOT_DEMONSTRATED",
        "cycle_reason": "cada carga de palabra de control consume una celda "
                        "ROT y no hay punto fijo ROT imprimible; el rearm "
                        "medido consume %d celdas nuevas; no se construyó "
                        "un ciclo cerrado" % len(consumed_r),
    }
    ok = ok and c4["rearm_executed"]["ok"] and len(seg_r) == 7
    say("  celdas escritas por el cuerpo=%d, CRAZYs mínimos=%d, cota=%d instr"
        % (c4["cells_written_by_body"], total_crazys,
           c4["lower_bound_instructions"]))
    say("  rearm 103: %s -> %s (objetivo %d) ok=%s; segmento=%d pasos, "
        "aux nuevas=%s"
        % (c4["rearm_executed"]["old"], c4["rearm_executed"]["new"],
           c4["rearm_executed"]["target"], c4["rearm_executed"]["ok"],
           c4["rearm_executed"]["segment_steps"],
           c4["rearm_executed"]["aux_cells"]))
    say("  ciclo cerrado=%s (%s)"
        % (c4["cycle_closed"], c4["cycle_status"]))
    results["c4_rearm"] = c4

    # ---------- veredicto ----------
    results["gates"] = {
        "G0_integrity": all(all(integrity[n][k] for k in
                                ("printable", "no_whitespace",
                                 "matches_rebuild", "matches_disk"))
                            for n in integrity),
        "G1_three_engines": all(engines[n]["agree"] for n in engines),
        "G2_control_word": (c1["instructions"] == 5 and c1["steps"] == 5
                            and c1["load_ok"]),
        "G3_restore_exact": (c2["executions"] == 2 and c2["ops"] == [5, 5]
                             and len(crazy_x) == 1
                             and crazy_x[0]["new"] == P.V),
        "G4_negative_control": (neg["executions"] == 2
                                and neg["second_op"] != 5 and not crazy_n),
        "G5_m8": (m8["m8_body_code_cells"] > 0
                  and m8["m8_body_code_cells"] == m8["independent_no_restore_count"]
                  and not m8["forbidden_literal_present"]),
        "G6_rearm": c4["rearm_executed"]["ok"],
    }
    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf8")
    (PACK / "stdout.raw.txt").write_text("\n".join(LINES) + "\n",
                                         encoding="utf8")
    say("[verdict] all_checks_pass=%s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
