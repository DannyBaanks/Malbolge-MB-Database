# Runners

Reproducible Malbolge execution environments.

## Directory Structure

```
runners/
├── malbolge-original/     ← 10-trit Classic (59049 cells)
├── malbolge-unshackled/   ← 19-20 trit Unshackled (~1T cells)
├── malbolge20/            ← Nagoya Malbolge20
└── README.md              ← this file
```

## Runner Requirements

Every runner must document:

1. **Source**: Where the interpreter code came from
2. **Version**: Exact version or commit hash
3. **Build command**: How to compile it
4. **Compiler**: Which compiler and version
5. **Flags**: Compilation flags
6. **SHA256**: Hash of the built binary
7. **Platform**: OS and architecture requirements
8. **Limitations**: Known issues or patches needed

## Acceptance Rule

A `.mb` file is not validated until:
1. It executes on the declared runner
2. Output matches expected
3. Steps/status are recorded
4. SHA256 of the artifact is recorded
5. Evidence JSON is produced

## Currently Available

| Runner | Status | Source | Notes |
|--------|--------|--------|-------|
| malbolge-original | NOT_AVAILABLE | — | Need to build from source |
| malbolge-unshackled | NOT_AVAILABLE | — | Need fast20.c or bolge19 |
| malbolge20 | NOT_AVAILABLE | — | Need Nagoya toolchain |

## Building Runners

### Original Malbolge (Python reference interpreter)

From ISyCo `workspace/assembly/malbolge/malbolge_interpreter.py`:
- Canonical Python interpreter
- 59049 cells, 10-trit words
- Verified against Wikipedia Hello World (48 steps)

### Unshackled (fast20.c)

Source: MalbolgeLISP repository or malbolge-lisp-forensics
- `fast20.c` or `bolge19` (Zig)
- Build: `clang -O3 -march=native fast20.c -o fast20`
- Windows: may need `mprotect` patch instead of `mmap(MAP_FIXED)`
