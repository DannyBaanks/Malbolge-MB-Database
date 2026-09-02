# Python / Malbolge — Prior Art Survey (Corrected)

**Date**: 2026-09-02 (Session 2 adversarial audit)
**Method**: Primary source code inspection, not README-only claims

---

## Classification Categories

| Category | Meaning |
|----------|---------|
| HOSTED_INTERPRETER | Interpreter for language X runs ON Malbolge |
| SEMANTIC_COMPILER | Compiler from language X preserving X semantics |
| COMPILER_TOOLCHAIN | Multi-stage compiler pipeline producing Malbolge |
| COMPILER_DESIGN | Design document or algorithm description, no implementation |
| FORMAL_SEMANTICS | Machine-checked formal semantics or verified infrastructure |
| OUTPUT_SYNTHESIS | Generates programs that print target strings |
| NOVELTY | Character transformation or toy, no semantic preservation |
| STUB | Scaffold with no working implementation |

---

## 1. Aiaid/pyMalbolge

| Field | Value |
|-------|-------|
| **URL** | https://github.com/Aiaid/pyMalbolge |
| **Classification** | COMPILER_TOOLCHAIN |
| **License** | MIT |
| **Direction** | Python subset → Malbolge20 |
| **Variant** | Malbolge20 (NOT Original, NOT Unshackled) |
| **Tests** | 441 passing |
| **Status** | Working |

**What it actually does**: Multi-stage compiler pipeline: `py2c` (Python AST → Nagoya C subset), `c2mg` (→ `.mg` pseudo-instructions), `mg2mc` (→ LAL), `mc2mb` (→ Malbolge20). Also has `py2mg` direct backend. Ships interpreters for Original Malbolge (10 trits) and Malbolge20 (20 trits), plus a full debugger.

**Python subset**: `int` arithmetic, `while`/`if`/`elif`/`else`, `for i in range(...)`, `break`/`continue`, chained comparisons, short-circuit `and`/`or`/`not`, function definitions with mutual recursion, `putchar()`/`getchar()`, `print()` with constant arguments.

**Key distinction**: This compiles Python TO Malbolge20 (host compilation). It does NOT run a Python interpreter ON Malbolge (hosted interpreter). The compiled programs cannot handle runtime input (no `input()` in compiled output). Targets Malbolge20, not Original or Unshackled.

**Relevance to python.mb**: Architecture reusable for toolchain design. Wrong variant target. Different direction (compiler vs interpreter).

---

## 2. Avantgarde95/pyMalbolge

| Field | Value |
|-------|-------|
| **URL** | https://github.com/Avantgarde95/pyMalbolge |
| **Classification** | HOSTED_INTERPRETER |
| **License** | Present in repo |
| **Direction** | Malbolge interpreter written in Python |
| **Variant** | Original (10 trits) |
| **Status** | Historical (11 commits, not maintained) |

**What it actually does**: Single-file Python Malbolge interpreter (~120 lines). Port of Ben Olmstead's C reference interpreter. No compiler, no code generation.

**Relevance**: Historical only. The Aiaid fork evolved into a completely different project (zero original source remains).

---

## 3. Vai-Te/Lascar

| Field | Value |
|-------|-------|
| **URL** | https://github.com/Vai-Te/Lascar |
| **Classification** | NOVELTY |
| **License** | Present in repo |
| **Direction** | "Python → Malbolge" (character transformer) |
| **Variant** | Original |
| **Status** | Working as designed (but misleading name) |

**What it actually does** (from `src/malbolge_utils.py`):

```python
class Malbolge:
    __syntax = letters + digits + punctuation

    @staticmethod
    def convert(code: str) -> str:
        syntax = Malbolge.__syntax
        converted = str()
        for char in code:
            index = (ord(char) + randint(1, 10)) % len(syntax)
            converted += choice(syntax[index])
        return converted
```

This is a **character-level substitution cipher with randomization**. Each input character maps to a random Malbolge-legal character. There is NO parsing, NO AST, NO code generation, NO semantic preservation. The seed is fixed (`seed(38)`) for determinism, but the transformation is semantically meaningless.

