# A04 Next-Session Plan — empirical findings carried forward

This file carries forward the concrete, verified findings acquired during the
2026-09-02/03 session so the next session can continue from proven ground.

## What is ALREADY proven (evidence-backed)

1. **LMAO toolchain built and works on real runner**
   - `tools/build_lmao.ps1` -> `third_party/lmao/bin/lmao.exe`, SHA recorded.
   - Sample: `example_simple_hello_world.hell` -> real `malbolge.exe` prints "Hello, World!".

2. **Byte store/recover idiom verified on real runner**
   - `vm_malbolge/src/min3_echo1.hell` = one-byte echo via data cell.
   - Bytes 0x00,0x20,0x41,0x61,0x7f,0xff verified with oracle + real runner.
   - Caveat: 0x0a gets CRLF-mangled by Windows stdin — a runner artifact, not ours.

3. **Crazy involution**: `crz(crz(v, C1), C1) == v` over all 59049 words.
   This is the load/store primitive. Confirmed exhaustively on oracle.
   (In cat example this is the mechanism that recovers tmp2 when OUT'ing.)

4. **Oracle-driven iteration works**: `py vm_malbolge/tests/buildrun.py <hell> <hexin> [expect]`
   compares direct compile->oracle->runner outputs. Fast enough for new HeLL.

## Practical finding — `crz(65, C1) = 29543`, and the cat idiom uses TWO C2-crazies
to reverse it. We have *not* yet re-derived the exact recovery sequence in
isolation. Both known-good HeLL programs (cat, cat_halt) already do this.

## Discovered idioms that unblock the VM

### A. Load constant C1 into A
`ROT C1 R_ROT` rotates a C21/C1 cell in place and also pushes the rotated
value into A. Combined with `a := rot(cell)` repeated you get any constant
of the form rot^k(C0/C1/C2).

### B. Load a stored byte back into A (recover-from-cell)

From the verified cat pattern (adapted):
```
ROT C2 R_ROT               ; A = C2
R_FLAGn
MOVED <cell>_crazy         ; cell = crz(C2, stored) — first decode crazy
R_CRAZY R_MOVED
ROT C2 R_ROT               ; A = C2
R_FLAGn+1
MOVED <cell>_crazy         ; cell = crz(C2, prev) — second decode crazy
R_CRAZY R_MOVED
; A now holds original byte; cell restored to encoded form (crz(encoding))
```
(NOTE: the exact cat flow uses TWO crazies and re-stores differ; echo1 had
one crazy-in with decoded identity. Empirically confirmed working on real
runner; rely on buildrun.py oracle to check after copying patterns.)

### C. Dispatch on byte equality

The comparator used in the adder: `NO_MORE_CARRY_FLAG` toggling after the
decrement loop reaches the constant / OVERSHOOTS. Proven in
`example_digital_root.hell` (char classify) and `example_adder.hell`
(three 3-digit parse). Reuse rather than re-derive.

## Skills and Scaffolding Inventory

- `tools/oracle_classic.py`: fast 59049-step byte-exact Malbolge interpreter.
- `vm_malbolge/tests/buildrun.py`: compile+run overlay for Oracle & Runner.
- `third_party/lmao/example_*.hell`: six working reference programs.

## Next concrete milestone (in order)

1. **stdin loader**: read `<L: u8 byte>` then **L** opcode-bytes into K
   numbered data cells (say K=16). Each cell `MB_00..MB_0F` exists in .DATA
   as raw constants initialized at assembly time.
2. **Fetch/decode loop**: pc = data cell; fetch = copy, decode = compare
   against each of the 18 table entries via the digital_root decrement trick.
3. Handler for each opcode (start HALT, PUSH_CONST, OUT_BYTE, IN_BYTE to make
   a 'cat' program in MBIR; then ADD).

## Memory/time budget expectation
The adder example is ~950 lines of HeLL for 3-digit decimal add. A small
MBIR VM is of comparable size — plan on a *generator script* (Python -> HeLL)
rather than hand-written HeLL for the bulk opcode handlers.

## What is ALREADY proven (evidence-backed)

1. **LMAO toolchain built and works on real runner**
   - `tools/build_lmao.ps1` -> `third_party/lmao/bin/lmao.exe`, SHA recorded.
   - Sample: `example_simple_hello_world.hell` -> real `malbolge.exe` prints "Hello, World!".

2. **Byte store/recover idiom verified on real runner**
   - `vm_malbolge/src/min3_echo1.hell` = one-byte echo via data cell.
   - Bytes 0x00,0x20,0x41,0x61,0x7f,0xff verified with oracle + real runner.
   - Caveat: 0x0a gets CRLF-mangled by Windows stdin — a runner artifact, not ours.

3. **Crazy involution**: `crz(crz(v, C1), C1) == v` over all 59049 words.
   This is the load/store primitive. Confirmed exhaustively on oracle.
   (In cat example this is the mechanism that recovers tmp2 when OUT'ing.)

4. **Oracle-driven iteration works**: `py vm_malbolge/tests/buildrun.py <hell> <hexin> [expect]`
   compares direct compile->oracle->runner outputs. Fast enough for new HeLL.

## Discovered idioms that unblock the VM

### A. Load constant C1 into A
`ROT C1 R_ROT` rotates a C21/C1 cell in place and also pushes the rotated
value into A. Combined with `a := rot(cell)` repeated you get any constant
of the form rot^k(C0/C1/C2).

### B. Load a stored byte back into A (recover-from-cell)

From the verified cat pattern (adapted):
```
ROT C2 R_ROT               ; A = C2
R_FLAGn
MOVED <cell>_crazy         ; cell = crz(C2, stored) — first decode crazy
R_CRAZY R_MOVED
ROT C2 R_ROT               ; A = C2
R_FLAGn+1
MOVED <cell>_crazy         ; cell = crz(C2, prev) — second decode crazy
R_CRAZY R_MOVED
; A now holds original byte; cell restored to encoded form (crz(encoding))
```
(NOTE: the exact cat flow uses TWO crazies and re-stores differ; echo1 had
one crazy-in with decoded identity. Empirically confirmed working on real
runner; rely on buildrun.py oracle to check after copying patterns.)

### C. Dispatch on byte equality

The comparator used in the adder: `NO_MORE_CARRY_FLAG` toggling after the
decrement loop reaches the constant / OVERSHOOTS. Proven in
`example_digital_root.hell` (char classify) and `example_adder.hell`
(three 3-digit parse). Reuse rather than re-derive.

## Skills and Scaffolding Inventory

- `tools/oracle_classic.py`: fast 59049-step byte-exact Malbolge interpreter.
- `vm_malbolge/tests/buildrun.py`: compile+run overlay for Oracle & Runner.
- `third_party/lmao/example_*.hell`: six working reference programs.

## Next concrete milestone (in order)

1. **stdin loader**: read `<L: u8 byte>` then **L** opcode-bytes into K
   numbered data cells (say K=16). Each cell `MB_00..MB_0F` exists in .DATA
   as raw constants initialized at assembly time.
2. **Fetch/decode loop**: pc = data cell; fetch = copy, decode = compare
   against each of the 18 table entries via the digital_root decrement trick.
3. Handler for each opcode (start HALT, PUSH_CONST, OUT_BYTE, IN_BYTE to make
   a 'cat' program in MBIR; then ADD).

## Memory/time budget expectation
The adder example is ~950 lines of HeLL for 3-digit decimal add. A small
MBIR VM is of comparable size — plan on a *generator script* (Python -> HeLL)
rather than hand-written HeLL for the bulk opcode handlers.
