#!/usr/bin/env python3
"""epoch_mask_native_v1 — verificador de la imagen autónoma (3 motores).

Motores:
  1. trazador Python con las primitivas del oráculo del repo
     (load_memory / crazy_op / _ENC), registra cada escritura con su dirección.
  2. oráculo del repo: tools/oracle_classic.oracle_run.
  3. runner C original: runners/malbolge-original/malbolge.

Comprobaciones:
  0. integridad de las instancias conservadas (reconstrucción + imprimibles).
  1. trazado físico: mem[41] = 29524 tras pc1 y mem[41] = 59048 tras el último
     CRAZY; OUT en pc = OUT_PC con el byte exacto; estado final de registros.
  2. triple motor sobre las 5 instancias.
  3. veredicto por control negativo (cada mutante debe fallar donde debe).
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
MEM = 3 ** 10


def trace(source: bytes, max_steps: int = 2000) -> dict:
    text = source.decode("latin-1")
    mem = oc.load_memory(text)
    a = c = d = 0
    out: list[int] = []
    writes: list[dict] = []
    log: list[dict] = []
    status = "MAX_STEPS"
    for step in range(1, max_steps + 1):
        cell = mem[c]
        op = (cell + c) % 94
        rec = {"step": step, "pc": c, "op": op, "byte": cell, "a": a, "d": d}
        if op == 5:
            out.append(a % 256)
            rec["emitted"] = a % 256
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
            mem[d] = oc.crazy_op(a, old)
            a = mem[d]
            rec["write"] = {"addr": d, "old": old, "new": mem[d], "kind": "crazy"}
            writes.append(rec["write"] | {"step": step})
        elif op == 81:
            status = "HALTED"
            log.append(rec)
            break
        if 33 <= mem[c] <= 126:
            rec["encrypted_at"] = c
            mem[c] = oc._ENC[mem[c]]
        rec["pc_after"] = (c + 1) % MEM
        log.append(rec)
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {"output": bytes(out), "steps": len(log), "status": status,
            "writes": writes, "log": log,
            "final": {"q_cell": mem[B.Q], "p_cell": mem[B.P],
                      "h_cell": mem[B.H], "registers": [a, c, d]}}


def run_c(path: Path, stdin_bytes: bytes = b"", timeout: int = 120):
    p = subprocess.run([str(C_RUNNER), str(path), "2000000"],
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    return p.stdout.hex(), p.returncode


def main() -> int:
    results: dict = {}
    ok = True

    # ---------- 0. integridad ----------
    integrity = {}
    for m in B.MUTANTS:
        name = m or "mask_native"
        raw = (PACK / (name + ".mb")).read_bytes()
        rebuilt, meta = B.build(m)
        integrity[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "matches_build": raw == rebuilt,
            "length": len(raw),
            "printable": meta["printable"],
            "blocks": meta["blocks"],
        }
        ok = ok and integrity[name]["matches_build"] and integrity[name]["printable"]
    results["integrity"] = integrity
    print("[integrity] " + json.dumps(
        {k: {"matches_build": v["matches_build"], "printable": v["printable"],
             "len": v["length"]} for k, v in integrity.items()}), flush=True)

    # ---------- 1. traza física de la instancia buena ----------
    data, meta = B.build("")
    tr = trace(data)
    q_writes = [w for w in tr["writes"] if w["addr"] == B.Q]
    boot_write = q_writes[0] if q_writes else None
    physical = {
        "boot_write": boot_write,
        "boot_is_29524": boot_write is not None and boot_write["new"] == 29524,
        "q_writes_total": len(q_writes),
        "last_q_write": q_writes[-1] if q_writes else None,
        "final_q_is_59048": tr["final"]["q_cell"] == 59048,
        "out_pcs": [r["pc"] for r in tr["log"] if r.get("op") == 5],
        "out_bytes": tr["output"].hex(),
        "steps": tr["steps"],
        "status": tr["status"],
        "registers": tr["final"]["registers"],
        "p_cell_final": tr["final"]["p_cell"],
        "writes_summary": [
            {"addr": w["addr"], "kind": w["kind"], "old": w["old"],
             "new": w["new"]} for w in tr["writes"]],
    }
    results["physical_trace"] = physical
    ok = ok and (physical["boot_is_29524"] and physical["final_q_is_59048"]
                 and physical["out_bytes"] == "a8" and physical["status"] == "HALTED")
    print("[physical] boot=%s Q_final=%s OUT=%s pasos=%d estado=%s "
          "escrituras_en_Q=%d" % (
              physical["boot_write"], physical["final_q_is_59048"],
              physical["out_bytes"], physical["steps"], physical["status"],
              physical["q_writes_total"]), flush=True)

    # ---------- 2. triple motor ----------
    engines = {}
    verdicts = {}
    for m in B.MUTANTS:
        name = m or "mask_native"
        path = PACK / (name + ".mb")
        dbytes, mmeta = B.build(m)
        rows = []
        tr2 = trace(dbytes)
        orc = oc.oracle_run(str(path), 2000000, "", stop_on_eof=True)
        cout, crc = run_c(path, b"")
        c_norm = cout[:-2] if cout.endswith("0a") else cout
        row = {
            "instance": name,
            "expected_q": mmeta["expected_q"],
            "expected_out": mmeta["expected_out"],
            "trace_out": tr2["output"].hex(),
            "trace_status": tr2["status"],
            "trace_final_q": tr2["final"]["q_cell"],
            "oracle_out": orc["output"].encode("latin-1").hex(),
            "oracle_status": orc["status"],
            "c_out": cout, "c_out_norm": c_norm, "c_exit": crc,
            "trace_eq_oracle": tr2["output"].hex() == orc["output"].encode("latin-1").hex(),
            "c_eq_oracle": c_norm == orc["output"].encode("latin-1").hex(),
        }
        if name == "mask_native":
            row["builds_59048"] = tr2["final"]["q_cell"] == 59048
            row["emits_168"] = c_norm == "a8"
        elif name == "bootstrap_only":
            row["builds_29524"] = tr2["final"]["q_cell"] == 29524
            row["emits_84"] = c_norm == "54"
        else:
            row["diverges_from_target"] = tr2["final"]["q_cell"] != 59048
        rows.append(row)
        engines[name] = rows
        verdicts[name] = {
            "trace_eq_oracle": row["trace_eq_oracle"],
            "c_eq_oracle": row["c_eq_oracle"],
            "final_q": row["trace_final_q"],
            "out": row["c_out_norm"],
        }
        print("[engine] %-24s traza=%s oraculo=%s C=%s Q_final=%s "
              "traza==oraculo=%s C==oraculo=%s" % (
                  name, row["trace_out"], row["oracle_out"], cout,
                  row["trace_final_q"], row["trace_eq_oracle"],
                  row["c_eq_oracle"]), flush=True)
    results["engines"] = engines
    results["verdicts"] = verdicts

    # ---------- 3. veredicto por instancia ----------
    good = engines["mask_native"][0]
    boot_only = engines["bootstrap_only"][0]
    ok = ok and (good["trace_eq_oracle"] and good["c_eq_oracle"]
                 and good["trace_final_q"] == 59048 and good["c_out_norm"] == "a8")
    ok = ok and (boot_only["trace_eq_oracle"] and boot_only["c_eq_oracle"]
                 and boot_only["trace_final_q"] == 29524
                 and boot_only["c_out_norm"] == "54")
    for m in B.MUTANTS:
        if m not in B.NEGATIVE:
            continue
        row = engines[m][0]
        ok = ok and row["trace_eq_oracle"] and row["c_eq_oracle"]
        ok = ok and row["trace_final_q"] != 59048
        print("[control] %-24s diverge=%s (Q=%s, OUT=%s)" % (
            m, row["trace_final_q"] != 59048, row["trace_final_q"],
            row["c_out_norm"]), flush=True)

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
