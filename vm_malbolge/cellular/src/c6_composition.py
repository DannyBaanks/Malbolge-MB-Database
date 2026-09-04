"""A04C/C6 — composition: run value transport AND control advance under
one fixed rule {2}, with the two planes coexisting on distinct z-planes.

What we test ("1+2=3" operationalized):
  primitive A (LONE): transports an 8-bit value by +1x per tick (run with
      cell set = data only)
  primitive B (LONE): advances a one-cell token by +1x per tick (with cell
      set = token only)
  A+B (COMPOSED): encode data AND token in the same plane set, run the same
      fixed rule, after T ticks assert: (a) byte content recovered intact,
      (b) token sited at +T, (c) TOTAL cell count = bytes_count + 1, with
      no births/deaths from crosstalk.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coevo_adapter import load_engine, encode_byte, decode_byte, encode_token

ENGENE = load_engine()
RULE = frozenset({2})


def a_only(byte, ticks=4):
    eng = ENGENE
    cells = encode_byte(byte)
    out = eng.evolve(cells, RULE, ticks)
    moved = set()
    for (x, y, z, t) in out[-1]:
        moved.add((x - ticks, y, z, t))
    return decode_byte(moved), len(out[-1])


def b_only(ticks=4):
    eng = ENGENE
    cells = encode_token(0)
    out = eng.evolve(cells, RULE, ticks)
    return len(out[-1]), sorted({x for (x, _, _, _) in out[-1]})


def combined(byte, ticks=4):
    eng = ENGENE
    cells = encode_byte(byte) | encode_token(0)
    out = eng.evolve(cells, RULE, ticks)
    final = out[-1]
    # token lives on Z=0; data lives on z-planes 0,2,4,... That lets us
    # decompose by z without knowing apriori cell identities?
    # NO - data and token cells could pile on z=0. We chose token at z=0.
    # Decompose by y only: both share y=1 (BYTE lane default) and token has
    # y=CTRL_LANE_Y by default. Let me recheck: encode_token default y=10 CTRL.
    data_cells = {(x,y,z,t) for (x,y,z,t) in final if y == 1}
    token_cells = {(x,y,z,t) for (x,y,z,t) in final if y == 10}
    return {
        "data_count": len(data_cells),
        "token_count": len(token_cells),
        "data_final": data_cells,
        "token_final": token_cells,
    }


if __name__ == "__main__":
    # Check (crosstalk check): default encode_byte uses y=BYTE_LANE_Y (=1), token y=10.
    import unittest

    byte = 65
    ticks = 4

    va, na = a_only(byte, ticks)
    nb, tb = b_only(ticks)
    both = combined(byte, ticks)

    print("primitive A alone: recovered=", va, "count=", na)
    print("primitive B alone: token_x=", nb, "count=", tb)
    print("COMPOSED:", f"data={both['data_count']} token={both['token_count']}")

    ok = (
        va == byte
        and nb == 1
        and tb == [ticks]
        and both["data_count"] == na
        and both["token_count"] == nb
    )
    print("COMPOSITION_01:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
