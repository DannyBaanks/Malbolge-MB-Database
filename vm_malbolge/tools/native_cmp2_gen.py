#!/usr/bin/env python3
"""Canonical generator for the TWO-OPERAND relational comparator.

Milestone (a), second stage: CMP_LT(a, b) with BOTH operands variable decimal
digits, in a single Classic Malbolge image emitted without LMAO.

Mechanism (traced and verified against vm_malbolge/src/mbir_native_cmp_decimal.mb):

  /  j j j j  p        ->  mem[49] = crz(A, C1);  a = crz(A, C1)
  (j *)x m             ->  mem[49] = rot^m(crz(A, C1));  a = the same
  /                    ->  a = B
  j j j                ->  d navigates 51 -> 84 -> 50 -> 49
  p                    ->  mem[49] = crz(B, rot^m(crz(A, C1)))   (the KEY)
  (j *)x n             ->  mem[49] = rot^n(KEY);  a = the same
  j  i                 ->  jump to KEY+1 (the route's branch block)
  p (branch block)     ->  Q = crz(KEY, 48)
  j j  i               ->  jump to Q+1 (the route's recipe)

So the routing key depends on BOTH stdin bytes, which is what the one-byte
dispatcher of mbir_native_cmp_decimal.mb cannot do.

The recipe of each route prints "1" if a < b and "0" otherwise.

Usage (from repo root):
    python3 vm_malbolge/tools/native_cmp2_gen.py [--kb-c1 C] [--kb-m M] [--kb-n N]
"""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "native_classic"))
sys.path.insert(0, str(HERE))

from constants import CHAR_OP_MAP, char_for_op, crazy_op as crz, rot_op  # noqa: E402
from native_two_routes_gen import (best_ops, loader_cells, run_mbref,  # noqa: E402
                                   run_oracle, run_runner)

ROOT = HERE.parents[1]

# --- key family parameters (found by search_key_wide.py) --------------------
KB_C1 = 85      # constant written at cell 49
KB_M = 0        # rotations applied to crz(A, C1) before reading B
KB_N = 7        # rotations applied to the combined key before the branch
KB_BRANCH = 48  # the branch block constant (cell 50, also a pointer waypoint)


def rot_n(x, n):
    for _ in range(n):
        x = rot_op(x)
    return x


def two_byte_bootstrap(m, n):
    return (["/"] + ["j"] * 4 + ["p"] + ["j", "*"] * m + ["/"]
            + ["j", "j", "j"] + ["p"] + ["j", "*"] * n + ["j", "i"])


def route_addr(a_digit, b_digit, c1=KB_C1, m=KB_M, n=KB_N, branch=KB_BRANCH):
    """Route address Q for the decimal digit pair (a, b)."""
    A, B = 48 + a_digit, 48 + b_digit
    key = rot_n(crz(B, rot_n(crz(A, c1), m)), n)
    return crz(key, branch)


def route_key(a_digit, b_digit, c1=KB_C1, m=KB_M, n=KB_N):
    A, B = 48 + a_digit, 48 + b_digit
    return rot_n(crz(B, rot_n(crz(A, c1), m)), n)


def build(routes, c1=KB_C1, m=KB_M, n=KB_N, branch=KB_BRANCH):
    bootstrap = two_byte_bootstrap(m, n)
    keys = {p: route_key(p[0], p[1], c1, m, n) for p in routes}
    qs = {p: crz(keys[p], branch) for p in routes}

    # per-route recipe selection (same backtracking as the one-byte emitter)
    options = {}
    for pair in sorted(routes):
        options[pair] = recipe_options_local(qs[pair], routes[pair])
    used = set(range(0, len(bootstrap)))
    used.update((40, 49, 50, 51, 78, 84, 85))
    for pair in routes:
        used.update(range(keys[pair] + 1, keys[pair] + 5))
        used.update(range(qs[pair] + 1, qs[pair] + 27))
    for pair in routes:
        options[pair] = [o for o in options[pair]
                         if not (set(o["cells"]) & used)]
    order = sorted(routes, key=lambda p: (len(options[p]), p))
    selected, occupied = {}, set(used)

    def backtrack(index):
        if index == len(order):
            return True
        pair = order[index]
        for option in options[pair]:
            cells = set(option["cells"])
            if cells & occupied:
                continue
            selected[pair] = option
            occupied.update(cells)
            if backtrack(index + 1):
                return True
            occupied.difference_update(cells)
            del selected[pair]
        return False

    if not backtrack(0):
        raise RuntimeError("no disjoint recipe selection for the 100 routes")

    size = max(max(k + 5 for k in keys.values()),
               max(q + 27 for q in qs.values()),
               max(o["b"] + o["length"] for o in selected.values()),
               len(bootstrap) + 4) + 2
    memory = [ord(char_for_op(CHAR_OP_MAP["j"], addr)) for addr in range(size)]
    for addr, opcode in enumerate(bootstrap):
        memory[addr] = ord(char_for_op(CHAR_OP_MAP[opcode], addr))
    for addr, value in {40: 77, 49: c1, 50: branch, 51: 83,
                        78: 84, 84: 49, 85: 48}.items():
        memory[addr] = value
    for pair in sorted(routes):
        s = keys[pair]
        addr = s + 1
        for offset, opcode in enumerate("p" + "j" * 2 + "i"):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        q = qs[pair]
        option = selected[pair]
        setup = "".join(["jj*"] * option["k"]) + "jjj"
        addr = q + 1
        for offset, opcode in enumerate(setup):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        addr = q + 1 + len(setup)
        for offset, opcode in enumerate(option["code"]):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        data_addr = option["b"]
        data_index = 0
        for group in option["code"].split("<"):
            for _opcode in group.replace("v", ""):
                memory[data_addr] = option["data"][data_index]
                data_index += 1
                data_addr += 1
            data_addr += 1
        if data_index != len(option["data"]):
            raise AssertionError("recipe data length mismatch")
    for addr, value in enumerate(memory):
        if not valid_cell_local(addr, value):
            raise AssertionError(f"invalid cell {addr}: {value}")
    return bytes(memory), keys, qs, selected


