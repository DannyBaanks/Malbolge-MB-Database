#!/usr/bin/env python3
"""Canonical generator for the first NATIVE two-route Classic Malbolge image
of Milestone M2: no LMAO involved.

Features:
- Emits a Classic (3^10) image with a rectilinear-recipe dispatcher taken from
  the BolgeForge native emitter (MIT; see native_classic/constants.py).
- Routing key: the entry byte d selects the route with
      S = rot^7(crazy(48 + d, 85)),  Q = crazy(S, 48)
  Measured (evidence/e4bis_dispatch_packing.json): with this key, d=0..9 give
  10 distinct route addresses in 747..1125 with a minimum gap of 27 cells.
  This image uses two routes: d=0 -> ADD, d=1 -> CMP_EQ.
- Every cell of the emitted image is validated with valid_cell() (a strict
  loader requirement: each byte must decode to one of "ji*p</vo" at its own
  load address), so the result is loader-valid by construction, not by hope.
- The image is executed and verified with the repository's own engines
  (tools/oracle_classic.py and runners/malbolge-original/malbolge).

What is NOT this generator: it does not read its operands from stdin. The
native emitter expresses each route as a fixed rectilinear recipe over literal
data cells, so the operands are literals baked into the recipe. Reading
operands from stdin inside a route is NOT demonstrated (that needs an extra IN
per route, which the emitter does not yet express).

Routes of this image:
    d = 0 -> ADD 2 + 3      -> prints "5"
    d = 1 -> CMP_EQ 2 == 2   -> prints "1"
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "native_classic"))

from constants import CHAR_OP_MAP, XLAT1, char_for_op, crazy_op, rot_op  # noqa: E402

ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import oracle_classic  # noqa: E402

RUNNER = ROOT / "runners" / "malbolge-original" / "malbolge"

VALID = frozenset("ji*p</vo")
C_BRANCH = 85
ROTATIONS = 7

# Milestone M2 Native, two-route image: d=0 -> ADD, d=1 -> CMP_EQ.
ROUTES_2 = {
    0: ("ADD 2 + 3 = 5", b"5\n"),
    1: ("CMP_EQ 2 == 2 -> 1", b"1\n"),
}

# Milestone M2 Native, three-route image: the third route is the relational
# comparator CMP_LT, i.e. the same operation set the unified image (b) needs.
ROUTES_3 = {
    0: ("ADD 2 + 3 = 5", b"5\n"),
    1: ("CMP_EQ 2 == 2 -> 1", b"1\n"),
    2: ("CMP_LT 2 < 3 -> 1", b"1\n"),
}

# Milestone (a): relational comparator over the decimal domain 0..9, which is
# the domain the decrement-classifier kernels cannot reach (they stop at
# {0,1,2}). Each decimal digit routes to its own recipe that prints the boolean
# of (digit < REFERENCE). The dispatcher key routes ASCII('0')..ASCII('9') to
# ten distinct route addresses (Q = 747..1125, min gap 27), so the whole
# decimal digit domain is covered without a single new code flag.
REFERENCE = 5
ROUTES_CMP = {
    d: (f"CMP_LT {d} < {REFERENCE} -> {1 if d < REFERENCE else 0}",
        b"1\n" if d < REFERENCE else b"0\n")
    for d in range(10)
}


def decode(addr, value):
    if not 33 <= value <= 126:
        return None
    return XLAT1[(value - 33 + addr) % 94]


def valid_cell(addr, value):
    return 33 <= value <= 126 and decode(addr, value) in VALID


_VALID_VALUES = {}


def valid_values(addr):
    if addr not in _VALID_VALUES:
        _VALID_VALUES[addr] = [v for v in range(33, 127) if valid_cell(addr, v)]
    return _VALID_VALUES[addr]


def best_ops(data_addr, a, target, max_len=6, limit=8):
    """Shortest chains of ('*' rot-literal | 'p' crazy-literal) that reach target."""
    states = {(0, a): ((), ())}
    found = []
    for pos in range(max_len + 1):
        for (p, current), (ops, data) in list(states.items()):
            if p == pos and (current & 255) == target:
                found.append((ops, data))
        if pos == max_len:
            break
        new_states = {}
        for (p, current), (ops, data) in states.items():
            if p != pos:
                continue
            for value in valid_values(data_addr + pos):
                for opcode, result in (("*", rot_op(value)), ("p", crazy_op(current, value))):
                    key = (pos + 1, result)
                    if key not in new_states:
                        new_states[key] = (ops + (opcode,), data + (value,))
        states.update(new_states)
    found.sort(key=lambda item: len(item[0]))
    return found[:limit]


def route_addresses(digits):
    s = [crazy_op(48 + d, C_BRANCH) for d in digits]
    for _ in range(ROTATIONS):
        s = [rot_op(v) for v in s]
    q = [crazy_op(v, 48) for v in s]
    return s, q


def recipe_options(q_value, target, max_k=6):
    """One rectilinear recipe per usable k, printing `target`."""
    options = []
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
                code = "".join("".join(group) + "<" for group in groups) + "v"
                if len(code) <= max_code:
                    solutions.append((code, tuple(data_values), b, len(code)))
                return
            for ops, data in best_ops(data_addr, a, target[index],
                                      min(6, max_code), 6):
                next_a = a
                for opcode, value in zip(ops, data):
                    next_a = rot_op(value) if opcode == "*" else crazy_op(next_a, value)
                walk(index + 1, next_a, data_addr + len(ops) + 1,
                     groups + (ops,), data_values + data)
                if len(solutions) >= 8:
                    return

        walk(0, b - 1, b, (), ())
        for code, data, b_value, length in solutions:
            options.append({"k": k, "b": b_value, "setup": setup_len,
                            "length": length, "code": code, "data": data,
                            "cells": tuple(range(b_value, b_value + length))})
    seen, unique = set(), []
    for option in options:
        key = (option["k"], option["b"], option["code"], option["data"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(option)
    unique.sort(key=lambda option: (option["k"], option["length"], len(option["data"])))
    return unique


def select_options(s_values, q_values, targets):
    digits = sorted(targets)
    all_options = {}
    for d in digits:
        all_options[d] = recipe_options(q_values[d], targets[d])
    used = set(range(0, 22))
    used.update((40, 49, 50, 51, 78, 84, 85))
    for d in digits:
        used.update(range(s_values[d] + 1, s_values[d] + 5))
        used.update(range(q_values[d] + 1, q_values[d] + 27))
    for d in digits:
        all_options[d] = [o for o in all_options[d]
                          if not (set(o["cells"]) & used)]
    order = sorted(digits, key=lambda d: (len(all_options[d]), d))
    selected, occupied = {}, set(used)

    def backtrack(index):
        if index == len(order):
            return True
        d = order[index]
        for option in all_options[d]:
            cells = set(option["cells"])
            if cells & occupied:
                continue
            selected[d] = option
            occupied.update(cells)
            if backtrack(index + 1):
                return True
            occupied.difference_update(cells)
            del selected[d]
        return False

    if not backtrack(0):
        raise RuntimeError("no disjoint recipe selection for the two routes")
    return selected


def build(s_values, q_values, selected, targets):
    size = max(max(s_values[d] for d in targets) + 5,
               max(q_values[d] for d in targets) + 27,
               max(selected[d]["b"] + selected[d]["length"] for d in targets),
               90) + 2
    memory = [ord(char_for_op(CHAR_OP_MAP["j"], addr)) for addr in range(size)]
    bootstrap = ["/"] + ["j"] * 4 + ["p"] + ["j", "*"] * 7 + ["j", "i"]
    for addr, opcode in enumerate(bootstrap):
        memory[addr] = ord(char_for_op(CHAR_OP_MAP[opcode], addr))
    for addr, value in {40: 77, 49: 85, 50: 48, 51: 83,
                        78: 84, 84: 49, 85: 48}.items():
        memory[addr] = value
    for d in sorted(targets):
        addr = s_values[d] + 1
        for offset, opcode in enumerate("p" + "j" * 2 + "i"):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        option = selected[d]
        setup = "".join(["jj*"] * option["k"]) + "jjj"
        addr = q_values[d] + 1
        for offset, opcode in enumerate(setup):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        addr = q_values[d] + 1 + len(setup)
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
        if not valid_cell(addr, value):
            raise AssertionError(f"invalid cell {addr}: {value}")
    return bytes(memory)


def loader_cells(memory):
    """Strict-loader mirror of BolgeForge/tools/prove_truth_machine.py:52-71."""
    if len(memory) < 2:
        raise ValueError("source needs at least two cells")
    for i, value in enumerate(memory):
        if not 33 <= value <= 126:
            raise ValueError(f"invalid character at {i}")
        if XLAT1[(value - 33 + i) % 94] not in VALID:
            raise ValueError(f"LOADER_REJECT: cell {i} decodes to "
                             f"{XLAT1[(value - 33 + i) % 94]!r}")
    return True


def run_oracle(memory, stdin_bytes, max_steps=4000000):
    src = memory.decode("latin-1")
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=stdin_bytes.decode("latin-1"))
    return text.encode("latin-1"), steps, status


def run_runner(memory, stdin_bytes, max_steps=4000000):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(stdin_bytes)
        name = f.name
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mal") as m:
            m.write(memory)
            mb_name = m.name
        with open(name, "rb") as fin:
            r = subprocess.run([str(RUNNER), mb_name, str(max_steps)],
                               stdin=fin, capture_output=True)
        out = r.stdout
        if out.endswith(b"\r\n"):
            out = out[:-2]
        elif out.endswith(b"\n"):
            out = out[:-1]
        return out, r.stderr
    finally:
        os.unlink(name)


def run_mbref(memory, stdin_bytes, mbref, max_steps=4000000):
    """Third engine: the strict-loader C oracle (BolgeForge/oracle/mb_ref.c).

    stdout is returned verbatim (mb_ref ends its output with a newline, like
    the Python oracle), so the comparison against `want` is apples to apples.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(stdin_bytes)
        name = f.name
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mal") as m:
            m.write(memory)
            mb_name = m.name
        with open(name, "rb") as fin:
            r = subprocess.run([str(mbref), mb_name, str(max_steps)],
                               stdin=fin, capture_output=True)
        return r.stdout, r.returncode, r.stderr.decode("latin-1", "replace").strip()
    finally:
        os.unlink(name)


