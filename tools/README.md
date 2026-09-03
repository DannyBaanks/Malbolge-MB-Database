# Tools

Build, run, and test utilities.

## Available (A01)

- `bootstrap_runners.ps1` — rebuild Malbolge runners from source, verify their
  SHA256 against the committed manifests (compare-first; never clobbers a
  matching committed binary).
- `runner_doctor.ps1` — verify runner integrity: binary presence, SHA256 vs
  manifest, known-vector execution, variant enforcement, exit/steps capture.
- `oracle_classic.py` — independent Classic (3^10) Malbolge interpreter used
  by the doctor as a reference cross-check.
- `fixtures/hello_world_40.mb` — known-vector Classic program
  (output "Hello World!" at 40 steps, HALTED; cross-verified against the
  C engine and the Python oracle).

## How to use

```
py powershell tools/runner_doctor.ps1    # verify runners (fast, no build)
py powershell tools/bootstrap_runners.ps1 # rebuild + hash-check runners
```

## Planned

- `run_mb.py` — execute `.mb` files with a specified runner
- `verify.py` — check artifact hashes and evidence records
- `generate_evidence.py` — produce evidence JSON from execution