# MBIR — Shared Semantic Runtime Contract

MB = Malbolge / Multi-Backend.

MBIR is a language-neutral intermediate representation executed by a shared
runtime that is ultimately hosted on Malbolge. It lets one Malbolge runtime
serve many language frontends (Python, Swift, Rust, Java, C).

```text
Python frontend ─┐
Swift frontend  ─┤
Rust frontend   ─┤
Java frontend   ─┤
C frontend      ─┘
                  ↓
                 MBIR
                  ↓
          Malbolge runtime
```

## Versioning

```text
MBIR_VERSION = 0
```

Every opcode has:
- numeric encoding,
- operands,
- stack effect,
- state effect,
- error behavior,
- reference tests.

Never change semantics in place. Increment the version.

## VM model

Minimal runtime state:

```text
pc               program counter (index into code stream)
stack            value stack (LIFO, byte values)
locals           current frame's local slots
call_stack       frames for CALL/RETURN
input_cursor     position in input stream (IN_BYTE)
output_stream    bytes emitted by OUT_BYTE
status           RUNNING / HALTED / ERROR(exit reason)
```

## Numeric model

Frozen for MBIR_VERSION 0:

```text
value type  : unsigned 8-bit integer (0..255)
operations  : modular arithmetic mod 256
ADD         : (a + b) & 0xFF
SUB         : (a - b) & 0xFF   (two's complement wrap)
MUL         : (a * b) & 0xFF
comparison  : on unsigned byte values
```

Rationale: Malbolge output is `% 256`, and the reference VM already operates on
byte values. This maps cleanly to the 3-trit cell domain of the Malbolge target.
Do not silently use Python's arbitrary precision for the *runtime*; the runtime
model is byte-modular. (Host tooling may use Python ints to build/hash, but
semantics are defined mod 256.)

## Instruction set (MBIR_VERSION 0)

| Num | Mnemonic | Operands | Stack effect | Effect | Error |
|-----|----------|----------|--------------|--------|-------|
| 0x00 | HALT | — | — | status = HALTED | — |
| 0x01 | PUSH_CONST | u8 | push const | push operand | — |
| 0x02 | POP | — | pop | discard top | underflow if empty |
| 0x03 | DUP | — | top -> top, top | duplicate top | underflow if empty |
| 0x04 | LOAD_LOCAL | u8 slot | push locals[slot] | read local | out-of-range slot -> ERROR |
| 0x05 | STORE_LOCAL | u8 slot | pop -> locals[slot] | write local | underflow if empty; out-of-range -> ERROR |
| 0x06 | ADD | — | pop b,a -> push a+b | modular + | underflow if <2 |
| 0x07 | SUB | — | pop b,a -> push a-b | modular - | underflow if <2 |
| 0x08 | MUL | — | pop b,a -> push a*b | modular * | underflow if <2 |
| 0x09 | CMP_EQ | — | pop b,a -> push (a==b) | push 1/0 | underflow if <2 |
| 0x0A | CMP_LT | — | pop b,a -> push (a<b) | push 1/0 | underflow if <2 |
| 0x0B | CMP_GT | — | pop b,a -> push (a>b) | push 1/0 | underflow if <2 |
| 0x0C | JUMP | u24 target | — | pc = target | invalid target -> ERROR |
| 0x0D | JUMP_IF_FALSE | u24 target | pop cond | pc = target if cond==0 | underflow if empty; invalid target -> ERROR |
| 0x0E | CALL | u8 addr, u8 nargs | pop nargs, call frame | push frame, pc = addr | invalid addr -> ERROR |
| 0x0F | RETURN | — | pop frame | pc = caller | no frame -> ERROR |
| 0x10 | OUT_BYTE | — | pop v | emit (v & 0xFF) | underflow if empty |
| 0x11 | IN_BYTE | — | push byte | push next input byte or 0xFF on EOF | — |

### Operand widths

| Operand | Width | Encoded as |
|---------|-------|-----------|
| const / slot / addr (small) | u8 | 1 byte |
| jump target | u24 | 3 bytes, little-endian |

### Encoding

Each instruction is one or more bytes:

```text
[opcode: 1 byte] [operand bytes per table]
```

Jump operands are little-endian u24 (3 bytes). A JUMP to an absolute index
must point at an instruction boundary (i.e. exactly at an opcode byte);
otherwise it is an invalid target -> ERROR.

### Frame / call semantics

CALL `(addr, nargs)`:
1. pop `nargs` arguments (order: last pushed is first arg) into the new frame,
2. record return address (pc after the CALL instruction) on the call stack,
3. set `pc = addr` and start a fresh frame with `nargs` locals.

RETURN:
1. pop the return address and the caller's frame,
2. restore caller locals,
3. `pc = return address`.

A RETURN with an empty call stack is an ERROR.

### I/O behavior

- `IN_BYTE` reads the next byte from the input stream; at end of input it
  pushes `0xFF` (EOF marker) and leaves the cursor at end (repeated EOF reads
  keep pushing 0xFF).
- `OUT_BYTE` pushes `(v & 0xFF)` onto the output stream.

### Invalid-bytecode behavior

- Unknown opcode byte: ERROR (BAD_OPCODE), halt with that status.
- Missing operand (truncated stream): ERROR (BAD_OPERAND).
- Stack underflow on any opcode that requires values: ERROR (STACK_UNDERFLOW).
- Invalid jump/call target (not an instruction boundary or out of bounds):
  ERROR (BAD_TARGET).
- Out-of-range local slot: ERROR (BAD_SLOT).

## Runtime identity

The Malbolge runtime must be immutable across the compile-once/test-many corpus.

```text
RUNTIME_SHA = constant
MBIR_PROGRAM_SHA = variable
```

If each test generates a different runtime containing the expected result, the
shared-runtime claim fails (A04 gate).

## Frontend responsibility

Frontend:
- parses the source subset,
- validates syntax,
- lowers to MBIR.

Frontend may NOT:
- execute arithmetic and replace it with a literal result,
- resolve runtime input,
- precompute branches whose runtime operands are unknown,
- bypass MBIR semantics.

Constant folding is allowed only if explicitly specified and separately tested
with unknown-runtime inputs so it cannot satisfy the whole corpus by
precomputation.