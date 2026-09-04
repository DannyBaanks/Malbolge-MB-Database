"""A04C substrate adapter: use the real CoEvo engine's substrate as a library.

This file does NOT copy CoEvo code; it imports `substrate.py` from the
original location via importlib. If the reference path moves, the experiment
fails loudly. That failure is the point (no hidden divergence).

We reuse exactly the public surface the engine documents:
  read_cells(), write_cells(), decode_rule(), encode_rule(),
  step(), evolve(), signature_index(), OFFSETS

Everything on top of that is experimental A04C code that lives in this repo.
"""
from __future__ import annotations
import importlib.util
import json
import os
import sys
from pathlib import Path

# Path to the CoEvo substrate. REQUIRED: the host sets MB_COEVO_SUBSTRATE
# (or COEVO_MB_DERIVE) to the directory containing substrate.py before
# running A04C experiments. The dependency is deliberately explicit —
# no hidden defaults-to-local-machine paths.
COEVO_PARENT = os.environ.get(
    "MB_COEVO_SUBSTRATE",
    os.environ.get("COEVO_MB_DERIVE", "")
).strip()

if not COEVO_PARENT:
    raise EnvironmentError(
        "A04C requires MB_COEVO_SUBSTRATE (or COEVO_MB_DERIVE) pointing at the "
        "directory containing the CoEvo engine's substrate.py"
    )

COEVO_PARENT = os.path.abspath(COEVO_PARENT)

def load_engine():
    mod_path = Path(COEVO_PARENT) / "substrate.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"CoEvo substrate not found at {mod_path}")
    spec = importlib.util.spec_from_file_location("coevo_substrate", mod_path)
    substrate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(substrate)
    return substrate


# --- A04C mechanics built on top of the substrate --------------------------------

BYTE_LANE_Y = 1     # data-lane u-coordinate
CTRL_LANE_Y = 10    # control lane
MARKER_Z = 5        # register plane marker plane


def encode_byte(v: int, x0: int = 0, y: int = BYTE_LANE_Y, z: int = 0, t: int = 0) -> set:
    """Encode 8 bits as live cells: bit i at (x0, y, z=2*i, t).

    Each bit occupies its own z-plane (separated by distance 2), so no two
    live cells are ever von- Neumann neighbors; a "move ahead +x" rule then
    transports each bit independently.
    """
    cells = set()
    for i in range(8):
        if (v >> i) & 1:
            cells.add((x0, y, z + 2 * i, t))
    return cells


def decode_byte(cells, x0: int = 0, y: int = BYTE_LANE_Y, z: int = 0, t: int = 0) -> int:
    """Recover the byte: test (x0, y, z+2i, t) for each bit i."""
    v = 0
    for i in range(8):
        if (x0, y, z + 2 * i, t) in cells:
            v |= 1 << i
    return v


def encode_token(x: int, y: int = CTRL_LANE_Y, z: int = 0, t: int = 0) -> set:
    return {(x, y, z, t)}


def find_token(cells, y: int = CTRL_LANE_Y, z: int = 0, t: int = 0):
    """Return the x of the control token alive on the control lane, else None."""
    found = [x for (x, yy, zz, tt) in cells if yy == y and zz == z and tt == t]
    return sorted(found)


def full_register_state(pc: int, value: int, out_bytes: list[int], halted: bool,
                        x_base: int = 0) -> set:
    """Encode a complete MBIR-visible state snapshot as cells.

    Memory plane (z=0, y=BYTE_LANE_Y): the program bytes stored at two cells
    per MBIR slot using a fixed 8-wide value window starting at
    ``data_base_x`` (we re-uuse PC as index, multiply by slot width).
    """
    cells = set()
    # PC as x offset on the control line, value as wire byte.
    # Layout for value wire: at x = x_base + 0..7
    cells |= encode_byte(value, x_base + 0, y=BYTE_LANE_Y)
    cells |= encode_token(x_base + pc, y=CTRL_LANE_Y)
    return cells


def project_state(cells, x_base: int = 0):
    """Read back pc and value from a live-cell state."""
    pc_cells = find_token(cells, y=CTRL_LANE_Y, z=0, t=0)
    pc = (pc_cells[0] - x_base) if pc_cells else None
    value = decode_byte(cells, x_base)
    return {"pc": pc, "value": value, "tokens": pc_cells}