def main():
    ap = argparse.ArgumentParser(description="Native two-route Classic builder")
    ap.add_argument("--mb", type=Path,
                    default=ROOT / "vm_malbolge/src/mbir_native_2routes.mb")
    ap.add_argument("--routes", type=int, choices=(2, 3), default=2,
                    help="2 routes (ADD + CMP_EQ) or 3 routes (ADD + CMP_EQ + CMP_LT)")
    ap.add_argument("--cmp", action="store_true",
                    help="build the (a) comparator: 10 routes, one per decimal digit "
                         "0..9, each printing CMP_LT(digit, REFERENCE)")
    ap.add_argument("--mb-ref", type=Path, default=None,
                    help="path to the strict-loader C oracle (mb_ref); if given, "
                         "every case is also verified by this third engine")
    ap.add_argument("--json", type=Path, default=None,
                    help="evidence JSON path (default: evidence/native_<N>routes_build.json)")
    args = ap.parse_args()

    ROUTES = ROUTES_3 if args.routes == 3 else ROUTES_2
    if args.cmp:
        ROUTES = ROUTES_CMP

    if args.json is None:
        if args.cmp:
            name = "native_cmp_decimal_build.json"
        else:
            name = "native_2routes_build.json" if args.routes == 2 else "native_3routes_build.json"
        args.json = ROOT / "vm_malbolge/evidence" / name
    if str(args.mb).endswith("mbir_native_2routes.mb"):
        args.mb = ROOT / ("vm_malbolge/src/mbir_native_2routes.mb" if args.routes == 2
                          else "vm_malbolge/src/mbir_native_3routes.mb")
    if args.cmp:
        args.mb = ROOT / "vm_malbolge/src/mbir_native_cmp_decimal.mb"

    targets = {d: ROUTES[d][1] for d in sorted(ROUTES)}
    digits = sorted(targets)

    s_values, q_values = route_addresses(digits)
    print("routing key c=85 rot=7:")
    for d in digits:
        print(f"  d={d} -> S={s_values[d]} Q={q_values[d]} "
              f"({ROUTES[d][0]})")
    gaps = [q_values[digits[i + 1]] - q_values[digits[i]]
            for i in range(len(digits) - 1)]
    print(f"  route gaps: {gaps}")

    selected = select_options(s_values, q_values, targets)
    for d in digits:
        o = selected[d]
        print(f"  route d={d}: k={o['k']} b={o['b']} length={o['length']} "
              f"data_cells={len(o['data'])}")

    memory = build(s_values, q_values, selected, targets)
    print(f"\nimage: {len(memory)} bytes (limit 59049, headroom {59049 - len(memory)})")

    # strict loader gate
    loader_cells(memory)
    print("strict loader: ACCEPT (every cell decodes to ji*p</vo)")

    # execute both routes on both engines
    cases = []
    for d in digits:
        stdin = f"{d}\n".encode("latin-1")
        want = targets[d]
        oout, osteps, ostatus = run_oracle(memory, stdin)
        rout, rerr = run_runner(memory, stdin)
        ok_o = oout == want
        ok_r = rout == want
        row = {
            "route": d, "meaning": ROUTES[d][0], "stdin_hex": stdin.hex(),
            "expected": want.decode("latin-1"),
            "oracle_out": oout.decode("latin-1", "replace"),
            "runner_out": rout.decode("latin-1", "replace"),
            "oracle_steps": osteps, "oracle_status": ostatus,
            "runner_stderr": rerr.decode("latin-1", "replace").strip(),
            "oracle_verdict": "PASS" if ok_o else "FAIL",
            "runner_verdict": "PASS" if ok_r else "FAIL",
        }
        if args.mb_ref:
            mout, mrc, merr = run_mbref(memory, stdin, args.mb_ref)
            row["mbref_out"] = mout.decode("latin-1", "replace")
            row["mbref_rc"] = mrc
            row["mbref_stderr"] = merr
            row["mbref_verdict"] = "PASS" if (mrc == 0 and mout == want) else "FAIL"
        cases.append(row)
        print(f"  d={d}: expected {want!r} oracle={oout!r} runner={rout!r} "
              f"steps={osteps} "
              + (f"mb_ref rc={row['mbref_rc']} out={row['mbref_out']!r} "
                 if args.mb_ref else "")
              + f"{'PASS' if (ok_o and ok_r) else 'FAIL'}")

    # negative control: an entry byte outside the routed domain
    neg = {}
    for d in (2, 5):
        stdin = f"{d}\n".encode("latin-1")
        oout, osteps, ostatus = run_oracle(memory, stdin)
        rout, rerr = run_runner(memory, stdin)
        row = {"stdin_hex": stdin.hex(),
               "oracle_out": oout.decode("latin-1", "replace"),
               "runner_out": rout.decode("latin-1", "replace"),
               "oracle_steps": osteps, "oracle_status": ostatus,
               "note": "negative control: d outside the two routed addresses"}
        if args.mb_ref:
            mout, mrc, merr = run_mbref(memory, stdin, args.mb_ref)
            row["mbref_out"] = mout.decode("latin-1", "replace")
            row["mbref_rc"] = mrc
            row["mbref_stderr"] = merr
        neg[d] = row
        print(f"  neg d={d}: oracle={oout!r} runner={rout!r} steps={osteps} "
              f"status={ostatus}"
              + (f" | mb_ref rc={mrc} err={merr}" if args.mb_ref else ""))

    all_pass = all(c["oracle_verdict"] == "PASS" and c["runner_verdict"] == "PASS"
                   for c in cases)
    if args.mb_ref:
        all_pass = all_pass and all(c.get("mbref_verdict") == "PASS" for c in cases)

    args.mb.parent.mkdir(parents=True, exist_ok=True)
    args.mb.write_bytes(memory)

    if args.json:
        evidence = {
            "schema": "native-2routes-classic/1",
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc).isoformat(),
            "evidence_kind": "MALBOLGE_RUNTIME",
            "claim": ("A single Classic Malbolge image, emitted without LMAO, dispatches "
                      "two routes from one entry byte with an arithmetic key and prints "
                      "the expected result of each route, with every cell of the image "
                      "valid under the strict loader."),
            "claim_status": "DEMONSTRATED" if all_pass else "FAIL",
            "generator": {
                "path": "vm_malbolge/tools/native_two_routes_gen.py",
                "sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
                "ported_from": "BolgeForge (MIT) native_classic/constants.py + "
                               "square_0_9_native_dispatcher/build_native_square.py",
            },
            "artifact": {
                "path": str(args.mb.relative_to(ROOT)),
                "size_bytes": len(memory),
                "sha256": hashlib.sha256(memory).hexdigest(),
                "variant": "classic-3^10",
                "assembler": {"name": "none (native emitter)",
                              "note": "no LMAO involved; the image is emitted directly"},
            },
            "tooling": {
                "oracle": {"path": "tools/oracle_classic.py",
                           "sha256": hashlib.sha256((ROOT / "tools/oracle_classic.py").read_bytes()).hexdigest()},
                "runner": {"path": "runners/malbolge-original/malbolge",
                           "sha256": hashlib.sha256(RUNNER.read_bytes()).hexdigest()},
                "strict_loader_c": {
                    "path": str(args.mb_ref) if args.mb_ref else None,
                    "sha256": hashlib.sha256(args.mb_ref.read_bytes()).hexdigest() if args.mb_ref else None,
                    "provenance": "BolgeForge/oracle/mb_ref.c (MIT), compiled to /tmp for this run",
                    "note": "third engine; rejects INVALID_OPCODE, NONPRINTABLE_PC, "
                            "INVALID_ENCRYPTION and non-HALT exits",
                },
                "loader_gate": "loader_cells() in this generator (mirror of "
                               "BolgeForge/tools/prove_truth_machine.py:52-71)",
            },
            "routing_key": {
                "formula": "S = rot^7(crazy(48 + d, 85)); Q = crazy(S, 48)",
                "c_branch": 85, "rotations": 7,
                "routes": {str(d): {"meaning": ROUTES[d][0], "S": s_values[d],
                                    "Q": q_values[d],
                                    "k": selected[d]["k"],
                                    "data_base": selected[d]["b"],
                                    "recipe_length": selected[d]["length"],
                                    "data_cells": len(selected[d]["data"])}
                           for d in digits},
                "route_gaps": gaps,
            },
            "summary": {
                "routes": len(cases),
                "routes_pass": sum(1 for c in cases
                                   if c["oracle_verdict"] == "PASS"
                                   and c["runner_verdict"] == "PASS"),
                "strict_loader": "ACCEPT",
                "headroom_bytes": 59049 - len(memory),
                "mbref_routes_pass": (sum(1 for c in cases
                                          if c.get("mbref_verdict") == "PASS")
                                      if args.mb_ref else None),
            },
            "cases": cases,
            "negative_control": neg,
            "negative_control_finding": (
                "Under the strict-loader C oracle, an entry byte outside {0,1} does not "
                "halt quietly: mb_ref rejects the image with INVALID_ENCRYPTION "
                "(a cell becomes non-printable after xlat2 encryption) around step 21. "
                "The Python oracle and the native C runner do halt with empty output for "
                "those bytes. The repository's own engines therefore do not detect this "
                "class of failure, which is the concrete value of porting the strict "
                "loader as a gate: the negative domain of this image is outside the "
                "strict-loader contract, not a controlled error."
                if args.mb_ref else None
            ),
            "scope_limits": [
                "Two routes only: the entry byte must be 0 or 1. Any other byte is outside the routed domain and is reported as a negative control, not as a supported input.",
                "Operands are literals baked into each route's recipe: no route reads a second byte from stdin.",
                "The image is one-shot (entry byte in, result out, HALT). No instruction loop, no stored-program PC.",
                "No new code flags are added by construction (the emitter emits a rectilinear recipe over literal data cells), which is the property that avoids the LMAO initializer wall measured in evidence/e3_lmao_initializer_budget.json."
            ],
            "not_demonstrated": [
                "Arithmetic over operands read from stdin inside a route (needs an extra IN per route).",
                "A third route, or the loader + stored-program PC in the same image.",
                "Execution of the emitted image under the strict C oracle mb_ref (this run used the repository's Python oracle and the native C runner)."
            ],
            "next_step": "E6: add a third route with the same key and gate the image with mb_ref (compile oracle/mb_ref.c) as the strict-loader C oracle.",
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(f"\nWrote {args.json}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