**Verdict**: Novelty toy. The output does NOT preserve Python semantics in any way. NOT a compiler, NOT an interpreter, NOT a transpiler. Calling it a "Python to Malbolge converter" is misleading.

---

## 4. AppalachianMounta1n/Rustbolge

| Field | Value |
|-------|-------|
| **URL** | https://github.com/AppalachianMounta1n/Rustbolge |
| **Classification** | STUB |
| **License** | Present in repo |
| **Direction** | Rust → Malbolge (intended) |
| **Status** | Non-compiling scaffold |

**What it actually does** (from `src/main.rs`):

```rust
fn main() {
    let mut input = String::new();
    io:stdin().read_line(&mut input).expect("Failed to read input.");
    let mut cmd: [String; 2] = ["", ""];
    for i in input { }
    let output = Command::new("echo").arg(cmd).output().expect();
}
```

This code does not compile (`io:stdin()` is invalid Rust syntax, empty loop, type errors). Zero Malbolge functionality implemented.

---

## 5. Lou Scheffer BF→Malbolge

| Field | Value |
|-------|-------|
| **URL** | http://www.lscheffer.com/bf2malbolge.html |
| **Classification** | COMPILER_DESIGN |
| **License** | N/A (design document) |
| **Direction** | Brainfuck → Malbolge (algorithm description) |
| **Status** | Design only |

**What it actually is**: A prose document describing algorithms for compiling Brainfuck to Malbolge. Covers data representation (243-cell load/store), increment/decrement via table lookup, conditional branch via 243-way computed branch, load/store via crazy tricks. No executable code provided. States: "Here is an outline of how to build a compiler."

**Historical significance**: Foundational analysis. Scheffer discovered the 2-cycle in Malbolge's encryption table and showed systematic programming was possible. His "copy" program was hand-assembled, not BF-compiled.

**Implementation artifact**: NOT_DEMONSTRATED. The page is an algorithm description, not a working compiler.

---

## 6. ilyasergey/langlib

| Field | Value |
|-------|-------|
| **URL** | https://github.com/ilyasergey/langlib |
| **Classification** | FORMAL_SEMANTICS + COMPILER_DESIGN |
| **License** | Present in repo |
| **Direction** | Turpentine → Malbolge / Malbolge Unshackled |
| **Variant** | Both |
| **Status** | Active research, incomplete |

**What it actually does** (from `MalbolgeUnshackled.lean`, ~500 lines):

- `wordFor`: assembler core — every instruction at every address
- `legalCell`: what the loader accepts
- `twoStep`: two crazy operations to move accumulator between values
- `emitPlan`/`build`: code generator for straight-line output
- `compileProgram`: runs source at compile time, emits output bytes as Malbolge

**Critical limitation** (documented by the project itself): "the Malbolge Unshackled backend compiles only programs that do not read input." The docs trace this to a fundamental obstacle: no chain of crazy operations against compiled-in constants can produce a flag depending on the accumulator.

**The completeness claim is still `open`** — Turing-completeness proof for Malbolge Unshackled not yet mechanized in Lean. The full compiler requires a counter machine with rotation, branch gadgets, and re-enterable dispatcher, none wired in yet.

**Generated demos exist**: `primes.mu` (348 cells), `sort.mu` (268 cells), `99bottles.mu` (64,886 cells). These are real Malbolge Unshackled programs that run.

**Key insight from the code**: "The known way through all three is a **VM inside Malbolge**: hand-write an interpreter whose bytecode lives in *data* cells, which are never executed and so never encrypt. That is how every substantial Malbolge program has been produced."

**Verdict**: Most mathematically rigorous Malbolge project. Compiler is real but limited to input-free programs (genuine proven limitation). Formal semantics are genuine verified infrastructure. NOT a production compiler for general-purpose use.

---

## 7. wallstop/malbolge-toolkit

| Field | Value |
|-------|-------|
| **URL** | https://github.com/wallstop/malbolge-toolkit |
| **Classification** | OUTPUT_SYNTHESIS |
| **License** | Present in repo |
| **Direction** | Target string → Malbolge program (BFS synthesis) |
| **Status** | Working (43 commits, 18 stars) |

