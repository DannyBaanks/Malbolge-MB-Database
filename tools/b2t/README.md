# B2T0 — Binary ⇄ ternary cell codec

`b2t.py` packs any byte stream into **10-trit cells** and back, with zero loss.

## Why it works

A Malbolge cell holds values `0..59048` (`3^10`).  
A 15-bit group holds values `0..32767` (`2^15`).

Because `2^15 < 3^10`, every 15-bit group fits in one cell:

```text
bits (15) ──► integer 0..32767 ──► cell value 0..59048
```

The cell value is the integer itself; its trits are that integer in base 3.

## Format

The container is a flat binary file:

```text
magic       4 bytes   b"B2T0"
version     1 byte    0
flags       1 byte    0
bit_length  8 bytes   little-endian uint64
word_count  4 bytes   little-endian uint32
crc32       4 bytes   little-endian uint32
payload     word_count * 2 bytes, each cell value as uint16
```

Only cell values `0..32767` are valid payload.  
Values `32768..59048` are **reserved** for a future escape/control layer and are rejected.

## Usage

```bash
# Encode
python3 b2t.py encode input.bin -o input.b2t

# Decode
python3 b2t.py decode input.b2t -o input.restored

# Inspect
python3 b2t.py inspect input.b2t
```

`decode` and `inspect` verify the container’s CRC before returning any data;
`encode` computes and writes it.

## Example

```text
input  = 01020103061000                       # 7 bytes: PUSH 2, PUSH 3, ADD, OUT, HALT
bits   = 56
cells  = 129, 64, 24770, 0
output = 05                                   # dispatch.py run: HALTED, 5 steps
```

## Limitations

- This codec does **not** execute Malbolge.
- It does **not** make data cells valid Malbolge opcodes.
- It adds no compression, no error correction, and no built-in executable meaning.
- Same as MAL-E02: a strict loader like `mb_ref` may reject the resulting data cells because it requires every source cell to encode a valid opcode.

## What this is for

This is the transport layer:

```text
bytes ─► bits ─► 10-trit cells ─► bits ─► bytes
```

It does not decide what those bits mean.  
That belongs to a **dispatcher**: `dispatch.py`, below.

## Dispatcher + trace (`dispatch.py`)

`dispatch.py` gives the transported trits meaning at the boundary: it decodes
the strict B2T0 container, treats the payload as an **MBIR v0** blob, and
executes it on the reference VM (`mbir/mbir_ref.py`) through the backend
contract (`mbir/backends.py`). It adds no opcodes and defines no IR — it is a
consumer of the frozen MBIR contract, and Malbolge still sees only cells.

```text
.b2t ──b2t.decode► MBIR bytes ──mbir_ref (A03 oracle)──► output
```

**Trace bridge** — every VM step reports the exact 10-trit cells whose trits
were dispatched at that step, and every byte reports the cells (and bits inside
them) that carried it:

```text
$ python3 dispatch.py run add.b2t --trace
backend=mbir-ref-python status=HALTED exit_code=0 steps=5
container: 7 bytes in 4 cells (bit_length=56, crc32=0x17499d7c)
output (1 byte): 05
trace:
  #1 pc=0 PUSH_CONST 0x02 bytes=[@0=0x01(#0) @1=0x02(#0,#1)] cells=[#0,#1] stack=[]
  #2 pc=2 PUSH_CONST 0x03 bytes=[@2=0x01(#1) @3=0x03(#1,#2)] cells=[#1,#2] stack=[2]
  #3 pc=4 ADD bytes=[@4=0x06(#2)] cells=[#2] stack=[2, 3]
  #4 pc=5 OUT_BYTE bytes=[@5=0x10(#2,#3)] cells=[#2,#3] stack=[5]
  #5 pc=6 HALT bytes=[@6=0x00(#3)] cells=[#3] stack=[]
```

A byte never spans more than two cells (8 bits vs. a 15-bit chunk), and the
per-step byte slices reassemble through the provenance map alone.

### Usage

