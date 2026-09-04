"""A04C/ held-out + determinism + control tests.

These exist to prevent cherry-picking: the same fixed cellular rule must
(a) transport values that were never used in design,
(b) produce identical traces across replays,
(c) fail when an essential neighbor-link is scrambled.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from coevo_adapter import load_engine, encode_byte, decode_byte, encode_token
ENGENE = load_engine()
RULE = frozenset({2})


def run_cellular_once(byte, ticks=8):
    eng = ENGENE
    cells = encode_byte(byte)
    out = eng.evolve(cells, RULE, ticks)
    last = out[-1]
    moved = {(x - ticks, y, z, t) for (x, y, z, t) in last}
    recovered = decode_byte(moved)
    trace_hash = hashlib.sha256(
        json.dumps([sorted(list(s)) for s in out], default=str, sort_keys=True).encode()
    ).hexdigest()
    return {"recovered": recovered, "trace_hash": trace_hash, "out_count": len(last)}


def test_replay():
    """Determinism: run the same input+rule+ticks twice and compare hashes."""
    r1 = run_cellular_once(65)
    r2 = run_cellular_once(65)
    ok = r1["trace_hash"] == r2["trace_hash"]
    return {"ok": ok, "hash1": r1["trace_hash"], "hash2": r2["trace_hash"]}


def test_heldout():
    """Values we did NOT use during design: must transport exactly."""
    heldout_values = [3, 7, 127, 200, 254, 255]
    ok = True
    results = []
    for v in heldout_values:
        r = run_cellular_once(v)
        got = r["recovered"] == v
        ok = ok and got
        results.append({"value": v, "recovered": r["recovered"], "ok": got})
    return {"ok": ok, "cases": results}


def test_negative_control():
    """If the rule mapping is broken, the pipeline must FAIL."""
    eng = ENGENE
    cells = encode_byte(65)
    # Broken rule: wrong signatures (rotate offsets by one) — this must fail.
    bad_rule = frozenset({1 << 7})  # decade-signal neighbor only
    out = eng.evolve(cells, bad_rule, 8)
    last = out[-1]
    moved = {(x - 8, y, z, t) for (x, y, z, t) in last}
    recovered = decode_byte(moved)
    broken = recovered != 65
    return {"ok": broken, "recovered": recovered}


if __name__ == "__main__":
    rp = test_replay()
    ho = test_heldout()
    nc = test_negative_control()
    print(f"replay:  {'PASS' if rp['ok'] else 'FAIL'}")
    for c in ho["cases"]:
        print(f"heldout {c['value']:>3} -> {c['recovered']:>3} {'OK' if c['ok'] else 'FAIL'}")
    print(f"heldout: {'PASS' if ho['ok'] else 'FAIL'}")
    print(f"negctl:  {'PASS' if nc['ok'] else 'FAIL'}")
    verdict = rp["ok"] and ho["ok"] and nc["ok"]
    print("OVERALL:", "PASS" if verdict else "FAIL")
    sys.exit(0 if verdict else 1)
