# Milestone P2 — Comparison Kernel: CMP_EQ in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Pure Malbolge Comparison Kernel (`CMP_EQ` Opcode 0x02) | `vm_malbolge/src/mbir_p2_cmp.hell` + `vm_malbolge/tools/mbir_p2_cmp_gen.py` + `vm_malbolge/src/mbir_p2_cmp.mb` (size: 57,511 bytes < 59,049 limit, 1,538 bytes headroom) + `vm_malbolge/evidence/mbir_p2_cmp_smoke.json` — **DEMONSTRATED 7/7** simultaneous PASS across both canonical Python reference oracle (`tools/oracle_classic.py`) and native C runner (`runners/malbolge-original/malbolge`). |
| 100% Bit-Exact Differential Step Parity | Every single test vector terminates with identical step count down to the individual step between the C runner and the Python reference oracle (Vector 1 at 81,069 steps, Vector 2 at 79,200 steps, Vector 3 at 78,654 steps, Vector 4 at 79,523 steps). |
| 2-Phase Boolean Comparison Engine | Evaluates binary equality $a == b$ in LIFO order: pops subtrahend $op_2 = b$ from Slot 1, decrements/classifies $op_2 \in \{0, 1, 2\}$, transitions through carry reset into Phase 2, pops minuend $op_1 = a$ from Slot 0, evaluates exact equality/difference, and pushes boolean result (1 if $a == b$, 0 if $a \neq b$) back into Slot 0 while resetting Slot 1 to empty. |
| Boolean Equality Properties Verified | - Reflexivity / Self-equality: $2 == 2 \implies 1$ (`01`)<br>- Predecessor inequality: $2 == 1 \implies 0$ (`00`)<br>- Zero operand inequality: $2 == 0 \implies 0$ (`00`)<br>- Multi-unit inequality: $4 == 2 \implies 0$ (`00`). |
| Zero-Extra-Flag Multiplexing | Uses strictly 6 code flags (`CLEAN_FLAG`, `ADD_FLAG`, `OP1_FLAG`, `SUBROUTINE_FLAG4..6`), fitting completely under the 59,049-word boundary with 1,538 bytes of headroom remaining. |

## Milestone P2 Verification Vectors

| Vector | Meaning | Expected Output | Oracle Steps | Runner C Steps | Verdict |
|---|---|---|---|---|---|
| `01 02 01 02 02 10 00` | Vector 1: CMP_EQ $2 == 2 \implies 1$ (true) | `01` | 81,069 | 81,069 | **MATCH (PASS)** |
| `01 02 01 01 02 10 00` | Vector 2: CMP_EQ $2 == 1 \implies 0$ (false) | `00` | 79,200 | 79,200 | **MATCH (PASS)** |
| `01 02 01 00 02 10 00` | Vector 3: CMP_EQ $2 == 0 \implies 0$ (false) | `00` | 78,654 | 78,654 | **MATCH (PASS)** |
| `01 04 01 02 02 10 00` | Vector 4: CMP_EQ $4 == 2 \implies 0$ (false) | `00` | 79,523 | 79,523 | **MATCH (PASS)** |
| `01 41 10 00` | Baseline 1: PUSH 'A', OUT, HALT | `41` ('A') | 67,097 | 67,097 | **MATCH (PASS)** |
| `01 41 01 42 10 10 00` | Baseline 2: 2-slot LIFO PUSH 'A', PUSH 'B', OUT, OUT, HALT | `42 41` ('BA') | 74,134 | 74,134 | **MATCH (PASS)** |
| `00` | Baseline 3: HALT (immediate) | *(empty)* | 60,054 | 60,054 | **MATCH (PASS)** |

## Differential Bridge Evidence

- `vm_malbolge/evidence/mbir_p2_cmp_smoke.json`: Complete 7-vector test suite results with SHA-256 hashes of generator, source, and binary artifacts.

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Full relational ordering (`CMP_LT`, `CMP_GT`) | Requires distinguishing sign of underflow rather than zero/non-zero delta. |
| In-memory MBIR program loader integration | Combining multi-opcode ALU with Milestone 2 RAM loader in a unified image. |
| Control Flow (`JMP`, `JZ`, `CALL`, `RET`) | Branching over an in-memory instruction stream driven by boolean ALU flags. |