```bash
python3 dispatch.py run add.b2t --trace       # execute + per-step trace
python3 dispatch.py run add.b2t --json        # full machine-readable envelope
python3 dispatch.py run echo.b2t --stdin -    # feed stdin bytes to IN_BYTE
python3 dispatch.py disasm add.b2t            # MBIR view with per-instruction cells
python3 dispatch.py provenance add.b2t         # byte <-> cell/bit map
python3 dispatch.py backends                  # registered execution backends
```

Exit codes for `run`: `0` HALTED · `1` ERROR · `2` MAX_STEPS.  
Corrupt containers exit 1 **before any execution**: transport checks
(magic, version, CRC-32, padding, reserved cells) precede semantics.

### Boundaries

- Executes **MBIR semantics only**, on the reference VM (A03 oracle).
- The Malbolge-hosted machines (A04) are one of the two registered
  backends: `a04-malbolge` (section below) alongside `mbir-ref-python`.
- Nothing here turns cell trits into Malbolge opcodes; the dispatcher, not
  Malbolge, is where the trits acquire meaning.

## A04 backend (`a04-malbolge`)

The second registered backend runs the demonstrated MBIR subset on the
**real Malbolge substrate**: the committed machine images under
`vm_malbolge/src/`, driven by the recorded C runner.  The runner binary is
gitignored (`runners/malbolge-original/malbolge`) — build Malbolge-Engine
(`make`) or point `A04_MALBOLGE_RUNNER` at one; the env var is
authoritative, with no silent fallback.

It is capability-honest: it executes exactly the shapes its machines
demonstrate and refuses everything else with an explicit envelope.  Dir
presence ≠ engine.

### Machines and routing

| id | image | evidence | answers |
|----|-------|----------|---------|
| `lifo` | `vm_malbolge/src/mbir_a05_lifo.mb` | `mbir_a05_lifo_smoke.json` (7 vectors) | `P^k O^j` LIFO bodies, alternation k ≤ 2 |
| `multicycle` | `vm_malbolge/src/mbir_a05_multicycle.mb` | `mbir_a05_multicycle_smoke.json` (9 vectors) | strict `(P,O)^k`, k ≥ 3 |

Routing is lifo-first: the older, cheaper image answers every k ≤ 2
shape.  Every executed run asserts byte-and-step dual-engine parity
against `tools/oracle_classic.py`, surfaced as `backend_meta.parity`.

### Capability profile

- Opcodes `{HALT 0x00, PUSH_CONST 0x01, OUT_BYTE 0x10}` only → anything
  else is `UNSUPPORTED_OPCODE` (including legal-MBIR opcodes like `ADD`,
  `POP`, loops — no machine executes them).
- Trailing `HALT` required, nothing after it, evidenced stack shapes only →
  otherwise `UNSUPPORTED_PROFILE`.
- stdin must be empty (the machines consume the program itself from stdin;
  `IN_BYTE` is out of profile) → `UNSUPPORTED_STDIN`.
- `--trace` is refused → `UNSUPPORTED_TRACE`; `mbir-ref-python` provides
  the annotated trace (`trace_supported=False`).
- Truncated or unknown bytes → `UNSUPPORTED_MBIR` (refused at decode).

Errors are envelopes — never a crash — with exit 1; `timeout` maps to
`MAX_STEPS` with exit 2 (steps consumed = budget).

### Budget translation

`max_steps` is MBIR-denominated; the substrate receives
`min(150_000 + 6_500 × max_steps, 4_000_000_000)` Malbolge steps
(600_000 when unset).  The substrate's unit is the Malbolge step, so
consumption inside one MBIR instruction is invisible at MBIR granularity —
a 1-MBIR-step budget still carries in-profile programs to completion.

### Usage

```bash
# from tools/b2t
printf '\001A\020\000' > prog.bin    # PUSH 0x41, OUT, HALT
python3 b2t.py encode prog.bin -o prog.b2t
python3 dispatch.py run --backend a04-malbolge --json prog.b2t
```

The bridge evidence record is
`vm_malbolge/evidence/mbir_a04_backend_bridge.json` — regenerate with
`python3 tools/b2t/a04_probe.py`; the probe refuses to write unless every
expectation holds.
