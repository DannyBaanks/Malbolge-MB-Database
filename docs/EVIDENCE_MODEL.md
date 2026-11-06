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

## Path Normalization in Evidence

Evidence records and generated artifacts must not embed the author's absolute
workstation paths. A published evidence record has to be readable and
re-checkable on a machine that is not the author's.

| Kind of reference | Required form | Example |
|---|---|---|
| File inside this repository | Repository-relative path | `vm_malbolge/src/mbir_alu.hell` |
| Tool outside this repository | Workspace-relative or descriptive location | `_external/LMAO/lmao.exe` |
| Historical ledger (append-only) | Left verbatim | see `vm_malbolge/LT_STATUS.md` |

### Normalization applied on 2026-11-06

The following records carried the build machine's absolute path and were
normalized in place, changing **only** the path strings — no measured value,
verdict, step count, output byte or hash of an artifact was altered:

| File | Field | Before | After |
|---|---|---|---|
| `vm_malbolge/evidence/mbir_zig_oracle_{a04_gate,a05_lifo,a05_twopush_match,alu,p0_add,p1_sub}.json` | `result.hell_source` | absolute path | repository-relative |
| `vm_malbolge/evidence/push_const_{cell_operand,dispatch_cell,later_fetch}_smoke.json` | `artifact.assembly_command` | `wine <abs>/_external/LMAO/lmao.exe …` | `wine _external/LMAO/lmao.exe …` |
| `vm_malbolge/src/mbir_{a05_lifo,m2_alu,m2_cf,m2_cf_cmp}.dbg` | `:SOURCE_FILE:` and `:MALBOLGE_FILE:` | absolute path | repository-relative |

The two evidence records that pin a `.dbg` hash
(`mbir_m2_alu_smoke.json`, `mbir_m2_cf_smoke.json`) had their `debug_sha256`
field updated to the hash of the normalized file.

### Second pass, 2026-11-06: case-mismatched variant

Three further records carried the *same* workstation path in its Windows
spelling — `C:` backslash `Development` backslash `ISyCo Git` backslash
`MALBOLGE-MB-DATABASE`, stored JSON-escaped — and were missed by the first pass
because that sweep matched the Linux path spelling only. They are normalized
here, again changing **only** the path string:

| File | Field | Before | After |
|---|---|---|---|
| `vm_malbolge/evidence/mbir_zig_oracle_halt_v3.json` | `result.hell_source` | `C:\…\vm_malbolge\src\byte_dispatch18.hell` | `vm_malbolge\src\byte_dispatch18.hell` |
| `vm_malbolge/evidence/mbir_zig_oracle_push_const_v3.json` | `result.hell_source` | `C:\…\vm_malbolge\src\byte_push_const_out.hell` | `vm_malbolge\src\byte_push_const_out.hell` |
| `vm_malbolge/evidence/mbir_zig_oracle_push_const_missing_halt_v3.json` | `result.hell_source` | `C:\…\vm_malbolge\src\byte_push_const_out.hell` | `vm_malbolge\src\byte_push_const_out.hell` |

Their hashes are pinned in `vm_malbolge/evidence/mbir_zig_oracle_hashes.json`,
which was updated to the hashes of the normalized files; the four records it
pins were re-verified to match.

### Caveat: the repo-engine gate misses the JSON-escaped spelling

`repo-engine doctor` reported 0 findings over 370 files both before and after
this second pass. The reason is not case: the three records above store the path
in its JSON-escaped spelling (a doubled backslash between components), and the
gate's `LOCAL_PATH_001_DOC` pattern does not match that spelling. The gate also
fires on this very document when the path is written in its plain spelling, so a
gate-clean report is not evidence that no workstation path is embedded —
normalization here is driven by the policy in this document, and the gate is
only a second check. Sweeps for embedded paths should try both spellings.

### Caveat: LMAO regenerates absolute paths in `.dbg`

LMAO v0.6.0 writes the build machine's absolute paths into the
`:SOURCE_FILE:` and `:MALBOLGE_FILE:` sections of a `.dbg` symbol map. A fresh
build therefore reproduces those two lines with the local absolute path, while
the committed `.dbg` files carry the repository-relative form. Everything else
in a `.dbg` — labels, address map, `:XLAT2:` table and
`:EXECUTION_STEPS_UNTIL_ENTRY_POINT:` — is byte-identical to LMAO's output.

This is the same class of hazard as the `.mb` end-of-line drift recorded in
the Finding 55 addendum: the committed artifact is canonical, and a rebuild
differs only in machine-local metadata.

### Exception: the append-only ledger

`vm_malbolge/LT_STATUS.md` keeps the exact shell commands of Findings 71-73
verbatim, including the workstation path they contain. That file is an
append-only historical ledger by repository convention and its command blocks
are evidence, so it is **not** rewritten; it is covered by a narrow
`.repo-engine-exceptions.toml` entry instead.

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
