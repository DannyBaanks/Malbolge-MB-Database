# A00 — Epistemic Repair Evidence

## Verdict

```text
A00_EPISTEMIC_REPAIR = DEMONSTRATED
```

## What was corrected

All 12 findings from the adversarial audit (`AUDIT_FINDINGS.md`) were
reproduced against the live repo and patched.

| ID | Finding | Resolution |
|----|---------|-----------|
| F01 | P1 overclaimed Malbolge hosting | P1 reclassified to REFERENCE_DEMONSTRATED |
| F02 | P2 docstring claimed Malbolge-hosted runtime | P2 reclassified to FRONTEND_DEMONSTRATED |
| F03 | P0 claimed pipeline but no artifact | P0 set to NOT_DEMONSTRATED, anti_fake=False |
| F04 | "infeasible" wording too strong | Reworded to NOT_DEMONSTRATED by current impl |
| F05 | Test harness claimed runner validation | Header corrected; reference-only; 21/21 pass |
| F06 | Label/module-name hashes | Replaced with source-content SHA-256 |
| F07 | `len(stack) < 0` impossible guard | Fixed to `< 1`; underflow negative tests added |
| F08 | artifacts.json empty vs runtime claim | registry runtime_demonstrated=false |
| F09 | README cited absent scripts | Marked as A01 planned |
| F10 | Manifests unverified | Documented as claims pending A01 doctor |
| F11 | Evidence model lacked kinds | Added evidence_kind taxonomy to EVIDENCE_MODEL.md |
| F12 | "required"/"too constrained" variant claims | Reworded to PRIMARY_TARGET/design choice |

## Gate test

Searched tracked files for phrases implying Malbolge-hosted execution that is
not demonstrated:

- "runs on Malbolge" — remaining occurrences are design definitions and
  prior-art findings (no project implements it), not claims about our code
- "infeasible/impossible" for our arithmetic — removed from p0_compiler.py/STATUS
- "P1/P2 = DEMONSTRATED" (unqualified) — removed; now REFERENCE/FRONTEND_DEMONSTRATED

## Honest current status

```text
PYTHON_REFERENCE_VM                = DEMONSTRATED (Python host)
PYTHON_AST_TO_MALPY_BYTECODE       = DEMONSTRATED (restricted subset)
MALBOLGE_HOSTED_MALPY_VM           = NOT_DEMONSTRATED
PYTHON_MB_INTERPRETER              = NOT_DEMONSTRATED
SWIFT_MB                           = NOT_STARTED
```

## Test results

- `py python/tests/test_harness.py` → 21/21 PASS (was 18/18; +3 negative tests)

## Supersession note

The earlier `run_p1_vm.json` / `run_p2_compiler.json` records asserted
`anti_fake_satisfied = True` and unqualified `DEMONSTRATED` verdicts. These
were superseded by the corrected records in this commit, which set
`evidence_kind` and label the Malbolge-hosted runtime as NOT_DEMONSTRATED.

## Next phase

```text
A01_RUNNER_DOCTOR = NOT_DEMONSTRATED  (implement bootstrap_runners.ps1 + runner_doctor.ps1)
```