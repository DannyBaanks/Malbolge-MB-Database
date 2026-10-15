# Milestone M2 CF + CMP_EQ — stored-program Control Flow with Relational Equality in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Seven fixed 11-byte shapes, bytes read from RAM | `vm_malbolge/src/mbir_m2_cf_cmp.hell` + `vm_malbolge/tools/mbir_m2_cf_cmp_gen.py` + `vm_malbolge/src/mbir_m2_cf_cmp.mb` (56,947 bytes, limit 59,049, headroom 2,102) + `vm_malbolge/evidence/mbir_m2_cf_cmp_smoke.json` — **DEMONSTRATED 7/7**. |
| JMP `0x0C` | Emits `prog_6`. Two immediates (`0x41` and `0x58`) take identical step counts (66,846) with distinct raw byte outputs, demonstrating data is loaded from RAM. |
| JZ / JNZ | Opcode `0x01`. `prog_1 == 0` emits `prog_8` (62,123 steps). `prog_1 == 1` emits `prog_7` (62,718 steps). Distinct paths and step counts. |
| CALL / return byte | Opcode `0x0E`. Emits `prog_8`, then `prog_4` (68,060 steps). One frame. |
| CMP_EQ `0x04` | Opcode `0x04`. In-memory relational equality comparison between `prog_1` (1) and `prog_4` (1 or 2). `1 == 1` takes branch and emits `prog_8` (0x42 'B', 64,572 steps). `1 != 2` falls through and emits `prog_7` (0x43 'C', 65,124 steps). |
| Oracle and C runner parity | Both engines halt on the identical step count and the exact same raw bytes across all 7 vectors (`max_steps` 500,000). |

The image stores `prog_0`, `prog_1`, `prog_4`, `prog_6`, `prog_7`, and `prog_8`. The other five positions of the 11-byte program are read from stdin and ignored, so those indexes stay aligned. Each stored byte has its own scratch cell.

## Vectors

| Vector | Input (hex) | Expected | Steps | Verdict |
|---|---|---|---|---|
| JMP skip HALT | `0c05000000014110000000` | `41` | 66,846 | **PASS** |
| JMP other immediate | `0c05000000015810000000` | `58` | 66,846 | **PASS** |
| JZ taken | `01000d0700000001421000` | `42` | 62,123 | **PASS** |
| JZ not taken | `01010d0900000143100000` | `43` | 62,718 | **PASS** |
| CALL then return byte | `0e0700014110000142100f` | `4241` | 68,060 | **PASS** |
| CMP_EQ taken (1==1) | `0401000001000043420000` | `42` | 64,572 | **PASS** |
| CMP_EQ not taken (1!=2) | `0401000002000043420000` | `43` | 65,124 | **PASS** |

Artifact SHA-256: `5f6f0eb33ee7a8c9ffbf581bc4af43d6271cb5670829ff5226f7aa6c6f4e331d`.

## What is NOT demonstrated

| item | why |
|---|---|
| General program counter | Dispatch uses hardcoded opcode routes, not an arbitrary fetch loop. |
| JMP target as an arbitrary selector | The path emits `prog_6`. Landing on HALT is not in this image. |
| CMP_EQ with arbitrary width operands | Demonstrated relational comparison evaluates in-memory equality within the specified domain (operands 1 and 2). |
| Call stack deeper than one | The return byte is `prog_4`, not an arbitrary stack. |
