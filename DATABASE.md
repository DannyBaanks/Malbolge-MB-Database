# DATABASE.md

Navigation map for the Malbolge MB Database.

## Quick Start

1. `docs/DEFINITIONS.md` — what "MB", "Classic", "Unshackled", ".mb" mean
2. `docs/VARIANTS.md` — Malbolge variant inventory and differences
3. `docs/EVIDENCE_MODEL.md` — how results are recorded and verified
4. `docs/REFERENCES.md` — external sources and citations
5. `registry/languages.json` — machine-readable language track metadata
6. `registry/artifacts.json` — machine-readable artifact inventory

## Language Tracks

| Track | Directory | Status | Active? |
|-------|-----------|--------|---------|
| Python | `python/` | REFERENCE_FRONTEND | Yes |
| Swift | `swift/` | NOT_STARTED | No |
| Rust | `rust/` | NOT_STARTED | No |
| Java | `java/` | NOT_STARTED | No |
| C | `c/` | NOT_STARTED | No |

## Per-Language Structure

Each active language directory contains:

```
<language>/
├── README.md          ← track overview
├── STATUS.md          ← current state, milestones, blockers
├── SPEC.md            ← target subset specification
├── research/          ← prior art survey, references
├── src/               ← source code (compiler, VM, tools)
├── build/             ← generated artifacts
├── tests/             ← test suites
├── evidence/          ← structured evidence per milestone
└── artifacts/         ← final .mb candidates
```

## Runners

```
runners/
├── malbolge-original/    ─ 10-trit Classic (59049 cells)
├── malbolge-unshackled/  ─ 19-trit (3^19 = ~1.16G cells)
└── malbolge20/           ─ Nagoya Malbolge20 (not available yet)
```

> Runner manifests record provenance (SHA256, source, build). A manifest is a
> CLAIM until a runner doctor (A01) verifies binary presence, hash match, and
> known-vector execution.

## Evidence Lifecycle

```
Claim → Execute → Record → Hash → Store → Verify
```

See `docs/EVIDENCE_MODEL.md` for the full model.
