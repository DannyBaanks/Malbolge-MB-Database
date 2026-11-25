#!/usr/bin/env python3
"""B2T0 dispatcher -- give 10-trit cell payloads executable meaning.

b2t (the codec) moves bytes into Malbolge-compatible cells and back, and
assigns no meaning to the bits.  This module is the layer that does:

    .b2t container
        -- b2t.decode_container (strict transport checks)  -->  MBIR bytes
        -- mbir.mbir_ref.MBIRRefVM (the MBIR v0 oracle)    -->  output

It adds no opcodes and defines no IR: the payload must already be a valid
MBIR v0 blob (docs/MBIR_CONTRACT.md, mbir/mbir.py).  Malbolge itself still
understands only ternary cells; the meaning of the trits is placed by this
dispatcher, at the boundary that leaves the transport layer.  The
Malbolge-hosted runtime (A04) remains a separate backend target.

Two extra surfaces make the boundary inspectable:

  * provenance -- for every payload byte, the exact 10-trit cells (and the
    bit positions inside them) that carry that byte's 8 bits;
  * trace bridge -- every VM step annotated with the cells whose trits
    were dispatched at that step, so a run can be followed in ternary
    transport terms.

Backend boundary: mbir/backends.py (BackendResult / BackendAdapter /
BackendCatalog).  The default backend `mbir-ref-python` wraps the
reference VM; the Malbolge-hosted substrate `a04-malbolge`
(a04_backend.py, the A04/A05 machines of vm_malbolge/) registers
alongside it.

Exit codes for `run`:  0 = HALTED, 1 = ERROR, 2 = MAX_STEPS.
Container / usage errors exit 1 before any execution starts.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Sequence

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
for _path in (_HERE, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import b2t
import a04_backend
from mbir import OPERANDS
from mbir import backends
from mbir import decode as mbir_decode
from mbir import mbir_ref
from mbir import operand_width

DEFAULT_BACKEND = "mbir-ref-python"
DEFAULT_MAX_STEPS = 1_000_000


class DispatchError(ValueError):
    """Raised for dispatcher-level misuse (bad backend id, bad options)."""


# ---------------------------------------------------------------------------
# Provenance: byte <-> cell bit map (the static half of the trace bridge)
# ---------------------------------------------------------------------------


def container_words(container: bytes) -> tuple[int, ...]:
    """Return the cell values carried by a (not yet validated) container."""
    if len(container) < b2t.HEADER.size:
        raise b2t.B2TError("container is shorter than the header")
    _magic, _version, _flags, bit_length, word_count, _crc = b2t.HEADER.unpack_from(
        container
    )
    expected = (bit_length + b2t.CHUNK_BITS - 1) // b2t.CHUNK_BITS
    if word_count != expected:
        raise b2t.B2TError("non-canonical word count")
    if len(container) != b2t.HEADER.size + 2 * word_count:
        raise b2t.B2TError("container length does not match its word count")
    return tuple(
        struct.unpack_from("<%dH" % word_count, container, b2t.HEADER.size)
    )


def byte_provenance(data: bytes, words: Sequence[int]) -> list[dict]:
    """Map every payload byte to the cells that carry its 8 bits.

    A byte occupies stream bits [8*b, 8*b+8); a cell i covers stream bits
    [15*i, 15*i+15).  A byte therefore never spans more than two cells.
    ``bit_positions`` are cell-local positions from the chunk start, so the
    bit at local position p is (word >> (CHUNK_BITS-1-p)) & 1.
    """
    expected_words = (len(data) * 8 + b2t.CHUNK_BITS - 1) // b2t.CHUNK_BITS
    if len(words) != expected_words:
        raise b2t.B2TError(
            f"{len(words)} cells cannot canonically carry {len(data)} bytes"
        )
    entries: list[dict] = []
    for offset, value in enumerate(data):
        first_bit = offset * 8
        last_bit = first_bit + 8  # exclusive
        first_cell = first_bit // b2t.CHUNK_BITS
        last_cell = (last_bit - 1) // b2t.CHUNK_BITS
        segments = []
        for cell_index in range(first_cell, last_cell + 1):
            seg_start = max(first_bit, cell_index * b2t.CHUNK_BITS)
            seg_end = min(last_bit, (cell_index + 1) * b2t.CHUNK_BITS)
            word = words[cell_index]
            segments.append(
                {
                    "cell": cell_index,
                    "word": word,
                    "trits": list(b2t.word_to_trits(word)),
                    "bit_start": seg_start,
                    "bit_end": seg_end,
                    "bit_positions": list(
                        range(
                            seg_start - cell_index * b2t.CHUNK_BITS,
                            seg_end - cell_index * b2t.CHUNK_BITS,
                        )
                    ),
                }
            )
        entries.append({"offset": offset, "value": value, "cells": segments})
    return entries


def reassemble_bytes(provenance: Sequence[dict]) -> bytes:
    """Rebuild the byte stream by following the provenance map only.

    This is an independent decode path: it never calls b2t.unpack_bits, it
    walks the (cell, bit_positions) segments.  Any inconsistency between
    the map and the stored values raises B2TError instead of returning
    bad data.
    """
    out = bytearray()
    for entry in provenance:
        value = 0
        collected = 0
        for segment in entry["cells"]:
            word = segment["word"]
            for position in segment["bit_positions"]:
                bit = (word >> (b2t.CHUNK_BITS - 1 - position)) & 1
                value = (value << 1) | bit
                collected += 1
        if collected != 8:
            raise b2t.B2TError(
                f"provenance for byte {entry['offset']} carries {collected} bits"
            )
        if value != entry["value"]:
            raise b2t.B2TError(f"provenance mismatch at byte {entry['offset']}")
        out.append(value)
    return bytes(out)


def load_payload(container: bytes) -> tuple[bytes, tuple[int, ...]]:
    """Decode a container and return (MBIR bytes, cell values)."""
    data = b2t.decode_container(container)  # strict: magic/version/CRC/padding
    words = container_words(container)       # the actual transported cells
    return data, words


# ---------------------------------------------------------------------------
# Program map: instruction <-> cell map (disasm view of the bridge)
# ---------------------------------------------------------------------------


def _operand_hex(spec: str | None, operands) -> str:
    if spec is None:
        return "\u2014"
    if spec == "u8":
        return "0x%02x" % operands
    if spec == "u24":
        return "0x%06x" % operands
    if spec == "u8,u8":
        return "0x%02x,0x%02x" % tuple(operands)
    raise DispatchError("unknown operand spec: %s" % spec)


def program_map(data: bytes, words: Sequence[int]) -> list[dict]:
    """Decode the MBIR payload and attach cell provenance per instruction.

    Raises mbir.MBIRDecodeError when the payload is not valid MBIR v0.
    """
    provenance = byte_provenance(data, words)
    instructions = []
    for mnemonic, operands, offset in mbir_decode(data):
        opcode = data[offset]
        spec = OPERANDS[opcode]
        length = 1 + operand_width(spec)
        span = provenance[offset : offset + length]
        cells = sorted({segment["cell"] for entry in span for segment in entry["cells"]})
        value = operands if operands != () else None
        instructions.append(
            {
                "offset": offset,
                "length": length,
                "opcode": opcode,
                "mnemonic": mnemonic,
                "operand": value,
                "operand_hex": _operand_hex(spec, operands if operands != () else None),
                "bytes": span,
                "byte_hex": " ".join("%02x" % entry["value"] for entry in span),
                "cells": cells,
            }
        )
    return instructions


# ---------------------------------------------------------------------------
# Backend: reference VM wrapped in the MBIR backend contract
# ---------------------------------------------------------------------------


class MBIRRefBackend:
    """BackendAdapter over mbir.mbir_ref.MBIRRefVM (MBIR v0 oracle)."""

    backend_id = DEFAULT_BACKEND

    def __init__(self, max_steps: int = DEFAULT_MAX_STEPS) -> None:
        self.max_steps = max_steps

    def run_full(
        self,
        blob: bytes,
        stdin: bytes = b"",
        max_steps: int | None = None,
        trace: bool = False,
    ) -> dict:
        """Execute and return (status, exit_code, steps, output, trace, error)."""
        vm = mbir_ref.MBIRRefVM(
            max_steps=max_steps if max_steps is not None else self.max_steps,
            trace=trace,
        )
        error: dict | None = None
        try:
            vm.load(blob, stdin)
            result = vm.run()
        except mbir_ref.MBIRError as exc:
            error = {"reason": exc.reason, "pc": exc.pc}
            result = None
        if error is not None:
            status = "ERROR"
            exit_code = 1
        else:
            status = result["status"]
            exit_code = {"HALTED": 0, "MAX_STEPS": 2}.get(status, 1)
        return {
            "status": status,
            "exit_code": exit_code,
            "steps": vm.steps,
            "output": bytes(vm.output),
            "trace_events": vm.trace_events,
            "in_cursor": vm.in_cursor,
            "error": error,
        }

    def execute(self, blob: bytes, stdin: bytes = b"") -> backends.BackendResult:
        """MBIR backend contract surface (mbir/backends.py)."""
        run = self.run_full(blob, stdin)
        stderr = b""
        if run["error"]:
            stderr = ("%s at pc=%d" % (run["error"]["reason"], run["error"]["pc"])).encode()
        return backends.BackendResult(
            backend_id=self.backend_id,
            status=run["status"],
            stdout=run["output"],
            stderr=stderr,
            exit_code=run["exit_code"],
        )


CATALOG = backends.BackendCatalog()
CATALOG.register(MBIRRefBackend())
a04_backend.register(CATALOG)  # a04-malbolge: the Malbolge-hosted machines


# ---------------------------------------------------------------------------
# Trace bridge: VM steps annotated with the cells being dispatched
# ---------------------------------------------------------------------------


def annotate_trace(events: Sequence[dict], data: bytes, words: Sequence[int]) -> list[dict]:
    """Attach per-instruction byte provenance to each recorded VM step."""
    provenance = byte_provenance(data, words)
    annotated = []
    for index, event in enumerate(events, start=1):
        pc = event["pc"]
        opcode = data[pc] if pc < len(data) else None
        spec = OPERANDS.get(opcode)
        width = operand_width(spec) if spec is not None else 0
        span_end = min(pc + 1 + width, len(data))
        span = provenance[pc:span_end]
        cells = sorted({segment["cell"] for entry in span for segment in entry["cells"]})
        operand_value = None
        operand_hex = "\u2014"
        if spec == "u8":
            operand_value = data[pc + 1]
            operand_hex = "0x%02x" % operand_value
        elif spec == "u24":
            operand_value = int.from_bytes(data[pc + 1 : pc + 4], "little")
            operand_hex = "0x%06x" % operand_value
        elif spec == "u8,u8":
            operand_value = (data[pc + 1], data[pc + 2])
            operand_hex = "0x%02x,0x%02x" % operand_value
        annotated.append(
            {
                "step": index,
                "pc": pc,
                "op": event["op"],
                "operand": operand_value,
                "operand_hex": operand_hex,
                "stack": event["stack"],
                "locals": event["locals"],
                "cells": cells,
                "bytes": span,
            }
        )
    return annotated


# ---------------------------------------------------------------------------
# Envelope: container + run + optional trace, one serializable dict
# ---------------------------------------------------------------------------


def dispatch_container(
    container: bytes,
    stdin: bytes = b"",
    *,
    max_steps: int | None = None,
    trace: bool = False,
    backend_id: str | None = None,
) -> dict:
    """Full pipeline: container -> MBIR bytes -> backend execution -> envelope."""
    backend = CATALOG.get(backend_id if backend_id is not None else DEFAULT_BACKEND)
    if trace and not hasattr(backend, "run_full"):
        raise DispatchError(
            "backend %s does not expose run_full(); tracing is unavailable" % backend.backend_id
        )
    if trace and not getattr(backend, "trace_supported", True):
        raise DispatchError(
            "backend %s does not support tracing; %s provides the annotated trace"
            % (backend.backend_id, DEFAULT_BACKEND)
        )
    data, words = load_payload(container)
    run = backend.run_full(data, stdin=stdin, max_steps=max_steps, trace=trace)
    _m, _v, _f, bit_length, word_count, crc = b2t.HEADER.unpack_from(container)
    envelope: dict = {
        "backend": backend.backend_id,
        "status": run["status"],
        "exit_code": run["exit_code"],
        "steps": run["steps"],
        "error": run["error"],
        "program_bytes": len(data),
        "bit_length": bit_length,
        "word_count": word_count,
        "crc32": "0x%08x" % crc,
        "cells": list(words),
        "trits": [list(b2t.word_to_trits(word)) for word in words],
        "stdin_consumed": run["in_cursor"],
        "stdout_bytes": list(run["output"]),
        "stdout_hex": run["output"].hex(),
        "trace": None,
        "backend_meta": run.get("meta"),
    }
    if trace:
        envelope["trace"] = annotate_trace(run["trace_events"], data, words)
    return envelope


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read_stdin(spec: str | None) -> bytes:
    if spec is None:
        return b""
    if spec == "-":
        return sys.stdin.buffer.read()
    return Path(spec).read_bytes()


def _cells_text(cells: Sequence[int]) -> str:
    return ",".join("#%d" % cell for cell in cells)


def _format_trace_event(event: dict) -> str:
    parts = ["  #%d pc=%d %s" % (event["step"], event["pc"], event["op"])]
    if event["operand"] is not None:
        parts[-1] += " " + event["operand_hex"]
    byte_bits = " ".join(
        "@%d=0x%02x(%s)"
        % (
            entry["offset"],
            entry["value"],
            ",".join("#%d" % segment["cell"] for segment in entry["cells"]),
        )
        for entry in event["bytes"]
    )
    parts.append("bytes=[%s]" % byte_bits)
    parts.append("cells=[%s]" % _cells_text(event["cells"]))
    parts.append("stack=%s" % event["stack"])
    return " ".join(parts)


def _cmd_run(args: argparse.Namespace) -> int:
    stdin_bytes = _read_stdin(args.stdin)
    envelope = dispatch_container(
        args.container.read_bytes(),
        stdin_bytes,
        max_steps=args.max_steps,
        trace=args.trace,
        backend_id=args.backend,
    )
    if args.json:
        print(json.dumps(envelope, indent=2, sort_keys=True))
        return envelope["exit_code"]
    print(
        "backend=%s status=%s exit_code=%d steps=%d"
        % (envelope["backend"], envelope["status"], envelope["exit_code"], envelope["steps"])
    )
    print(
        "container: %d bytes in %d cells (bit_length=%d, crc32=%s)"
        % (
            envelope["program_bytes"],
            envelope["word_count"],
            envelope["bit_length"],
            envelope["crc32"],
        )
    )
    if envelope["error"] is not None:
        print("error: %s at pc=%d" % (envelope["error"]["reason"], envelope["error"]["pc"]))
    out = envelope["stdout_bytes"]
    if out:
        print("output (%d byte%s): %s" % (len(out), "" if len(out) == 1 else "s", " ".join("%02x" % b for b in out)))
    else:
        print("output: (empty)")
    if args.trace and envelope["trace"] is not None:
        print("trace:")
        for event in envelope["trace"]:
            print(_format_trace_event(event))
    return envelope["exit_code"]


def _cmd_disasm(args: argparse.Namespace) -> int:
    data, words = load_payload(args.container.read_bytes())
    instructions = program_map(data, words)
    if args.json:
        print(
            json.dumps(
                {"program_bytes": len(data), "cells": list(words), "instructions": instructions},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print("off  bytes      mnemonic        operand     cells")
    for instruction in instructions:
        print(
            "%04x %-10s  %-14s %-11s %s"
            % (
                instruction["offset"],
                instruction["byte_hex"],
                instruction["mnemonic"],
                instruction["operand_hex"],
                _cells_text(instruction["cells"]),
            )
        )
    return 0


def _cmd_provenance(args: argparse.Namespace) -> int:
    data, words = load_payload(args.container.read_bytes())
    provenance = byte_provenance(data, words)
    # Rebuild through the map itself: it must reproduce the payload.
    reassemble_bytes(provenance)
    _m, _v, _f, bit_length, word_count, crc = b2t.HEADER.unpack_from(args.container.read_bytes())
    if args.json:
        print(
            json.dumps(
                {
                    "bit_length": bit_length,
                    "word_count": word_count,
                    "crc32": "0x%08x" % crc,
                    "cells": list(words),
                    "bytes": provenance,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print(
        "container: %d bytes, %d bits, %d cells, crc32=0x%08x"
        % (len(data), bit_length, word_count, crc)
    )
    for entry in provenance:
        segments = " + ".join(
            "#%d bits[%d..%d)" % (segment["cell"], segment["bit_start"], segment["bit_end"])
            for segment in entry["cells"]
        )
        print("byte %d  value=0x%02x  cells: %s" % (entry["offset"], entry["value"], segments))
    return 0


def _cmd_backends(_args: argparse.Namespace) -> int:
    for backend_id in CATALOG.ids():
        print(backend_id)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b2t-dispatch",
        description="Execute the MBIR payload carried by a B2T0 container.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="decode and execute the container payload")
    run.add_argument("container", type=Path)
    run.add_argument("-s", "--stdin", help="input bytes: a file path, or '-' for raw stdin")
    run.add_argument("--trace", action="store_true", help="print one annotated line per VM step")
    run.add_argument("--json", action="store_true", help="print the full envelope as JSON")
    run.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    run.add_argument("--backend", default=DEFAULT_BACKEND)

    disasm = sub.add_parser("disasm", help="list MBIR instructions with their cells")
    disasm.add_argument("container", type=Path)
    disasm.add_argument("--json", action="store_true")

    provenance = sub.add_parser("provenance", help="map every byte to its carrying cells")
    provenance.add_argument("container", type=Path)
    provenance.add_argument("--json", action="store_true")

    backends_cmd = sub.add_parser("backends", help="list registered execution backends")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return _cmd_run(args)
        if args.command == "disasm":
            return _cmd_disasm(args)
        if args.command == "provenance":
            return _cmd_provenance(args)
        if args.command == "backends":
            return _cmd_backends(args)
    except KeyError as exc:  # unknown backend id
        print("b2t-dispatch: error: %s (available: %s)" % (exc, ", ".join(CATALOG.ids())), file=sys.stderr)
        return 1
    except (b2t.B2TError, DispatchError, OSError) as exc:
        print(f"b2t-dispatch: error: {exc}", file=sys.stderr)
        return 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
