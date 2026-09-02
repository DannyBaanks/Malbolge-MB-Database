# Runners

Reproducible Malbolge execution environments.

## Currently Available

| Runner | Variant | Status | Binary | SHA256 |
|--------|---------|--------|--------|--------|
| bolge19 | Unshackled (3^19) | BUILT | `malbolge-unshackled/bolge19.exe` | `58D0B5E8...` |
| malbolge-engine | Original (3^10) | COPIED | `malbolge-original/malbolge.exe` | `9A7AD87E...` |
| malbolge20 | Malbolge20 | NOT_AVAILABLE | — | — |

## bolge19 (Unshackled)

- **Source**: `malbolge-lisp-forensics/src/bolge19/main.zig`
- **License**: MIT
- **Build**: `zig build-exe -O ReleaseFast main.zig -femit-bin=bolge19.exe`
- **Platform**: Windows native (no Cygwin, no mmap)
- **CLI**: `bolge19.exe <image.mb> [--max-steps N]`
- **Verified**: MalbolgeLISP v1.2 boots, `(+ 1 2)` → `3`

## malbolge-engine (Classic)

- **Source**: `Malbolge-Engine/src/vm.c`
- **License**: MIT
- **Build**: `make`
- **Platform**: Windows (pre-built exe)
- **CLI**: `malbolge.exe <input.mb`
- **IPC**: `malbolge-ipc.exe` (JSONL protocol)
- **Limitation**: 3^10 only — cannot run Unshackled programs

## Bootstrap Scripts

- `tools/bootstrap_runners.ps1` — download/build all runners
- `tools/runner_doctor.ps1` — verify runner integrity

## Acceptance Rule

A `.mb` file is not validated until:
1. It executes on the declared runner
2. Output matches expected
3. Steps/status are recorded
4. SHA256 of the artifact is recorded
5. Evidence JSON is produced
