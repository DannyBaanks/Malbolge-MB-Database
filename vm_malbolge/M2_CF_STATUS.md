# Milestone M2 CF — stored-program JMP / JZ / CALL in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Five fixed 11-byte shapes, bytes read from RAM | `vm_malbolge/src/mbir_m2_cf.hell` + `vm_malbolge/tools/mbir_m2_cf_gen.py` + `vm_malbolge/src/mbir_m2_cf.mb` (55,819 bytes, limit 59,049, headroom 3,230) + `vm_malbolge/evidence/mbir_m2_cf_smoke.json` — **DEMONSTRATED 5/5**. |
| JMP `0x0C` | Emits `prog_6`. Two immediates (`0x41` and `0x58`) take the same number of steps and different output bytes, so the byte is the one loaded from RAM. |
| JZ / JNZ | Opcode `0x01`. `prog_1 == 0` emits `prog_8`. `prog_1 == 1` emits `prog_7`. The step counts differ. |
| CALL / return byte | Opcode `0x0E`. Emits `prog_8`, then `prog_4`. One frame. |
| Oracle and C runner parity | Both engines halt on the same step count and the same raw bytes. `max_steps` 500,000. |

The image stores `prog_0`, `prog_1`, `prog_4`, `prog_6`, `prog_7`, and `prog_8`. The other five positions of the 11-byte program are read from stdin and ignored, so those indexes stay aligned. Each stored byte has its own scratch cell.

## Vectors

| Vector | Input (hex) | Expected | Steps | Verdict |
|---|---|---|---|---|
| JMP skip HALT | `0c05000000014110000000` | `41` | 65,825 | **PASS** |
| JMP other immediate | `0c05000000015810000000` | `58` | 65,825 | **PASS** |
| JZ taken | `01000d0700000001421000` | `42` | 61,100 | **PASS** |
| JZ not taken | `01010d0900000143100000` | `43` | 61,692 | **PASS** |
| CALL then return byte | `0e0700014110000142100f` | `4241` | 67,037 | **PASS** |

Artifact SHA-256: `549d23b61b280b0eee7b3ff762c5b16df00df3cce568237f02e99ab4fdbb1ebd`.

## What is NOT demonstrated

| item | why |
|---|---|
| General program counter | Dispatch is three hardcoded opcode routes, not a fetch loop. |
| JMP target as a selector | The path always emits `prog_6`. Landing on HALT is not in this image. |
| JZ for other conditions | Only condition 0 versus condition 1. |
| Call stack deeper than one | The return byte is `prog_4`, not a pushed frame. |
| Streaming ALU and CMP_EQ | Those stay in their own binaries. |
