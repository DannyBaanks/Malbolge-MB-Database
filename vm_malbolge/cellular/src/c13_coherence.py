"""A04C coherence metrics — real measurements only.

REPORTS CELLULAR_TRACES, not VM claims. No votes are made for Malbolge-side
semantic interpretations of CA dynamics.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from coevo_adapter import load_engine, encode_byte

ENGENE = load_engine()
OFFSETS = ENGENE.OFFSETS
RULE = frozenset({2})


def count_links(live):
    bits = 0
    for cell in live:
        seen = 0
        for dx, dy, dz, dt in OFFSETS:
            if (cell[0]+dx, cell[1]+dy, cell[2]+dz, cell[3]+dt) in live:
                seen += 1
        bits += seen
    return bits


def run_trace(byte=65, ticks=8):
    eng = ENGENE
    init = encode_byte(byte)
    trace = eng.evolve(init, RULE, ticks)
    counts = [len(s) for s in trace]
    linkages = [count_links(s) for s in trace]
    stable = all(counts[i] == counts[0] for i in range(len(counts)))
    return {
        "byte_in": byte,
        "ticks": ticks,
        "cells_start_end": [counts[0], counts[-1]],
        "counts_per_tick": counts,
        "intra_tick_links": linkages,
        "invariant_cell_count": stable,
    }


def main():
    r1 = run_trace(65)
    r2 = run_trace(66)
    # invariant means: the number of live cells remains constant over the ticks.
    # Since encoding preserves bit count, both bytes are 2-cell (bits 0 and 6).
    ok = r1["invariant_cell_count"] and r2["invariant_cell_count"]
    print(json.dumps({
        "call_1": {"byte": 65, "final_count": r1['counts_per_tick'][-1]},
        "call_2": {"byte": 66, "final_count": r2['counts_per_tick'][-1]},
        "invariant": ok,
        "metric_class": "preserve_count_single_lane_mover",
    }, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
