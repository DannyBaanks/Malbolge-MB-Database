# A05 / A05b — Current Status (verbatim, no polish)

## What is demonstrated

| item | evidence |
|---|---|
| Universal 3-Crazy Reset Theorem | `crz(C0, crz(C2, crz(C1, X))) == 29524 (C1)` holds for **ALL 59,049 words** of Malbolge. Discovered and verified exhaustively on `oracle_classic.py`. Allows unconditional reset of any data cell back to `C1` using only 3 subroutine calls. |
| Streamlined Data Cell Architecture | Removed legacy `tmp1..tmp4` definitions and `check_for_C2` dead code from `min3_echo1.hell`. Reduces compiled binary size from 52,623 to 40,309 bytes (saving >12,000 bytes under the 59,049-word limit) and saves ~20,000 initialization steps in `ENTRY`. |
| Shared Reset Flag Multiplexing | Data cells (`value`, `value_C1`, `stack_scratch`, `stack_top`, `stack_scratch_1`, `stack_top_1`) all share `RESET_FLAG1..3`. Zero extra `.CODE` flags needed, avoiding LMAO's `Forced xlat cycle doesn't exist` trap (since Malbolge has only one 2-cycle in XLAT2: `F <-> J`). |
| Re-entrant Multi-Cycle Fetch Loop (A05) | `vm_malbolge/src/mbir_a05_multicycle.hell` + `vm_malbolge/tools/mbir_a05_multicycle_gen.py` + `vm_malbolge/evidence/mbir_a05_multicycle_smoke.json` — **DEMONSTRATED 8/8** on independent Classic Python oracle, real `malbolge-original` C runner, and `mbir-zig`. Emits arbitrary sequential strings (`4142` -> "AB", `414243` -> "ABC", `68656c6c6f` -> "hello") with exact step scaling (+6,046 steps per iteration) and 100% bit-exact output. |
| Elimination of A04 Multi-Cycle Boundary | The previous limitation vector `01 41 10 01 42 10 00` (which previously produced `41 43` due to contaminated cell state) cleanly produces `41 42` ("AB") in 54,747 steps on both independent engines. |
| Pure Malbolge 2-Slot LIFO Stack Machine (A05b) | `vm_malbolge/src/mbir_a05_lifo.hell` + `vm_malbolge/tools/mbir_a05_lifo_gen.py` + `vm_malbolge/evidence/mbir_a05_lifo_smoke.json` + `vm_malbolge/evidence/mbir_zig_oracle_a05_lifo.json` — **DEMONSTRATED 7/7**. LMAO size: 51,877 bytes. Implements true dynamic stack depth tracking via `SLOT0_FLAG` and `SLOT1_FLAG`. Demonstrates true LIFO inversion (`PUSH 'A'`, `PUSH 'B'`, `OUT`, `OUT`, `HALT` -> `"BA"` = `42 41`) bit-exact across Zig oracle, Python reference oracle, and native C runner! |

## A05 Multi-Cycle Verification Vectors

| Vector | Meaning | Salida esperada | Pasos Oracle | Pasos Runner C | Pasos Zig | Veredicto |
|---|---|---|---|---|---|---|
| `01 41 10 00` | 1-push A | `41` (`A`) | 48,701 | 48,701 | 3 | **MATCH** |
| `01 42 10 00` | 1-push B | `42` (`B`) | 48,701 | 48,701 | 3 | **MATCH** |
| `00` | HALT | *(empty)* | 42,655 | 42,655 | 1 | **MATCH** |
| `01 41 00` | 1-push A, no out | *(empty)* | 46,322 | 46,322 | 2 | **MATCH** |
| `01 41 10 01 42 10 00` | 2-cycle sequential | `41 42` (`AB`) | 54,747 | 54,747 | 5 | **MATCH** |
| `01 41 10 01 42 10 01 43 10 00` | 3-cycle sequential | `41 42 43` (`ABC`) | 60,793 | 60,793 | 7 | **MATCH** |
| `01 7a 10 01 00 10 01 ff 10 00` | 3-cycle boundary | `7a 00 ff` | 60,793 | 60,793 | 7 | **MATCH** |
| `01 68 10 01 65 10 01 6c 10 01 6c 10 01 6f 10 00` | 5-cycle hello | `68 65 6c 6c 6f` (`hello`) | 72,885 | 72,885 | 11 | **MATCH** |

## A05b 2-Slot LIFO Verification Vectors

| Vector | Meaning | Salida esperada | Pasos Oracle | Pasos Runner C | Pasos Zig | Veredicto |
|---|---|---|---|---|---|---|
| `01 41 10 00` | 1-push A, out, halt | `41` (`A`) | 59,752 | 59,752 | 3 | **MATCH** |
| `01 42 10 00` | 1-push B, out, halt | `42` (`B`) | 59,752 | 59,752 | 3 | **MATCH** |
| `00` | HALT (immediate) | *(empty)* | 53,700 | 53,700 | 1 | **MATCH** |
| `01 41 00` | 1-push A, halt (no out) | *(empty)* | 57,369 | 57,369 | 2 | **MATCH** |
| `01 41 10 01 42 10 00` | 2 sequential 1-pushes | `41 42` (`AB`) | 65,804 | 65,804 | 5 | **MATCH** |
| **`01 41 01 42 10 10 00`** | **2-slot LIFO: PUSH A, PUSH B, OUT, OUT, HALT** | **`42 41` (`BA`)** | **65,804** | **65,804** | **5** | **MATCH** |
| `01 41 01 42 10 00` | 2-slot top pop: PUSH A, PUSH B, OUT, HALT | `42` (`B`) | 63,421 | 63,421 | 4 | **MATCH** |

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Stack depth > 2 | Storing 3 or more operands simultaneously requires additional slot cells or indirect memory addressing. |
| Arithmetic Kernel (`ADD` / `SUB`) | Milestone P0: lower binary addition (`ADD`: opcode 0x02) popping two operands from `stack_top_1` and `stack_top`, computing ternary digital root sum, and pushing result. |
| In-memory MBIR program loader | Reading the complete bytecode binary into an array of Malbolge cells prior to execution. |
| Control Flow (`JMP`, `JZ`, `CALL`, `RET`) | Branching over an in-memory instruction stream. |

## Toolchain & Substrate Insights

- **Single 2-cycle in Malbolge XLAT2:** `F (70) <-> J (74)` is the only 2-cycle in the entire 94-character translation permutation. Consequently, flags (`Nop/MovD`) can only be positioned at addresses where `c = (40 - 74) % 94` or `(40 - 70) % 94`. Declaring excessive separate flags in `.CODE` exhausts valid offsets and triggers LMAO's `Forced xlat cycle doesn't exist` error. Reusing `RESET_FLAG1..3` across data cells is mandatory and architecturally sound.
- **Universal 3-Crazy Reset Formula:** Applying crazy operations sequentially with constants `C1`, `C2`, and `C0` transforms any value `X in [0..59048]` into `29524 (C1)` unconditionally.
- **Dynamic Stack Depth FSM:** Two flag sites (`SLOT0_FLAG` and `SLOT1_FLAG`) emulate a 2-bit stack pointer:
  - Empty: `SLOT0 = Nop, SLOT1 = Nop`
  - 1 item: `SLOT0 = MovD, SLOT1 = Nop` (item in Slot 0)
  - 2 items: `SLOT0 = MovD, SLOT1 = MovD` (Slot 0 + Slot 1 occupied)
  - Popping from depth 2 transitions to depth 1 (Slot 0 remains, Slot 1 cleared and reset to `C1`).
  - Popping from depth 1 transitions to depth 0 (Slot 0 cleared and reset to `C1`).