**What it actually does**: BFS algorithm that synthesizes Malbolge programs producing target strings. Starts with bootstrap `"i" + "o" * 99`, tries opcode suffixes, prunes dead branches, uses state signature caching. The interpreter is high-performance with cycle detection and snapshot extension.

**NOT a language compiler**. Generates programs by brute-force search that print a given string. Cannot compile arbitrary programs, handle control flow, or preserve semantics. Modern equivalent of Andrew Cooke's 2000 beam search.

---

## 8. esoteric-programmer/LMAO

| Field | Value |
|-------|-------|
| **URL** | https://github.com/esoteric-programmer/LMAO |
| **Classification** | COMPILER_TOOLCHAIN |
| **License** | GPL-3 |
| **Direction** | HeLL (assembly) → Malbolge |
| **Variant** | **Original Malbolge ONLY** |
| **Status** | Working (11 commits, 12 stars) |

**What it actually does**: Assembler translating HeLL (Hellish Low-level Language) to Malbolge. HeLL is a low-level assembly with `.CODE` sections (xlat2 cycle descriptions), `.DATA` sections (ternary constants), labels, block structure. Built with gcc/flex/bison/make.

**Variant support**: **Original Malbolge ONLY** (10-trit, 59049 words). The docs reference LMFAO as a separate tool for Malbolge Unshackled. LMAO does NOT support Unshackled.

**Key distinction**: LMAO is to Malbolge what NASM is to x86. It's the infrastructure layer, not a high-level compiler. MalbolgeLISP was assembled with LMAO/LMFAO (per primary evidence).

**Relevance to python.mb**: If we write the Python VM in HeLL, LMAO is the assembler. But it only targets Original Malbolge. For Unshackled, we need LMFAO or a different approach.

---

## 9. Nagoya University Toolchain

| Field | Value |
|-------|-------|
| **URL** | https://git.trs.css.i.nagoya-u.ac.jp/malbolge |
| **Classification** | COMPILER_TOOLCHAIN |
| **License** | MIT |
| **Direction** | C subset → Malbolge20 |
| **Variant** | Malbolge20 |
| **Status** | Working (last commit 2021) |

**Three-stage pipeline**: `highlevel` (C → `.mg`), `ternary` (`.mg` → LAL), `lowass` (LAL → Malbolge20). C++/flex/bison/Perl implementation.

**Foundation for pyMalbolge** (Aiaid fork is a pure-Python port). Not directly usable for Original or Unshackled Malbolge.

---

## Summary Classification Table

| # | Project | Classification | Actually Works? | Relevant to python.mb? |
|---|---------|---------------|----------------|----------------------|
| 1 | Aiaid/pyMalbolge | COMPILER_TOOLCHAIN | Yes (441 tests) | Toolchain design reference |
| 2 | Avantgarde95/pyMalbolge | HOSTED_INTERPRETER | Yes (trivial) | Historical only |
| 3 | Vai-Te/Lascar | NOVELTY | As designed (misleading) | No |
| 4 | Rustbolge | STUB | No (doesn't compile) | No |
| 5 | Lou Scheffer | COMPILER_DESIGN | N/A (design doc) | Algorithm reference |
| 6 | LangLib | FORMAL_SEMANTICS + COMPILER_DESIGN | Partial (input-free only) | VM-in-Malbolge insight |
| 7 | malbolge-toolkit | OUTPUT_SYNTHESIS | Yes | Interpreter useful |
| 8 | LMAO | COMPILER_TOOLCHAIN | Yes (Original only) | HeLL→Malbolge assembler |
| 9 | Nagoya | COMPILER_TOOLCHAIN | Yes (Malbolge20) | pyMalbolge foundation |

## Key Finding

**NO_PRIOR_IMPLEMENTATION_FOUND_IN_SEARCH_AS_OF_2026_09_02 for a Python interpreter that runs ON Malbolge (Python semantics executed by Malbolge code).**

The two closest precedents:
1. **pyMalbolge**: Compiles Python TO Malbolge20 (forward direction, subset only, different variant)
2. **MalbolgeLisp**: Implements Lisp interpreter AS Malbolge Unshackled source (reverse direction, right pattern, wrong language)

Building `python.mb` (Python interpreter as Malbolge source) would be **unprecedented** as of this survey date.
