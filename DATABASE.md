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

## Shared Infrastructure

```
mbir/                 ─ MBIR shared runtime contract (A02, MBIR_VERSION 0)
  ├── mbir.py         ─ encoder/decoder + static validation
  ├── tests/          ─ conformance suite (23/23 PASS)
  └── README.md
docs/MBIR_CONTRACT.md ─ full contract spec
```

The MBIR contract is language-neutral and shared by all tracks. A language
frontend or backend adapter may lower/translate its supported subset to MBIR;
the resulting boundary representation can be handed to a compatible execution
substrate. Native Malbolge, Rustbolge, Javolge, Pibolge, and other engines are
separate backends, not imports into this repository. A single omnilingual
Malbolge VM is **NOT** a requirement and remains NOT_DEMONSTRATED.

```text
language program -> frontend -> MBIR middleware -> backend adapter -> substrate
```

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

External substrates (the -bolge engine family: Rustbolge, Swiftbolge, Javolge,
Cobolge, Fortranbolge, Zigbolge, Pibolge, Pibolge19, Wasmbolge, MalbolgeEngineCPP,
malbolge-free, malbolge-oracle, MalboGost) are registered **by reference** —
see `runners/README.md` → "External Substrates" and `registry/substrates.json`
(13 CLAIM manifests, no binaries vendored; the MBIR backends you hand MBIR to).

## Evidence Lifecycle

```
Claim → Execute → Record → Hash → Store → Verify
```

See `docs/EVIDENCE_MODEL.md` for the full model.
