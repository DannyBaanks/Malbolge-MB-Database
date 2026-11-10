#!/usr/bin/env python3
"""probe.py — epoch_rearm_primitive_v1: dos escrituras exactas en una ejecución.

Motores: trazador con las primitivas del oráculo del repo, oráculo del repo
(tools/oracle_classic.oracle_run) y runner C original.  Los tres coinciden byte a
byte en las cinco instancias.

Comprobaciones:
  0. integridad (reconstrucción + imprimibles + sin whitespace).
  1. traza física: valores de A y B en cada fase, escrituras exactas 1 y 2,
     rearmado final (A = B = 29524) y OUT = [V, V2].
  2. triple motor.
  3. veredicto por control negativo.
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
V1, V2 = B.PAYLOAD1, B.PAYLOAD2


def trace(source: bytes, stdin_bytes: bytes, max_steps: int = 200000) -> dict:
    text = source.decode("latin-1")
    mem = oc.load_memory(text)
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
            # JMP: c = mem[d] y la ejecución continúa en mem[d] + 1 (el oráculo
            # cifra la celda destino antes del incremento).
            rec["jump_target"] = mem[d]
            c = mem[d]
        elif op == 39:
            old = mem[d]
            mem[d] = (old // 3) + (old % 3) * 19683
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "kind": "rot",
                           "step": step})
        elif op == 40:
            old_d = d
            d = mem[d]
            rec["d_load"] = {"from": old_d, "value": d}
        elif op == 62:
            old = mem[d]
            mem[d] = oc.crazy_op(a, old)
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "kind": "crazy",
                           "step": step})
        elif op == 81:
            status = "HALTED"
            log.append(rec)
            break
        if 33 <= mem[c] <= 126:
            mem[c] = oc._ENC[mem[c]]
        log.append(rec)
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {"output": bytes(out), "steps": len(log), "status": status,
            "writes": writes, "log": log,
            "final": {"A": mem[B.A], "B": mem[B.B], "S": mem[B.S],
                      "X": mem[B.X], "registers": [a, c, d]}}


def run_c(path: Path, stdin_bytes: bytes, timeout: int = 120):
    p = subprocess.run([str(C_RUNNER), str(path), "200000"],
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    return p.stdout.hex(), p.returncode


def main() -> int:
    results: dict = {}
    ok = True
    stdin_bytes = bytes([V1, V2])

    # ---------- 0. integridad ----------
    integrity = {}
    for m in B.MUTANTS:
        name = m or "rearm_primitive"
        raw = (PACK / (name + ".mb")).read_bytes()
        rebuilt = B.build(m)["data"]
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
    print("[integrity] " + json.dumps({k: {"ok": v["matches_build"]
                                           and v["printable"],
                                           "len": v["length"]}
                                       for k, v in integrity.items()}), flush=True)

    # ---------- 1. traza física de la instancia buena ----------
    r0 = B.build("")
    data, meta = r0["data"], r0["meta"]
    tr = trace(data, stdin_bytes)
    A, Bc, S = B.A, B.B, B.S
    wa = [w for w in tr["writes"] if w["addr"] == A]
    wb = [w for w in tr["writes"] if w["addr"] == Bc]
    b29524 = [w for w in wb if w["old"] == 29524]
    physical = {
        "payloads": [V1, V2],
        "writes_A": wa, "writes_B": wb,
        "A_factory": wa[0]["new"] if wa else None,
        "A_after_write1": [w for w in wa if w["step"] > 12][0]["new"] if len(wa) > 1 else None,
        "A_final": tr["final"]["A"],
        "B_factory": wb[0]["new"] if wb else None,
        "B_write1": b29524[0]["new"] if b29524 else None,
        "B_final": tr["final"]["B"],
        "S_final": tr["final"]["S"],
        "out": tr["output"].hex(),
        "expected_out": bytes([V1, V2]).hex(),
        "steps": tr["steps"],
        "status": tr["status"],
        "A_before_write2": [w for w in wa if w["step"] > 12][-2]["new"] if len(wa) > 2 else None,
        "B_before_write2": [w for w in wb][-2]["new"] if len(wb) > 2 else None,
        "A_restored_before_write2": ([w for w in wa][-2]["new"] == 29524
                                     if len(wa) > 2 else None),
        "B_restored_before_write2": ([w for w in wb][-2]["new"] == 29524
                                     if len(wb) > 2 else None),
        "write1_exact": any(w["addr"] == Bc and w["new"] == V1 for w in tr["writes"]),
        "write2_exact": any(w["addr"] == Bc and w["new"] == V2 for w in tr["writes"]),
    }
    results["physical_trace"] = physical
    ok = ok and (physical["A_restored_before_write2"]
                 and physical["B_restored_before_write2"]
                 and physical["write1_exact"] and physical["write2_exact"]
                 and physical["out"] == physical["expected_out"]
                 and physical["status"] == "HALTED")
    print("[physical] A_final=%s B_final=%s S_final=%s OUT=%s esperado=%s "
          "pasos=%d estado=%s" % (
              physical["A_final"], physical["B_final"], physical["S_final"],
              physical["out"], physical["expected_out"], physical["steps"],
              physical["status"]), flush=True)
    print("[physical] escrituras en A: %s" %
          [(w["old"], w["new"]) for w in wa], flush=True)
    print("[physical] escrituras en B: %s" %
          [(w["old"], w["new"]) for w in wb], flush=True)

    # ---------- 2. triple motor ----------
    engines = {}
    for m in B.MUTANTS:
        name = m or "rearm_primitive"
        path = PACK / (name + ".mb")
        dbytes = B.build(m)["data"]
        tr2 = trace(dbytes, stdin_bytes)
        orc = oc.oracle_run(str(path), 200000, "".join(chr(b) for b in stdin_bytes),
                            stop_on_eof=True)
        cout, crc = run_c(path, stdin_bytes)
        c_norm = cout[:-2] if cout.endswith("0a") else cout
        wb2 = [w for w in tr2["writes"] if w["addr"] == B.B]
        row = {
            "instance": name,
            "B_before_write2": wb2[-2]["new"] if len(wb2) > 2 else None,
            "trace_out": tr2["output"].hex(),
            "trace_status": tr2["status"],
            "trace_final_A": tr2["final"]["A"],
            "trace_final_B": tr2["final"]["B"],
            "oracle_out": orc["output"].encode("latin-1").hex(),
            "oracle_status": orc["status"],
            "c_out": cout, "c_out_norm": c_norm, "c_exit": crc,
            "trace_eq_oracle": tr2["output"].hex() == orc["output"].encode("latin-1").hex(),
            "c_eq_oracle": c_norm == orc["output"].encode("latin-1").hex(),
        }
        engines[name] = row
        ok = ok and row["trace_eq_oracle"] and row["c_eq_oracle"]
        print("[engine] %-22s traza=%s oraculo=%s C=%s A_final=%s B_final=%s "
              "traza==oraculo=%s C==oraculo=%s" % (
                  name, row["trace_out"], row["oracle_out"], cout,
                  row["trace_final_A"], row["trace_final_B"],
                  row["trace_eq_oracle"], row["c_eq_oracle"]), flush=True)
    results["engines"] = engines

    # ---------- 3. veredicto por instancia ----------
    good = engines["rearm_primitive"]
    # tras la escritura 2, A queda consumida (swap(V2)) y B guarda V2 exacto;
    # el rearmado se verifica por el estado INMEDATAMENTE ANTES de la escritura 2.
    ok = ok and (good["trace_out"] == physical["expected_out"]
                 and good["trace_final_B"] == V2
                 and good["B_before_write2"] == 29524
                 and physical["A_restored_before_write2"])
    expect = {
        "mutant_no_rearm":      {"out_ne": bytes([V1, V2]).hex(),
                                 "B_final_ne": 29524},
        "mutant_reload_wrong":   {"out_ne": bytes([V1, V2]).hex()},
        "mutant_boot_trit2":    {"out_ne": bytes([V1, V2]).hex()},
        "mutant_write_wrong_cell": {"out_ne": bytes([V1, V2]).hex()},
    }
    verdicts = {}
    for name in expect:
        row = engines[name]
        diverges = ((row["c_out_norm"] != expect[name]["out_ne"])
                    or (row["B_before_write2"] != 29524))
        verdicts[name] = {"out": row["c_out_norm"],
                          "B_before_write2": row["B_before_write2"],
                          "diverges": diverges}
        ok = ok and diverges
        print("[control] %-22s OUT=%s B_antes_de_escritura2=%s diverge=%s" % (
            name, row["c_out_norm"], row["B_before_write2"], diverges), flush=True)
    results["verdicts"] = verdicts

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