def valid_cell_local(addr, value):
    from constants import XLAT1
    VALID = frozenset("ji*p</vo")
    if not 33 <= value <= 126:
        return False
    return XLAT1[(value - 33 + addr) % 94] in VALID


def recipe_options_local(q_value, target, max_k=6):
    """Rectilinear recipe that prints `target`, mirroring the one-byte emitter."""
    out = []
    for k in range(1, max_k + 1):
        b = q_value
        for _ in range(k):
            b = rot_op(b)
        b += 1
        setup_len = 3 * k + 3
        max_code = 26 - setup_len
        if max_code < 3:
            continue
        solutions = []

        def walk(index, a, data_addr, groups, data_values):
            if len(solutions) >= 8:
                return
            if index == len(target):
                code = "".join("".join(g) + "<" for g in groups) + "v"
                if len(code) <= max_code:
                    solutions.append((code, tuple(data_values), b, len(code)))
                return
            for ops, data in best_ops(data_addr, a, target[index],
                                      min(6, max_code), 6):
                next_a = a
                for opcode, value in zip(ops, data):
                    next_a = rot_op(value) if opcode == "*" else crz(next_a, value)
                walk(index + 1, next_a, data_addr + len(ops) + 1,
                     groups + (ops,), data_values + data)
                if len(solutions) >= 8:
                    return

        walk(0, b - 1, b, (), ())
        for code, data, b_value, length in solutions:
            out.append({"k": k, "b": b_value, "setup": setup_len, "length": length,
                        "code": code, "data": data,
                        "cells": tuple(range(b_value, b_value + length))})
    seen, uniq = set(), []
    for o in out:
        key = (o["k"], o["b"], o["code"], o["data"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(o)
    uniq.sort(key=lambda o: (o["k"], o["length"], len(o["data"])))
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_native_cmp2.mb")
    ap.add_argument("--json", type=Path,
                    default=ROOT / "vm_malbolge/evidence/native_cmp2_build.json")
    ap.add_argument("--kb-c1", type=int, default=KB_C1)
    ap.add_argument("--kb-m", type=int, default=KB_M)
    ap.add_argument("--kb-n", type=int, default=KB_N)
    ap.add_argument("--mb-ref", type=Path, default=None)
    args = ap.parse_args()

    routes = {}
    for a in range(10):
        for b in range(10):
            routes[(a, b)] = b"1\n" if a < b else b"0\n"

    print(f"clave: C1={args.kb_c1} m={args.kb_m} n={args.kb_n} rama={KB_BRANCH}")
    qs = {p: route_addr(p[0], p[1], args.kb_c1, args.kb_m, args.kb_n) for p in routes}
    uniq = sorted(set(qs.values()))
    gaps = [uniq[i + 1] - uniq[i] for i in range(len(uniq) - 1)]
    print(f"  100 pares -> {len(uniq)} direcciones distintas, gap minimo "
          f"{min(gaps) if gaps else 0}, rango {uniq[0]}..{uniq[-1]}")

    if len(uniq) != 100:
        # Guardia: sin 100 direcciones distintas, dos pares compartirian receta y
        # la imagen daria un booleano equivocado. Medido (cmp2_two_operand_blocker.json):
        # esta familia de claves da como maximo 56/100.
        print("\nRECHAZADO: la clave no da 100 direcciones distintas.")
        print("  Los pares que colisionen compartirian una receta y imprimirian un")
        print("  booleano incorrecto, así que la imagen no seria valida.")
        print("  Medicion completa y el porque (separabilidad de CRAZY/ROT) en")
        print("  vm_malbolge/evidence/cmp2_two_operand_blocker.json")
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps({
                "schema": "native-cmp2-classic/1",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "evidence_kind": "MALBOLGE_RUNTIME",
                "claim": ("Refused to build: the two-byte routing key does not yield 100 "
                          "distinct route addresses for the 100 decimal-digit pairs, so the "
                          "image would print wrong booleans for the colliding pairs."),
                "claim_status": "NOT_BUILT",
                "routing_key": {
                    "formula": "KEY = rot^n(crz(B, rot^m(crz(A, C1)))); Q = crz(KEY, 48)",
                    "c1": args.kb_c1, "m": args.kb_m, "n": args.kb_n,
                    "branch": KB_BRANCH,
                    "distinct_addresses": len(uniq),
                    "min_gap": min(gaps) if gaps else 0,
                    "range": [uniq[0], uniq[-1]],
                },
                "blocker": "vm_malbolge/evidence/cmp2_two_operand_blocker.json",
            }, indent=2), encoding="utf-8")
            print(f"Wrote {args.json}")
        return 2

    memory, keys, q_values, selected = build(routes, args.kb_c1, args.kb_m, args.kb_n)
    print(f"imagen: {len(memory)} bytes (limite 59049, margen {59049 - len(memory)})")
    loader_cells(memory)
    print("loader estricto: ACCEPT")

    cases = []
    for pair in sorted(routes):
        a, b = pair
        want = routes[pair]
        stdin = f"{a}{b}".encode("latin-1")
        oout, osteps, ostatus = run_oracle(memory, stdin)
        rout, rerr = run_runner(memory, stdin)
        row = {"a": a, "b": b, "stdin_hex": stdin.hex(),
               "expected": want.decode("latin-1"),
               "oracle_out": oout.decode("latin-1", "replace"),
               "runner_out": rout.decode("latin-1", "replace"),
               "oracle_steps": osteps, "oracle_status": ostatus,
               "oracle_verdict": "PASS" if oout == want else "FAIL",
               "runner_verdict": "PASS" if rout == want else "FAIL"}
        if args.mb_ref:
            mout, mrc, merr = run_mbref(memory, stdin, args.mb_ref)
            row.update({"mbref_out": mout.decode("latin-1", "replace"),
                        "mbref_rc": mrc, "mbref_stderr": merr,
                        "mbref_verdict": "PASS" if (mrc == 0 and mout == want) else "FAIL"})
        cases.append(row)
    ok = sum(1 for c in cases if c["oracle_verdict"] == "PASS"
             and c["runner_verdict"] == "PASS")
    print(f"rutas PASS: {ok}/100")

    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({
        "schema": "native-cmp2-classic/1",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "evidence_kind": "MALBOLGE_RUNTIME",
        "claim": ("A single Classic Malbolge image, emitted without LMAO, compares TWO "
                  "variable decimal-digit operands read from stdin and prints 1 if a < b "
                  "and 0 otherwise, with every cell valid under the strict loader."),
        "claim_status": "DEMONSTRATED" if ok == 100 else "FAIL",
        "generator": {
            "path": "vm_malbolge/tools/native_cmp2_gen.py",
            "sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        },
        "artifact": {
            "path": str(args.mb.relative_to(ROOT) if args.mb.is_relative_to(ROOT) else args.mb),
            "size_bytes": len(memory),
            "sha256": hashlib.sha256(memory).hexdigest(),
            "variant": "classic-3^10",
            "assembler": {"name": "none (native emitter)"},
        },
        "routing_key": {
            "formula": "KEY = rot^n(crz(B, rot^m(crz(A, C1)))); Q = crz(KEY, 48)",
            "c1": args.kb_c1, "m": args.kb_m, "n": args.kb_n, "branch": KB_BRANCH,
            "bootstrap": two_byte_bootstrap(args.kb_m, args.kb_n),
            "distinct_addresses": len(uniq),
            "min_gap": min(gaps) if gaps else 0,
            "range": [uniq[0], uniq[-1]],
        },
        "tooling": {
            "oracle": {"path": "tools/oracle_classic.py",
                       "sha256": hashlib.sha256((ROOT / "tools/oracle_classic.py").read_bytes()).hexdigest()},
            "runner": {"path": "runners/malbolge-original/malbolge",
                       "sha256": hashlib.sha256((ROOT / "runners/malbolge-original/malbolge").read_bytes()).hexdigest()},
            "strict_loader_c": {
                "path": str(args.mb_ref) if args.mb_ref else None,
                "provenance": "BolgeForge/oracle/mb_ref.c (MIT), compiled to /tmp for this run",
            } if args.mb_ref else None,
        },
        "summary": {"routes": 100, "routes_pass": ok,
                    "strict_loader": "ACCEPT",
                    "headroom_bytes": 59049 - len(memory)},
        "cases": cases,
        "scope_limits": [
            "Operands are single decimal digits (0..9), read as two consecutive ASCII characters.",
            "One-shot: two bytes in, one boolean out, HALT. No loop, no stored-program PC.",
            "Negative results and non-digit input are out of scope.",
        ],
        "not_demonstrated": [
            "Multi-digit operands and arbitrary precision.",
            "A stored-program loader in the same image.",
        ],
    }, indent=2), encoding="utf-8")
    print(f"Wrote {args.json}")
    return 0 if ok == 100 else 1


if __name__ == "__main__":
    sys.exit(main())
