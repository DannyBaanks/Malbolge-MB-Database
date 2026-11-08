#!/usr/bin/env python3
"""v3: verificador del resolvedor de epocas (3 motores + controles).

Motores:
  1. trazador Python: usa las primitivas del oraculo del repo
     (tools/oracle_classic.load_memory / crazy_op / _ENC) y registra cada
     escritura de memoria con su direccion fisica.
  2. oraculo Python del repo: tools/oracle_classic.oracle_run.
  3. runner C original: runners/malbolge-original/malbolge.

Salida: results.json (mismo directorio) + traza por stdout.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

sys.path.insert(0, str(PACK))
import build as B  # noqa: E402

C_RUNNER = ROOT / "runners/malbolge-original/malbolge"
PROBE_PAYLOADS = [63, 33, 65, 90, 126, 47, 92, 96]
MEM = B.MEM


def trace_run(source: bytes, stdin_bytes: bytes, max_steps: int = 1000) -> dict:
    """Replica instrumentada de tools/oracle_classic.run (mismas primitivas)."""
    text = source.decode("latin-1")
    mem = oc.load_memory(text)
    a = c = d = 0
    ip = 0
    out: list[int] = []
    log: list[dict] = []
    writes: list[dict] = []
    status = "MAX_STEPS"
    for step in range(1, max_steps + 1):
        cell = mem[c]
        op = (cell + c) % 94
        jumped = False
        target = 0
        rec = {"step": step, "pc": c, "op": op, "byte": cell, "a": a, "d": d}
        if op == 4:
            target = mem[d]
            jumped = True
            rec["jump_read"] = {"cell": d, "value": target}
        elif op == 5:
            out.append(a % 256)
            rec["emitted"] = a % 256
        elif op == 23:
            if ip >= len(stdin_bytes):
                status = "EOF"
                log.append(rec)
                break
            a = stdin_bytes[ip]
            ip += 1
            rec["read_byte"] = a
        elif op == 39:
            old = mem[d]
            mem[d] = (old // 3) + (old % 3) * (3 ** 9)
            a = mem[d]
            rec["write"] = {"addr": d, "old": old, "new": mem[d], "kind": "rot"}
            writes.append(rec["write"] | {"step": step})
        elif op == 40:
            old_d = d
            d = mem[d]
            rec["d_load"] = {"from": old_d, "value": d}
        elif op == 62:
            old = mem[d]
            old_a = a
            mem[d] = oc.crazy_op(a, old)
            a = mem[d]
            rec["write"] = {"addr": d, "old": old, "new": mem[d],
                            "a_before": old_a, "kind": "crazy"}
            writes.append(rec["write"] | {"step": step})
        elif op == 81:
            status = "HALTED"
            log.append(rec)
            break
        if jumped:
            c = target
        if 33 <= mem[c] <= 126:
            rec["encrypted_at"] = c
            mem[c] = oc._ENC[mem[c]]
        rec["pc_after"] = (c + 1) % MEM
        log.append(rec)
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {
        "output": bytes(out),
        "steps": len(log),
        "status": status,
        "log": log,
        "writes": writes,
        "final": {
            "pointer_cell": mem[B.W],
            "req_scratch": mem[B.W1],
            "pay_scratch": mem[B.S],
            "epoch_cells": {str(e): mem[e] for e in B.EPOCHS},
            "successors": {str(e): mem[e + 1] for e in B.EPOCHS},
            "registers": [a, c, d],
        },
    }


def run_c(path: Path, stdin_bytes: bytes) -> tuple[str, int]:
    p = subprocess.run([str(C_RUNNER), str(path), "2000000"],
                       input=stdin_bytes, capture_output=True, timeout=120)
    return p.stdout.hex(), p.returncode


def main() -> int:
    results: dict = {}
    ok = True

    # ---------- 0. integridad de las instancias conservadas ----------
    integrity = {}
    for mutant in B.MUTANTS:
        name = mutant or "resolver"
        path = PACK / (name + ".mb")
        raw = path.read_bytes()
        rebuilt, meta = B.build(mutant)
        integrity[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "matches_build": raw == rebuilt,
            "length": len(raw),
            "printable": all(33 <= b <= 126 for b in raw),
            "no_whitespace": not any(chr(b).isspace() for b in raw),
        }
        ok = ok and integrity[name]["matches_build"] and integrity[name]["printable"]
    results["integrity"] = integrity
    print("[integrity] " + json.dumps(integrity, indent=2), flush=True)

    # ---------- 1. barrido de exactitud 0..255 en las tres epocas ----------
    data, meta = B.build("")
    sweep = {}
    for ep in meta["epochs"]:
        req = meta["request_bytes"][str(ep)]
        bad = []
        for payload in range(256):
            tr = trace_run(data, bytes([req, payload]))
            w = [x for x in tr["writes"] if x["addr"] == ep]
            if len(w) != 1 or w[0]["old"] != B.MASK or w[0]["new"] != payload:
                bad.append({"payload": payload, "writes": w})
        sweep[str(ep)] = {"checked": 256, "mismatches": len(bad), "examples": bad[:5]}
        ok = ok and not bad
    results["exactness_sweep_0_255"] = sweep
    print("[exactness] " + json.dumps(sweep), flush=True)

    # ---------- 2. triple motor ----------
    engines = {}
    verdicts = {}
    for mutant in B.MUTANTS:
        name = mutant or "resolver"
        path = PACK / (name + ".mb")
        dbytes, m = B.build(mutant)
        rows = []
        for ep in m["epochs"]:
            req = m["request_bytes"][str(ep)]
            for payload in PROBE_PAYLOADS:
                tr = trace_run(dbytes, bytes([req, payload]))
                stdin_bytes = bytes([req, payload])
                orc = oc.oracle_run(str(path), 2000000,
                                    "".join(chr(b) for b in stdin_bytes),
                                    stop_on_eof=True)
                cout, crc = run_c(path, stdin_bytes)
                c_norm = cout[:-2] if cout.endswith("0a") else cout
                decoded = (payload + ep) % 94
                row = {
                    "epoch": ep,
                    "request": req,
                    "payload": payload,
                    "payload_opcode_at_epoch": decoded,
                    "trace_out": tr["output"].hex(),
                    "trace_status": tr["status"],
                    "trace_steps": tr["steps"],
                    "out_pcs": [r["pc"] for r in tr["log"] if r.get("op") == 5],
                    "oracle_out": orc["output"].encode("latin-1").hex(),
                    "oracle_status": orc["status"],
                    "oracle_steps": orc["steps"],
                    "c_out": cout,
                    "c_exit": crc,
                    "epoch_writes": [x for x in tr["writes"] if x["addr"] == ep],
                    "pointer_cell": tr["final"]["pointer_cell"],
                }
                row["trace_eq_oracle"] = row["trace_out"] == row["oracle_out"]
                row["c_eq_oracle"] = c_norm == row["oracle_out"]
                row["write_exact"] = (len(row["epoch_writes"]) == 1
                                      and row["epoch_writes"][0]["new"] == payload
                                      and row["epoch_writes"][0]["old"] == B.MASK)
                row["executed_at_epoch"] = (row["out_pcs"] == [ep]
                                            if decoded == B.OPS["OUT"] else True)
                rows.append(row)
                ok = ok and row["trace_eq_oracle"] and row["c_eq_oracle"]
        engines[name] = rows
        # veredicto por control
        expect_fail = {
            "resolver": set(),
            "mutant_residue": {m["epochs"][2]},
            "mutant_journal": set(m["epochs"]),
            "mutant_pointer": set(m["epochs"]),
            "mutant_mask": {m["epochs"][2]},
            "mutant_target": set(m["epochs"]),
        }[name]
        detail = []
        for ep in m["epochs"]:
            r63 = [r for r in rows if r["epoch"] == ep and r["payload"] == 63][0]
            produced = r63["oracle_out"] == "3f"
            should = ep not in expect_fail
            detail.append({"epoch": ep, "out_produced": produced,
                           "expected": should, "ok": produced == should})
            if name == "resolver":
                ok = ok and produced and r63["write_exact"] and r63["executed_at_epoch"]
            else:
                ok = ok and produced == should
        verdicts[name] = {"cases": detail,
                          "trace_eq_oracle": all(r["trace_eq_oracle"] for r in rows),
                          "c_eq_oracle": all(r["c_eq_oracle"] for r in rows)}
        print(f"[engine] {name:16s} filas={len(rows)} "
              f"trace==oracle={verdicts[name]['trace_eq_oracle']} "
              f"c==oracle={verdicts[name]['c_eq_oracle']} "
              f"casos_ok={all(c['ok'] for c in detail)}", flush=True)
    results["engines"] = engines
    results["verdicts"] = verdicts

    # ---------- 3. traza fisica (direccion de escritura y de ejecucion) ----------
    physical = {}
    for ep in meta["epochs"]:
        req = meta["request_bytes"][str(ep)]
        tr = trace_run(data, bytes([req, 63]))
        physical[str(ep)] = {
            "request_byte": req,
            "epoch_address": ep,
            "epoch_residue": ep % 94,
            "pointer_cell_value": tr["final"]["pointer_cell"],
            "pointer_equals_request": tr["final"]["pointer_cell"] == req,
            "writes": tr["writes"],
            "epoch_write": [x for x in tr["writes"] if x["addr"] == ep],
            "out_pc": [r["pc"] for r in tr["log"] if r.get("op") == 5],
            "executed_at_epoch": [r["pc"] for r in tr["log"] if r.get("op") == 5] == [ep],
            "opcode_of_payload_at_epoch": (63 + ep) % 94,
            "successor_value": tr["final"]["successors"][str(ep)],
            "successor_opcode": (tr["final"]["successors"][str(ep)] + ep + 1) % 94,
            "log": tr["log"],
        }
        ok = ok and physical[str(ep)]["pointer_equals_request"]
        ok = ok and physical[str(ep)]["executed_at_epoch"]
    results["physical_trace"] = physical

    # tabla de decodificacion: el mismo byte en las tres celdas de epoca
    decode_table = {
        str(e): {"residue": e % 94,
                 "opcode_of_63": (63 + e) % 94,
                 "opcode_of_0": (0 + e) % 94}
        for e in B.EPOCHS
    }
    decode_table["mutant_residue_223"] = {"residue": 223 % 94,
                                          "opcode_of_63": (63 + 223) % 94,
                                          "opcode_of_0": (0 + 223) % 94}
    results["decode_table"] = decode_table
    print("[decode] " + json.dumps(decode_table), flush=True)

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                        encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
