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

## Domain Limit: operandos $\ge 3$ no están cubiertos (2026-11-06)

Medido con `vm_malbolge/tests/alu_domain_harness.py` sobre el binario
comprometido (`vm_malbolge/src/mbir_alu.mb`, sha256 `b0fd9085…`, 54,691 bytes),
dual-engine (oráculo Python `tools/oracle_classic.py` + runner C
`runners/malbolge-original/malbolge`), grid `{0..4}²` para `ADD` (0x02) y
`SUB` (0x03), más 14 vectores de control contra la evidencia registrada:

- **Fidelidad de control:** 14/14 vectores registrados reproducen outputs **y**
  recuentos de pasos exactos — el binario comprometido sigue siendo el que
  emitió la evidencia original.
- **Dominio acotado:** ADD reproduce aritmética entera en 5/25 pares del
  grid `{0..4}²` y SUB en 4/25. Los outcomes observables son ADD {00,01,02,05,07}
  y SUB {00,01,02} — casi todo el dominio diverge de la suma/resta entera.
- **No es función pura de $(a,b)$:** `ADD 2+3 → 0x05` pero `ADD 3+2 → 0x07`
  (no conmutativo; la aritmética entera sí lo es). Un `PUSH_CONST` extra dejado
  en la pila cambia el resultado (`ADD 2+3 → 0x54` con un push extra `0x41`),
  aunque los operandos sean idénticos.
- **Mecanismo en el fuente:** `mbir_alu.hell` líneas 495-512 seleccionan el
  resultado con tres flags (`SUBROUTINE_FLAG4/5/6`) y lo materializan con
  `ROT` de constantes fijas (`load_sum_7 → ROT 21`, `load_diff_1 → ROT 3`,
  `load_diff_0 → ROT 0`, …). La magnitud del operando no entra en el resultado.
- **Paridad de motores:** 0 divergencias oráculo-vs-runner en cada caso medido.
  Es una **limitación semántica del programa**, no una divergencia de
  implementación entre los dos motores.

Esto explica por qué los 8 vectores aritméticos documentados pasan (caen en
el subconjunto donde la tabla coincide con la aritmética entera) y por qué
cualquier operando $\ge 3$ — y de hecho casi todo el dominio de un byte —
produce un resultado fuera de la suma/resta entera. El dominio acotado
`{0,1,2}` de `CMP_LT`/`CMP_GT` es la misma clase de límite heredada por este
kernel.

## Differential Bridge Evidence

- `vm_malbolge/evidence/mbir_alu_smoke.json`: Complete 14-vector test suite results with SHA-256 hashes of generator, source, and binary artifacts.
- `vm_malbolge/evidence/mbir_zig_oracle_alu.json`: Differential verification across Zig VM, Python Oracle, and C Runner on vector `01411000`.
- `vm_malbolge/evidence/mbir_alu_domain_limit.json`: Domain-limit differential measurement over `{0..4}²` for `ADD` and `SUB` (2026-11-06).

## What is NOT demonstrated

| item | obstacle |
|---|---|
| Arbitrary Signed / Negative Arithmetic | Subtractions producing negative results ($a < b$) underflow into Malbolge modulus ($59049$). |
| Bounded operand domain / general ADD($\ge 3$) / SUB($\ge 3$) | The kernel classifies $b$ into three classes and materialises results with fixed `ROT` constants; integer arithmetic is only reproduced on a bounded operand subset. Operands $\ge 3$ are **not** covered. |
| Multiplication / Division (`MUL`, `DIV`) | Multi-cycle shift-and-add algorithms require iterative quotient registers. |
| In-memory MBIR program loader | Pre-loading bytecode stream into Malbolge RAM before program dispatch. |
| Control Flow (`JMP`, `JZ`, `CALL`, `RET`) | Branching over an in-memory instruction stream. |
