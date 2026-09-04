# A04C — CoEvo Substrate Audit (COEVO_SUBSTRATE_UNDERSTOOD)

Date of audit: 2026-09-03.  
Scope: ONLY what the code on disk actually does.  
Source audited: the coevo_mu_genesis_gpt CoEvo engine (path supplied by
env `MB_COEVO_SUBSTRATE`), typically a sibling checkout of this repo.

## Substrate mechanics (from `substrate.py`, verified by reading)

| Property | What the code does |
|----------|--------------------|
| Grid | Z^4 (infinite 4-D integer lattice). Points are plain tuples. |
| State | Binary (alice=live/dead). A `live` set holds coordinates; everything else is dead. |
| Neighborhood | Von Neumann, radius 1, 4-D: 8 offsets `(±1,0,0,0),(0,±1,0,0),(0,0,±1,0),(0,0,0,±1)`. |
| Local signature | `sign_index = (256 if self_live else 0) + (mask of 8 neighbor bits)`. Range 0..511. |
| Rule format | A subset of {0..511} (active set) held as a 4x4x4x8 lattice of live "rule cells". |
| Update | Synchronous, one tick: new_live = frontier(cells) ∩ {c : sign(c) in active}, where frontier = live + its neighbor offsets. |
| Initialization | A `.cells4d` text file listing live-cell coordinates (one per line). |
| Boundary | None — Z^4 is open; cells with no live neighbors do not persist. |
| Toroidal wrap | NOT PRESENT. No wraparound. |
| Stopping | None —`evolve()` just runs N ticks; no error state, no halt detector. |
| Determinism | Deterministic given (initial live set, active rule, tick count). `substrate.py` has no randomness. |

## What the "genesis" engine actually found

From `genesis.py` + `verify.py`, verified by reading and by running (`verify.py` →
`FINAL=PASS`):

- Fitness target: evolve a fixed 4-cell witness (x=0, cells at (0,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1)) into exactly two copies at x=±2 after 2 ticks.
- Resulting rule after ablation: **two** 4x4x4x8 miniature active cells = 2 signatures in the 512-set.
- A single-live-cell atom (at origin) splits into exactly two child live cells on tick 1. Witness: `atom.cells4d` → `atom_t1.cells4d`.
- `substrate.py` does not contain arithmetic, PC, memory-table, branching on values, or IO.

## What this substrate is NOT

- Not a general-purpose computer substrate. There is no encoded "value" other
  than live/dead and position.
- Not a proven VM host. No counter, no stack, no address arithmetic, no
  input-from-bytes, no comparison-to-constant.
- Not a Malbolge translator. There is no pathway shown between a Malbolge
  memory word and a `.cells4d` state that preserves UPDATE semantics.

## What is transferable for A04C

- The substrate engine **as a library**: `read_cells`, `write_cells`, `decode_rule`,
  `encode_rule`, `step`, `evolve`, `signature_index`, `OFFSETS`.
- Explicit deterministic replay of any `(initial, rule, ticks)` triple.
- A small searchable signature space (512 signatures per rule; search over them
  is feasible in Python — done already in `genesis.py` with a hill-climber).

## Limitations that bind A04C

- **No value state** inside a single cell. To carry a byte you would need to
  encode it across a PATTERN of live cells — and then test transport.
- **No dynamic indexing.** There is no "go to cell whose address equals a
  variable" — addresses are an abstract Z^4, not a memory array with ALU.
- **Rules are static.** We cannot change the rule mid-run based on opcode.
  Mid-run rule changes would be host-side interference (explicitly forbidden).

## Verdict

```text
COEVO_SUBSTRATE_UNDERSTOOD = DEMONSTRATED
```
