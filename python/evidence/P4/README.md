# Python MB — P4 Evidence

## Status: FRONTEND_DEMONSTRATED

P4 lowers top-level Python functions to MBIR_VERSION 0 and runs them on
`mbir/mbir_ref.py`. Evidence kind: `FRONTEND` (host_language = Python).

On top of the P3 subset:

- `def` with plain parameters
- a call with the matching number of arguments
- `return` of one expression

The body is a fresh frame. Parameters are locals 0..n-1. `RETURN` leaves the
value on the stack for the caller. Bodies are emitted before the module code
because `CALL` addresses are one byte. A direct call to the function being
compiled is rejected. Recursion is P5.

`print(add(2, 3))` halts in 10 steps with byte `05`. The blob is
`JUMP`, `LOAD_LOCAL`, `LOAD_LOCAL`, `ADD`, `RETURN`, then `PUSH 2`, `PUSH 3`,
`CALL`, `OUT_BYTE`, `HALT`. Two calls share that one `ADD`.

It does not demonstrate:

- execution on a Malbolge-hosted runtime
- recursion, a lexer, or `python.mb`

## Evidence record

- `run_p4_compiler.json` — execution record (`evidence_kind = FRONTEND`)
