from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import b2t
import dispatch
from mbir import MBIRDecodeError, backends

# PUSH_CONST 0x02, PUSH_CONST 0x03, ADD, OUT_BYTE, HALT -> emits 0x05
ADD_PROGRAM = bytes([0x01, 0x02, 0x01, 0x03, 0x06, 0x10, 0x00])
# IN_BYTE, OUT_BYTE, IN_BYTE, OUT_BYTE, HALT -> echoes two stdin bytes
ECHO_PROGRAM = bytes([0x11, 0x10, 0x11, 0x10, 0x00])
# IN_BYTE, OUT_BYTE, HALT on empty stdin -> IN pushes the 0xFF EOF marker
EOF_PROGRAM = bytes([0x11, 0x10, 0x00])
# JUMP 0 -> runs until MAX_STEPS
LOOP_PROGRAM = bytes([0x0C, 0x00, 0x00, 0x00])

# (cell, bit_start, bit_end) segments per byte of ADD_PROGRAM
EXPECTED_ADD_SEGMENTS = {
    0: [(0, 0, 8)],
    1: [(0, 8, 15), (1, 15, 16)],
    2: [(1, 16, 24)],
    3: [(1, 24, 30), (2, 30, 32)],
    4: [(2, 32, 40)],
    5: [(2, 40, 45), (3, 45, 48)],
    6: [(3, 48, 56)],
}

# cells touched per instruction offset of ADD_PROGRAM
EXPECTED_ADD_INSTRUCTION_CELLS = {0: [0, 1], 2: [1, 2], 4: [2], 5: [2, 3], 6: [3]}

SCRIPT = Path(dispatch.__file__).resolve()


class TestProvenance(unittest.TestCase):
    def test_byte_provenance_exact_map(self) -> None:
        encoded = b2t.encode_bytes(ADD_PROGRAM)
        provenance = dispatch.byte_provenance(ADD_PROGRAM, encoded.words)
        self.assertEqual(len(provenance), len(ADD_PROGRAM))
        for entry in provenance:
            expected = EXPECTED_ADD_SEGMENTS[entry["offset"]]
            actual = [
                (segment["cell"], segment["bit_start"], segment["bit_end"])
                for segment in entry["cells"]
            ]
            self.assertEqual(actual, expected)
            self.assertEqual(entry["value"], ADD_PROGRAM[entry["offset"]])

    def test_byte_never_spans_more_than_two_cells(self) -> None:
        for length in range(1, 65):
            data = bytes((index * 113 + 5) % 256 for index in range(length))
            encoded = b2t.encode_bytes(data)
            for entry in dispatch.byte_provenance(data, encoded.words):
                self.assertLessEqual(len(entry["cells"]), 2)
                self.assertEqual(sum(len(s["bit_positions"]) for s in entry["cells"]), 8)

    def test_provenance_reassembly_lengths(self) -> None:
        for length in range(0, 49):
            data = bytes((index * 149 + 7) % 256 for index in range(length))
            encoded = b2t.encode_bytes(data)
            provenance = dispatch.byte_provenance(data, encoded.words)
            self.assertEqual(dispatch.reassemble_bytes(provenance), data)

    def test_reassemble_rejects_tampered_map(self) -> None:
        encoded = b2t.encode_bytes(b"\x05a")
        provenance = dispatch.byte_provenance(b"\x05a", encoded.words)
        provenance[0]["value"] ^= 0x01
        with self.assertRaises(b2t.B2TError):
            dispatch.reassemble_bytes(provenance)

    def test_provenance_rejects_wrong_cell_count(self) -> None:
        with self.assertRaises(b2t.B2TError):
            dispatch.byte_provenance(b"\x00\x00\x00\x00", (0,))

    def test_container_words_canonical(self) -> None:
        for length in (0, 1, 7, 8, 15, 16, 31, 100):
            data = bytes((index * 71 + 3) % 256 for index in range(length))
            encoded = b2t.encode_bytes(data)
            self.assertEqual(dispatch.container_words(encoded.container), encoded.words)


