#!/usr/bin/env python3
"""probe.py — epoch_resolver_word_v1: payload de 10 trits, escritura exacta y ejecución.

Motores: trazador con las primitivas del oráculo del repo, oráculo del repo y
runner C original.

Comprobaciones:
  0. integridad (reconstrucción, imprimibles, sin whitespace).
  1. traza física: el puntero W guarda el byte de petición exacto, la celda de
     época T guarda el payload EXACTO (palabra de 10 trits con 2s en posiciones
     altas), el OUT se emite en pc = T (el payload se ejecuta) con V % 256, y el
     programa para en T+1 (END).
  2. triple motor en las tres instancias.
  3. veredicto por control: con la máscara 121 la escritura del payload falla.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools"),
                str(ROOT / "vm_malbolge/tools/native_classic")]
import oracle_classic as oc  # noqa: E402
import constants as nc        # motor independiente (tables + crazy_op/rot_op)

sys.path.insert(0, str(PACK))
import build as B  # noqa: E402

C_RUNNER = ROOT / "runners/malbolge-original/malbolge"
MEM = 3 ** 10


def trace(source: bytes, stdin_bytes: bytes, max_steps: int = 200000,
          engine: str = "repo") -> dict:
    text = source.decode("latin-1")
    if engine == "nc":
        # load_memory de native_classic no existe: réplica exacta con sus primitivas
        chars = [c for c in text if not c.isspace()]
        mem = [0] * MEM
        for i, c in enumerate(chars):
            mem[i] = ord(c)
        for i in range(len(chars), MEM):
            mem[i] = nc.crazy_op(mem[i - 1], mem[i - 2])
        crazy = nc.crazy_op
        rot = lambda v: nc.rot_op(v)
        enc = None
    else:
        mem = oc.load_memory(text)
        crazy = oc.crazy_op
        rot = lambda v: (v // 3) + (v % 3) * 19683
        enc = oc._ENC
    a = c = d = 0
    ip = 0
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
        elif op == 23:
            if ip >= len(stdin_bytes):
                status = "EOF"
                log.append(rec)
                break
            a = stdin_bytes[ip]
            ip += 1
            rec["read_byte"] = a
        elif op == 4:
            rec["jump_target"] = mem[d]
            c = mem[d]
        elif op == 39:
            old = mem[d]
            mem[d] = rot(old)
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "kind": "rot",
                           "step": step})
        elif op == 40:
            old_d = d
            d = mem[d]
            rec["d_load"] = {"from": old_d, "value": d}
        elif op == 62:
            old = mem[d]
            mem[d] = crazy(a, old)
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "kind": "crazy",
                           "step": step})
        elif op == 81:
            status = "HALTED"
            log.append(rec)
            break
        if 33 <= mem[c] <= 126:
            mem[c] = (enc or {33 + i: nc.XLAT2[i] for i in range(94)})[mem[c]]
        log.append(rec)
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {"output": bytes(out), "steps": len(log), "status": status,
            "writes": writes, "log": log,
            "final": {"T": mem[B.T], "W": mem[B.W], "P": mem[B.P],
                      "A": mem[B.A], "S": mem[B.S], "registers": [a, c, d]}}


def run_c(path: Path, stdin_bytes: bytes, timeout: int = 120):
    p = subprocess.run([str(C_RUNNER), str(path), "200000"],
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    return p.stdout.hex(), p.returncode


def main() -> int:
    results: dict = {}
    ok = True
    V = B.V
    T = B.T
    req = bytes([B.REQUEST])

    # ---------- 0. integridad ----------
    integrity = {}
    for name in ("resolver_word", "resolver_word_dynamic",
                 "mutant_mask_121", "mutant_wrong_payload"):
        raw = (PACK / (name + ".mb")).read_bytes()
        rebuilt = B.build_all()[name]["data"]
        integrity[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "matches_build": raw == rebuilt,
            "length": len(raw),
            "printable": all(33 <= b <= 126 for b in raw),
            "no_whitespace": not any(chr(b).isspace() for b in raw),
        }
        ok = ok and (integrity[name]["matches_build"]
                     and integrity[name]["printable"])
    results["integrity"] = integrity
    print("[integrity] " + json.dumps(
        {k: {"ok": v["matches_build"] and v["printable"], "len": v["length"]}
         for k, v in integrity.items()}), flush=True)

    # ---------- 1. traza física de la instancia buena ----------
    data = B.build_all()["resolver_word"]["data"]
    tr = trace(data, req)
    wT = [w for w in tr["writes"] if w["addr"] == T]
    wW = [w for w in tr["writes"] if w["addr"] == B.W]
    out_pcs = [r["pc"] for r in tr["log"] if r.get("op") == 5]
    physical = {
        "request_byte": B.REQUEST,
        "epoch_cell": T,
        "payload": V,
        "pointer_writes": wW,
        "pointer_exact": bool(wW) and wW[-1]["new"] == B.REQUEST,
        "epoch_writes": wT,
        "epoch_exact": bool(wT) and wT[-1]["new"] == V,
        "out_pcs": out_pcs,
        "out_bytes": tr["output"].hex(),
        "expected_out": f"{V % 256:02x}",
        "emitted_at_epoch": out_pcs == [T],
        "status": tr["status"],
        "steps": tr["steps"],
        "final": tr["final"],
    }
    results["physical_trace"] = physical
    ok = ok and (physical["pointer_exact"] and physical["epoch_exact"]
                 and physical["emitted_at_epoch"]
                 and physical["out_bytes"] == physical["expected_out"]
                 and physical["status"] == "HALTED")
    print("[physical] puntero W=%s exacto=%s | época T=%s exacto=%s | "
          "OUT=%s esperado=%s en pc=%s | pasos=%d estado=%s" % (
              wW[-1]["new"] if wW else None, physical["pointer_exact"],
              tr["final"]["T"], physical["epoch_exact"],
              physical["out_bytes"], physical["expected_out"], out_pcs,
              physical["steps"], physical["status"]), flush=True)
    print("[physical] escrituras en la época: %s" %
          [(w["old"], w["new"]) for w in wT], flush=True)

    # ---------- 2. triple motor ----------
    engines = {}
    for name in ("resolver_word", "resolver_word_dynamic",
                 "mutant_mask_121", "mutant_wrong_payload"):
        path = PACK / (name + ".mb")
        dbytes = B.build_all()[name]["data"]
        tr2 = trace(dbytes, req, engine="repo")
        tr3 = trace(dbytes, req, engine="nc")
        orc = oc.oracle_run(str(path), 200000, "".join(chr(b) for b in req),
                            stop_on_eof=True)
        cout, crc = run_c(path, req)
        c_norm = cout[:-2] if cout.endswith("0a") else cout
        row = {
            "instance": name,
            "trace_out": tr2["output"].hex(),
            "trace_status": tr2["status"],
            "trace_final_T": tr2["final"]["T"],
            "oracle_out": orc["output"].encode("latin-1").hex(),
            "oracle_status": orc["status"],
            "c_out": cout, "c_out_norm": c_norm, "c_exit": crc,
            "trace_eq_oracle": tr2["output"].hex() == orc["output"].encode("latin-1").hex(),
            "nc_trace_out": tr3["output"].hex(),
            "nc_eq_oracle": tr3["output"].hex() == orc["output"].encode("latin-1").hex(),
            "nc_final_T": tr3["final"]["T"],
            "c_eq_oracle": c_norm == orc["output"].encode("latin-1").hex(),
        }
        engines[name] = row
        ok = ok and row["trace_eq_oracle"] and row["nc_eq_oracle"]
        print("[engine] %-22s repo=%s native_classic=%s oraculo=%s C=%s "
              "T_final=%s repo==oraculo=%s nc==oraculo=%s C==oraculo=%s" % (
                  name, row["trace_out"], row["nc_trace_out"],
                  row["oracle_out"], cout, row["trace_final_T"],
                  row["trace_eq_oracle"], row["nc_eq_oracle"],
                  row["c_eq_oracle"]), flush=True)
    results["engines"] = engines

    # ---------- 3. veredicto por control ----------
    good = engines["resolver_word"]
    ok = ok and (good["trace_final_T"] == V
                 and good["trace_out"] == physical["expected_out"])
    m121 = engines["mutant_mask_121"]
    mpay = engines["mutant_wrong_payload"]
    ctrl_121 = {
        "T_final": m121["trace_final_T"],
        "payload_corrupted": m121["trace_final_T"] != V,
        "out": m121["c_out_norm"],
        "out_differs": m121["c_out_norm"] != physical["expected_out"],
    }
    ctrl_pay = {
        "T_final": mpay["trace_final_T"],
        "out": mpay["c_out_norm"],
        "out_differs": mpay["c_out_norm"] != physical["expected_out"],
    }
    results["controls"] = {"mutant_mask_121": ctrl_121,
                           "mutant_wrong_payload": ctrl_pay}
    ok = ok and ctrl_121["payload_corrupted"] and ctrl_121["out_differs"]
    ok = ok and ctrl_pay["out_differs"]
    print("[control] mutant_mask_121      T=%s (payload corrupto=%s) OUT=%s" % (
        ctrl_121["T_final"], ctrl_121["payload_corrupted"], ctrl_121["out"]),
        flush=True)
    print("[control] mutant_wrong_payload T=%s OUT=%s" % (
        ctrl_pay["T_final"], ctrl_pay["out"]), flush=True)

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
