# Milestone M2 Native — first Classic image emitted without LMAO

## Status: DEMONSTRATED (2 routes)

`vm_malbolge/src/mbir_native_2routes.mb` is a single Classic (3^10) Malbolge
image, **28,478 bytes** (headroom 30,571 under the 59,049 limit), emitted
directly by a Python generator — **no LMAO involved, no HeLL source**.

It dispatches two routes from one entry byte with an arithmetic key:

| entry byte | route | prints | oracle | runner C | mb_ref (strict) |
|---|---|---|---|---|---|
| `0` | ADD 2 + 3 | `5\n` | PASS | PASS | rc=0, `5` |
| `1` | CMP_EQ 2 == 2 | `1\n` | PASS | PASS | rc=0, `1` |

Both routes also pass the strict-loader gate: **every cell of the image
decodes to one of `ji*p</vo` at its own load address** (`loader_cells()` in the
generator, mirroring `BolgeForge/tools/prove_truth_machine.py:52-71`), and the
compiled C strict oracle accepts and executes both routes.

## Why this matters for the unified image (b)

Milestone M2 was blocked because LMAO's initializer runs out of room.
Experiment E3 (`vm_malbolge/evidence/e3_lmao_initializer_budget.json`) measured
that the wall is **new code flags, not data cells**: on `mbir_alu.hell`, 64 data
cells still assemble (57,229 B) while the 4th new code flag already fails.

The native emitter needs **no new code flags** — it emits a rectilinear recipe
over literal data cells, exactly the dimension E3 measured as cheap. And
experiment E4-bis (`vm_malbolge/evidence/e4bis_dispatch_packing.json`) measured
that the routing key `S = rot^7(crazy(48+d, 85)); Q = crazy(S, 48)` yields
**10 distinct route addresses** for `d = 0..9` with a minimum gap of 27 cells,
which is the per-route arena of the emitter.

This image is the first concrete proof that the hybrid path for (b) is real:
arithmetic and comparison routes emitted natively, loader/PC kept with LMAO.

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Operands read from stdin inside a route | Each route is a fixed rectilinear recipe over literal data cells; the emitter does not yet express an extra `IN` per route. The operands are literals baked into the recipe. |
| More than two routes | Only `d ∈ {0,1}` is routed. A third route is experiment E6. |
| Loader + stored-program PC in the same image | Not attempted here; this image is one-shot. |
| Clean failure outside the routed domain | Under the strict-loader oracle, `d ∈ {2,5}` is **not** a controlled error: `mb_ref` rejects the image with `INVALID_ENCRYPTION` (a cell becomes non-printable after xlat2 encryption) around step 21, while the Python oracle and the native C runner halt quietly with empty output. The negative domain is outside the strict-loader contract. |
| CMP_LT / CMP_GT over operands ≥ 3 | Unrelated to this image; see `ATTACK_PLAN_2026-11-06.md`. |

## Toolchain and provenance

- Generator: `vm_malbolge/tools/native_two_routes_gen.py`
- Encoding primitives: `vm_malbolge/tools/native_classic/constants.py`,
  **ported verbatim from `BolgeForge/constants.py` (MIT, Copyright (c) 2026
  ISyCo Contributors)**.
- Routing/dispatch/recipe architecture adapted from
  `BolgeForge/experiments/square_0_9_native_dispatcher/build_native_square.py`
  (same MIT license). No LMAO-derived code is used.
- Engines used to verify: `tools/oracle_classic.py`,
  `runners/malbolge-original/malbolge`, and the strict-loader C oracle
  `BolgeForge/oracle/mb_ref.c` (MIT, compiled to `/tmp` for this run).
- Evidence: `vm_malbolge/evidence/native_2routes_build.json`.

## Reproduce

```
python3 vm_malbolge/tools/native_two_routes_gen.py \
    --mb-ref /path/to/mb_ref
```
