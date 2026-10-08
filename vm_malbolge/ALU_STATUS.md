# Milestone Unified ALU — Arithmetic Logic Unit: ADD (0x02) & SUB (0x03) in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Pure Malbolge Unified ALU (`ADD` 0x02 & `SUB` 0x03) | `vm_malbolge/src/mbir_alu.hell` + `vm_malbolge/tools/mbir_alu_gen.py` + `vm_malbolge/src/mbir_alu.mb` (size: 54,691 bytes < 59,049 limit, 4,358 bytes headroom) + `vm_malbolge/evidence/mbir_alu_smoke.json` — **DEMONSTRATED 14/14** simultaneous PASS across both canonical Python reference oracle (`tools/oracle_classic.py`) and native C runner (`runners/malbolge-original/malbolge`). |
| Multi-Opcode ALU Cohabitation | `ADD` (0x02) and `SUB` (0x03) running simultaneously within the same binary image without exceeding the strict 59,049-word boundary. |
| Chained Sequential Arithmetic | Sequential chained expressions across distinct operations in a single instruction stream: `(1 + 1) - 1 = 1` (`01`), `(1 + 1) - 2 = 0` (`00`), and `(2 - 1) + 1 = 2` (`02`). |
| 100% Bit-Exact Differential Step Parity | Every single test vector terminates with identical step count down to the individual cycle between the C runner and the Python reference oracle across all 14 vectors. |
| 5-Opcode Sequential Dispatch | Sequential zero-cost discrimination for `HALT` (0x00), `PUSH_CONST` (0x01), `ADD` (0x02), `SUB` (0x03), and `OUT_BYTE` (0x10) leveraging reclaimed `SUBROUTINE_FLAG1`. |
| Shared Arithmetic Engine | Both operations share Slot 1 pop, Phase 1 decrement, carry reset, Slot 0 pop, Phase 2 decrement, common Slot 0 result push, and Slot 1 reset. |
| 6,486-Byte Dead Code Reclamation | Eliminated 74 lines of obsolete loop logic in `increment_value`, shrinking binary size from 57,511 to 51,025 bytes before opcode multiplexing and yielding 4,358 bytes of net headroom in the unified binary. |
| Single-Test Flag Demultiplexing | Multiplexes 5 distinct arithmetic outcomes ({0, 1, 2, 5, 7}) using existing code flags (`SUBROUTINE_FLAG4..6`, `OP1_FLAG`), testing and clearing each flag exactly once. |

## Unified ALU Verification Vectors

| Vector | Operation / Meaning | Expected Output | Oracle Steps | Runner C Steps | Verdict |
|---|---|---|---|---|---|
| `01 02 01 03 02 10 00` | ADD $2 + 3 = 5$ | `05` | 70,305 | 70,305 | **MATCH (PASS)** |
| `01 04 01 03 02 10 00` | ADD $4 + 3 = 7$ | `07` | 69,095 | 69,095 | **MATCH (PASS)** |
| `01 01 01 01 02 10 00` | ADD $1 + 1 = 2$ | `02` | 68,600 | 68,600 | **MATCH (PASS)** |
| `01 02 01 00 02 10 00` | ADD $2 + 0 = 2$ | `02` | 68,159 | 68,159 | **MATCH (PASS)** |
| `01 04 01 02 03 10 00` | SUB $4 - 2 = 2$ | `02` | 69,509 | 69,509 | **MATCH (PASS)** |
| `01 02 01 02 03 10 00` | SUB $2 - 2 = 0$ | `00` | 70,722 | 70,722 | **MATCH (PASS)** |
| `01 02 01 01 03 10 00` | SUB $2 - 1 = 1$ | `01` | 69,177 | 69,177 | **MATCH (PASS)** |
| `01 02 01 00 03 10 00` | SUB $2 - 0 = 2$ | `02` | 68,731 | 68,731 | **MATCH (PASS)** |
| `01 41 10 00` | Baseline 1: PUSH 'A', OUT, HALT | `41` ('A') | 60,564 | 60,564 | **MATCH (PASS)** |
| `01 41 01 42 10 10 00` | Baseline 2: 2-slot LIFO PUSH 'A', PUSH 'B', OUT, OUT, HALT | `42 41` ('BA') | 65,217 | 65,217 | **MATCH (PASS)** |
| `00` | Baseline 3: HALT (immediate) | *(empty)* | 55,905 | 55,905 | **MATCH (PASS)** |
| `01 01 01 01 02 01 01 03 10 00` | Chained 1: $(1 + 1) - 1 = 1$ | `01` | 77,213 | 77,213 | **MATCH (PASS)** |
| `01 01 01 01 02 01 02 03 10 00` | Chained 2: $(1 + 1) - 2 = 0$ | `00` | 78,758 | 78,758 | **MATCH (PASS)** |
| `01 02 01 01 03 01 01 02 10 00` | Chained 3: $(2 - 1) + 1 = 2$ | `02` | 77,213 | 77,213 | **MATCH (PASS)** |

## Differential Bridge Evidence

- `vm_malbolge/evidence/mbir_alu_smoke.json`: Complete 14-vector test suite results with SHA-256 hashes of generator, source, and binary artifacts.
- `vm_malbolge/evidence/mbir_zig_oracle_alu.json`: Differential verification across Zig VM, Python Oracle, and C Runner on vector `01411000`.

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Arbitrary Signed / Negative Arithmetic | Subtractions producing negative results ($a < b$) underflow into Malbolge modulus ($59049$). |
| Multiplication / Division (`MUL`, `DIV`) | Multi-cycle shift-and-add algorithms require iterative quotient registers. |
| In-memory MBIR program loader | Pre-loading bytecode stream into Malbolge RAM before program dispatch. |
| Control Flow (`JMP`, `JZ`, `CALL`, `RET`) | Branching over an in-memory instruction stream. |
