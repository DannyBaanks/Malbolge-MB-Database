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

## Quine Corpus

| Artifact | Size | Note |
|---|---|---|
| `quine/quine_53562_m281.mb` | 53,562 B | Classic quine record (m=281, BolgeForge, 2026-10-17): smallest verified in the ecosystem, 6,290 B below the Lutter reference (59,852 B) and 572 B below the previous record |
| `quine/quine_54134_m284.mb` | 54,134 B | Previous record (m=284, 2026-10-16), kept as ladder step |
| `quine/ladder/` | 54,706–58,709 B | Verified ladder m=287/293/308 |

See `quine/README.md` and `quine/evidence/quine_53562_verification.json`.

## PureEpoch Corpus (Stateful Execution & Autonomous Loops)

| Artifact | Size | Description |
|---|---|---|
| `pureepoch/programs/m1a_rot10.mal` | 98 B | M1A: Mutación reversible de 10 rotaciones |
| `pureepoch/programs/m1b_normal.mal` | 308 B | M1B: Checkpoint interno en diario |
| `pureepoch/programs/m1c_normal.mal` | 29,526 B | M1C: Decisión in-band y rollback ante error |
| `pureepoch/programs/m1e_normal.mal` | 29,531 B | M1E: Recuperación con dependencia de estado anterior |
| `pureepoch/programs/m2_normal.mal` | 55,770 B | M2: Continuación autónoma de dos épocas continuas |
| `pureepoch/programs/m3_normal.mal` | 55,770 B | M3: Cadena de 3 épocas consecutivas |
| `pureepoch/programs/quine94_ceiling_probe.mal` | 94 B | M3: Sonda de techo quine de 94 bytes |
| `pureepoch/programs/torus_borrow_e_t2.mal` | 677 B | Torus T2: Préstamo de celdas en espacio muerto D \ C \ E |
| `pureepoch/programs/torus_e_t3_normal.mal` | 29,842 B | Torus T3: Préstamo y devolución completa inter-época |
| `pureepoch/programs/boss1_byzantine.mal` | 29,531 B | Boss 1: Falla Bizantina en cascada (J1 -> J2) |
| `pureepoch/programs/boss2_brainfuck.mal` | 1,303 B | Boss 2: Máquina de Turing / Intérprete Brainfuck en memoria baja [65..69] |
| `pureepoch/programs/boss3_autonomous_loop.mal` | 50,000 B | **Boss 3 (El Santo Grial):** Bucle autónomo dinámico while x > 0 sin trucos de host |

See `pureepoch/README.md` and `pureepoch/evidence/boss3_autonomous_loop_verification.json`.

## Evidence Lifecycle

```
Claim → Execute → Record → Hash → Store → Verify
```

See `docs/EVIDENCE_MODEL.md` for the full model.
