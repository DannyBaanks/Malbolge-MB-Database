# Malbolge MB Database

A reproducible database and research laboratory for substantial Malbolge programs and foreign-language runtimes hosted on Malbolge.

## Mission

Investigate, build, execute, and conserve `.mb` programs — especially interpreters/runtimes of other languages implemented over Malbolge.

Long-term targets:

```
python.mb    ← current priority
swift.mb     ← NOT_STARTED
rust.mb      ← NOT_STARTED
java.mb      ← NOT_STARTED
c.mb         ← NOT_STARTED
```

## Central Principle

**NEVER GUESS.** If a property is not demonstrated by code, documentation, execution, test, trace, hash, artifact, or independent reproduction, classify it:

```
NOT_DEMONSTRATED
```

README ≠ evidence. Filename ≠ evidence. Claim ≠ implementation.

## Language Tracks

| Language | Target | Variant | Status | Highest Milestone | Evidence |
|----------|--------|---------|--------|-------------------|----------|
| Python   | python.mb | TBD | RESEARCH | — | — |
| Swift    | swift.mb  | TBD | NOT_STARTED | — | — |
| Rust     | rust.mb   | TBD | NOT_STARTED | — | — |
| Java     | java.mb   | TBD | NOT_STARTED | — | — |
| C        | c.mb      | TBD | NOT_STARTED | — | — |

## Repository Structure

```
MALBOLGE-MB-DATABASE/
├── README.md              ← this file
├── DATABASE.md            ← database overview and navigation
├── LICENSE
├── registry/              ← structured metadata per language
├── docs/                  ← definitions, variants, evidence model
├── references/            ← external reference documentation
├── tools/                 ← utilities for building, running, testing
├── runners/               ← reproducible Malbolge execution environments
├── python/                ← python.mb track (ACTIVE)
├── swift/                 ← swift.mb track (NOT_STARTED)
├── rust/                  ← rust.mb track (NOT_STARTED)
├── java/                  ← java.mb track (NOT_STARTED)
└── c/                     ← c.mb track (NOT_STARTED)
```

## How to Use

1. Read `DATABASE.md` for navigation.
2. Read `docs/DEFINITIONS.md` for terminology.
3. Read the target language's `STATUS.md` for current state.
4. Read `docs/EVIDENCE_MODEL.md` before interpreting any result.

## Anti-Fake Rule

To demonstrate `print(2 + 3)`, we do NOT accept a `.mb` that simply prints `5`. We must demonstrate an operational representation equivalent to:

```
PUSH 2
PUSH 3
ADD
PRINT
```

and that changing operands modifies the result correctly without fabricating an independent print program for each output.
