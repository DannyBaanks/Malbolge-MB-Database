# Python MB — P3 Evidence

## Status: FRONTEND_DEMONSTRATED

P3 lowers a Python subset to MBIR_VERSION 0 and runs it on `mbir/mbir_ref.py`.
Evidence kind: `FRONTEND` (host_language = Python).

The subset is cumulative with the earlier print-of-addition case:

- assignment to one name, and a later load of that name
- `print` of one expression, emitted as the raw byte (`OUT_BYTE`)
- `+`, `-`, `*` with wrap mod 256
- one comparison: `==`, `<`, `>`
- `if` / `else` / `elif`
- `while`, with assignments inside the body left out of the set of names that are assigned after the loop

`python/src/p3_compiler.py` parses with `ast.parse`. It does not call `eval` or `exec`, and it does not replace an operation with its result. A taken `if 5 > 3` still contains `CMP_GT`, `JUMP_IF_FALSE`, and the bytes of both arms. The `while` case contains one `OUT_BYTE` and prints three bytes.

It does not demonstrate:

- execution on a Malbolge-hosted runtime
- functions, recursion, a lexer, or `python.mb`

## Evidence record

- `run_p3_compiler.json` — execution record (`evidence_kind = FRONTEND`)
