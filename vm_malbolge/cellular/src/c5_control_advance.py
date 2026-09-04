"""A04C/C5 — control token advance.

Question: does a single-cell token move forward by a fixed amount per tick
under the fixed rule {2} on the control lane, with no host intervention to
choose the next active slot?

We encode the token as a single live cell (the same primitive that already
moves bytes). If the token starts at x=0 and survives to end at x=ticks,
admission is mechanical (no "if PC should advance" logic on the host side).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coevo_adapter import load_engine, encode_token, find_token

ENGENE = load_engine()

def rule():
    return frozenset({2})  # same unit mover

def experiment(program_len: int = 6, ticks: int = 6):
    eng = ENGENE
    out = eng.evolve(encode_token(0), rule(), ticks)
    tokens = sorted(find_token(out[-1]), key=lambda p: p)
    expected = [ticks]
    success = tokens == expected
    return {
        "program_len": program_len,
        "ticks": ticks,
        "tokens_final": tokens,
        "expected": expected,
        "success": success,
    }


if __name__ == "__main__":
    r = experiment()
    print(f"rule={sorted(rule())}, ticks={r['ticks']}")
    print(f"  tokens: <initial> {r['expected']} -> final {r['tokens_final']}")
    if r["success"]:
        print("CONTROL_ADVANCE: PASS")
        sys.exit(0)
    print("CONTROL_ADVANCE: FAIL")
    sys.exit(1)
