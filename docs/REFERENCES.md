# References

## Primary References

### MalbolgeLisp
- **Repository**: https://github.com/iczelia/malbolge-lisp
- **Author**: Kamila Szewczyk (iczelia / kspalaiologos / Palaiologos)
- **License**: GPLv3 (core.mb: CC0-1.0)
- **Paper**: `MalbolgeLisp.pdf` in repository
- **Variant**: Malbolge Unshackled (fast20.c, 19-trit rotation)
- **Significance**: Most complex Malbolge program ever created; proves VM-in-Malbolge pattern for high-level language interpreters
- **Size**: ~371 MB compiled

### pyMalbolge
- **Repository**: https://github.com/Aiaid/pyMalbolge
- **Author**: Anend (fork of Avantgarde95/pyMalbolge)
- **License**: MIT
- **Direction**: Python subset → Malbolge20 compiler
- **Significance**: Closest existing project to python.mb; compiles Python to Malbolge (different direction but reusable architecture)
- **Tests**: 441 passing

### Nagoya University Toolchain
- **Repository**: https://git.trs.css.i.nagoya-u.ac.jp/malbolge
- **Project**: https://www.trs.cm.is.nagoya-u.ac.jp/projects/Malbolge/
- **License**: MIT
- **Direction**: C subset → Malbolge20 (three-stage compiler)
- **Papers**: Kato et al. 2013, Kanbe et al. 2016, Sakanashi et al. 2017

### LMAO / HeLL
- **Repository**: https://github.com/esoteric-programmer/LMAO
- **Author**: Matthias Lutter
- **Purpose**: Assembler for HeLL (Hellish Low-level Language) → Malbolge / Unshackled
- **Significance**: Toolchain used to build MalbolgeLisp and other complex Malbolge programs

### malbolge-lisp-forensics
- **Repository**: https://github.com/DannyBaanks/malbolge-lisp-forensics
- **Purpose**: Forensic analysis of MalbolgeLisp; includes `bolge19` (native Windows Zig VM)
- **Findings**: Identifies Cygwin mmap issue; validates Classic Malbolge across 4 backends

### Lou Scheffer's BF→Malbolge
- **URL**: http://www.lscheffer.com/bf2malbolge.html
- **Direction**: Brainfuck → Original Malbolge compiler
- **Significance**: Essential techniques for compiling to Original Malbolge (managing self-modification, crazy operation lookup tables)

## Malbolge Specification

### Original
- Ben Olmstead's original specification
- 59049 cells (3^10), 10-trit words
- Instructions: values 33-126 (printable ASCII)

### Unshackled
- Extension by Ben Olmstead
- 3^19 or 3^20 cells
- Same instruction encoding, wider words
- Requires custom interpreter (fast20.c)

### Malbolge20
- Formalized by Nagoya University
- 20-trit words
- Toolchain: highlevel → ternary → lowass

## ISyCo Genealogy

Local reference (read-only, ISyCo workspace):
```
<ISYCO_GIT_ROOT>/GENEALOGIA_MALBOLGE/
```

Key documents:
- `CAPABILITY_MATRIX.md` — quick capability lookup
- `CLASSIC.md` — Classic-preserving resources
- `UNSHACKLED.md` — Unshackled resources
- `GENERATORS.md` — code generators
- `SEARCHERS.md` — search/synthesis engines
- `INTERPRETERS.md` — independent runtimes
- `VERIFIED_PRIMITIVES.md` — actually executed programs
- `KNOWN_BLOCKERS.md` — current limits
- `PROVENANCE.md` — audit trail and evidence rules
