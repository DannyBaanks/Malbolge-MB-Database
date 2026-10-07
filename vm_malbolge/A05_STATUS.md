# A05 — Current Status (verbatim, no polish)

## What is demonstrated

| item | evidence |
|---|---|
| Universal 3-Crazy Reset Theorem | `crz(C0, crz(C2, crz(C1, X))) == 29524 (C1)` holds for **ALL 59,049 words** of Malbolge. Discovered and verified exhaustively on `oracle_classic.py`. Allows unconditional reset of any data cell back to `C1` using only 3 subroutine calls. |
| Streamlined Data Cell Architecture | Removed legacy `tmp1..tmp4` definitions and `check_for_C2` dead code from `min3_echo1.hell`. Reduces compiled binary size from 52,623 to 40,309 bytes (saving >12,000 bytes under the 59,049-word limit) and saves ~20,000 initialization steps in `ENTRY`. |
| Shared Reset Flag Multiplexing | Data cells (`value`, `value_C1`, `stack_scratch`, `stack_top`) all share `RESET_FLAG1..3`. Zero extra `.CODE` flags needed, avoiding LMAO's `Forced xlat cycle doesn't exist` trap (since Malbolge has only one 2-cycle in XLAT2: `F <-> J`). |
| Re-entrant Multi-Cycle Fetch Loop (A05) | `vm_malbolge/src/mbir_a05_multicycle.hell` + `vm_malbolge/tools/mbir_a05_multicycle_gen.py` + `vm_malbolge/evidence/mbir_a05_multicycle_smoke.json` — **DEMONSTRATED 8/8** on independent Classic Python oracle, real `malbolge-original` C runner, and `mbir-zig`. Emits arbitrary sequential strings (`4142` -> "AB", `414243` -> "ABC", `68656c6c6f` -> "hello") with exact step scaling (+6,046 steps per iteration) and 100% bit-exact output. |
| Elimination of A04 Multi-Cycle Boundary | The previous limitation vector `01 41 10 01 42 10 00` (which previously produced `41 43` due to contaminated cell state) now cleanly produces `41 42` ("AB") in 54,747 steps on both independent engines. |

## Verification Vectors

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

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Concurrent multi-element stack depth (>1 items in stack simultaneously) | Vector `01 41 01 42 10 10 00` (pushing both before popping) requires dynamic stack pointer indexing over multiple memory slots rather than the single dedicated slot pair. Code flags cannot store persistent stack depth because `R_FLAG` restores subroutine phases rather than persisting numeric state. |
| Arithmetic Kernel (ADD / SUB) | Lowering binary addition (`ADD`: opcode 0x02) onto the ternary adder digital-root idioms. |
| In-memory MBIR program loader | Reading the complete bytecode binary into an array of Malbolge cells prior to execution. |

## Toolchain & Substrate Insights

- **Single 2-cycle in Malbolge XLAT2:** `F (70) <-> J (74)` is the only 2-cycle in the entire 94-character translation permutation. Consequently, flags (`Nop/MovD`) can only be positioned at addresses where `c = (40 - 74) % 94` or `(40 - 70) % 94`. Declaring excessive separate flags in `.CODE` exhausts valid offsets and triggers LMAO's `Forced xlat cycle doesn't exist` error. Reusing `RESET_FLAG1..3` across data cells is mandatory and architecturally sound.
- **Universal 3-Crazy Reset Formula:** Applying crazy operations sequentially with constants `C1`, `C2`, and `C0` transforms any value `X in [0..59048]` into `29524 (C1)` unconditionally.
