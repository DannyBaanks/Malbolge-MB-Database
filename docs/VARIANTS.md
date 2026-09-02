# Malbolge Variants

## Overview

Malbolge exists in multiple incompatible variants. A `.mb` file must declare which machine it targets. Never execute a `.mb` on a different variant and use the failure as evidence against the program.

## Original Malbolge

| Property | Value |
|----------|-------|
| Memory | 59049 cells (3^10) |
| Word width | 10 trits |
| Address space | 0 to 59048 |
| Instructions | Values 33-126 (printable ASCII) |
| Self-modification | `crazy(a, mem[c])` after each instruction at address `c` |
| Rotation | `rotate(n) = 3^8 * (n % 3) + n / 3` |
| Turing complete | No (finite state space) |
| Interpreter | Standard Malbolge interpreters (Python, C, Zig, etc.) |
| Use case | Bounded programs, fixed-output generation, simple interpreters |

### Limitations
- 59049 cells is extremely constrained for complex programs
- Self-modification makes debugging nearly impossible
- No standard I/O beyond single-character input/output
- Programs that need persistent state across "ticks" must work within the memory bound

## Malbolge Unshackled

| Property | Value |
|----------|-------|
| Memory | ~1 trillion cells (3^19 or 3^20) |
| Word width | 19-20 trits |
| Address space | Effectively unbounded |
| Instructions | Same encoding as Original |
| Self-modification | Same `crazy` operation, wider words |
| Turing complete | Yes (effectively, given enough memory) |
| Interpreter | `fast20.c` (C), `bolge19` (Zig), custom interpreters |
| Use case | Complex programs, interpreters, full applications |

### Why It Matters
- Enables writing substantial programs (MalbolgeLisp: 371 MB compiled)
- Lisp interpreter, Brainfuck interpreter, and other complex programs exist
- The only practical way to implement a high-level language runtime in Malbolge
- Requires `fast20.c` or equivalent — standard Malbolge interpreters cannot run these programs

### Key Interpreter: fast20.c
- Derived from Matthias Lutter's `Unshackled-20.c`
- Uses `mmap` + `SIGSEGV` for memory management
- Fixed rotation width of 19 trits (marginally faster than 20)
- Build: `clang -O3 -march=native fast20.c -o fast20`
- Platform note: Windows/Cygwin may need patches (use `mprotect` instead of `mmap(MAP_FIXED)`)

## Malbolge20

| Property | Value |
|----------|-------|
| Memory | 3^20 cells (~1 trillion) |
| Word width | 20 trits |
| Address space | 0 to 3^20 - 1 |
| Toolchain | Nagoya University (highlevel, ternary, lowass) |
| Interpreter | `malbolge20` (Nagoya) |
| Use case | Compiler targets (C subset → Malbolge20) |

### Toolchain
- `highlevel`: C subset → `.mg` pseudo-instructions
- `ternary`: `.mg` → LAL (low-level assembly)
- `lowass`: LAL → Malbolge20 binary

### Relation to Unshackled
Malbolge20 and Unshackled are conceptually similar (wide-word Malbolge) but differ in specification details. Programs compiled for one may not run on the other without modification.

## Compatibility Matrix

| Feature | Original | Unshackled | Malbolge20 |
|---------|----------|------------|------------|
| Memory cells | 59049 | ~1T | ~1T |
| Self-modification | Yes | Yes | Yes |
| Turing complete | No | Yes | Yes |
| Standard interpreters | Yes | No | No |
| Custom interpreter needed | No | fast20.c | Nagoya |
| Existing complex programs | Limited | MalbolgeLisp, BF interp | C subset programs |
| Best for python.mb | Too constrained | Primary target | Alternative |

## Recommendation for python.mb

**Primary target: Malbolge Unshackled**

Rationale:
1. The 59049-cell limit of Original Malbolge is too restrictive for a Python interpreter
2. MalbolgeLisp proves the VM-in-Malbolge pattern works at scale in Unshackled
3. `fast20.c` is available and proven
4. Original Malbolge may be used for early milestones (P0-P1) as a proving ground

## Runner Requirements

Each runner must document:
- Source/origin of the interpreter binary
- Version/commit hash
- Build command and compiler
- Compiler flags
- SHA256 of the built binary
- Which `.mb` files it can execute
- Platform requirements
