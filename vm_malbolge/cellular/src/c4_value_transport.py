"""A04C/C4 — value-transport probe.

Question under test:
  Can a byte live-cell pattern be moved in +x by one step per tick
  under a fixed signature rule without using host computations of the
  answer?

Construction (no invented physics):
  Rule {2} means: a dead cell with its DIRECT -x neighbor alive becomes
  alive; an alive cell drops only if its signature isn't active.
  Applying {2} moves any isolated live cell one x step per tick.
  Verify on t=1 and embed the byte data as a window of 8 cells.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coevo_adapter import load_engine, encode_byte, decode_byte

ENGENE = load_engine()
OFFSETS = ENGENE.OFFSETS


def make_mover_rule():
    """Active signature set = {2}, i.e. dead cell with its -x neighbor alive.

    Signature notation: bit index i corresponds to OFFSETS[i].
    offsets[0] = (+1,0,0,0), offsets[1] = (-1,0,0,0).
    A dead cell with just its -x neighbor alive gets index 1<<1 = 2.
    """
    dead_with_west = frozenset({1 << 1})
    return dead_with_west


def experiment(per_step: int = 8, ticks: int = 8, plus_x_per_tick: int = 1):
    """Take the 8-bit test vector x, put it on a wire, run mover rules, collect.

    Bits live on separate z-planes (spacing=2). A mover rule {2} births a
    dead cell whose -x neighbor is alive; alive cells die when their own
    signature isn't in the rule. Each bit's plane is independent.
    """
    results = []
    rule = make_mover_rule()

    for vector in [0x00, 0x01, 0x02, 0x03, 0x2A, 0x41, 0x7F, 0x80, 0xFF]:
        cells = encode_byte(vector, x0=0, y=0, z=0)
        out = ENGENE.evolve(cells, rule, ticks)
        # After T ticks, content should sit T units further in +x.
        moved_cells = set()
        for (x, y, z, t) in out[-1]:
            moved_cells.add((x - ticks, y, z, t))
        recovered = decode_byte(moved_cells, x0=0, y=0, z=0)
        ok = recovered == vector
        results.append({
            "input": vector,
            "final_cells": sorted(out[-1]),
            "recovered": recovered,
            "ok": ok,
        })
    return results


if __name__ == "__main__":
    out = experiment()
    fail = [r for r in out if not r["ok"]]
    for r in out:
        print(
            f"in={r['input']:>3} -> recovered={r['recovered']:>3} ok={r['ok']}",
            f"(stored {len(r['final_cells'])} cells)"
        )
    print("VALUE_TRANSPORT:", "PASS" if not fail else f"FAIL ({len(fail)} bad)")
    sys.exit(0 if not fail else 1)
