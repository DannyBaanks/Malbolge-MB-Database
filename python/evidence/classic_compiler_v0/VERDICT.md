# Classic literal-functions compiler v0 — verdict

Scope: host Python compiler emitting standalone strict Classic Malbolge images. This closes the bounded compiler task, not the Malbolge-hosted Python interpreter track.

| Claim | Status | Evidence |
|---|---|---|
| Eight trusted fixtures match CPython byte-for-byte on Olmstead, clasesbolge, local instruction trace and REA | DEMONSTRATED | run01/run02 results.json, trace.json, rea.json and raw streams |
| Real numeric CALL/RET, nested slot isolation, reset, one-shot execution | DEMONSTRATED for the corpus | 12 call/return pairs per run; REA contiguous event windows agree with local trace |
| Independent builds deterministic | DEMONSTRATED for the corpus | Images/maps and results/REA reports identical in both fresh runs, and results/REA match original agent run01 |
| Unsupported syntax, encoding errors, existing outputs and actual layout rejection | DEMONSTRATED for tested cases | tests.stderr.raw.txt; regression tests for __debug__ and unknown encoding |
| General Python, loops, recursion, variables, dynamic dispatch, return values, reusable physical function code, self-hosted compiler | NOT_DEMONSTRATED / out of scope | DESIGN.md |
| Full repository gate green | NOT_DEMONSTRATED | Existing mbir/zig/tests/runtime.zig fails zig fmt --check; unchanged relative to HEAD. Zig runtime tests and MBIR pytest pass. |

Fresh runs performed from installed source (not /tmp drafts). No original measured artifact modified. Source-program hashes are hashes of decoded UTF-8 text; raw fixture and emitted-file hashes are separate. No publication. The compiler does not execute the input; the evidence harness executes only its trusted fixtures in CPython as an oracle. Two engines count HALT differently (clasesbolge steps exclude the final halt; local/REA include it); output/status parity is the gate. Output/map creation is exclusive but not transactional. The earlier agent's implementation was retained, formatted, and extended by two narrowly scoped regressions.

Commands from repo root (choose fresh run directories when reproducing):

```sh
python3 -B python/tests/test_classic_compiler.py
python3 -B python/evidence/classic_compiler_v0/smoke.py python/evidence/classic_compiler_v0/run01
python3 -B python/evidence/classic_compiler_v0/smoke.py python/evidence/classic_compiler_v0/run02
node python/evidence/classic_compiler_v0/rea.mjs /home/danny/Development/rea/dist python/evidence/classic_compiler_v0/run01
node python/evidence/classic_compiler_v0/rea.mjs /home/danny/Development/rea/dist python/evidence/classic_compiler_v0/run02
python3 -B -m pytest mbir/tests -q
zig fmt --check mbir/zig
(cd mbir/zig && zig build test --summary all)
```

Run01/run02 are archival; never write into them. Substitute distinct nonexistent output directories. See `environment.txt`, raw logs and `hashes.sha256`. Restore/rollback by reverting the local feature commit, without removing unrelated working-tree changes or historical evidence.
