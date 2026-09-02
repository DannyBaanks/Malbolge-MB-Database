# Evidence Model

## Principle

Every claim about a `.mb` program must be backed by reproducible evidence. The evidence model defines what to record, how to store it, and how to verify it.

## Evidence Kind

Every evidence record must declare an `evidence_kind`. This prevents reference
work (a Python VM) from being mistaken for Malbolge-runtime evidence.

| Kind | Meaning |
|------|---------|
| `REFERENCE_MODEL` | Oracle/reference implementation on the host (e.g. Python VM). Host language must be stated. |
| `FRONTEND` | Source-language → MBIR/bytecode compiler. Does NOT imply Malbolge execution. |
| `MBIR_CONFORMANCE` | Bytecode validates against a frozen MBIR contract. |
| `MALBOLGE_RUNTIME` | A `.mb` artifact executes semantics on a declared Malbolge runner. |
| `END_TO_END` | Source → frontend → MBIR → Malbolge runtime → output, equality against oracle. |
| `RUNNER_PROVENANCE` | Runner binary/source provenance, doctor checks, known-vector execution. |

Rule: an `evidence_kind` of `REFERENCE_MODEL` or `FRONTEND` must NOT be labeled
`runtime = Malbolge`. Only `MALBOLGE_RUNTIME` / `END_TO_END` evidence implies
Malbolge-hosted execution.

## Evidence Directory Structure

```
<language>/evidence/
├── P0/                    ← milestone directory
│   ├── README.md          ← what was attempted
│   ├── run_YYYYMMDD.json  ← execution record
│   └── artifacts/         ← generated .mb files
├── P1/
│   └── ...
└── ...
```

## Execution Record Schema

Each execution produces a JSON record:

```json
{
  "timestamp": "2026-09-02T12:00:00Z",
  "milestone": "P0",
  "command": "py malbolge_interpreter.py < input.mb",
  "input": {
    "description": "Arithmetic kernel: 2+3",
    "sha256": "abc123..."
  },
  "stdout": "5",
  "stderr": "",
  "exit_code": 0,
  "runtime": {
    "name": "malbolge-interpreter-py",
    "version": "1.0",
    "sha256": "def456...",
    "variant": "original"
  },
  "steps": 48,
  "wall_time_ms": 1200,
  "artifacts": [
    {
      "path": "artifacts/arithmetic_v1.mb",
      "sha256": "789abc...",
      "size_bytes": 2048,
      "variant": "original"
    }
  ],
  "expected": {
    "output": "5",
    "status": "HALTED"
  },
  "observed": {
    "output": "5",
    "status": "HALTED"
  },
  "verdict": "PASS"
}
```

## Verdict Values

| Verdict | Meaning |
|---------|---------|
| `PASS` | Expected matches observed |
| `FAIL` | Expected does not match observed |
| `TIMEOUT` | Execution exceeded step limit |
| `CRASH` | Runtime error or invalid state |
| `NOT_DEMONSTRATED` | Insufficient evidence to judge |

## Artifact Classification

Each `.mb` artifact must record:

| Field | Description |
|-------|-------------|
| `language` | Target language (e.g., "python") |
| `artifact` | Filename (e.g., "python.mb") |
| `variant` | Malbolge variant it requires |
| `purpose` | What it implements |
| `source_stage` | How it was produced (handwritten, compiled, generated) |
| `generated_or_handwritten` | "generated" or "handwritten" |
| `toolchain` | Tools used to produce it |
| `size_bytes` | File size |
| `sha256` | Content hash |
| `runner` | Which interpreter runs it |
| `expected_behavior` | What it should do |
| `observed_behavior` | What it actually did |
| `status` | Current status code |
| `evidence` | List of evidence record paths |

## Provenance Requirements

Every generated artifact must have:

1. **Source files** that produced it
2. **Tool versions** (exact, with SHA256 when possible)
3. **Generation command** (copy-pasteable)
4. **Input hashes** (SHA256 of all inputs)
5. **Output hash** (SHA256 of the artifact)
6. **Variant** declared
7. **Timestamp** of generation

If the toolchain introduces non-determinism, document it explicitly.

## Anti-Fake Rule

An artifact that prints a constant string does NOT demonstrate computation. To prove arithmetic:

```
PUSH 2
PUSH 3
ADD
PRINT
```

must be demonstrably different from:

```
PRINT "5"
```

Evidence must show the operational representation, not just the output.

## Verification Chain

```
1. Artifact exists on disk
2. SHA256 matches recorded hash
3. Runner executes it
4. Output matches expected
5. Steps/status match expected
6. Evidence record exists with all fields
7. Independent reproduction possible
```

Steps 1-6 are mandatory. Step 7 is aspirational but strongly recommended.