class TestDispatchRun(unittest.TestCase):
    def test_arithmetic_program_runs(self) -> None:
        encoded = b2t.encode_bytes(ADD_PROGRAM)
        envelope = dispatch.dispatch_container(encoded.container)
        self.assertEqual(envelope["backend"], "mbir-ref-python")
        self.assertEqual(envelope["status"], "HALTED")
        self.assertEqual(envelope["exit_code"], 0)
        self.assertEqual(envelope["steps"], 5)
        self.assertEqual(envelope["stdout_bytes"], [0x05])
        self.assertEqual(envelope["stdout_hex"], "05")
        self.assertEqual(envelope["program_bytes"], 7)
        self.assertEqual(envelope["bit_length"], 56)
        self.assertEqual(envelope["word_count"], 4)
        self.assertEqual(len(envelope["cells"]), 4)
        self.assertIsNone(envelope["error"])
        self.assertIsNone(envelope["trace"])

    def test_trace_steps_annotated(self) -> None:
        encoded = b2t.encode_bytes(ADD_PROGRAM)
        envelope = dispatch.dispatch_container(encoded.container, trace=True)
        trace = envelope["trace"]
        self.assertEqual(len(trace), 5)
        self.assertEqual([event["pc"] for event in trace], [0, 2, 4, 5, 6])
        self.assertEqual(
            [event["op"] for event in trace],
            ["PUSH_CONST", "PUSH_CONST", "ADD", "OUT_BYTE", "HALT"],
        )
        self.assertEqual(
            [event["operand"] for event in trace], [2, 3, None, None, None]
        )
        self.assertEqual(
            [event["stack"] for event in trace],
            [[], [2], [2, 3], [5], []],
        )
        for offset, event in zip(sorted(EXPECTED_ADD_INSTRUCTION_CELLS), trace):
            self.assertEqual(event["cells"], EXPECTED_ADD_INSTRUCTION_CELLS[offset])
            # The per-step byte slice must reassemble to exactly the dispatched
            # instruction bytes, through the provenance map only.
            span = event["bytes"]
            self.assertEqual(dispatch.reassemble_bytes(span), ADD_PROGRAM[event["pc"] : event["pc"] + len(span)])

    def test_trace_determinism(self) -> None:
        encoded = b2t.encode_bytes(ADD_PROGRAM)
        first = dispatch.dispatch_container(encoded.container, trace=True)
        second = dispatch.dispatch_container(encoded.container, trace=True)
        self.assertEqual(first["trace"], second["trace"])
        self.assertEqual(first["stdout_bytes"], second["stdout_bytes"])

    def test_stdin_echo(self) -> None:
        encoded = b2t.encode_bytes(ECHO_PROGRAM)
        envelope = dispatch.dispatch_container(encoded.container, stdin=b"AB")
        self.assertEqual(envelope["status"], "HALTED")
        self.assertEqual(envelope["stdout_bytes"], [65, 66])
        self.assertEqual(envelope["stdin_consumed"], 2)
        self.assertEqual(envelope["steps"], 5)

    def test_stdin_eof_marker(self) -> None:
        encoded = b2t.encode_bytes(EOF_PROGRAM)
        envelope = dispatch.dispatch_container(encoded.container)
        self.assertEqual(envelope["status"], "HALTED")
        self.assertEqual(envelope["stdout_bytes"], [0xFF])
        self.assertEqual(envelope["stdin_consumed"], 0)

    def test_max_steps(self) -> None:
        encoded = b2t.encode_bytes(LOOP_PROGRAM)
        envelope = dispatch.dispatch_container(encoded.container, max_steps=7, trace=True)
        self.assertEqual(envelope["status"], "MAX_STEPS")
        self.assertEqual(envelope["exit_code"], 2)
        self.assertEqual(envelope["steps"], 7)
        self.assertEqual(len(envelope["trace"]), 7)
        self.assertEqual({event["pc"] for event in envelope["trace"]}, {0})

    def test_bad_opcode_is_an_error_envelope(self) -> None:
        encoded = b2t.encode_bytes(b"\x7f")
        envelope = dispatch.dispatch_container(encoded.container)
        self.assertEqual(envelope["status"], "ERROR")
        self.assertEqual(envelope["exit_code"], 1)
        self.assertEqual(envelope["steps"], 0)
        self.assertEqual(envelope["error"]["reason"], "BAD_OPCODE")
        self.assertEqual(envelope["error"]["pc"], 0)

    def test_empty_payload_is_an_error_envelope(self) -> None:
        encoded = b2t.encode_bytes(b"")
        envelope = dispatch.dispatch_container(encoded.container)
        self.assertEqual(envelope["status"], "ERROR")
        self.assertEqual(envelope["error"]["reason"].startswith("BAD_OPERAND"), True)

    def test_truncated_operand_is_an_error_envelope(self) -> None:
        encoded = b2t.encode_bytes(b"\x01")
        envelope = dispatch.dispatch_container(encoded.container)
        self.assertEqual(envelope["status"], "ERROR")
        self.assertEqual(envelope["error"]["reason"], "BAD_OPERAND")

    def test_corrupt_container_refused_before_execution(self) -> None:
        raw = bytearray(b2t.encode_bytes(ADD_PROGRAM).container)
        raw[-1] ^= 0xFF  # breaks the CRC
        with self.assertRaises(b2t.B2TError):
            dispatch.dispatch_container(bytes(raw))


