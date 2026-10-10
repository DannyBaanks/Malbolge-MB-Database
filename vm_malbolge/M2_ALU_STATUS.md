# Milestone M2 ALU — Stored-program ADD/SUB in Pure Malbolge

## What is demonstrated

| item | evidence |
|---|---|
| Stored-program ADD (0x02) and SUB (0x03) | `vm_malbolge/src/mbir_m2_alu.hell` + `vm_malbolge/tools/mbir_m2_alu_gen.py` + `vm_malbolge/src/mbir_m2_alu.mb` (56,361 bytes, limit 59,049, headroom 2,688) + `vm_malbolge/evidence/mbir_m2_alu_smoke.json` — **DEMONSTRATED 8/8**. |
| One load, then arithmetic from RAM | A 7-byte program is loaded once. The two `01` PUSH markers are consumed. `op1`, `op2`, and the opcode stay in `prog_1`, `prog_3`, and `prog_4`. |
| Small-operand lookup | Operands in `{0,1,2,3,4}`. Three decrements split opcode `0x02` from `0x03`. The result byte is `ROT` 0, 3, 6, 15, or 21. |
| Oracle and C runner parity | Both engines halt on the same step count and the same raw output byte. |

## Vectors

| Vector | Input (hex) | Expected | Steps | Verdict |
|---|---|---|---|---|
| ADD 2+3 | `01020103021000` | `05` | 65,951 | **PASS** |
| ADD 4+3 | `01040103021000` | `07` | 64,360 | **PASS** |
| ADD 1+1 | `01010101021000` | `02` | 66,331 | **PASS** |
| ADD 2+0 | `01020100021000` | `02` | 66,342 | **PASS** |
| SUB 4−2 | `01040102031000` | `02` | 64,360 | **PASS** |
| SUB 2−2 | `01020102031000` | `00` | 65,954 | **PASS** |
| SUB 2−1 | `01020101031000` | `01` | 65,348 | **PASS** |
| SUB 2−0 | `01020100031000` | `02` | 64,754 | **PASS** |

Artifact SHA-256: `1c641b880d1b0bd1825546c494ce163e9ca2c336318831c7fef83d3bb37f71d5`.

## What is NOT demonstrated

| item | obstacle |
|---|---|
| General subtractor | `check_sub` assumes `op1` is 2, except the dedicated `op1 = 4` path. |
| Chained programs | The image stores one opcode and two operands. `(1+1)-1` does not fit this loader. |
| The 14 streaming ALU vectors | Those run in `mbir_alu.mb`, which reads the instruction stream from STDIN. |
| CMP_EQ in this image | P2 is a separate 57,511-byte binary. This image has 2,688 bytes of file headroom and the init budget already rejected a 15-cell addition. |
| JMP, JZ, CALL, RET | No control-flow opcode is fetched from RAM. |
