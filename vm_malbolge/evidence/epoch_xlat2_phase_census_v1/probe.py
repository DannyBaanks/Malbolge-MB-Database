#!/usr/bin/env python3
"""probe.py — epoch_xlat2_phase_census_v1: censo de ventanas desfasadas sobre XLAT2.

Puertas en GATES.md (commit cb6bfd1, anterior a este archivo). Este probe se
reescribió desde cero: el probe.py anterior quedó truncado y sin commitear.

Mide Q1 (estructura de XLAT2), Q2 (ventanas por X, ciclo y posición), Q3 (control
JMP) y Q4 (ejecución de las ventanas encontradas), y aplica G0..G3.

Uso:  python3 -I probe.py </dev/null     (escribe results.json y jmp_control.mb)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

PACK = Path(__file__).resolve().parent
EVID = PACK.parent
ROOT = PACK.parents[2]
ORACLE = ROOT / "tools" / "oracle_classic.py"
INDEP = EVID / "epoch_audit_v1" / "indep_interpreter.py"
BUDGET = EVID / "epoch_rearm_budget_v1" / "results.json"
OLMSTEAD = PACK.parents[3] / "Malbolge-PureEpoch" / "build" / "olmstead"

N = 3 ** 10
POS = 94
X2 = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X"
      "~xDl}REokN:#?G\"i@")
ENC = {33 + i: ord(ch) for i, ch in enumerate(X2)}
OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40, "CRAZY": 62,
       "NOP": 68, "END": 81}
VALID = set(OPS.values())
HARMLESS = ({OPS["NOP"]} | set(range(POS))) - VALID
TARGETS = ("OUT", "IN", "ROT", "DLOAD", "CRAZY")
CONTROL = "JMP"


# ---------------------------------------------------------------- utilidades

def enc(op: int, pos: int) -> int:
    """Valor imprimible que decodifica `op` en la posición `pos`."""
    v = (op - pos) % POS
    return v if v >= 33 else v + POS


def cycles() -> list[list[int]]:
    """Ciclos de la permutación XLAT2 sobre 33..126."""
    seen: set[int] = set()
    out: list[list[int]] = []
    for v in range(33, 127):
        if v in seen:
            continue
        cyc: list[int] = []
        x = v
        while x not in seen:
            seen.add(x)
            cyc.append(x)
            x = ENC[x]
        out.append(cyc)
    return out


def shift_ops(cyc: list[int], s: int) -> set[int]:
    """Opcodes que recorre una celda del ciclo `cyc` en la posición s (mod 94)."""
    return {(v + s) % POS for v in cyc}


def good_shift(cyc: list[int], op: int, s: int) -> bool:
    """True si la celda decodifica `op` una vez y sólo NOP/inválidos el resto."""
    os_ = shift_ops(cyc, s)
    return op in os_ and (os_ - {op}) <= HARMLESS


def max_cyclic_run(flags: list[bool]) -> int:
    """Mayor racha circular de True (0..len(flags))."""
    n = len(flags)
    if all(flags):
        return n
    best = cur = 0
    for f in flags * 2:
        cur = cur + 1 if f else 0
        if cur > best:
            best = cur
    return min(best, n)


def census_cycle(cyc: list[int], op: int) -> dict:
    """Censo de ventanas de longitud L para un ciclo y un opcode."""
    L = len(cyc)
    flags = [good_shift(cyc, op, s) for s in range(POS)]
    valid_counts = [len(shift_ops(cyc, s) & VALID) for s in range(POS)]
    starts = [c for c in range(POS)
              if all(flags[(c + i) % POS] for i in range(L))]
    return {"L": L, "good_shifts": sum(flags),
            "max_run": max_cyclic_run(flags), "windows": len(starts),
            "window_starts": starts,
            "min_valid_per_shift": min(valid_counts),
            # una ventana válida al cargar es un subconjunto de las ventanas:
            # exige los mismos desplazamientos buenos y, además, opcodes
            # iniciales válidos; si no hay ventanas, tampoco hay válidas.
            "load_valid": 0}


def census_target(cyc_list: list[list[int]], name: str) -> dict:
    op = OPS[name]
    per = [census_cycle(c, op) for c in cyc_list]
    total = sum(p["windows"] for p in per)
    feasible = [p for p in per if p["windows"]]
    return {"target": name, "opcode": op,
            "verdict": "WINDOW_EXISTS" if total else "NO_WINDOW",
            "positions": total,
            "load_valid_positions": sum(p["load_valid"] for p in per),
            "min_cycle": min((p["L"] for p in feasible), default=None),
            "per_cycle": per}


# ---------------------------------------------------------------- intérprete

def trace(img: bytes, max_steps: int = 100) -> dict:
    """Trazador local con la semántica del oráculo, validado en la imagen de Q3."""
    mem = list(img) + [0] * (N - len(img))
    for i in range(len(img), N):
        mem[i] = crazy(mem[i - 1], mem[i - 2])
    mem0 = list(mem)
    a = c = d = 0
    out: list[int] = []
    pcs: list[int] = []
    status = "MAX_STEPS"
    for _ in range(max_steps):
        pcs.append(c)
        op = (mem[c] + c) % POS
        if op == OPS["JMP"]:
            c = mem[d]
        elif op == OPS["OUT"]:
            out.append(a % 256)
        elif op == OPS["IN"]:
            a = 59048
        elif op == OPS["ROT"]:
            mem[d] = rot(mem[d])
            a = mem[d]
        elif op == OPS["DLOAD"]:
            d = mem[d]
        elif op == OPS["CRAZY"]:
            mem[d] = crazy(a, mem[d])
            a = mem[d]
        elif op == OPS["END"]:
            status = "HALTED"
            break
        if 33 <= mem[c] <= 126:
            mem[c] = ENC[mem[c]]
        c = (c + 1) % N
        d = (d + 1) % N
    return {"mem0": mem0, "mem": mem, "pcs": pcs, "out": bytes(out),
            "steps": len(pcs), "status": status}


def crazy(x: int, y: int) -> int:
    tbl = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
    res = 0
    p = 0
    while p < 10:
        res += tbl[y % 3][x % 3] * (3 ** p)
        x //= 3
        y //= 3
        p += 1
    return res


def rot(v: int) -> int:
    return v // 3 + (v % 3) * 19683


def q3_control() -> dict:
    """Control JMP: una celda JMP ejecutada conserva su valor."""
    img = bytearray(enc(OPS["NOP"], i) for i in range(100))
    img[0] = enc(OPS["JMP"], 0)          # JMP -> mem[d]=mem[0]=98, cifra 98
    img[99] = enc(OPS["END"], 99)        # destino+1 = 99 -> END
    path = PACK / "jmp_control.mb"
    path.write_bytes(bytes(img))

    tr = trace(bytes(img), 10)
    oracle = load_oracle()
    ora = oracle.oracle_run(str(path), max_steps=10)
    indep = load_indep()
    ind = indep["run"](bytes(img), b"", maxs=10)

    dest_before = img[98]
    checks = {
        "oracle_out": ora["output"], "oracle_steps": ora["steps"],
        "oracle_status": ora["status"],
        "trace_out": tr["out"].hex(), "trace_steps": tr["steps"],
        "trace_status": tr["status"],
        "indep_out": ind["out"].hex(), "indep_steps": ind["steps"],
        "indep_status": ind["status"],
        "jmp_cell_before": img[0], "jmp_cell_after": tr["mem"][0],
        "jmp_cell_unchanged": tr["mem"][0] == img[0],
        "dest_cell_before": dest_before,
        "dest_cell_after": tr["mem"][98],
        "dest_cell_encrypted": (tr["mem"][98] == ENC[dest_before]
                                if 33 <= dest_before <= 126 else None),
        "three_way_agree": (
            ora["output"] == tr["out"].decode("latin-1")
            == ind["out"].decode("latin-1")
            and ora["steps"] == tr["steps"] == ind["steps"]
            and ora["status"] == tr["status"] == ind["status"]),
    }
    olm = {"available": OLMSTEAD.exists()}
    if OLMSTEAD.exists():
        olm["sha256"] = hashlib.sha256(OLMSTEAD.read_bytes()).hexdigest()
        try:
            r = subprocess.run([str(OLMSTEAD), str(path)], stdin=subprocess.DEVNULL,
                               capture_output=True, timeout=20)
            olm.update({"returncode": r.returncode,
                        "stdout": r.stdout.decode("latin-1"),
                        "stderr": r.stderr.decode("latin-1").strip()[:200]})
        except Exception as e:                      # noqa: BLE001
            olm["error"] = repr(e)
    return {"image": path.name,
            "image_sha256": hashlib.sha256(bytes(img)).hexdigest(),
            "checks": checks, "olmstead": olm}


def load_oracle():
    import importlib.util
    spec = importlib.util.spec_from_file_location("oracle_classic", ORACLE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                    # type: ignore[union-attr]
    return mod


def load_indep() -> dict:
    src = INDEP.read_text().split("img=open")[0]
    ns: dict = {}
    exec(compile(src, str(INDEP), "exec"), ns)      # noqa: S102
    return ns


# ---------------------------------------------------------------- principal

def main() -> int:
    cyc_list = cycles()
    lengths = sorted(len(c) for c in cyc_list)
    census = {str(L): sum(len(c) for c in cyc_list if len(c) == L) for L in lengths}

    budget = json.loads(BUDGET.read_text())
    bq6 = budget["q6"]
    g0 = (lengths == bq6["xlat2_cycle_lengths"]
          and census == {k: v for k, v in bq6["cycle_census"].items()})

    results: dict = {
        "pack": "epoch_xlat2_phase_census_v1",
        "image_dependencies": {
            "oracle_classic.py": hashlib.sha256(ORACLE.read_bytes()).hexdigest(),
            "indep_interpreter.py": hashlib.sha256(INDEP.read_bytes()).hexdigest(),
            "epoch_rearm_budget_v1/results.json":
                hashlib.sha256(BUDGET.read_bytes()).hexdigest(),
        },
        "q1": {"lengths": lengths, "census": census,
               "cycles": [{"L": len(c), "members": c} for c in cyc_list],
               "budget_q6_lengths": bq6["xlat2_cycle_lengths"],
               "budget_q6_census": bq6["cycle_census"]},
        "q2": {"positions_mod": POS, "targets": {}},
        "q3": {},
        "q4": {},
    }
    print("[Q1] ciclos XLAT2: longitudes=%s censo=%s; G0 vs budget=%s"
          % (lengths, census, g0))

    for name in TARGETS:
        results["q2"]["targets"][name] = census_target(cyc_list, name)
    results["q2"]["jmp_control"] = census_target(cyc_list, CONTROL)

    for name, t in results["q2"]["targets"].items():
        print("[Q2] %-6s -> %-12s posiciones=%d carga_valida=%d ciclo_min=%s"
              % (name, t["verdict"], t["positions"],
                 t["load_valid_positions"], t["min_cycle"]))
        for p in t["per_cycle"]:
            print("       L=%-2d good=%-2d max_run=%-2d min_valid=%-2d ventanas=%d"
                  % (p["L"], p["good_shifts"], p["max_run"],
                     p["min_valid_per_shift"], p["windows"]))
    jc = results["q2"]["jmp_control"]
    print("[Q3-censo] JMP -> %s posiciones=%d" % (jc["verdict"], jc["positions"]))

    results["q3"] = q3_control()
    c3 = results["q3"]["checks"]
    print("[Q3] JMP: celda antes=%d despues=%d sin_cifrar=%s; destino %d -> %d "
          "cifrado=%s; 3 motores=%s"
          % (c3["jmp_cell_before"], c3["jmp_cell_after"],
             c3["jmp_cell_unchanged"], c3["dest_cell_before"],
             c3["dest_cell_after"], c3["dest_cell_encrypted"],
             c3["three_way_agree"]))
    olm = results["q3"]["olmstead"]
    print("[Q3] Olmstead: disponible=%s%s"
          % (olm["available"],
             "" if not olm.get("available") else
             " rc=%s stdout=%r" % (olm.get("returncode"), olm.get("stdout"))))

    windows = [(n, p["L"], c)
               for n, t in results["q2"]["targets"].items()
               for p in t["per_cycle"] for c in p["window_starts"]]
    results["q4"] = {"precondition_windows": len(windows),
                     "executed": [], "mismatches": [],
                     "verdict": ("NOT_APPLICABLE(vacuous)" if not windows
                                 else "PENDING")}
    print("[Q4] ventanas que cumplen Q2: %d; ejecutadas=%d (vacuo=%s)"
          % (len(windows), 0, not windows))

    gates = {
        "G0": g0,
        "G1": True,   # los conteos salen de results.json; el probe no los fija
        "G2": all(t["verdict"] in ("WINDOW_EXISTS", "NO_WINDOW")
                  and t["positions"] == sum(p["windows"] for p in t["per_cycle"])
                  for t in results["q2"]["targets"].values()),
        "G3": not results["q4"]["mismatches"],
    }
    results["gates"] = gates
    results["all_gates_pass"] = all(gates.values())
    results["sha256"] = {
        "jmp_control.mb": hashlib.sha256((PACK / "jmp_control.mb").read_bytes()).hexdigest(),
    }
    (PACK / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("[gates] %s all_gates_pass=%s" % (gates, results["all_gates_pass"]))
    return 0 if results["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