class TestBackendContract(unittest.TestCase):
    def test_catalog_lists_reference_backend(self) -> None:
        self.assertEqual(dispatch.CATALOG.ids(), ("mbir-ref-python",))
        backend = dispatch.CATALOG.get("mbir-ref-python")
        self.assertEqual(backend.backend_id, "mbir-ref-python")

    def test_execute_returns_backend_result(self) -> None:
        backend = dispatch.CATALOG.get("mbir-ref-python")
        result = backend.execute(ADD_PROGRAM)
        self.assertIsInstance(result, backends.BackendResult)
        self.assertEqual(result.backend_id, "mbir-ref-python")
        self.assertEqual(result.status, "HALTED")
        self.assertEqual(result.stdout, b"\x05")
        self.assertEqual(result.stderr, b"")
        self.assertEqual(result.exit_code, 0)

    def test_execute_error_envelope(self) -> None:
        backend = dispatch.CATALOG.get("mbir-ref-python")
        result = backend.execute(b"\x7f")
        self.assertEqual(result.status, "ERROR")
        self.assertIn(b"BAD_OPCODE", result.stderr)
        self.assertEqual(result.exit_code, 1)


class TestProgramMap(unittest.TestCase):
    def test_disasm_add_program(self) -> None:
        encoded = b2t.encode_bytes(ADD_PROGRAM)
        instructions = dispatch.program_map(ADD_PROGRAM, encoded.words)
        self.assertEqual([instruction["offset"] for instruction in instructions], [0, 2, 4, 5, 6])
        self.assertEqual(
            [instruction["mnemonic"] for instruction in instructions],
            ["PUSH_CONST", "PUSH_CONST", "ADD", "OUT_BYTE", "HALT"],
        )
        self.assertEqual([instruction["length"] for instruction in instructions], [2, 2, 1, 1, 1])
        self.assertEqual([instruction["operand"] for instruction in instructions], [2, 3, None, None, None])
        self.assertEqual(
            [instruction["operand_hex"] for instruction in instructions],
            ["0x02", "0x03", "\u2014", "\u2014", "\u2014"],
        )
        for instruction in instructions:
            self.assertEqual(
                instruction["cells"], EXPECTED_ADD_INSTRUCTION_CELLS[instruction["offset"]]
            )

    def test_disasm_rejects_invalid_payload(self) -> None:
        encoded = b2t.encode_bytes(b"\x99")
        with self.assertRaises(MBIRDecodeError):
            dispatch.program_map(b"\x99", encoded.words)


def _run_cli(args: list[str], cwd: Path, stdin: bytes = b"") -> subprocess.CompletedProcess:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        cwd=str(cwd),
        input=stdin,
        capture_output=True,
    )
    return subprocess.CompletedProcess(
        args, proc.returncode, proc.stdout.decode(), proc.stderr.decode()
    )


