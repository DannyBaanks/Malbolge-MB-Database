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

## Runner Verification Status (A01)

Runner availability is now verified by the runner doctor, not assumed.

```text
A01_RUNNER_DOCTOR = DEMONSTRATED
```

Run the doctor:

```
py powershell tools/runner_doctor.ps1
```

It verifies for each runner:
1. binary exists,
2. SHA256 matches the manifest,
3. a known-vector program executes (`hello_world_40.mb` -> "Hello World!"),
4. the expected variant is enforced (variant firewall),
5. exit code / steps / status are captured.

It also cross-checks the Classic runner against an independent Python oracle
(`tools/oracle_classic.py`, 3^10 reference) — both agree on
`hello_world_40.mb` -> "Hello World!" at 40 steps, HALTED.

Reproducibility caveat: `tools/bootstrap_runners.ps1` can rebuild both runners
from source, but a fresh gcc/zig rebuild produces different bytes than the
committed binaries (toolchain/compiler drift). The committed binaries are
authoritative and their SHA256 is pinned in the manifests; the doctor verifies
against those pinned hashes.

Scripts:
- `tools/bootstrap_runners.ps1` — rebuild runners from source, verify hash (compare-first; never clobbers a matching committed binary)
- `tools/runner_doctor.ps1` — the integrity/known-vector doctor

## Acceptance Rule

A `.mb` file is not validated until:
1. It executes on the declared runner
2. Output matches expected
3. Steps/status are recorded
4. SHA256 of the artifact is recorded
5. Evidence JSON is produced
