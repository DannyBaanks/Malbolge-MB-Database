#!/usr/bin/env python3
"""tr_mutants.py — controles contra falsos positivos (6 mutantes deliberados).

Cada mutante es una forma concreta de "cono más fácil" que el sistema debe
RECHAZAR o detectar por divergencia.  Donde se puede, la refutación se hace
contra un motor independiente (runner C original), no contra el propio solver.

  M1  tabla crz con una entrada alterada          -> diferencial nativo
  M2  rotación en dirección equivocada            -> diferencial nativo
  M3  conversión ternaria con el error de 35      -> autocontrol de round-trip
  M4  59048 precargado clandestinamente           -> cadena de procedencia
  M5  decodificador de opcodes ciego a posición   -> traza del resolvedor v3
  M6  verificador que sólo mira la escritura      -> mutantes del pack v3

M1 y M2 usan un programa nativo mínimo (mismo patio de células que el pack v3):
    pc0 IN (a = byte de stdin), pc1 DLOAD (d -> destino), pc2 CRAZY|ROT,
    pc3 OUT, pc4 END;  celda 40 = 33 (dato imprimible).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

from tr_spec import MEM, NTRITS, CRZ_C, crz, from_trits, spec_crazy, spec_rot, ternary  # noqa: E402

C_RUNNER = ROOT / "runners/malbolge-original/malbolge"
V3 = PACK.parent / "epoch_algebra_v3"
OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40,
       "CRAZY": 62, "NOP": 68, "END": 81}


def enc(addr: int, op: int) -> int:
    return 33 + ((op - 33 - addr) % 94)


# ---------- mutantes de operación ----------

def crz_mutant_1(a: int, d: int) -> int:
    """M1: crz[4] (a=1, d=1) cambiado de 0 a 1."""
    table = list(CRZ_C)
    table[4] = 1
    res = 0
    p = 1
    for _ in range(NTRITS):
        res += table[a % 3 + 3 * (d % 3)] * p
        a //= 3
        d //= 3
        p *= 3
    return res


def spec_rot_left(d: int) -> int:
    """M2: rotación hacia el otro lado."""
    return (d % (3 ** (NTRITS - 1))) * 3 + d // (3 ** (NTRITS - 1))


# ---------- programa nativo mínimo ----------

def build_native(kind: str) -> tuple[bytes, dict]:
    cells = {}
    cells[0] = enc(0, OPS["IN"])
    cells[1] = enc(1, OPS["DLOAD"])          # valor 39 -> d = 40
    assert cells[1] == 39, cells[1]
    cells[2] = enc(2, OPS[kind])             # CRAZY o ROT sobre mem[40]
    cells[3] = enc(3, OPS["OUT"])
    cells[4] = enc(4, OPS["END"])
    for a in range(5, 40):
        cells[a] = enc(a, OPS["NOP"])
    cells[40] = 33                            # dato imprimible
    last = max(cells)
    data = bytes(cells.get(a, enc(a, OPS["NOP"])) for a in range(last + 1))
    return data, {"kind": kind, "length": len(data), "cell40": 33}


def run_c(path: Path, stdin_bytes: bytes, timeout: int = 120):
    p = subprocess.run([str(C_RUNNER), str(path), "2000000"],
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    return p.stdout.hex(), p.returncode


# ---------- trazador con decodificador configurable (M5) ----------

def trace_with_decoder(source: bytes, stdin_bytes: bytes, blind: bool,
                       max_steps: int = 200000) -> dict:
    text = source.decode("latin-1")
    mem = oc.load_memory(text)
    a = c = d = 0
    ip = 0
    out: list[int] = []
    for _ in range(max_steps):
        cell = mem[c]
        op = (cell % 94) if blind else (cell + c) % 94
        if op == 4:
            c = mem[d]
        elif op == 5:
            out.append(a % 256)
        elif op == 23:
            if ip >= len(stdin_bytes):
                return {"output": bytes(out), "status": "EOF"}
            a = stdin_bytes[ip]
            ip += 1
        elif op == 39:
            mem[d] = (mem[d] // 3) + (mem[d] % 3) * (3 ** 9)
            a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = oc.crazy_op(a, mem[d])
            a = mem[d]
        elif op == 81:
            return {"output": bytes(out), "status": "HALTED"}
        if 33 <= mem[c] <= 126:
            mem[c] = oc._ENC[mem[c]]
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {"output": bytes(out), "status": "MAX_STEPS"}


# ---------- trazador genérico con registro de escrituras (M6) ----------

def trace_writes(source: bytes, stdin_bytes: bytes, max_steps: int = 200000):
    text = source.decode("latin-1")
    mem = oc.load_memory(text)
    a = c = d = 0
    ip = 0
    out: list[int] = []
    writes = []
    out_pcs = []
    for _ in range(max_steps):
        cell = mem[c]
        op = (cell + c) % 94
        if op == 5:
            out.append(a % 256)
            out_pcs.append(c)
        elif op == 23:
            if ip >= len(stdin_bytes):
                break
            a = stdin_bytes[ip]
            ip += 1
        elif op == 4:
            c = mem[d]
        elif op == 39:
            old = mem[d]
            mem[d] = (old // 3) + (old % 3) * (3 ** 9)
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "kind": "rot"})
        elif op == 40:
            d = mem[d]
        elif op == 62:
            old = mem[d]
            mem[d] = oc.crazy_op(a, old)
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "kind": "crazy"})
        elif op == 81:
            break
        if 33 <= mem[c] <= 126:
            mem[c] = oc._ENC[mem[c]]
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {"output": bytes(out), "writes": writes, "out_pcs": out_pcs}


def main() -> dict:
    res: dict = {"mutants": {}}
    ok = True

    # ================= M1: tabla crz alterada =================
    data, meta = build_native("CRAZY")
    p = PACK / "mutant_m1_crazy33.mb"
    p.write_bytes(data)
    true_pred = oc.crazy_op(33, 33) % 256
    mut_pred = crz_mutant_1(33, 33) % 256
    orc = oc.oracle_run(str(p), 2000000, "!", stop_on_eof=True)
    cout, crc = run_c(p, b"!")
    c_norm = cout[:-2] if cout.endswith("0a") else cout
    row = {"program_meta": meta, "true_prediction": true_pred,
           "mutant_prediction": mut_pred, "oracle_out": orc["output"].encode("latin-1").hex(),
           "c_out": cout, "c_out_norm": c_norm, "c_exit": crc,
           "native_agrees_with_true": c_norm == f"{true_pred:02x}",
           "native_agrees_with_mutant": c_norm == f"{mut_pred:02x}",
           "mutant_refuted": c_norm == f"{true_pred:02x}" and true_pred != mut_pred}
    res["mutants"]["M1_crz_table_altered"] = row
    ok = ok and row["mutant_refuted"]
    print("[M1] pred verdadera=%d mutante=%d | oráculo=%s C=%s -> mutante refutado=%s"
          % (true_pred, mut_pred, row["oracle_out"], cout, row["mutant_refuted"]))

    # ================= M2: rotación en dirección equivocada =================
    data, meta = build_native("ROT")
    p = PACK / "mutant_m2_rot33.mb"
    p.write_bytes(data)
    true_pred = spec_rot(33) % 256
    mut_pred = spec_rot_left(33) % 256
    orc = oc.oracle_run(str(p), 2000000, "!", stop_on_eof=True)
    cout, crc = run_c(p, b"!")
    c_norm = cout[:-2] if cout.endswith("0a") else cout
    # además: rot^10 sigue siendo la identidad en el mutante (por eso no se
    # detecta por ciclo), pero recoloca los trits al otro lado
    l33 = spec_rot_left(33)
    r33 = spec_rot(33)
    row = {"program_meta": meta, "true_prediction": true_pred,
           "mutant_prediction": mut_pred,
           "oracle_out": orc["output"].encode("latin-1").hex(),
           "c_out": cout, "c_out_norm": c_norm, "c_exit": crc,
           "native_agrees_with_true": c_norm == f"{true_pred:02x}",
           "native_agrees_with_mutant": c_norm == f"{mut_pred:02x}",
           "mutant_order10_still_identity": all(
               (lambda w: [ (w := (w % (3**9))*3 + w//(3**9)) for _ in range(10) ] and w == v)(v)
               for v in (0, 33, 54, 242)),
           "mutant_moves_2_other_way": r33 != l33 and
                                      from_trits(ternary(r33)) == r33 and
                                      ternary(l33) != ternary(r33),
           "mutant_refuted": c_norm == f"{true_pred:02x}" and true_pred != mut_pred}
    res["mutants"]["M2_rot_wrong_direction"] = row
    ok = ok and row["mutant_refuted"]
    print("[M2] verdadera=%d mutante=%d | C=%s -> refutado=%s (orden 10 del mutante=%s)"
          % (true_pred, mut_pred, cout, row["mutant_refuted"],
             row["mutant_order10_still_identity"]))

    # ================= M3: error de conversión ternaria en 35 =================
    t = ternary(35)
    mutant_digits = "".join(str(x) for x in reversed(t))
    mutant_value = from_trits([2, 1, 0, 1] + [0] * 6)   # 35 mal leído: pos1 = 2 -> 1
    row = {"true_trits": t, "true_digits": mutant_digits,
           "round_trip_ok": from_trits(t) == 35,
           "mutant_digits": "1012", "mutant_value": mutant_value,
           "mutant_value_differs": mutant_value != 35,
           "detected": from_trits(t) == 35 and mutant_value != 35}
    res["mutants"]["M3_ternary_35_error"] = row
    ok = ok and row["detected"]
    print("[M3] 35 = %s_3 (trits %s); lectura errónea 1012_3 = %d -> detectado=%s"
          % (mutant_digits, t, mutant_value, row["detected"]))

    # ================= M4: 59048 precargado clandestinamente =================
    from tr_solver import Witness, OP_CRAZY, OP_IMG, OP_IN, OP_ROT
    legit = Witness()
    a = legit.img(54)
    b = legit.img(54)
    c = legit.crazy(a, b)
    cheats = Witness()
    x = cheats._add(59048, {"op": "PRELOAD", "value": 59048})   # constante ilegal
    row = {"legit_steps": len(legit.ops), "legit_value": legit.cells[c],
           "legit_provenance_ok": legit.provenance_ok(),
           "cheat_steps": len(cheats.ops), "cheat_value": cheats.cells[x],
           "cheat_provenance_ok": cheats.provenance_ok(),
           "detected": legit.provenance_ok() and not cheats.provenance_ok()
                      and legit.replay_independent() == 29524}
    res["mutants"]["M4_clandestine_preload"] = row
    ok = ok and row["detected"]
    print("[M4] testigo legítimo (procedencia ok=%s, %d pasos) vs precargado "
          "(procedencia ok=%s, %d pasos) -> detectado=%s"
          % (row["legit_provenance_ok"], row["legit_steps"],
             row["cheat_provenance_ok"], row["cheat_steps"], row["detected"]))

    # ================= M5: decodificador ciego a la posición =================
    v3_resolver = (V3 / "resolver.mb").read_bytes()
    # petición: byte 35 (época 36) + payload 63
    ref = oc.oracle_run(str(V3 / "resolver.mb"), 2000000, chr(35) + chr(63),
                        stop_on_eof=True)
    blind = trace_with_decoder(v3_resolver, bytes([35, 63]), blind=True)
    good = trace_with_decoder(v3_resolver, bytes([35, 63]), blind=False)
    blind_match = blind["output"].hex() == ref["output"].encode("latin-1").hex()
    true_match = good["output"].hex() == ref["output"].encode("latin-1").hex()
    row = {"program": "epoch_algebra_v3/resolver.mb",
           "stdin": [35, 63],
           "oracle_out": ref["output"].encode("latin-1").hex(),
           "decoder_true_trace": good["output"].hex(),
           "decoder_blind_trace": blind["output"].hex(),
           "blind_matches_oracle": blind_match,
           "true_matches_oracle": true_match,
           "detected": (not blind_match) and true_match}
    res["mutants"]["M5_position_blind_decoder"] = row
    ok = ok and row["detected"]
    print("[M5] oráculo=%s decodificador correcto=%s decodificador ciego=%s -> detectado=%s"
          % (row["oracle_out"], row["decoder_true_trace"],
             row["decoder_blind_trace"], row["detected"]))

    # ================= M6: verificador que sólo mira la escritura =================
    rows = []
    epochs_by_instance = {
        "resolver": [36, 130, 224],
        "mutant_residue": [36, 130, 223],
        "mutant_journal": [36, 130, 224],
        "mutant_pointer": [36, 130, 224],
        "mutant_mask": [36, 130, 224],
        "mutant_target": [36, 130, 224],
    }
    for name, eps in epochs_by_instance.items():
        src = (V3 / (name + ".mb")).read_bytes()
        for ep in eps:
            req = ep - 1          # la petición selecciona T = b + 1
            tr = trace_writes(src, bytes([req, 63]))
            ep_writes = [w for w in tr["writes"] if w["addr"] == ep]
            write_exact = (len(ep_writes) == 1
                           and ep_writes[0]["new"] == 63
                           and ep_writes[0]["old"] == 121)
            out_at_epoch = tr["out_pcs"] == [ep]
            rows.append({"instance": name, "epoch": ep,
                         "write_exact": write_exact,
                         "out_at_epoch": out_at_epoch,
                         "write_only_verdict": write_exact,
                         "full_verdict": write_exact and out_at_epoch})
    # el mutante de residuo debe pasar el verificador débil y fallar el completo
    mres = [r for r in rows if r["instance"] == "mutant_residue" and r["epoch"] == 223][0]
    detected = mres["write_only_verdict"] and not mres["full_verdict"]
    res["mutants"]["M6_write_only_verifier"] = {
        "rows": rows,
        "false_positive_case": mres,
        "detected": detected}
    ok = ok and detected
    print("[M6] mutant_residue @223: escritura exacta=%s OUT en época=%s "
          "-> verificador débil acepta=%s completo rechaza=%s (detectado=%s)"
          % (mres["write_exact"], mres["out_at_epoch"],
             mres["write_only_verdict"], not mres["full_verdict"], detected))

    res["verdict"] = bool(ok)
    return res


if __name__ == "__main__":
    r = main()
    print("[mutants] ok =", r["verdict"])
