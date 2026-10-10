# Python MB — P5 Evidence

## Status: FRONTEND_DEMONSTRATED

P5 lowers direct recursion to MBIR_VERSION 0 and runs it on `mbir/mbir_ref.py`.
Evidence kind: `FRONTEND` (host_language = Python).

A function may call itself. Each call gets its own frame. `print` still emits
the raw byte. `print(fib(6))` halts in 251 steps with byte `08`. The blob has
three `CALL` instructions and one `ADD`. The constant 8 is not pushed.
`fact(5)` keeps the `MUL` and returns byte 120. `down(3)` prints 3, 2, 1 and
then 0, with one `OUT_BYTE` inside the function.

P4 still rejects the same self-call.

It does not demonstrate:

- execution on a Malbolge-hosted runtime
- a lexer, a parser, or `python.mb`

## Evidence record

- `run_p5_compiler.json` — execution record (`evidence_kind = FRONTEND`)
