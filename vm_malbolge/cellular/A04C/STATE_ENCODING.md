# A04C — VM_STATE ↔ CELLULAR_STATE encoding (concrete, mechanical)

This document fixes one exact mapping used in the experiment. No metaphors.

## Coordinate roles

| Axis | Use |
|------|-----|
| `x` | spatial conveyor (patterns move toward +x per tick) |
| `y` | lane separation for distinct logical wires |
| `z` | "register plane" — data carries vs markers |
| `t` | fresh dimension for staging/extra lanes |

All cells are integer lattice points. Higher x = later in "execution".

## Byte encoding (BYTE_ON_WIRE v0)

A byte `v` (0..255) is eight live cells:

```
cell_i = (base_x + i, y_lane, z, t)
     where   bit = (v >> i) & 1  decides if cell_i is alive
             i  runs 0 (LSB) to 7 (MSB)
             `1` => cell present; `0` => absent
```

A single contiguous wire is 8 x-positions wide. Multiple wires can stack at
different `(y, z)`.

Liveness = "1-cardinality" over the wire: value determined by which of the
eight cells are live.

## Control token (CONTROL_TOKEN v0)

A separate single live cell (not part of `BYTE_ON_WIRE`) that moves in the
x-direction through the instruction lane:

```
control_cell = (instr_base_x + k * SLOT_WIDTH, y_instr, z_instr, t)
```

When the token sits in slot `k` (at instruction index k), that instruction
is "active".

## Register / marker states

Minimal registers are modeled with marker cells on fixed columns:

- `halted`: a live cell at `HALT_MARKER = (0, HALT_Y, HALT_Z, 0)` means the
  program has halted. Absence = still running.

## Program (MBIR bytes)

The immutable MBIR program is laid out at fixed addresses in a read-only
memory plane, one byte per 8 cells on the "+x increasing" memory wire. The
program does not move — the control token moves through it.

Bootstrapping is done entirely in the initial `.cells4d` state for M0.

## Round-trip test

The encoding proves itself by encoding -> decode must equal identity. This
is a **host-side check** over stored shows only — the CA must not build the
answer.

## Notes / constraints admitted openly

- This treats the CA as a conveyor belt. Nothing yet proves it can make any
  computation happen.
- The substrate does not carry integers; every sampled "value" is encoding
  matter, not physics.
