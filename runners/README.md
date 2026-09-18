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

## External Substrates (the -bolge family)

The engine family around the vendored runners — *Rustbolge, Swiftbolge, Javolge,
Cobolge, Fortranbolge, Zigbolge, Pibolge, Pibolge19, Wasmbolge, MalbolgeEngineCPP,
malbolge-free, malbolge-oracle, MalboGost* — is registered **by reference**, not
vendored (see `DATABASE.md`: engines are separate backends, not imports into this
repository). Each substrate has a `runners/<name>/manifest.json` following the
same manifest schema as the vendored runners, with:

- `vendored_binary: false` / `binary_sha256: null` — the binary lives in its own
  repository; build it with the manifest's `build_command`.
- `registration.status: "CLAIM"` — per `docs/EVIDENCE_MODEL.md`, every claim
  (gate tuple, cross-checks, snapshot hashes) is cited from the substrate's own
  README/evidence and stays a CLAIM until independently rebuilt and gate-executed.
- `source_commit` — the HEAD hash of the substrate's repo at registration time,
  re-verified against live git during registration (2026-09-18: 14/14 match).

Machine-readable index: `registry/substrates.json` (schema `substrates/1`),
with cross-family evidence pointers (six_bolge_challenge; the step-17 snapshot
SHA-256 `29372AAD…` shared by Rustbolge/Swiftbolge/Javolge/Cobolge; the
documented EOF divergence D5) and a verification block sealing the SHA-256 of
each manifest.

| Substrate | Variant | Host language | Role |
|-----------|---------|---------------|------|
| rustbolge | original | Rust | fast VM + snapshot/resume JSON |
| swiftbolge | original | Swift | fast VM; resumes Rustbolge snapshots |
| javolge | original | Java | zero-dependency JVM VM + snapshots |
| cobolge | original (+19 in-repo) | GnuCOBOL | enterprise VM + local 3^19 runtime |
| fortranbolge | original (+19 in-repo) | Fortran 2008 | numerics-language VM + local 3^19 runtime |
| zigbolge | original | Zig | minimal VM |
| pibolge | original (+19 in-repo) | Pitón | esolang-hosted VM (needs PITON) |
| pibolge19 | unshackled | Pitón | bit-exact 3^19 port of bolge19 |
| wasmbolge | original (+19 ABI) | Rust→wasm32 | embeddable ABI (Node verified; browser NOT_DEMONSTRATED) |
| malbolgeenginecpp | original | C++20 | embeddable library + step tracing |
| malbolge-free | free | Zig | Free dialect (w-variable) — NOT Classic |
| malbolge-oracle | original | Python | REFERENCE_MODEL: the independent control |
| malbogost | original | C | Classic VM + Malbolge-hosted frontend |

Cross-check harness (not a runner — it contains no interpreter):
`malbolge-differential` (`python -m mdiff.diff <program.mb>`) runs the same
program across `engine` / `oracle` / `rust` backends and records divergences
(`findings/D5_eof_halt_vs_59048.md`).

The runner doctor (`tools/runner_doctor.ps1`) covers only the VENDORED runners
above; it deliberately does not pass/fail these CLAIM substrates.

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
