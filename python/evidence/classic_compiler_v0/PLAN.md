# Classic literal-functions compiler Implementation Plan

Goal: compile the stated AST subset to standalone strict Classic, including real call/return semantics.
Architecture: validated AST → acyclic invocation instances → native emitter and numeric return slots → BolgeForge bootstrap → image and optional map. Tech: Python stdlib, existing BolgeForge resynthesis, native Olmstead for optional execution. Spec: DESIGN.md.

Global constraints: no source eval/exec; no host runtime simulation; output refusal on overwrite; no edits to historical evidence; bytecode/MBIR contracts unchanged.

Review focus: call before definition; repeated calls into encrypted code; nested return-slot isolation; UTF-8 and invalid surrogates; code/preamble/data capacity and existing output preservation.

- [ ] Frontend and meaningful tests: parse literal prints/functions/calls, ordered resolution, recursion/budget diagnostics and early return.
- [ ] Backend: sparse pointer banks, byte constants preserved by ROT^10, numeric calls/returns and per-depth journals, layout checks, deterministic images.
- [ ] CLI: source encoding, source-position errors, exclusive output creation, optional map/run; verify overwrite behavior.
- [ ] Native evidence: CPython differential corpus, native and independent engines, real call/return maps and two builds; test rejection paths.
- [ ] Human guide/examples: run exact owner commands, document supported subset and specialization; install new files, check focused tests, hash evidence and commit only owned paths.

Execution: native implementation in this session, as requested by CONTINUA. Scope and implementation choices are stated to the user; no publication requested.

## Execution closure (2026-11-24)

Frontend, backend, CLI, differential corpus, guide, examples, fresh evidence and two regression tests completed; see VERDICT.md and raw logs. Commit step is confirmed separately by git history.
