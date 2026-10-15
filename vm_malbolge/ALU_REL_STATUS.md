# Milestone ALU_REL — Unified Relational ALU: ADD (0x02), SUB (0x03) & CMP_EQ (0x04) in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Pure Malbolge Unified Relational ALU (`ADD` 0x02, `SUB` 0x03, `CMP_EQ` 0x04) | `vm_malbolge/src/mbir_alu_rel.hell` + `vm_malbolge/tools/mbir_alu_rel_gen.py` + `vm_malbolge/src/mbir_alu_rel.mb` (size: 57,511 bytes < 59,049 limit, 1,538 bytes headroom) + `vm_malbolge/evidence/mbir_alu_rel_smoke.json` — **DEMONSTRATED 25/25** simultaneous PASS across both canonical Python reference oracle (`tools/oracle_classic.py`) and native C runner (`runners/malbolge-original/malbolge`). |
| Multi-Opcode Arithmetic & Relational Cohabitation | `ADD` (0x02), `SUB` (0x03), and `CMP_EQ` (0x04) running simultaneously within the same binary image without exceeding the strict 59,049-word boundary. |
| Cross-Arithmetic and Relational Chained Expressions | Sequential chained evaluation in a single instruction stream combining arithmetic and relational comparison: `(1 + 1) == 2 -> 1` (`01`), `(1 + 1) == 1 -> 0` (`00`), `(4 - 2) == 2 -> 1` (`01`), `(4 - 2) == 1 -> 0` (`00`), `(4 - 2) == 0 -> 0` (`00`), `(2 + 0) == 2 -> 1` (`01`), `(2 + 0) == 1 -> 0` (`00`), as well as pure arithmetic chains `(1 + 1) - 1 = 1` (`01`), `(1 + 1) - 2 = 0` (`00`), and `(2 - 1) + 1 = 2` (`02`). |
| 100% Bit-Exact Differential Step Parity | Every single test vector terminates with identical step count down to the individual cycle between the C runner and the Python reference oracle across all 25 vectors. |
| 6-Opcode Sequential Dispatch | Sequential zero-cost discrimination for `HALT` (0x00), `PUSH_CONST` (0x01), `ADD` (0x02), `SUB` (0x03), `CMP_EQ` (0x04), and `OUT_BYTE` (0x10) leveraging `SUBROUTINE_FLAG1` and reclaimed `SUBROUTINE_FLAG7`. |
| Zero-Extra-Block Result Mapping | Reuses existing result push logic (`load_diff_1` for 1, `load_diff_0` for 0) and falls through directly to `add_push_common` without allocating redundant data blocks, maintaining LMAO 0.6.0 initialization code compatibility. |

## Unified Relational ALU Verification Vectors (25/25 PASS)

