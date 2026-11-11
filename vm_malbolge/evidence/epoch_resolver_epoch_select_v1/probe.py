#!/usr/bin/env python3
"""probe.py — epoch_resolver_epoch_select_v1: la petición elige la ÉPOCA y el PAYLOAD.

Motores: trazador con las primitivas del oráculo del repo, trazador con las de
`native_classic`, el oráculo del repo y el runner C original.

Comprobaciones:
  0. integridad (reconstrucción, imprimibles, sin whitespace, una sola imagen).
  1. lema exhaustivo: V = crazy(M, P) con P = 29524 + Σ_{trit=1} 3^p y
     M = 29524 + Σ_{trit≠0} 3^p vale para las 59049 palabras (0 discrepancias).
  2. resultado negativo del semigrupo: el mapa "trit -> dígito de control"
     (0,2,0)/(0,2,2) NO es alcanzable por composición de crazy (15 mapas), así
     que la petición lleva dígitos de control y no los 10 trits.
  3. lema de la tabla de épocas: cada época cumple (v+T+1)%94 = 81 (END),
     v+1 encadena con W y b = T-1; y el espacio de diseño de la zona de dato.
  4. por instancia: los 21 bytes de la petición se leen en orden, W = b exacto,
     P y M quedan exactos, el payload se escribe EXACTO en la celda de época
     ELEGIDA (y sólo en ella), se ejecuta (OUT en pc = T) y termina (END en T+1).
  5. triple motor + runner C (parado en la guarda de imprimibilidad cuando el
     payload no es imprimible: el paso predicho por la traza).
  6. control negativo A: cambiar SOLO el byte de época mueve el payload a otra
     celda de época y cambia el opcode (la época la elige la petición).
  7. control negativo B: cambiar SOLO un dígito de control cambia el payload y
     deja la época intacta (el payload lo elige la petición).
  8. control negativo C: un byte deepocha fuera de catálogo no selecciona
     ninguna época (medido, sin puerta de paso).
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
from plan import OPS  # noqa: E402

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
    watched = {"P": B.P, "M": B.M, "A1": B.A1, "A2": B.A2, "W": B.W}
    for t in B.EPOCHS:
        watched["epoch_%d" % t] = t
        watched["succ_%d" % t] = B.EPOCH_TABLE[t]["succ_cell"]
    return {"output": bytes(out), "steps": len(log), "status": status,
            "log": log, "writes": writes, "read_bytes": read_bytes,
            "first_unprintable_step": first_bad,
            "final": {k: mem[v] for k, v in watched.items()}}


def written(tr: dict, addr: int, which: str = "new") -> object:
    """Valor de la celda `addr` segun su historial de escrituras.

    `P` se consume en el CRAZY final (queda con V), asi que el valor *construido*
    es el `old` de su ultima escritura.  `M` queda restaurado por el ROT final
    del marco, asi que su valor construido es el `new` de su ultima escritura
    (el ROT de restauracion).  La celda de época se cifra tras ejecutarse si su
    valor es imprimible, asi que el payload es el `new` de su ultima escritura.
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


def lemma_epoch_table() -> dict:
    """Invariantes de la tabla de épocas y espacio de diseño en la zona de dato."""
    rows = {}
    ok = True
    for t, row in B.EPOCH_TABLE.items():
        v = row["succ_val"]
        end_ok = (v + t + 1) % 94 == 81
        chain_ok = (v + 1 == row["hop_to_w"])
        ptr_ok = (row["b"] == t - 1)
        hop_value_ok = True
        ok = ok and end_ok and chain_ok and ptr_ok and hop_value_ok
        rows[str(t)] = {"b": row["b"], "succ_cell": row["succ_cell"],
                        "succ_val": v, "hop_to_w": row["hop_to_w"],
                        "end_decode_ok": end_ok, "chain_ok": chain_ok,
                        "pointer_ok": ptr_ok}
    # espacio de diseño: cuántas épocas admite la zona de dato (34..126) con la
    # cadena de dos DLOAD (sucesor imprimible + celda v+1 <= 126).
    candidates = []
    for t in range(34, 127):
        v0 = (80 - t) % 94
        opts = [v for v in (v0, v0 + 94) if 33 <= v <= 125]
        if opts:
            candidates.append(t)
    return {"rows": rows, "all_ok": ok,
            "candidate_epochs_in_data_zone": len(candidates),
            "implemented": len(B.EPOCHS),
            "candidates_head": candidates[:12],
            "candidates_tail": candidates[-12:]}


