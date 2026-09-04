"""A04C/C7-gate probe: prove that a data bit only moves forward when a
control token is present at the aligned position.

Design under test:
- Data lane: cells at (x, y=0, z=0, t=0) — x is the "byte lane" dimension.
- Control lane: cells at (x, y=1, z=0, t=0) — one axis north of data.

With the rule {2} alone, every live cell shifts +1 x per turn. For a gate
we add signatures that depend on the token being aligned:
  signature = 256*self_alive + sum over OFFSETS of active bits per offset.
  Offset list (substrate): bit i = OFFSETS[i]. So offsets are:
      0: (+1,0,0,0), 1: (-1,0,0,0), ..., bit for direction (0,+1,0,0) = 4,
      (0,-1,0,0) = 8.

Rule: gate_rule = { ? } chosen so birth only happens when data cell has
a control cell directly north (y+1), i.e. bit for (0,+1,0,0) is set.

Concretely: a dead data cell whose *west* neighbor is alive and whose
*north* neighbor (token lane) is alive must come alive. Its signature is:
 mask = west-neighbor bit (OFFSETS idx 1 -> bit 1<<1=2) |
        north-neighbor bit (OFFSETS idx 2 -> bit 1<<2=4)
 signature = 2 | 4 = 6 (with the dead self-cell legacy bit 8=off).

So the gate rule for a y=0 data flow gated by a y=1 control cell is:
    ACTIVE_RULE = { 6 }

Test:
  Move exactly one live byte through data lane ONLY when a token sits on
  the same x-coordinate on the control lane.
  Case 1: token at x_tok=2 — fetches x=2 ground state alive only; the byte
          at x=0 never progresses (because token not aligned with it at t=0).
  Case 2: token at x_tok=0  — the byte moves to x=1 because control aligned.

If the gate works, byte does NOT move in case 1 but *does* move in case 2.
Negative control included: run with token at x=999 (unreachable gate), and
the data must remain still.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from coevo_adapter import load_engine, encode_byte, decode_byte, encode_token

ENGENE = load_engine()

OFFSETS = ENGENE.OFFSETS
# Signature bit indices: bit i corresponds to OFFSETS[i]
WEST_BIT = 1 << 1  # (-1,0,0,0)
NORTH_BIT = 1 << 2 # (0,+1,0,0)

GATE_RULE = frozenset({ WEST_BIT | NORTH_BIT })  # birth only if west+north live


def emit_state(with_token_at=None, data_x_positions=(0,)):
    """Produce an initial live set with data bits at given x and an
    optional token at `with_token_at`.
    """
    cells = set()
    for dx in data_x_positions:
        cells.add((dx, 0, 0, 0))
    if with_token_at is not None:
        cells.add((with_token_at, 1, 0, 0))
    return frozenset(cells)


def x_positions(cells):
    return sorted({x for (x, y, z, t) in cells})


def run_case(name, with_token_at, data_x_positions, ticks=3):
    init = emit_state(with_token_at, data_x_positions)
    out = ENGENE.evolve(init, GATE_RULE, ticks)
    final_xs = x_positions(out[-1])
    return {"name": name, "init_x_control": with_token_at,
            "data_x_positions": list(data_x_positions),
            "final_live_x": final_xs,
            "tick_count": len(out)-1}


CASES = [
    # aligned token: data bit should move when token adjacent to data's next x
    {"name": "control_aligned",  "with_token_at": 1, "data_x_positions": [0], "ticks": 1},
    # misaligned token: token with x=100 can't help x=0 move
    {"name": "control_far",      "with_token_at": 100, "data_x_positions": [0], "ticks": 5},
    # no token at all
    {"name": "control_absent",   "with_token_at": None, "data_x_positions": [0], "ticks": 5},
]


def main():
    oks = []
    for case in CASES:
        r = run_case(**case)
        print(r)
        if case["name"] == "control_aligned":
            # data must have moved from 0 -> 1
            ok = 1 in r["final_live_x"] and 0 not in r["final_live_x"]
        else:
            # data cannot move: stays at 0 forever
            ok = r["final_live_x"] == [0] or r["final_live_x"] == []
        oks.append((r["name"], ok))
        print(f"{r['name']}: {'PASS' if ok else 'FAIL'}")

    if all(ok for _, ok in oks):
        print("GATE_TEST: PASS")
        return 0
    print("GATE_TEST: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
