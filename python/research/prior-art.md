# Python / Malbolge — Prior Art Survey

**Date**: 2026-09-02
**Method**: Web search for existing projects combining Python and Malbolge

---

## 1. pyMalbolge (Python → Malbolge20 Compiler)

| Field | Value |
|-------|-------|
| **URL** | https://github.com/Aiaid/pyMalbolge |
| **Author** | Anend (fork of Avantgarde95/pyMalbolge) |
| **License** | MIT |
| **Direction** | Python subset → Malbolge20 |
| **Variant** | Malbolge20 |
| **Status** | Working (441 tests) |
| **Relevance** | CRITICAL — closest existing project |

**What it does**: Pure-Python compiler from a Python subset to Malbolge20. Two backends: `py2c` (Python AST → Nagoya C subset) and `py2mg` (Python AST → `.mg` pseudo-instructions directly).

**Python subset supported**: `print()`, `for i in range(...)`, `while`, `if/elif/else`, `break`/`continue`, chained comparisons, short-circuit `and`/`or`, `*`/`//`/`%`. No classes, no imports, no closures, no `input()`, no strings beyond constant args to `print()`.

**Pipeline**: Python AST → Nagoya C subset → `.mg` → `.mc` (LAL) → `.mb` (Malbolge20).

**Relevance to python.mb**: Architecture is directly reusable but targets Malbolge20 (not Original or Unshackled). Compiles Python TO Malbolge (not an interpreter).

---

## 2. Nagoya University Toolchain (C → Malbolge20)

| Field | Value |
|-------|-------|
| **URL** | https://git.trs.css.i.nagoya-u.ac.jp/malbolge |
| **License** | MIT |
| **Direction** | C subset → Malbolge20 |
| **Variant** | Malbolge20 |

**What it does**: Three-stage compiler: `highlevel` (C → `.mg`), `ternary` (`.mg` → LAL), `lowass` (LAL → Malbolge20).

**Papers**: Kato et al. 2013, Kanbe et al. 2016, Sakanashi et al. 2017.

**Relevance**: Foundation for pyMalbolge. Not directly usable for Original or Unshackled Malbolge.

---

## 3. MalbolgeLisp

| Field | Value |
|-------|-------|
| **URL** | https://github.com/iczelia/malbolge-lisp |
| **Author** | Kamila Szewczyk |
| **License** | GPLv3 (core.mb: CC0) |
| **Direction** | Lisp runtime AS Malbolge source |
| **Variant** | Malbolge Unshackled |
| **Status** | Working |

**What it does**: Full Lisp interpreter (~371 MB compiled) written as Malbolge Unshackled source. Supports `define`, `defun`, `lambda`, `cond`, `let`, `if`, `atom`, `cons`, `car`, `cdr`, higher-order programming, partial application, TCO.

**Architecture**: VM-in-Malbolge pattern. Bytecode/data stored in data cells (never executed, so never encrypted). Dispatch loop written in Malbolge instructions.

**Relevance**: CRITICAL PRECEDENT. Proves the pattern we need for python.mb: interpreter written as Malbolge source with bytecode in data cells.

---

## 4. Lou Scheffer's BF→Malbolge

| Field | Value |
|-------|-------|
| **URL** | http://www.lscheffer.com/bf2malbolge.html |
| **Direction** | Brainfuck → Original Malbolge |
| **Variant** | Original |

**What it does**: Compiles Brainfuck to Original Malbolge. Uses 243-cell load/store architecture, table lookup for arithmetic.

**Relevance**: Essential techniques for compiling to Original Malbolge.

---

## 5. LMAO / HeLL

| Field | Value |
|-------|-------|
| **URL** | https://github.com/esoteric-programmer/LMAO |
| **Author** | Matthias Lutter |
| **Direction** | HeLL → Malbolge / Unshackled |
| **Variant** | Both |

**What it does**: Assembler for HeLL (Hellish Low-level Language) producing Malbolge or Unshackled output.

**Relevance**: Toolchain for writing substantial Malbolge programs. Used to build MalbolgeLisp.

---

## 6. malbolge-lisp-forensics

| Field | Value |
|-------|-------|
| **URL** | https://github.com/DannyBaanks/malbolge-lisp-forensics |
| **Direction** | Forensic analysis |
| **Variant** | Both |

**What it does**: Forensic analysis of MalbolgeLisp. Includes `bolge19` (native Windows Zig VM). Identifies Cygwin mmap issue.

**Relevance**: Practical runner for Unshackled on Windows.

---

## 7. Other Malbolge Interpreters

| Project | Language | Notes |
|---------|----------|-------|
| return/malbolge | Rust | Interpreter + cat program |
| cmannett85/malbolge | C++20 | VM implementation |
| zb3/malbolge-vm | Node.js | Step-by-step execution |
| mfourne/malbolge2 | Haskell | Unshackled support (2025) |

---

## Key Finding

**NO project implements a Python interpreter that runs ON Malbolge.**

The two closest precedents:
1. **pyMalbolge**: Compiles Python TO Malbolge20 (forward direction, subset only, different variant)
2. **MalbolgeLisp**: Implements Lisp interpreter AS Malbolge Unshackled source (reverse direction, right pattern, wrong language)

Building `python.mb` (Python interpreter as Malbolge source) would be **unprecedented**.

## Architectural Model

The proven pattern from MalbolgeLISP:

```
1. Write interpreter in HeLL/LMAO (assembly language for Malbolge)
2. Store bytecode in data cells (never executed, so never encrypted)
3. Dispatch loop in Malbolge instructions reads data cells
4. Assemble to Malbolge Unshackled binary
5. Execute with fast20.c
```

For python.mb:
1. Design MalPy bytecode format
2. Write Python VM (stack machine) in HeLL/LMAO
3. Store MalPy bytecode in data cells
4. Compile Python source to MalPy on host (initially)
5. Later: build lexer/parser in Malbolge too (P6-P7)
