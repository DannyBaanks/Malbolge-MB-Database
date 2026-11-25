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
- `b2t/` — `b2t.py`, binary⇄ternary cell codec (B2T0): packs a byte stream
  into 15-bit groups, each into one 10-trit Malbolge cell (`2^15 < 3^10`),
  with a strict container (bit length, CRC-32, reserved-cell rejection);
  `dispatch.py` executes the transported MBIR v0 payload via `mbir_ref` and
  traces every VM step back to the cells carrying the dispatched bytes;
  `test_b2t.py` covers the full round trip and the whole 32,768-value payload
  space, `test_dispatch.py` the dispatch/trace bridge.

## How to use

```
py powershell tools/runner_doctor.ps1    # verify runners (fast, no build)
py powershell tools/bootstrap_runners.ps1 # rebuild + hash-check runners
python3 tools/b2t/b2t.py inspect input.b2t # show cells/metadata (encode/decode too)
python3 tools/b2t/dispatch.py run input.b2t --trace # execute MBIR payload, trace steps→cells
```

## Planned

- `run_mb.py` — execute `.mb` files with a specified runner
- `verify.py` — check artifact hashes and evidence records
- `generate_evidence.py` — produce evidence JSON from execution