class TestCLI(unittest.TestCase):
    def test_run_json_with_trace_from_foreign_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "add.b2t"
            container.write_bytes(b2t.encode_bytes(ADD_PROGRAM).container)
            proc = _run_cli(["run", str(container), "--json", "--trace"], cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            envelope = json.loads(proc.stdout)
            self.assertEqual(envelope["status"], "HALTED")
            self.assertEqual(envelope["steps"], 5)
            self.assertEqual(len(envelope["trace"]), 5)
            self.assertEqual(envelope["stdout_bytes"], [5])

    def test_run_text_trace_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "add.b2t"
            container.write_bytes(b2t.encode_bytes(ADD_PROGRAM).container)
            proc = _run_cli(["run", str(container), "--trace"], cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("status=HALTED", proc.stdout)
            self.assertIn("#1 pc=0 PUSH_CONST 0x02", proc.stdout)
            self.assertIn("#4 pc=5 OUT_BYTE", proc.stdout)
            self.assertIn("#5 pc=6 HALT", proc.stdout)

    def test_run_bad_opcode_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "bad.b2t"
            container.write_bytes(b2t.encode_bytes(b"\x7f").container)
            proc = _run_cli(["run", str(container)], cwd=tmp)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("status=ERROR", proc.stdout)
            self.assertIn("BAD_OPCODE", proc.stdout)

    def test_run_max_steps_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "loop.b2t"
            container.write_bytes(b2t.encode_bytes(LOOP_PROGRAM).container)
            proc = _run_cli(["run", str(container), "--max-steps", "7"], cwd=tmp)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("status=MAX_STEPS", proc.stdout)
            self.assertIn("steps=7", proc.stdout)

    def test_run_stdin_dash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "echo.b2t"
            container.write_bytes(b2t.encode_bytes(ECHO_PROGRAM).container)
            proc = _run_cli(["run", str(container), "--stdin", "-", "--json"], cwd=tmp, stdin=b"AB")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            envelope = json.loads(proc.stdout)
            self.assertEqual(envelope["stdout_bytes"], [65, 66])
            self.assertEqual(envelope["stdin_consumed"], 2)

    def test_run_stdin_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "echo.b2t"
            container.write_bytes(b2t.encode_bytes(ECHO_PROGRAM).container)
            source = tmp / "in.bin"
            source.write_bytes(b"\x01\x02")
            proc = _run_cli(["run", str(container), "--stdin", str(source)], cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("01 02", proc.stdout)

    def test_disasm_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "add.b2t"
            container.write_bytes(b2t.encode_bytes(ADD_PROGRAM).container)
            proc = _run_cli(["disasm", str(container)], cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("0000 01 02", proc.stdout)
            self.assertIn("PUSH_CONST", proc.stdout)
            self.assertIn("OUT_BYTE", proc.stdout)
            self.assertIn("#2,#3", proc.stdout)

    def test_disasm_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "add.b2t"
            container.write_bytes(b2t.encode_bytes(ADD_PROGRAM).container)
            proc = _run_cli(["disasm", str(container), "--json"], cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertEqual(len(report["instructions"]), 5)

    def test_provenance_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "add.b2t"
            container.write_bytes(b2t.encode_bytes(ADD_PROGRAM).container)
            proc = _run_cli(["provenance", str(container)], cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("7 bytes, 56 bits, 4 cells", proc.stdout)
            self.assertIn("byte 1  value=0x02  cells: #0 bits[8..15) + #1 bits[15..16)", proc.stdout)
            self.assertIn("byte 6", proc.stdout)

    def test_provenance_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "add.b2t"
            container.write_bytes(b2t.encode_bytes(ADD_PROGRAM).container)
            proc = _run_cli(["provenance", str(container), "--json"], cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertEqual(len(report["bytes"]), 7)
            self.assertEqual(len(report["cells"]), 4)

    def test_backends_listing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            proc = _run_cli(["backends"], cwd=Path(tmp_dir_name))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(), "mbir-ref-python")

    def test_unknown_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            container = tmp / "add.b2t"
            container.write_bytes(b2t.encode_bytes(ADD_PROGRAM).container)
            proc = _run_cli(["run", str(container), "--backend", "nope"], cwd=tmp)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("unknown MBIR backend", proc.stderr)

    def test_corrupt_container_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            raw = bytearray(b2t.encode_bytes(ADD_PROGRAM).container)
            raw[b2t.HEADER.size] ^= 1  # payload bit flip -> decoded bytes differ -> CRC mismatch
            container = tmp / "broken.b2t"
            container.write_bytes(bytes(raw))
            proc = _run_cli(["run", str(container)], cwd=tmp)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("CRC", proc.stderr)


if __name__ == "__main__":
    unittest.main()
