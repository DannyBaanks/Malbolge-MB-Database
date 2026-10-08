# Milestone P1 — Arithmetic Kernel: SUB (Opcode 0x02) in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Pure Malbolge Subtraction Kernel (`SUB` 0x02) | `vm_malbolge/src/mbir_p1_sub.hell` + `vm_malbolge/tools/mbir_p1_sub_gen.py` + `vm_malbolge/src/mbir_p1_sub.mb` (size: 57,511 bytes < 59,049 limit) + `vm_malbolge/evidence/mbir_p1_sub_smoke.json` — **DEMONSTRATED 7/7** simultaneous PASS across both canonical Python reference oracle (`tools/oracle_classic.py`) and native C runner (`runners/malbolge-original/malbolge`). |
| 100% Bit-Exact Differential Step Parity | Every single test vector terminates with identical step count down to the individual step between the C runner and the Python reference oracle (Vector 1 at 79,593 steps, Vector 2 at 81,139 steps, Vector 3 at 79,270 steps, Vector 4 at 78,724 steps). |
| 2-Phase Subtraction Engine | Evaluates binary subtraction $a - b$ in LIFO order: pops subtrahend $op_2 = b$ from Slot 1, decrements/classifies $op_2 \in \{0, 1, 2\}$, transitions through clean carry reset into Phase 2 when necessary, pops minuend $op_1 = a$ from Slot 0, evaluates exact difference $a - b$, and pushes result back into Slot 0 while resetting Slot 1 to empty. |
| Subtraction Algebraic Properties Verified | - Zero subtraction identity: $2 - 0 = 2$ (`02`)<br>- Predecessor subtraction: $2 - 1 = 1$ (`01`)<br>- Nilpotence / self-subtraction: $2 - 2 = 0$ (`00`)<br>- Multi-unit reduction: $4 - 2 = 2$ (`02`). |
| Zero-Extra-Flag Multiplexing | Uses strictly 6 code flags (`CLEAN_FLAG`, `ADD_FLAG`, `OP1_FLAG`, `SUBROUTINE_FLAG4..6`), fitting completely under the 59,049-word boundary with 1,538 bytes of headroom remaining. |

## Milestone P1 Verification Vectors

| Vector | Meaning | Expected Output | Oracle Steps | Runner C Steps | Verdict |
|---|---|---|---|---|---|
| `01 04 01 02 02 10 00` | Vector 1: SUB $4 - 2 = 2$ | `02` | 79,593 | 79,593 | **MATCH (PASS)** |
| `01 02 01 02 02 10 00` | Vector 2: SUB $2 - 2 = 0$ | `00` | 81,139 | 81,139 | **MATCH (PASS)** |
| `01 02 01 01 02 10 00` | Vector 3: SUB $2 - 1 = 1$ | `01` | 79,270 | 79,270 | **MATCH (PASS)** |
| `01 02 01 00 02 10 00` | Vector 4: SUB $2 - 0 = 2$ | `02` | 78,724 | 78,724 | **MATCH (PASS)** |
| `01 41 10 00` | Baseline 1: PUSH 'A', OUT, HALT | `41` ('A') | 67,167 | 67,167 | **MATCH (PASS)** |
| `01 41 01 42 10 10 00` | Baseline 2: 2-slot LIFO PUSH 'A', PUSH 'B', OUT, OUT, HALT | `42 41` ('BA') | 74,204 | 74,204 | **MATCH (PASS)** |
| `00` | Baseline 3: HALT (immediate) | *(empty)* | 60,124 | 60,124 | **MATCH (PASS)** |

## Differential Bridge Evidence

- `vm_malbolge/evidence/mbir_p1_sub_smoke.json`: Complete 7-vector test suite results with SHA-256 hashes of generator, source, and binary artifacts.
- `vm_malbolge/evidence/mbir_zig_oracle_p1_sub.json`: Differential verification across Zig VM, Python Oracle, and C Runner on the baseline vector `01411000`.

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Arbitrary Signed / Negative Arithmetic | Subtractions producing negative results ($a < b$) underflow into Malbolge modulus ($59049$). |
| Multi-Opcode ALU Cohabitation | Having both `ADD` and `SUB` active simultaneously within a single binary without exceeding 59,049 words. |
| In-memory MBIR program loader | Pre-loading bytecode stream into Malbolge RAM before program dispatch. |
| Control Flow (`JMP`, `JZ`, `CALL`, `RET`) | Branching over an in-memory instruction stream. |
