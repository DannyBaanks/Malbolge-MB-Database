# Milestone P0 — Arithmetic Kernel: ADD (Opcode 0x02) in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Pure Malbolge Arithmetic Kernel (`ADD` 0x02) | `vm_malbolge/src/mbir_p0_add.hell` + `vm_malbolge/tools/mbir_p0_add_gen.py` + `vm_malbolge/src/mbir_p0_add.mb` (size: 57,511 bytes < 59,049 limit) + `vm_malbolge/evidence/mbir_p0_add_smoke.json` — **DEMONSTRATED 7/7** simultaneous PASS across both canonical Python reference oracle (`tools/oracle_classic.py`) and native C runner (`runners/malbolge-original/malbolge`). |
| 100% Bit-Exact Differential Step Parity | Every single test vector terminates with identical step count down to the individual step between the C runner and the Python reference oracle (e.g., Vector 1 at 81,360 steps, Vector 2 at 79,817 steps, Vector 3 at 79,292 steps, Vector 4 at 78,752 steps). |
| Dynamic 2-Phase Addition Engine | Emulates binary arithmetic addition via sequential operand evaluation: pops `op2` from Slot 1, decrements/classifies value, transitions through clean carry reset into Phase 2, pops `op1` from Slot 0, evaluates ternary sum, and pushes exact sum back to Slot 0 while resetting Slot 1 to empty. |
| Elimination of Runtime Stack Init Loop | Replaced legacy 36-line runtime crazy initialization loop with direct `C1` pre-initialization on all four stack cells and `ENTRY: MOVED next_opcode`. Reclaimed 5,076 bytes of code space, expanding LMAO headroom to fit the full arithmetic kernel under the 59,049-byte boundary. |
| Zero-Extra-Flag Multiplexing | Compounded code flags down to strictly 6 flags (`CLEAN_FLAG`, `ADD_FLAG`, `OP1_FLAG`, `SUBROUTINE_FLAG4..6`), preventing LMAO's translation cycle exhaustion (`Forced xlat cycle doesn't exist`) while preserving full subroutine re-entrancy. |
| Resolution of `MOVED` Toggle Inversion Traps | Identified and fixed the toggle inversion asymmetry where branches taken by `NO_MORE_CARRY_FLAG` left `MOVED` armed (`MovD`). Executing `R_MOVED` on those paths inverted `MOVED` into `Nop` causing fall-through. Removing `R_MOVED` from `op2_is_3` and `sum_is_7` enabled flawless transitions into `reset_and_loop` and `sum_is_2`. |

## Milestone P0 Verification Vectors

| Vector | Meaning | Expected Output | Oracle Steps | Runner C Steps | Verdict |
|---|---|---|---|---|---|
| `01 02 01 03 02 10 00` | Vector 1: ADD $2 + 3 = 5$ | `05` | 81,360 | 81,360 | **MATCH (PASS)** |
| `01 04 01 03 02 10 00` | Vector 2: ADD $4 + 3 = 7$ | `07` | 79,817 | 79,817 | **MATCH (PASS)** |
| `01 01 01 01 02 10 00` | Vector 3: ADD $1 + 1 = 2$ | `02` | 79,292 | 79,292 | **MATCH (PASS)** |
| `01 02 01 00 02 10 00` | Vector 4: ADD $2 + 0 = 2$ | `02` | 78,752 | 78,752 | **MATCH (PASS)** |
| `01 41 10 00` | Baseline 1: PUSH 'A', OUT, HALT | `41` ('A') | 67,195 | 67,195 | **MATCH (PASS)** |
| `01 41 01 42 10 10 00` | Baseline 2: 2-slot LIFO PUSH 'A', PUSH 'B', OUT, OUT, HALT | `42 41` ('BA') | 74,232 | 74,232 | **MATCH (PASS)** |
| `00` | Baseline 3: HALT (immediate) | *(empty)* | 60,152 | 60,152 | **MATCH (PASS)** |

## Differential Bridge Evidence

- `vm_malbolge/evidence/mbir_p0_add_smoke.json`: Complete 7-vector test suite results with SHA-256 hashes of generator, source, and binary artifacts.
- `vm_malbolge/evidence/mbir_zig_oracle_p0_add.json`: Differential verification across Zig VM, Python Oracle, and C Runner on the baseline vector `01411000`.

## What is NOT demonstrated

| item | obstacle |
|---|---|
| General N-bit Addition | Arbitrary dynamic operand addition beyond digital sum table. |
| Arithmetic Kernel Subtraction (`SUB`) | Milestone P1: Opcode 0x07 subtraction. |
| Stack Depth > 2 | Storing 3 or more operands simultaneously requires additional slot cells or dynamic address rotation. |
| In-memory MBIR program loader | Pre-loading bytecode stream into Malbolge RAM before program dispatch. |

## Substrate & Architectural Insights

1. **Self-Modifying Toggle Inversion in LMAO/Malbolge:**
   In Malbolge, instruction cells defined as `X/Y` toggle their opcode between `X` and `Y` every time they are executed. Flags conditional branches work by arming `MovD target` followed by `Jmp`. When a conditional jump (like `NO_MORE_CARRY_FLAG`) branches into a handler without executing `MOVED`, `MOVED` remains armed as `MovD`. Adding an explicit `R_MOVED` at the start of that handler inverts `MOVED` into `Nop`, causing the subsequent jump to fall through into adjacent code blocks.
2. **Phase Flag Multiplexing:**
   The arithmetic engine operates across two discrete phases: Phase 1 evaluates `op2` from Slot 1, and Phase 2 evaluates `op1` from Slot 0. By utilizing `OP1_FLAG` to multiplex between the two phases, the same low-level decrement subroutines (`decrement_value`) and return branches are reused without requiring duplicate code paths.
3. **Universal 3-Crazy Reset Integration:**
   All temporary variables and data cells are cleanly restored to `C1` via the universal formula `crz(C0, crz(C2, crz(C1, X))) == C1`, ensuring complete isolation across multi-cycle operations.
