#!/usr/bin/env python3
"""tr_fillprobe.py — semántica del relleno de memoria más allá del programa.

Pregunta medible: ¿con qué valores se inicializa la memoria después de la
última celda del programa?  El oráculo del repo rellena con
mem[i] = crazy(mem[i-1], mem[i-2]); otros cargadores rellenan con 0.  La
respuesta decide si la palabra 0 (y por tanto 29524 = crazy(0,0)) está
disponible "gratis" en una región virgen.

Experimento (un solo programa, tres motores):

    pc 0        IN      a = 0            (stdin = byte 0x00)
    pc 1..F-1   NOP     d avanza +1 por instrucción -> d = F
    pc F        CRAZY   mem[F] = crazy(0, mem[F]) ; a = resultado
    pc F+1      OUT     emite a % 256
    pc F+2      END

El valor emitido depende de mem[F], que está en la región de relleno (F >> len
del programa).  Predicciones:
    relleno cero    -> mem[F] = 0        -> OUT = 29524 % 256 = 84
    relleno crazy   -> mem[F] = fill(F)  -> OUT = crazy(0, fill(F)) % 256

Motores: trazador con las primitivas del oráculo del repo, el oráculo del repo,
y el runner C original.  El trazador y el oráculo comparten load_memory (relleno
crazy); el runner C es independiente — su salida es la que decide.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

from tr_spec import MEM, spec_crazy, spec_rot  # noqa: E402

C_RUNNER = ROOT / "runners/malbolge-original/malbolge"
OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40,
       "CRAZY": 62, "NOP": 68, "END": 81}


def enc(addr: int, op: int) -> int:
    return 33 + ((op - 33 - addr) % 94)


def build_image(far: int) -> tuple[bytes, dict]:
    cells: dict[int, int] = {}
    cells[0] = enc(0, OPS["IN"])
    for a in range(1, far):
        cells[a] = enc(a, OPS["NOP"])
    cells[far] = enc(far, OPS["CRAZY"])
    cells[far + 1] = enc(far + 1, OPS["OUT"])
    cells[far + 2] = enc(far + 2, OPS["END"])
    last = max(cells)
    data = bytes(cells.get(a, enc(a, OPS["NOP"])) for a in range(last + 1))
    return data, {"far": far, "length": len(data),
                  "printable": all(33 <= b <= 126 for b in data)}


def trace(source: bytes, stdin_bytes: bytes, max_steps: int = 5000) -> dict:
    text = source.decode("latin-1")
    mem = oc.load_memory(text)
    a = c = d = 0
    ip = 0
    out: list[int] = []
    writes = []
    for step in range(1, max_steps + 1):
        cell = mem[c]
        op = (cell + c) % 94
        if op == 5:
            out.append(a % 256)
        elif op == 23:
            if ip >= len(stdin_bytes):
                return {"output": bytes(out), "status": "EOF", "steps": step,
                        "writes": writes}
            a = stdin_bytes[ip]
            ip += 1
        elif op == 62:
            old = mem[d]
            mem[d] = oc.crazy_op(a, old)
            a = mem[d]
            writes.append({"addr": d, "old": old, "new": mem[d], "step": step})
        elif op == 81:
            return {"output": bytes(out), "status": "HALTED", "steps": step,
                    "writes": writes}
        if 33 <= mem[c] <= 126:
            mem[c] = oc._ENC[mem[c]]
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    return {"output": bytes(out), "status": "MAX_STEPS", "steps": max_steps,
            "writes": writes}


def run_c(path: Path, stdin_bytes: bytes, timeout: int = 120):
    p = subprocess.run([str(C_RUNNER), str(path), "5000000"],
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    return p.stdout.hex(), p.returncode


def main() -> dict:
    res: dict = {"targets": []}
    ok = True
    for far in (1200, 1300, 1200 + 94, 58000, 58900):
        data, meta = build_image(far)
        path = PACK / f"fillprobe_{far}.mb"
        path.write_bytes(data)

        # predicciones
        mem_zero = [0] * MEM
        pred_zero = spec_crazy(0, 0) % 256
        text = data.decode("latin-1")
        mem_crazy = oc.load_memory(text)
        pred_crazy = spec_crazy(0, mem_crazy[far]) % 256
        fill_value = mem_crazy[far]

        # motor 1: trazador con las primitivas del oráculo del repo
        tr = trace(data, b"\x00", max_steps=far + 200)
        # motor 2: oráculo del repo
        orc = oc.oracle_run(str(path), 5000000, "\x00", stop_on_eof=True)
        # motor 3: runner C original
        cout, crc = run_c(path, b"\x00")
        c_norm = cout[:-2] if cout.endswith("0a") else cout

        row = {
            "far": far,
            "length": meta["length"],
            "printable": meta["printable"],
            "fill_value_at_far": fill_value,
            "pred_zero_fill": pred_zero,
            "pred_crazy_fill": pred_crazy,
            "trace_out": tr["output"].hex(),
            "trace_status": tr["status"],
            "oracle_out": orc["output"].encode("latin-1").hex(),
            "oracle_status": orc["status"],
            "c_out": cout,
            "c_out_norm": c_norm,
            "c_exit": crc,
            "c_matches_zero": c_norm == f"{pred_zero:02x}",
            "c_matches_crazy": c_norm == f"{pred_crazy:02x}",
            "trace_matches_oracle": tr["output"].hex() == orc["output"].encode("latin-1").hex(),
            "c_matches_oracle": c_norm == orc["output"].encode("latin-1").hex(),
        }
        res["targets"].append(row)
        ok = ok and row["printable"] and row["trace_matches_oracle"]
        print(f"[fill] far={far} len={meta['length']} fill={fill_value} "
              f"pred_cero={pred_zero} pred_crazy={pred_crazy} "
              f"trace={tr['output'].hex()} oracle={row['oracle_out']} "
              f"c={cout} (exit {crc}) "
              f"c==cero:{row['c_matches_zero']} c==crazy:{row['c_matches_crazy']}",
              flush=True)
    res["verdict"] = bool(ok)
    return res


if __name__ == "__main__":
    r = main()
    print("[fill] ok =", r["verdict"])
