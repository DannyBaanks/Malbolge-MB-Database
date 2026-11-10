#!/usr/bin/env python3
"""probe.py — epoch_resolver_request_v1: el payload de 10 trits lo elige la petición.

Motores: trazador con las primitivas del oráculo del repo, trazador con las de
`native_classic` y el oráculo del repo.

Comprobaciones:
  0. integridad (reconstrucción, imprimibles, sin whitespace).
  1. lema exhaustivo: V = crazy(M, P) con P = 29524 + Σ_{trit=1} 3^p y
     M = 29524 + Σ_{trit≠0} 3^p vale para las 59049 palabras (0 discrepancias).
  2. resultado negativo del semigrupo: el mapa "trit -> dígito de control"
     (0,2,0)/(0,2,2) NO es alcanzable por composición de crazy (15 mapas), así
     que la petición lleva dígitos de control y no los 10 trits.
  3. por instancia: los 20 bytes de la petición se leen en orden, P y M quedan
     exactos, T queda con el payload EXACTO y el payload se ejecuta (OUT en
     pc = T con V % 256, END en T+1).
  4. triple motor en las cuatro instancias.
  5. control negativo: una petición alterada produce OTRO payload (el payload
     no está fijo en el programa).
  6. el runner C se detiene en la guarda de imprimibilidad, en el paso que el
     trazador predice (c_printable_guard_v1).
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
    writes: list[dict] = []
    log: list[dict] = []
    read_bytes: list[int] = []
    status = "MAX_STEPS"
    for step in range(1, max_steps + 1):
        cell = mem[c]
        op = (cell + c) % 94
        rec = {"step": step, "pc": c, "op": op, "byte": cell}
        if op == 5:
            out.append(a % 256)
            rec["emitted"] = a % 256
        elif op == 23:
            if ip >= len(stdin_bytes):
                status = "EOF"
                log.append(rec)
                break
            a = stdin_bytes[ip]
            read_bytes.append(a)
            ip += 1
            rec["read_byte"] = a
        elif op == 4:
            c = mem[d]
        elif op == 39:
            old = mem[d]
            mem[d] = rot(mem[d])
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "kind": "rot",
                           "step": step})
        elif op == 40:
            d = mem[d]
        elif op == 62:
            old = mem[d]
            mem[d] = crazy(a, mem[d])
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
    first_bad = next((r["step"] for r in log if r["byte"] not in PRINTABLE), None)
    return {"output": bytes(out), "steps": len(log), "status": status,
            "log": log, "writes": writes, "read_bytes": read_bytes,
            "first_unprintable_step": first_bad,
            "final": {"P": mem[B.P], "M": mem[B.M], "T": mem[B.T], "A": mem[B.A]}}


def written(tr: dict, addr: int, which: str = "new") -> object:
    """Valor de la celda `addr` segun su historial de escrituras.

    `P` se consume en el CRAZY final (queda con V), asi que el valor *construido*
    es el `old` de su ultima escritura.  `M` queda restaurado por el ROT final
    del marco, asi que su valor construido es el `new` de su ultima escritura
    (el ROT de restauracion).  `T` se cifra tras ejecutarse si su valor es
    imprimible, asi que el payload es el `new` de su ultima escritura.
    """
    ws = [w for w in tr["writes"] if w["addr"] == addr]
    if not ws:
        return None
    return ws[-1][which]


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


def lemma_decomposition() -> dict:
    """V = crazy(M, P) para las 59049 palabras."""
    bad = []
    for v in range(59049):
        p, m = B.expected_p(v), B.expected_m(v)
        if oc.crazy_op(m, p) != v:
            bad.append(v)
            if len(bad) > 8:
                break
    return {"words": 59049, "mismatches": len(bad), "examples": bad[:8]}


def lemma_semigroup() -> dict:
    """El semigrupo de composiciones de crazy sobre un trit: 15 mapas."""
    gens = [tuple(oc._CRAZY[b][a] for a in range(3)) for b in range(3)]
    ident = (0, 1, 2)
    seen = {ident: "id"}
    frontier = [ident]
    while frontier:
        nxt = []
        for f in frontier:
            for g in gens:
                h = tuple(f[g[x]] for x in range(3))
                if h not in seen:
                    seen[h] = True
                    nxt.append(h)
        frontier = nxt
    wanted = {"trit->ctrl de P (0,2,0)": (0, 2, 0),
              "trit->ctrl de M (0,2,2)": (0, 2, 2),
              "trit->ctrl (0,0,2)": (0, 0, 2)}
    return {"maps": len(seen),
            "reachable": {k: (v in seen) for k, v in wanted.items()},
            "all_maps": sorted(seen.keys())}


def main() -> int:
    results: dict = {}
    ok = True
    data = B.build()["data"]
    path = PACK / "resolver_request.mb"

    # ---------- 0. integridad ----------
    raw = path.read_bytes()
    integrity = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "matches_build": raw == data,
        "length": len(raw),
        "printable": all(33 <= b <= 126 for b in raw),
        "no_whitespace": not any(chr(b).isspace() for b in raw),
    }
    ok = ok and integrity["matches_build"] and integrity["printable"]
    results["integrity"] = integrity
    print("[integrity] " + json.dumps(integrity), flush=True)

    # ---------- 1. lema exhaustivo ----------
    lem = lemma_decomposition()
    results["lemma_decomposition"] = lem
    ok = ok and lem["mismatches"] == 0
    print("[lema] V = crazy(M,P) sobre %d palabras: %d discrepancias"
          % (lem["words"], lem["mismatches"]), flush=True)

    # ---------- 2. resultado negativo del semigrupo ----------
    sem = lemma_semigroup()
    results["lemma_semigroup"] = sem
    neg_ok = (not sem["reachable"]["trit->ctrl de P (0,2,0)"]
              and not sem["reachable"]["trit->ctrl de M (0,2,2)"]
              and sem["reachable"]["trit->ctrl (0,0,2)"])
    ok = ok and neg_ok
    print("[lema] semigrupo de crazy: %d mapas; el mapa trit->ctrl que haría "
          "falta NO es alcanzable (%s); el (0,0,2) sí lo es"
          % (sem["maps"], neg_ok), flush=True)

    # ---------- 3. instancias ----------
    instances = {}
    for name, v in B.PAYLOADS.items():
        req = B.request_for(v)
        tr = trace(data, req)
        tr_nc = trace(data, req, engine="nc")
        orc = oc.oracle_run(str(path), 200000, req.decode("latin-1"),
                            stop_on_eof=True)
        out_pcs = [r["pc"] for r in tr["log"] if r.get("op") == 5]
        c = run_c(path, req)
        pred = tr["first_unprintable_step"]
        # si no hay celda no imprimible, el C debe recorrer el programa entero;
        # si la hay, debe parar en ella (c_printable_guard_v1)
        expect_c_steps = pred if pred is not None else tr["steps"]
        p_built = written(tr, B.P, "old")     # P construido (antes del crazy final)
        m_built = written(tr, B.M, "new")     # M construido
        t_written = written(tr, B.T, "new")   # payload escrito en la época
        row = {
            "payload": v,
            "request_hex": req.hex(),
            "request_read_in_order": tr["read_bytes"] == list(req),
            "n_bytes_read": len(tr["read_bytes"]),
            "P_built": p_built, "P_expected": B.expected_p(v),
            "P_exact": p_built == B.expected_p(v),
            "M_built": m_built, "M_expected": B.expected_m(v),
            "M_exact": m_built == B.expected_m(v),
            "T_written": t_written, "T_exact": t_written == v,
            "T_final_mem": tr["final"]["T"],
            "T_encrypted_after_exec": (tr["final"]["T"] != v
                                       and 33 <= v <= 126),
            "out_pcs": out_pcs,
            "out_bytes": tr["output"].hex(),
            "expected_out": f"{v % 256:02x}",
            "emitted_at_epoch": out_pcs == [B.T],
            "status": tr["status"], "steps": tr["steps"],
            "oracle_out": orc["output"].encode("latin-1").hex(),
            "oracle_status": orc["status"],
            "trace_eq_oracle": (tr["output"].hex()
                                == orc["output"].encode("latin-1").hex()
                                and tr["steps"] == orc["steps"]),
            "nc_eq_oracle": (tr_nc["output"] == tr["output"]
                             and tr_nc["steps"] == tr["steps"]
                             and written(tr_nc, B.T, "new") == v),
            "c_steps": c["steps"], "c_out": c["out_norm"],
            "c_predicted_guard_step": pred,
            "c_expected_steps": expect_c_steps,
            "c_matches_prediction": c["steps"] == expect_c_steps,
            "c_out_eq_oracle": c["out_norm"] == orc["output"].encode("latin-1").hex(),
        }
        instances[name] = row
        ok = ok and all([row["request_read_in_order"], row["P_exact"],
                         row["M_exact"], row["T_exact"], row["emitted_at_epoch"],
                         row["out_bytes"] == row["expected_out"],
                         row["status"] == "HALTED", row["trace_eq_oracle"],
                         row["nc_eq_oracle"], row["c_matches_prediction"]])
        # el C sólo puede coincidir con el oráculo si no choca con la guarda
        ok = ok and (row["c_out_eq_oracle"] if pred is None else not row["c_out_eq_oracle"])
        print("[instancia] %-16s leidos=%d P=%s(%s) M=%s(%s) T=%s(%s) "
              "OUT=%s esperado=%s en pc=%s pasos=%d C=%s(C esperado %s) "
              "guarda=%s" % (
                  name, row["n_bytes_read"], row["P_built"], row["P_exact"],
                  row["M_built"], row["M_exact"], row["T_written"], row["T_exact"],
                  row["out_bytes"], row["expected_out"], row["out_pcs"],
                  row["steps"], row["c_steps"], row["c_expected_steps"], pred),
              flush=True)
    results["instances"] = instances

    # ---------- 4. control negativo: petición alterada ----------
    base_v = 29797
    base_req = bytearray(B.request_for(base_v))
    base_req[0] = 2 - base_req[0]          # invierte el dígito de control 0
    tr = trace(data, bytes(base_req))
    ctrl = {
        "base_payload": base_v,
        "mutated_request_hex": bytes(base_req).hex(),
        "T_written": written(tr, B.T, "new"),
        "payload_changed": written(tr, B.T, "new") != base_v,
        "out_bytes": tr["output"].hex(),
        "status": tr["status"],
        "steps": tr["steps"],
    }
    results["control_mutated_request"] = ctrl
    ok = ok and ctrl["payload_changed"]
    print("[control] petición alterada (byte 0 invertido): T=%s (payload "
          "cambiado=%s) OUT=%s estado=%s" % (
              ctrl["T_written"], ctrl["payload_changed"], ctrl["out_bytes"],
              ctrl["status"]), flush=True)

    # ---------- 5. los cuatro payloads son distintos ----------
    distinct = len({i["T_written"] for i in instances.values()}) == len(instances)
    outs = {i["out_bytes"] for i in instances.values()}
    results["distinct_payloads"] = {"distinct_T": distinct,
                                    "distinct_out": len(outs) == len(instances)}
    ok = ok and distinct and len(outs) == len(instances)
    print("[control] payloads distintos: T=%s OUT=%s" % (distinct, len(outs)),
          flush=True)

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
