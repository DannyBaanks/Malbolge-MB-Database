# P6 — Python lexer in Malbolge

## Status: NOT_DEMONSTRATED

No Malbolge program in this repo reads a Python source and emits its tokens.

P5 (`python/src/p5_compiler.py`) lowers recursion on the host reference VM.
That is not a lexer, and it does not run inside Malbolge.

## What was tried

The one-byte classifier `vm_malbolge/src/byte_dispatch18.hell` already emits one
marker for opcode bytes `0x01`..`0x11` and then halts. A copy under `/tmp`
replaced each of the 18 `OUT` / `HALT` tails with `OUT`, `R_MOVED`, `MOVED ENTRY`,
so a second input byte would enter the same classifier. LMAO 0.6.0 assembled it.

| artifact | bytes | sha256 |
|---|---:|---|
| `/tmp/disp18_loop.hell` |  | `ae8d2d691b3fa3f1501f0d46bf0f610cba7e6c1f25474e57073d074141292512` |
| `/tmp/disp18_loop.mb` | 49239 | `0aabe3442d418f82e5fc1af36bca50be904626824e61b9bcd8188587e2c2b37b` |

Commands, 2026-10-10, max_steps 300000 on the C runner and 200000 on
`tools/oracle_classic.py`:

| input | C runner stdout payload | C steps | oracle stdout | oracle steps |
|---|---|---:|---|---:|
| `01` | `50` | 52101 | `50dadadadadada3939` | 52799 |
| `01 02` | `50` | 52468 | `50dadadadadada3939` | 52799 |

The C runner's trailing `0a` is the runner trailer, not a token. The second
input byte was supposed to emit `52` (`R`), the marker for `0x02`. It did not.
The oracle does not match the C runner on the same binary. Both halt.

A separate copy of `cell_stack_loop_echo.hell` plus eight `Nop/MovD` flags did
assemble (`/tmp/lex_flags.mb`, 27826 bytes). The input loop has room for more
flags. That probe does not classify tokens. The failure above is the missing
reset between bytes, not the 59049 file cap.

## Not started

P7 (parser in Malbolge) and P8 (`python.mb`) were not started.
