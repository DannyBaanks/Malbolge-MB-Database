# Milestone 2: Stored-Program MBIR Virtual Machine in Pure Malbolge

## Executive Summary

Milestone 2 establishes a fully operational **Stored-Program MBIR Virtual Machine in Pure Malbolge**.
Unlike previous probes which dispatched instructions streaming directly from STDIN on-the-fly, Milestone 2 implements:
1. **In-Memory RAM Cells (`prog_0..prog_3`)**: Program bytes are ingested during a dedicated Loader phase and committed to distinct memory cells using the verified Matthias Lutter double-crazy write theorem.
2. **Program Counter (`PC`) Dispatch**: Execution decouples from standard input; opcodes and immediate operands are fetched sequentially from RAM cells, driving the stack machine and execution lifecycle.
3. **Double-C2 Operand Extraction**: Operand bytes stored within memory cells are recovered non-destructively using the ternary digital conjugate identity $\operatorname{crz}(C_2, \operatorname{crz}(C_2, \text{cell})) \equiv \text{byte} \pmod{256}$.
4. **100% Bit-Exact Parity**: All 4 test vectors achieve bit-exact differential execution parity across both the reference Python oracle (`tools/oracle_classic.py`) and the native C Malbolge runtime (`runners/malbolge-original/malbolge`).

## Technical Metrics

- **Binary Size**: 40,309 bytes (assembled by LMAO 0.6.0).
- **Headroom**: 18,740 bytes below the hard 59,049-word limit ($3^{10}$).
- **Evidence Record**: `vm_malbolge/evidence/mbir_m2_loader_smoke.json`.
- **Test Vectors**: 4/4 PASS (100% differential agreement).

## Test Vector Differential Results

| Vector | Input (Hex) | MBIR Semantics | Expected Output | Oracle Output | Runner Output | Steps | Verdict |
|---|---|---|---|---|---|---|---|
| Vector 1 | `01 41 10 00` | `PUSH 'A'`, `OUT`, `HALT` | `41` ('A') | `41` | `41` | 41,343 | **PASS** |
| Vector 2 | `01 42 10 00` | `PUSH 'B'`, `OUT`, `HALT` | `42` ('B') | `42` | `42` | 41,343 | **PASS** |
| Vector 3 | `00` | Immediate `HALT` | (none) | (empty) | (empty) | 42,062 | **PASS** |
| Vector 4 | `01 41 00` | `PUSH 'A'`, `HALT` (no `OUT`) | (none) | (empty) | (empty) | 42,564 | **PASS** |

## Key Architectural Proofs

1. **Storage Invariance**: For any byte $B \in [0, 255]$ and scratch cell $S$ initialized to $C_1$, executing $\operatorname{crz}(B, S)$ followed by $\operatorname{crz}(\operatorname{crz}(B, S), \text{cell})$ leaves $\text{cell} = \operatorname{crz}(\operatorname{crz}(B, C_1), C_1) \equiv B$.
2. **Decoupled Flag Invariance**: Employing dedicated successor flags (`FLAG_P0_STORE`, `FLAG_P1_R1`, etc.) eliminates cross-subroutine flag contamination in Malbolge's XLAT2 rotation cycles.
3. **Re-entrant Underflow Detection**: Ternary carry classification accurately identifies terminal opcodes (`0x00`) during both loading and execution phases without destructive accumulator decay.