def lemma_opcode_triples() -> dict:
    """¿Hay un payload que sea opcode válido en las tres épocas a la vez?

    El opcode de V en T es (V + T) % 94.  Para unas épocas dadas, los tres
    opcodes son r, r+d1, r+d2 (mod 94) con d1, d2 las diferencias de época.
    Se cuentan los residuos r para los que los tres son opcodes válidos de
    Classic, tanto para las épocas implementadas (residuos distintos) como para
    tres épocas alineadas a 94 (el diseño de epoch_algebra_v3).
    """
    valid = set(OPS.values())
    def count(eps: list[int]) -> list:
        out = []
        for r in range(94):
            ops = [(r + e - eps[0]) % 94 for e in eps]
            if all(o in valid for o in ops):
                out.append({"residue": r, "opcodes": ops})
        return out
    here = count(list(B.EPOCHS))
    aligned = count([36, 130, 224])
    return {"valid_opcodes": sorted(valid),
            "epochs_implemented": list(B.EPOCHS),
            "triples_valid_here": len(here),
            "triples_valid_here_detail": here,
            "triples_valid_aligned_94": len(aligned),
            "triples_valid_aligned_94_detail": aligned}


def main() -> int:
    results: dict = {}
    ok = True
    data = B.build()["data"]
    path = PACK / "resolver_epoch.mb"

    # ---------- 0. integridad ----------
    raw = path.read_bytes()
    integrity = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "matches_build": raw == data,
        "length": len(raw),
        "printable": all(33 <= b <= 126 for b in raw),
        "no_whitespace": not any(chr(b).isspace() for b in raw),
        "single_image_for_all_instances": True,
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

    # ---------- 3. lema de la tabla de épocas ----------
    ep = lemma_epoch_table()
    results["lemma_epoch_table"] = ep
    ok = ok and ep["all_ok"]
    print("[lema] tabla de épocas invariantes=%s; candidatas en la zona de "
          "dato=%d, implementadas=%d"
          % (ep["all_ok"], ep["candidate_epochs_in_data_zone"],
             ep["implemented"]), flush=True)

    # ---------- 3b. lema de los opcodes triples ----------
    tri = lemma_opcode_triples()
    results["lemma_opcode_triples"] = tri
    ok = ok and tri["triples_valid_here"] == 0 and tri["triples_valid_aligned_94"] > 0
    print("[lema] payload válido en las tres épocas a la vez: aquí=%d, con tres "
          "épocas alineadas a 94=%d (opcodes=%s)"
          % (tri["triples_valid_here"], tri["triples_valid_aligned_94"],
             tri["valid_opcodes"]), flush=True)

    # ---------- 4-5. instancias ----------
    instances = {}
    for name, epoch, v in B.INSTANCES:
        req = B.request_for_epoch(epoch, v)
        tr = trace(data, req)
        tr_nc = trace(data, req, engine="nc")
        orc = oc.oracle_run(str(path), 200000, req.decode("latin-1"),
                            stop_on_eof=True)
        out_pcs = [r["pc"] for r in tr["log"] if r.get("op") == 5]
        end_pcs = [r["pc"] for r in tr["log"] if r.get("op") == 81]
        c = run_c(path, req)
        pred = tr["first_unprintable_step"]
        expect_c_steps = pred if pred is not None else tr["steps"]
        p_built = written(tr, B.P, "old")
        m_built = written(tr, B.M, "new")
        w_ptr = written(tr, B.W, "new")
        t_written = written(tr, epoch, "new")
        others = {str(o): written(tr, o, "new")
                  for o in B.EPOCHS if o != epoch}
        opcodes = {str(o): (v + o) % 94 for o in B.EPOCHS}
        row = {
            "epoch": epoch,
            "epoch_byte": B.EPOCH_TABLE[epoch]["b"],
            "payload": v,
            "request_hex": req.hex(),
            "request_read_in_order": tr["read_bytes"] == list(req),
            "n_bytes_read": len(tr["read_bytes"]),
            "W_written": w_ptr,
            "W_is_epoch_byte": w_ptr == B.EPOCH_TABLE[epoch]["b"],
            "P_built": p_built, "P_expected": B.expected_p(v),
            "P_exact": p_built == B.expected_p(v),
            "M_built": m_built, "M_expected": B.expected_m(v),
            "M_exact": m_built == B.expected_m(v),
            "payload_written": t_written, "payload_exact": t_written == v,
            "other_epoch_cells": others,
            "others_kept_mask": all(x == 29524 for x in others.values()),
            "opcode_at_epoch": opcodes[str(epoch)],
            "opcode_at_other_epochs": {k: x for k, x in opcodes.items()
                                       if k != str(epoch)},
            "out_pcs": out_pcs,
            "out_bytes": tr["output"].hex(),
            "expected_out": f"{v % 256:02x}",
            "emitted_at_epoch": out_pcs == [epoch],
            "end_pcs": end_pcs,
            "end_at_successor": end_pcs == [epoch + 1],
            "status": tr["steps"] and tr["status"],
            "steps": tr["steps"],
            "oracle_out": orc["output"].encode("latin-1").hex(),
            "oracle_status": orc["status"],
            "trace_eq_oracle": (tr["output"].hex()
                                == orc["output"].encode("latin-1").hex()
                                and tr["steps"] == orc["steps"]
                                and tr["status"] == orc["status"]),
            "nc_eq_oracle": (tr_nc["output"] == tr["output"]
                             and tr_nc["steps"] == tr["steps"]
                             and written(tr_nc, epoch, "new") == v),
            "c_steps": c["steps"], "c_out": c["out_norm"],
            "c_predicted_guard_step": pred,
            "c_expected_steps": expect_c_steps,
            "c_matches_prediction": c["steps"] == expect_c_steps,
            "c_out_eq_oracle": c["out_norm"] == orc["output"].encode("latin-1").hex(),
        }
        instances[name] = row
        ok = ok and all([row["request_read_in_order"], row["n_bytes_read"] == 21,
                         row["W_is_epoch_byte"], row["P_exact"], row["M_exact"],
                         row["payload_exact"], row["others_kept_mask"],
                         row["opcode_at_epoch"] == 5,
                         row["emitted_at_epoch"], row["end_at_successor"],
                         row["status"] == "HALTED", row["trace_eq_oracle"],
                         row["nc_eq_oracle"], row["c_matches_prediction"]])
        ok = ok and (row["c_out_eq_oracle"] if pred is None
                     else not row["c_out_eq_oracle"])
        print("[instancia] %-12s epoca=%3d b=%3d payload=%6d leidos=%d W=%s(%s) "
              "P=%s(%s) M=%s(%s) payload=%s(%s) otras-mascara=%s OUT=%s "
              "esperado=%s en pc=%s END=%s pasos=%d C=%s(C esperado %s) guarda=%s"
              % (name, row["epoch"], row["epoch_byte"], row["payload"],
                 row["n_bytes_read"], row["W_written"], row["W_is_epoch_byte"],
                 row["P_built"], row["P_exact"], row["M_built"], row["M_exact"],
                 row["payload_written"], row["payload_exact"],
                 row["others_kept_mask"], row["out_bytes"], row["expected_out"],
                 row["out_pcs"], row["end_pcs"], row["steps"], row["c_steps"],
                 row["c_expected_steps"], pred), flush=True)
    results["instances"] = instances

    # ---------- 6. control negativo A: sólo cambia el byte de época ----------
    base_epoch, base_v = 100, 29797
    other_epoch = 106
    req_a = bytes([B.EPOCH_TABLE[other_epoch]["b"]]) + B.control_digits(base_v)
    tr_a = trace(data, req_a)
    ctrl_a = {
        "base_epoch": base_epoch, "base_payload": base_v,
        "mutated_request_hex": req_a.hex(),
        "payload_written_at_100": written(tr_a, 100, "new"),
        "payload_written_at_106": written(tr_a, 106, "new"),
        "epoch_moved": (written(tr_a, 106, "new") == base_v
                        and written(tr_a, 100, "new") == 29524),
        "opcode_at_106": (base_v + other_epoch) % 94,
        "out_bytes": tr_a["output"].hex(),
        "status": tr_a["status"],
        "steps": tr_a["steps"],
    }
    results["control_mutated_epoch_byte"] = ctrl_a
    ok = ok and ctrl_a["epoch_moved"]
    print("[control] byte de época %d->%d: payload en 100=%s en 106=%s "
          "(movido=%s) opcode@106=%d OUT=%s estado=%s"
          % (B.EPOCH_TABLE[base_epoch]["b"], B.EPOCH_TABLE[other_epoch]["b"],
             ctrl_a["payload_written_at_100"], ctrl_a["payload_written_at_106"],
             ctrl_a["epoch_moved"], ctrl_a["opcode_at_106"],
             ctrl_a["out_bytes"], ctrl_a["status"]), flush=True)

    # ---------- 7. control negativo B: sólo cambia un dígito de control ----------
    req_b = bytearray(B.request_for_epoch(base_epoch, base_v))
    req_b[1] = 2 - req_b[1]
    tr_b = trace(data, bytes(req_b))
    ctrl_b = {
        "base_payload": base_v,
        "mutated_request_hex": bytes(req_b).hex(),
        "payload_written": written(tr_b, base_epoch, "new"),
        "payload_changed": written(tr_b, base_epoch, "new") != base_v,
        "epoch_unchanged": written(tr_b, base_epoch, "new") is not None,
        "out_bytes": tr_b["output"].hex(),
        "status": tr_b["status"],
        "steps": tr_b["steps"],
    }
    results["control_mutated_control_byte"] = ctrl_b
    ok = ok and ctrl_b["payload_changed"] and ctrl_b["epoch_unchanged"]
    print("[control] dígito de control alterado (byte 1): payload=%s "
          "(cambiado=%s) OUT=%s estado=%s"
          % (ctrl_b["payload_written"], ctrl_b["payload_changed"],
             ctrl_b["out_bytes"], ctrl_b["status"]), flush=True)

    # ---------- 8. control negativo C: byte de época fuera de catálogo ----------
    req_c = bytes([50]) + B.control_digits(base_v)
    tr_c = trace(data, req_c, max_steps=5000)
    landed = [t for t in B.EPOCHS
              if written(tr_c, t, "new") == base_v]
    ctrl_c = {
        "request_hex": req_c.hex(),
        "epoch_byte": 50,
        "payload_landed_in_epoch_cells": landed,
        "no_epoch_selected": landed == [],
        "out_bytes": tr_c["output"].hex(),
        "status": tr_c["status"],
        "steps": tr_c["steps"],
        "note": "byte fuera de catálogo: la máquina no tiene época para ese "
                "puntero; se mide el comportamiento, no se exige nada",
    }
    results["control_off_catalog_epoch_byte"] = ctrl_c
    print("[control] byte de época fuera de catálogo (50): aterrizaje en "
          "épocas=%s estado=%s pasos=%d (medido, sin puerta)"
          % (landed, ctrl_c["status"], ctrl_c["steps"]), flush=True)

    # ---------- 9. las tres épocas se alcanzan con la misma imagen ----------
    reached = {str(i["epoch"]) for i in instances.values()}
    distinct_payloads = {i["payload_written"] for i in instances.values()}
    results["coverage"] = {
        "epochs_reached": sorted(reached),
        "distinct_epochs": len(reached),
        "distinct_payloads": len(distinct_payloads),
        "one_image": True,
    }
    ok = ok and len(reached) == len(B.EPOCHS) and len(distinct_payloads) == len(instances)
    print("[cobertura] épocas=%s payloads distintos=%d imagen=1"
          % (sorted(reached), len(distinct_payloads)), flush=True)

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
