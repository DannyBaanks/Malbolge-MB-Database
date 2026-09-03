"""
MBIR reference VM — MBIR_VERSION 0 semantics.

This is the authoritative REFERENCE implementation of the MBIR contract
(docs/MBIR_CONTRACT.md). It implements the full semantic model so that:

- it is the oracle the Malbolge-hosted runtime (A04) must match,
- frontends can validate lowering,
- negative / error behavior is precisely defined and tested.

It consumes raw MBIR bytes (mbir.encode output) and, optionally, an input
byte stream. Execution is deterministic: for identical (blob, input) it
produces identical (output, steps, status, trace).

Evidence kind: REFERENCE_MODEL (host_language = Python).
"""
from __future__ import annotations

import hashlib

try:
    from . import mbir as M
except ImportError:  # pragma: no cover - fallback when run as a bare script
    import mbir as M


class MBIRError(Exception):
    """Runtime error with a machine-checkable reason."""
    def __init__(self, reason, pc=-1):
        super().__init__("%s at pc=%d" % (reason, pc))
        self.reason = reason
        self.pc = pc


class Frame:
    __slots__ = ("return_pc", "locals")

    def __init__(self, return_pc, locals_):
        self.return_pc = return_pc
        self.locals = locals_


class MBIRRefVM:
    def __init__(self, max_steps=1_000_000, trace=False):
        self.max_steps = max_steps
        self.trace = trace
        self.reset()

    def reset(self):
        self.pc = 0
        self.stack = []
        self.frames = []          # call stack of Frame
        self.locals = {}          # current frame locals: slot -> u8
        self.in_cursor = 0
        self.in_data = b""
        self.output = bytearray()
        self.steps = 0
        self.status = "RUNNING"
        self.boundaries = []      # valid jump targets (opcode offsets)
        self.code = b""
        self.trace_events = []    # deterministic per-step record

    def load(self, blob: bytes, input_bytes: bytes = b""):
        self.reset()
        self.code = blob
        self.in_data = input_bytes
        # Validate structure + collect boundaries. Structural decode errors
        # (bad opcode, truncated operand) surface as MBIRError for uniform
        # runtime behavior.
        try:
            self.boundaries = M.instruction_boundaries(blob)
        except M.MBIRDecodeError as e:
            reason = str(e).split(":")[0].strip()  # BAD_OPCODE / BAD_OPERAND
            raise MBIRError(reason, self.pc) from e
        return self

    def _check_target(self, target):
        if target not in self.boundaries:
            raise MBIRError("BAD_TARGET", self.pc)

    def _need(self, n):
        if len(self.stack) < n:
            raise MBIRError("STACK_UNDERFLOW", self.pc)

    def run(self):
        """Execute until HALT, MAX_STEPS, or error. Returns result dict."""
        n = len(self.code)
        while True:
            if self.steps >= self.max_steps:
                self.status = "MAX_STEPS"
                break
            if self.pc >= n:
                self.status = "ERROR"
                raise MBIRError("BAD_OPERAND (pc past end)", self.pc)
            op = self.code[self.pc]
            pc0 = self.pc
            if self.trace:
                self.trace_events.append({
                    "pc": pc0,
                    "op": M.MNEMONICS.get(op, "?"),
                    "stack": list(self.stack),
                    "locals": dict(self.locals),
                })
            self.pc += 1
            self.steps += 1  # every dispatched instruction counts as one step

            if op == M.HALT:
                self.status = "HALTED"
                break

            elif op == M.PUSH_CONST:
                v = self.code[self.pc]; self.pc += 1
                self.stack.append(v)

            elif op == M.POP:
                self._need(1); self.stack.pop()

            elif op == M.DUP:
                self._need(1); self.stack.append(self.stack[-1])

            elif op == M.LOAD_LOCAL:
                slot = self.code[self.pc]; self.pc += 1
                if slot not in self.locals:
                    raise MBIRError("BAD_SLOT", pc0)
                self.stack.append(self.locals[slot])

            elif op == M.STORE_LOCAL:
                slot = self.code[self.pc]; self.pc += 1
                self._need(1)
                # slots are pre-allocated on CALL; direct use requires it too
                self.locals[slot] = self.stack.pop()

            elif op == M.ADD:
                self._need(2); b = self.stack.pop(); a = self.stack.pop()
                self.stack.append((a + b) & 0xFF)
            elif op == M.SUB:
                self._need(2); b = self.stack.pop(); a = self.stack.pop()
                self.stack.append((a - b) & 0xFF)
            elif op == M.MUL:
                self._need(2); b = self.stack.pop(); a = self.stack.pop()
                self.stack.append((a * b) & 0xFF)

            elif op == M.CMP_EQ:
                self._need(2); b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(1 if a == b else 0)
            elif op == M.CMP_LT:
                self._need(2); b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(1 if a < b else 0)
            elif op == M.CMP_GT:
                self._need(2); b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(1 if a > b else 0)

            elif op == M.JUMP:
                t = int.from_bytes(self.code[self.pc:self.pc + 3], "little"); self.pc += 3
                self._check_target(t)
                self.pc = t

            elif op == M.JUMP_IF_FALSE:
                t = int.from_bytes(self.code[self.pc:self.pc + 3], "little"); self.pc += 3
                self._need(1)
                cond = self.stack.pop()
                self._check_target(t)
                if cond == 0:
                    self.pc = t

            elif op == M.CALL:
                addr = self.code[self.pc]; nargs = self.code[self.pc + 1]; self.pc += 2
                self._check_target(addr)
                self._need(nargs)
                # pop nargs, last pushed becomes local slot nargs-1
                args = [self.stack.pop() for _ in range(nargs)]
                args.reverse()
                self.frames.append(Frame(self.pc, self.locals))
                self.locals = {i: v for i, v in enumerate(args)}
                self.pc = addr

            elif op == M.RETURN:
                if not self.frames:
                    raise MBIRError("NO_FRAME", pc0)
                f = self.frames.pop()
                self.locals = f.locals
                self.pc = f.return_pc

            elif op == M.OUT_BYTE:
                self._need(1)
                v = self.stack.pop()
                self.output.append(v & 0xFF)

            elif op == M.IN_BYTE:
                if self.in_cursor < len(self.in_data):
                    v = self.in_data[self.in_cursor]
                    self.in_cursor += 1
                else:
                    v = 0xFF  # EOF marker
                self.stack.append(v)

            else:
                raise MBIRError("BAD_OPCODE", pc0)

        return self.get_result()

    def get_result(self):
        return {
            "output": bytes(self.output).decode("latin-1"),
            "output_bytes": list(self.output),
            "steps": self.steps,
            "status": self.status,
            "stack": list(self.stack),
            "locals": dict(self.locals),
            "trace": self.trace_events if self.trace else None,
        }


def source_hash(path) -> str:
    """SHA-256 of the exact source file bytes (implementation provenance)."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()