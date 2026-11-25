"""Vector tables for the a04-malbolge backend tests and probe.

Machine-evidenced expectations are never transcribed here: tests and the
probe load them from the committed machine evidence JSONs (frozen,
append-only records under vm_malbolge/evidence/).  Only two kinds of tables
live in this module:

- EXTENSION_VECTORS: new probes introduced by this backend — operand bytes
  and cycle counts inside the machines' own generality claims; the pinned
  step counts were first observed by the bridge evidence run
  (vm_malbolge/evidence/mbir_a04_backend_bridge.json) and must be
  reproduced exactly by any conforming runner.
- REFUSAL_VECTORS: programs the backend must refuse with a stated reason
  (the honesty contract of a04_backend.py).
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EVIDENCE_FILES = {
    "lifo": "vm_malbolge/evidence/mbir_a05_lifo_smoke.json",
    "multicycle": "vm_malbolge/evidence/mbir_a05_multicycle_smoke.json",
}


def machine_cases(machine: str) -> list[dict]:
    """Committed evidence cases for a machine, verbatim."""
    path = _REPO_ROOT / EVIDENCE_FILES[machine]
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)["cases"]


def case_by_input(machine: str, input_hex: str) -> dict:
    """The committed evidence case of `machine` for a given input."""
    for case in machine_cases(machine):
        if case["input_hex"] == input_hex:
            return case
    raise KeyError("%s evidence has no case for input %s" % (machine, input_hex))


# (machine, input_hex, expected_hex, expected_steps, note)
# New probes: operand bytes and cycle counts inside the machines'
# demonstrated shapes; steps pinned from the bridge evidence run.
EXTENSION_VECTORS = [
    ("lifo", "010a1000", "0a", 59752,
     "operand 0x0a: exercises the raw-byte stdin channel and the runner's "
     "single-trailing-newline strip"),
    ("lifo", "012110015a1000", "215a", 65804,
     "two sequential cycles with generic operands 0x21/0x5a"),
    ("lifo", "01fb1001fd1000", "fbfd", 65804,
     "high-operand boundary pair 0xfb/0xfd"),
    ("multicycle", "01411001421001431001441000", "41424344", 66839,
     "k=4 alternation (the evidence set spans k=1..5; k=4 sits inside it "
     "but was not individually recorded)"),
    ("multicycle", "01611001621001631001641001651001661000", "616263646566", 78931,
     "k=6 alternation, beyond the evidenced k<=5: covered by the machine's "
     "arbitrary-cycle-count claim and re-verified live by the per-run "
     "parity assertion"),
]

# (input_hex, expected_reason, note) — run_full must refuse each of these.
REFUSAL_VECTORS = [
    ("01020103061000", "UNSUPPORTED_OPCODE",
     "the canonical B2T0 demo (ADD program): ADD is outside the A04 subset"),
    ("1110111000", "UNSUPPORTED_OPCODE",
     "echo program: IN_BYTE is outside the A04 subset"),
    ("0c000000", "UNSUPPORTED_OPCODE",
     "JUMP loop program: control flow is outside the A04 subset"),
    ("101000", "UNSUPPORTED_PROFILE",
     "OUT_BYTE on an empty stack: no demonstrated machine covers it"),
    ("014110", "UNSUPPORTED_PROFILE",
     "missing trailing HALT (the machines EOF-halt; the profile refuses)"),
    ("0000", "UNSUPPORTED_PROFILE",
     "instructions after HALT are not accepted"),
    ("0141014201431000", "UNSUPPORTED_PROFILE",
     "three concurrent pushes exceed the 2-slot machines (A06 frontier)"),
    ("0141100100", "UNSUPPORTED_PROFILE",
     "unfinished PUSH after a completed cycle: a matchless shape"),
    ("1001", "UNSUPPORTED_MBIR",
     "truncated PUSH (OUT_BYTE then opcode 0x01 with no operand byte): refused "
     "at decode, before any machine or runner is consulted"),
    ("ff", "UNSUPPORTED_MBIR",
     "unknown opcode byte 0xff: refused at MBIR decode"),
    ("0200", "UNSUPPORTED_OPCODE",
     "POP decodes legally in MBIR but is outside the A04 subset: the "
     "mnemonic gate refuses it after a clean decode"),
]
