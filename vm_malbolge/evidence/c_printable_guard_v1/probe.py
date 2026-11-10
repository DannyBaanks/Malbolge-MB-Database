#!/usr/bin/env python3
"""probe.py — c_printable_guard_v1: mide la guarda de imprimibilidad del runner C.

Motores: trazador con las primitivas del oráculo del repo, trazador con las de
`native_classic` y el runner C original.

Comprobaciones:
  0. integridad (reconstrucción, imprimibles, sin whitespace).
  1. programas mínimos: para cada instancia, el trazador calcula el paso en que
     entra por primera vez en una celda NO imprimible.  Predicción: el C para
     exactamente en ese paso.  Con celdas imprimibles (fronteras 33 y 126) la
     predicción es "recorre todo el programa hasta END".
  2. reproducción sobre las cuatro instancias de `epoch_resolver_word_v1`: el
     contador de pasos del C debe coincidir con el paso en que el oráculo toca
     por primera vez la celda de época no imprimible.
  3. control de motor: los dos trazadores Python coinciden byte a byte.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools"),
                str(ROOT / "vm_malbolge/tools/native_classic")]
import oracle_classic as oc  # noqa: E402
import constants as nc        # noqa: E402

sys.path.insert(0, str(PACK))
import build as B  # noqa: E402

C_RUNNER = ROOT / "runners/malbolge-original/malbolge"
RESOLVER = ROOT / "vm_malbolge/evidence/epoch_resolver_word_v1"
MEM = 3 ** 10
PRINTABLE = range(33, 127)


def trace(source: bytes, stdin_bytes: bytes, max_steps: int = 200000,
          engine: str = "repo") -> dict:
    text = source.decode("latin-1")
    if engine == "nc":
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
    log: list[dict] = []
    status = "MAX_STEPS"
    for step in range(1, max_steps + 1):
        cell = mem[c]
        op = (cell + c) % 94
        rec = {"step": step, "pc": c, "byte": cell, "op": op}
        if op == 5:
            out.append(a % 256)
        elif op == 23:
            if ip >= len(stdin_bytes):
                status = "EOF"
                log.append(rec)
                break
            a = stdin_bytes[ip]
            ip += 1
        elif op == 4:
            c = mem[d]
        elif op == 39:
            mem[d] = rot(mem[d])
            a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = crazy(a, mem[d])
            a = mem[d]
        elif op == 81:
            status = "HALTED"
            log.append(rec)
            break
        if 33 <= mem[c] <= 126:
            mem[c] = (enc or {33 + i: nc.XLAT2[i] for i in range(94)})[mem[c]]
        log.append(rec)
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    first_bad = next((r["step"] for r in log if r["byte"] not in PRINTABLE), None)
    return {"output": bytes(out), "steps": len(log), "status": status,
            "log": log, "first_unprintable_step": first_bad,
            "first_unprintable_pc": next(
                (r["pc"] for r in log if r["byte"] not in PRINTABLE), None),
            "first_unprintable_byte": next(
                (r["byte"] for r in log if r["byte"] not in PRINTABLE), None)}


def run_c(path: Path, stdin_bytes: bytes, timeout: int = 120) -> dict:
    p = subprocess.run([str(C_RUNNER), str(path), "200000"],
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    m = re.search(r"steps:\s*(\d+)\s*\|\s*status:\s*(\w+)",
                  p.stderr.decode("latin-1", "replace"))
    out = p.stdout
    return {"stdout_hex": out.hex(),
            "out_norm": out[:-1].hex() if out.endswith(b"\n") else out.hex(),
            "steps": int(m.group(1)) if m else None,
            "status": m.group(2) if m else None,
            "exit": p.returncode}


def main() -> int:
    results: dict = {}
    ok = True

    # ---------- 0. integridad ----------
    integrity = {}
    for name, data in B.build_all().items():
        path = PACK / (name + ".mb")
        if not path.exists():
            print(f"FALTA {name}.mb", file=sys.stderr)
            return 1
        raw = path.read_bytes()
        integrity[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "matches_build": raw == data,
            "length": len(raw),
            "printable": all(33 <= b <= 126 for b in raw),
            "no_whitespace": not any(chr(b).isspace() for b in raw),
        }
        ok = ok and integrity[name]["matches_build"] and integrity[name]["printable"]
    results["integrity"] = integrity
    print("[integrity] " + json.dumps(
        {k: {"ok": v["matches_build"] and v["printable"], "len": v["length"]}
         for k, v in integrity.items()}), flush=True)

    # ---------- 1. programas mínimos ----------
    minimal = {}
    for name in B.INSTANCES:
        data = B.build_all()[name]
        meta = B.meta_for(name)
        path = PACK / (name + ".mb")
        tr = trace(data, b"")
        tr_nc = trace(data, b"", engine="nc")
        orc = oc.oracle_run(str(path), 200000, "", stop_on_eof=True)
        c = run_c(path, b"")
        predicted = tr["first_unprintable_step"]
        expect_c = predicted if predicted is not None else tr["steps"]
        row = {
            "mode": meta["mode"],
            "pivot_value": meta["pivot_value"],
            "pivot_printable": meta["pivot_printable"],
            "opcode_at_pivot": meta["opcode_at_pivot"],
            "trace_steps": tr["steps"],
            "trace_status": tr["status"],
            "first_unprintable_step": predicted,
            "first_unprintable_pc": tr["first_unprintable_pc"],
            "predicted_c_steps": expect_c,
            "premise": ("guarda" if predicted is not None else "corre hasta END"),
            "c_steps": c["steps"],
            "c_status": c["status"],
            "c_out": c["out_norm"],
            "c_matches_prediction": c["steps"] == expect_c,
            "oracle_steps": orc["steps"],
            "oracle_status": orc["status"],
            "oracle_eq_trace": orc["steps"] == tr["steps"],
            "nc_eq_trace": tr_nc["steps"] == tr["steps"]
                            and tr_nc["output"] == tr["output"],
        }
        minimal[name] = row
        ok = ok and row["c_matches_prediction"] and row["oracle_eq_trace"] \
            and row["nc_eq_trace"]
        print("[minimal] %-20s pivote=%6d imprimible=%-5s pasos(traza)=%d "
              "primer_no_imprimible=%s C=%s pasos (predicho %s) coincide=%s" % (
                  name, row["pivot_value"], row["pivot_printable"],
                  row["trace_steps"], predicted, c["steps"], expect_c,
                  row["c_matches_prediction"]), flush=True)
    results["minimal_programs"] = minimal

    # ---------- 2. reproducción sobre epoch_resolver_word_v1 ----------
    replay = {}
    for name in ("resolver_word", "resolver_word_dynamic",
                 "mutant_mask_121", "mutant_wrong_payload"):
        path = RESOLVER / (name + ".mb")
        data = path.read_bytes()
        tr = trace(data, b"c")
        c = run_c(path, b"c")
        predicted = tr["first_unprintable_step"]
        expect_c = predicted if predicted is not None else tr["steps"]
        row = {
            "trace_steps": tr["steps"],
            "trace_status": tr["status"],
            "first_unprintable_step": predicted,
            "first_unprintable_pc": tr["first_unprintable_pc"],
            "first_unprintable_byte": tr["first_unprintable_byte"],
            "predicted_c_steps": expect_c,
            "c_steps": c["steps"],
            "c_status": c["status"],
            "c_out": c["out_norm"],
            "c_matches_prediction": c["steps"] == expect_c,
            "c_silent": c["out_norm"] == "",
        }
        replay[name] = row
        ok = ok and row["c_matches_prediction"]
        print("[replay]  %-22s primer_no_imprimible pc=%s byte=%s en paso %s | "
              "C para en %s (predicho %s) coincide=%s" % (
                  name, row["first_unprintable_pc"],
                  row["first_unprintable_byte"], predicted, c["steps"],
                  expect_c, row["c_matches_prediction"]), flush=True)
    results["resolver_replay"] = replay

    # ---------- 3. veredicto ----------
    guard_instances = ("guard_high", "guard_low")
    control_instances = ("control_seed_33", "control_seed_126")
    verdict = {
        "guards_halt_the_c_runner": all(minimal[n]["c_matches_prediction"]
                                        and minimal[n]["premise"] == "guarda"
                                        for n in guard_instances),
        "printable_controls_run_to_end": all(
            minimal[n]["c_matches_prediction"]
            and minimal[n]["premise"] == "corre hasta END"
            for n in control_instances),
        "resolver_divergence_explained": all(
            r["c_matches_prediction"] for r in replay.values()),
        "two_python_engines_agree": all(
            r["oracle_eq_trace"] and r["nc_eq_trace"] for r in minimal.values()),
    }
    results["verdict"] = verdict
    ok = ok and all(verdict.values())
    results["verdict_all_checks_pass"] = bool(ok)

    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf8")
    print("[verdict] " + json.dumps(verdict), flush=True)
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