| Vector | Operation / Meaning | Expected Output | Oracle Steps | Runner C Steps | Verdict |
|---|---|---|---|---|---|
| `01 41 10 00` | Baseline 1: PUSH 'A', OUT, HALT | `41` ('A') | 63,937 | 63,937 | **MATCH (PASS)** |
| `01 41 01 42 10 10 00` | Baseline 2: 2-slot LIFO PUSH 'A', PUSH 'B', OUT, OUT, HALT | `42 41` ('BA') | 69,179 | 69,179 | **MATCH (PASS)** |
| `00` | Baseline 3: HALT (immediate) | *(empty)* | 58,689 | 58,689 | **MATCH (PASS)** |
| `01 02 01 03 02 10 00` | ADD $2 + 3 = 5$ | `05` | 73,681 | 73,681 | **MATCH (PASS)** |
| `01 04 01 03 02 10 00` | ADD $4 + 3 = 7$ | `07` | 72,471 | 72,471 | **MATCH (PASS)** |
| `01 01 01 01 02 10 00` | ADD $1 + 1 = 2$ | `02` | 71,976 | 71,976 | **MATCH (PASS)** |
| `01 02 01 00 02 10 00` | ADD $2 + 0 = 2$ | `02` | 71,535 | 71,535 | **MATCH (PASS)** |
| `01 04 01 02 03 10 00` | SUB $4 - 2 = 2$ | `02` | 72,885 | 72,885 | **MATCH (PASS)** |
| `01 02 01 02 03 10 00` | SUB $2 - 2 = 0$ | `00` | 74,098 | 74,098 | **MATCH (PASS)** |
| `01 02 01 01 03 10 00` | SUB $2 - 1 = 1$ | `01` | 72,553 | 72,553 | **MATCH (PASS)** |
| `01 02 01 00 03 10 00` | SUB $2 - 0 = 2$ | `02` | 72,107 | 72,107 | **MATCH (PASS)** |
| `01 01 01 01 02 01 01 03 10 00` | Chained Arith 1: $(1 + 1) - 1 = 1$ | `01` | 80,592 | 80,592 | **MATCH (PASS)** |
| `01 01 01 01 02 01 02 03 10 00` | Chained Arith 2: $(1 + 1) - 2 = 0$ | `00` | 82,137 | 82,137 | **MATCH (PASS)** |
| `01 02 01 01 03 01 01 02 10 00` | Chained Arith 3: $(2 - 1) + 1 = 2$ | `02` | 80,592 | 80,592 | **MATCH (PASS)** |
| `01 02 01 02 04 10 00` | CMP_EQ $2 == 2 \implies 1$ (true) | `01` | 74,530 | 74,530 | **MATCH (PASS)** |
| `01 02 01 01 04 10 00` | CMP_EQ $2 == 1 \implies 0$ (false) | `00` | 72,991 | 72,991 | **MATCH (PASS)** |
| `01 02 01 00 04 10 00` | CMP_EQ $2 == 0 \implies 0$ (false) | `00` | 72,545 | 72,545 | **MATCH (PASS)** |
| `01 04 01 02 04 10 00` | CMP_EQ $4 == 2 \implies 0$ (false) | `00` | 73,323 | 73,323 | **MATCH (PASS)** |
| `01 01 01 01 02 01 02 04 10 00` | Chained Rel 1: $(1 + 1) == 2 \implies 1$ | `01` | 82,569 | 82,569 | **MATCH (PASS)** |
| `01 01 01 01 02 01 01 04 10 00` | Chained Rel 2: $(1 + 1) == 1 \implies 0$ | `00` | 81,030 | 81,030 | **MATCH (PASS)** |
| `01 04 01 02 03 01 02 04 10 00` | Chained Rel 3: $(4 - 2) == 2 \implies 1$ | `01` | 83,478 | 83,478 | **MATCH (PASS)** |
| `01 04 01 02 03 01 01 04 10 00` | Chained Rel 4: $(4 - 2) == 1 \implies 0$ | `00` | 81,939 | 81,939 | **MATCH (PASS)** |
| `01 04 01 02 03 01 00 04 10 00` | Chained Rel 5: $(4 - 2) == 0 \implies 0$ | `00` | 81,493 | 81,493 | **MATCH (PASS)** |
| `01 02 01 00 02 01 02 04 10 00` | Chained Rel 6: $(2 + 0) == 2 \implies 1$ | `01` | 82,128 | 82,128 | **MATCH (PASS)** |
| `01 02 01 00 02 01 01 04 10 00` | Chained Rel 7: $(2 + 0) == 1 \implies 0$ | `00` | 80,589 | 80,589 | **MATCH (PASS)** |

## Differential Bridge Evidence

- `vm_malbolge/evidence/mbir_alu_rel_smoke.json`: Complete 25-vector test suite results with SHA-256 hashes of generator, source, and binary artifacts.
- `vm_malbolge/evidence/artifacts/alu_rel_pass25.mb`: Canonical binary artifact (SHA-256: `3b6c011bf3f8f1c7bb610b99812956d7268719557b81ec7e85d481edf240f977`).
- Source: `vm_malbolge/src/mbir_alu_rel.hell` (SHA-256: `54eb0723027b3e322ab19aa4e45809c4c8574344eb3b945164e452340ec773db`).
- Generator: `vm_malbolge/tools/mbir_alu_rel_gen.py` (SHA-256: `8c1d0fdb4cc07e29c04126dcf49be83b5127f9997dded864470188342337b5ff`).

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Complete Relational Ordering in Unified Image (`CMP_LT`, `CMP_GT`) | While `CMP_LT` and `CMP_GT` are independently demonstrated 12/12 in standalone kernels (`mbir_cmp_lt.mb` and `mbir_cmp_gt.mb`), multiplexing all comparison orders into the unified ALU requires additional code blocks that approach LMAO's memory layout collision boundary. |
| Arbitrary Signed / Negative Arithmetic | Subtractions producing negative results ($a < b$) underflow into Malbolge modulus ($59049$). |
| Multiplication / Division (`MUL`, `DIV`) | Multi-cycle shift-and-add algorithms require iterative quotient registers. |
| In-memory MBIR program loader integration | Combining multi-opcode ALU with Milestone 2 RAM loader in a unified image. |
