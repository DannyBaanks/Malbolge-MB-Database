# Milestone P2 relational ordering — CMP_GT (Pure Malbolge Strict Greater-Than)

## Status: 12/12 DEMONSTRATED on both engines

Canonical image `vm_malbolge/src/mbir_cmp_gt.mb` (compiled from `vm_malbolge/src/mbir_cmp_gt.hell` via LMAO v0.6.0) achieves 100% bit-exact parity across all 9 ordered comparison pairs over $\{0,1,2\}^2$ plus all 3 baselines (12/12) on both `tools/oracle_classic.py` and `runners/malbolge-original/malbolge`.

Size: 57,511 bytes (< 59,049 memory capacity with 1,538 bytes headroom).

## 1. Architecture and Mathematical Specification

Given two values $a$ (minuend, Slot 0) and $b$ (subtrahend, Slot 1) popped from the 2-slot LIFO stack, the kernel evaluates boolean strict greater-than:
$$\text{CMP\_GT}(a, b) = \begin{cases} 1 & \text{if } a > b \\ 0 & \text{if } a \le b \end{cases}$$

Truth table over $\{0, 1, 2\}^2$:
- $(0, 0) \to 00$
- $(0, 1) \to 00$
- $(0, 2) \to 00$
- $(1, 0) \to 01$
- $(1, 1) \to 00$
- $(1, 2) \to 00$
- $(2, 0) \to 01$
- $(2, 1) \to 01$
- $(2, 2) \to 00$

### 1.1 Symmetrical Arithmetic Underflow Routing

1. **Phase 1 (Decrement $b$ via `decrement_value`)**:
   - $b=2$: Does not underflow on 2nd decrement. `NO_MORE_CARRY_FLAG diff_is_2_trampoline` immediately routes to `diff_is_2` (`00`), skipping Phase 2 entirely because $a > 2$ is impossible in $\{0,1,2\}$.
   - $b=1$: Underflows on 2nd decrement. Sets dedicated flag `R_GT_B1` and falls through straight-line to `reset_and_loop` to enter Phase 2.
   - $b=0$: Underflows on 1st decrement. Leaves `GT_B1` in `Nop` state and falls through straight-line to `reset_and_loop` to enter Phase 2.

2. **Phase 2 (Decrement $a$ via `decrement_value`)**:
   - At `return_from_dec_op1_1` (Dec 1 of $a$):
     - Evaluates `GT_B1 check_b1 R_GT_B1`.
     - If $b=0$ (`GT_B1` inactive): tests Dec 1 carry:
       - No underflow ($a \ge 1$): `NO_MORE_CARRY_FLAG` jumps to `diff_is_0` (`01`).
       - Underflow ($a = 0$): falls through to `diff_is_2` (`00`).
     - If $b=1$ (`GT_B1` active): jumps to `check_b1`.
       - In `check_b1`: tests Dec 1 carry via `NO_MORE_CARRY_FLAG a_is_1_or_2; MOVED diff_is_2`.
       - If $a = 0$: Dec 1 underflowed $\implies$ routes to `diff_is_2` (`00`).
       - If $a \ge 1$: routes to `a_is_1_or_2`, which triggers Dec 2 of $a$.
       - At `return_from_dec_op1_2`:
         - If $a = 2$: Dec 2 does not underflow $\implies$ `NO_MORE_CARRY_FLAG` jumps to `diff_is_0` (`01`).
         - If $a = 1$: Dec 2 underflows $\implies$ falls through to `diff_is_2` (`00`).

## 2. Verification Results (`vm_malbolge/tests/gt_harness.py`)

```text
cmp_gt(0,0)          in=01000100021000   want=00     oracle=00     runner=00     steps=81611 PASS
cmp_gt(0,1)          in=01000101021000   want=00     oracle=00     runner=00     steps=82151 PASS
cmp_gt(0,2)          in=01000102021000   want=00     oracle=00     runner=00     steps=77893 PASS
cmp_gt(1,0)          in=01010100021000   want=01     oracle=01     runner=01     steps=79884 PASS
cmp_gt(1,1)          in=01010101021000   want=00     oracle=00     runner=00     steps=82691 PASS
cmp_gt(1,2)          in=01010102021000   want=00     oracle=00     runner=00     steps=77893 PASS
cmp_gt(2,0)          in=01020100021000   want=01     oracle=01     runner=01     steps=79884 PASS
cmp_gt(2,1)          in=01020101021000   want=01     oracle=01     runner=01     steps=80964 PASS
cmp_gt(2,2)          in=01020102021000   want=00     oracle=00     runner=00     steps=77893 PASS
baseline1 push+out   in=01411000         want=41     oracle=41     runner=41     steps=67520 PASS
baseline2 lifo       in=01410142101000   want=4241   oracle=4241   runner=4241   steps=74578 PASS
baseline3 halt       in=00               want=(empty) oracle=(empty) runner=(empty) steps=60456 PASS
== 12/12 PASS
```

## 3. Artifacts and Provenance

| fichero | sha256 | papel |
|---|---|---|
| `vm_malbolge/src/mbir_cmp_gt.hell` | `477d5408a1e0e26a88a06b9b5f5f9486eb752bb0571dea6692b190f601706897` | código fuente canónico HeLL para CMP_GT |
| `vm_malbolge/src/mbir_cmp_gt.mb` | `1f17062a9585bbbb5b23ab2383f1b22fd60614e1b84bace32c52fa9e40f52f50` | imagen binaria Malbolge ejecutable 12/12 (57.511 B) |
| `vm_malbolge/src/mbir_cmp_gt.dbg` | `21ae15e4ae49e2d3655f08580878a163e4ff69d1dbb02a43d7db6fa6fa92b435` | mapa de símbolos y direcciones LMAO |
| `vm_malbolge/evidence/artifacts/gt_pass12.mb` | `1f17062a9585bbbb5b23ab2383f1b22fd60614e1b84bace32c52fa9e40f52f50` | artefacto inmutable verificado |
| `vm_malbolge/evidence/gt_12_12_harness.json` | `3091ba6beb52b21e3afff4924ef1d4814efed5a65f0cf122359facaab3fc62b7` | manifiesto JSON diferencial con pasos y hashes |
| `vm_malbolge/tools/mbir_cmp_gt_gen.py` | `bcfdcce562ac576d2c5fd12b462dbf3af9a745f2798ffd9e0e4f44fedbb961dd` | generador y compilador determinista LMAO |
| `vm_malbolge/tests/gt_harness.py` | `885f4c50be331e3866a492619fa9c3c52a22f235d79f9e07635aad5804806cf7` | harness diferencial de verificación dual |
