# A01 — Runner Doctor Evidence

## Verdict

```text
A01_RUNNER_DOCTOR = DEMONSTRATED
```

## What was implemented

- `tools/runner_doctor.ps1` — runner integrity doctor.
- `tools/bootstrap_runners.ps1` — rebuild-from-source + hash-check.
- `tools/oracle_classic.py` — independent Classic (3^10) Python oracle.
- `tools/fixtures/hello_world_40.mb` — known-vector Classic program.
- `runners/*/manifest.json` — added `reproducible` + reproducibility note.

## Doctor checks (per runner)

1. binary exists
2. SHA256 matches the committed manifest
3. known-vector executes (`hello_world_40.mb` -> "Hello World!")
4. expected variant enforced (variant firewall)
5. exit code / steps / status captured

Plus an independent cross-check: `oracle_classic.py` (3^10 reference) on the
same fixture -> "Hello World!", 40 steps, HALTED — agreeing with the C engine.

## Result

```text
PASS: 15   FAIL: 0   (runner_doctor.ps1, exit 0)
```

- malbolge-engine (Classic): binary present, SHA256 matches, "Hello World!",
  40 steps, HALTED, exit 0.
- bolge19 (Unshackled): binary present, SHA256 matches, executes (exit 0),
  variant enforced (does NOT reproduce Classic output on 19-trit — correct
  variant firewall behavior).
- oracle_classic.py: "Hello World!", 40 steps, HALTED (matches C engine).

## Reproducibility caveat (honest)

`bootstrap_runners.ps1` rebuilds both runners from source, but a fresh
gcc/zig rebuild produces DIFFERENT bytes than the committed binaries
(toolchain/compiler drift — local gcc 16.1.0 / zig 0.16.0 differ from the
original build environments). Measured:

| Runner | committed SHA256 | fresh rebuild SHA256 | reproducible? |
|--------|------------------|----------------------|---------------|
| malbolge-engine | `9A7AD87E...` | `9767BC5B...` | no |
| bolge19 | `58D0B5E8...` | `370B312A...` | no |

The committed binaries are authoritative; the doctor verifies against the
pinned manifest hashes. The bootstrap is compare-first and never overwrites a
matching committed binary with a non-matching rebuild.

## Evidence kinds

- `RUNNER_PROVENANCE` — manifest hashes, doctor checks.
- `REFERENCE_MODEL` — oracle_classic.py cross-check.

## Artifact hashes (this record)

```
956C134AA67FA3FC049BDA71406673050B64B18663EE603B16C7B694E13FE6C1  tools/fixtures/hello_world_40.mb
5DAE8F31EAA296FDC5BB1A65B9BAB93E94B3F230DE5D1929D5D5D904DD4778CF  tools/oracle_classic.py
4AE7E15A70FFEAEC6AACF5B4060183D5BB4391548F73CE26229AD3E9910BF9FE  tools/runner_doctor.ps1
A63A0040615E3EE747A6B7B3018E33A730CDA5C15048C80288A09F75F64813B4  tools/bootstrap_runners.ps1
```

## Next phase

```text
A02_MBIR_CONTRACT = NOT_DEMONSTRATED  (freeze language-neutral MBIR)
```