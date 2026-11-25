"""Tests for the a04-malbolge backend.

Two layers, deliberately separated:

- Pure routing/contract tests (always run): the capability profile, honest
  refusal envelopes, budget translation, runner-resolution honesty and the
  CLI backend listing.  No substrate required.
- Substrate e2e tests (skip without a runnable Malbolge runner): every
  machine-evidenced vector through the routed pipeline with dual-engine
  parity, the committed instances re-verified against their evidence case
  by case, extension vectors, the MAX_STEPS translation, CLI runs and
  cross-backend agreement with the reference VM.

Expectations come from the committed machine evidence JSONs (frozen records
under vm_malbolge/evidence/), never from transcription; only the
extension/refusal literals of a04_vectors.py are hand-pinned (observed by
the bridge evidence run this feature ships).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import a04_backend
import a04_vectors
import b2t
import dispatch
from dispatch import DispatchError

REPO_ROOT = Path(a04_backend.__file__).resolve().parent.parent.parent
BACKEND = dispatch.CATALOG.get(a04_backend.BACKEND_ID)


def _executable_runner():
    """Mirror a04_backend's resolution (the env override is authoritative)."""
    env = os.environ.get("A04_MALBOLGE_RUNNER")
    if env:
        candidate = Path(env)
        return candidate if candidate.is_file() and os.access(candidate, os.X_OK) else None
    candidate = REPO_ROOT / a04_backend.DEFAULT_RUNNER_REL
    return candidate if candidate.is_file() and os.access(candidate, os.X_OK) else None


HAVE_RUNNER = _executable_runner() is not None
NEEDS_RUNNER = unittest.skipUnless(
    HAVE_RUNNER,
    "no executable Malbolge runner: build Malbolge-Engine (make) or set A04_MALBOLGE_RUNNER",
)


def _program(body, operand=0x41):
    """Materialize a P/O token body into MBIR bytes plus trailing HALT."""
    out = bytearray()
    for token in body:
        if token == "P":
            out += bytes([0x01, operand])
        else:
            out.append(0x10)
    out.append(0x00)
    return bytes(out)


def _container_envelope(program, **kwargs):
    container = b2t.encode_bytes(program).container
    return dispatch.dispatch_container(
        container, backend_id=a04_backend.BACKEND_ID, **kwargs
    )


class TestProfileRouting(unittest.TestCase):
    """Pure: routing and refusals never touch the substrate."""

    def test_lifo_bodies_route_to_lifo(self):
        for body, label in a04_backend.LIFO_BODIES.items():
            with self.subTest(shape=body, label=label):
                self.assertEqual(a04_backend.route_machine(_program(body)), "lifo")

    def test_alternation_routing_is_lifo_first(self):
        # k <= 2 alternation is LIFO-evidenced too: the committed LIFO image
        # executes it, so the router prefers the cheaper, older machine.
        for k in (1, 2):
            self.assertEqual(a04_backend.route_machine(_program(("P", "O") * k)), "lifo")
        for k in range(3, 9):
            with self.subTest(k=k):
                self.assertEqual(
                    a04_backend.route_machine(_program(("P", "O") * k)), "multicycle"
                )

    def test_refusal_envelopes(self):
        for input_hex, reason, note in a04_vectors.REFUSAL_VECTORS:
            with self.subTest(input_hex=input_hex, note=note):
                run = BACKEND.run_full(bytes.fromhex(input_hex))
                self.assertEqual(run["status"], "ERROR")
                self.assertEqual(run["exit_code"], 1)
                self.assertEqual(run["output"], b"")
                self.assertEqual(run["error"]["reason"], reason)
                # the CLI error line prints pc=%d: it must always be an int
                self.assertIsInstance(run["error"]["pc"], int)

    def test_nonempty_stdin_refused(self):
        run = BACKEND.run_full(bytes.fromhex("01411000"), stdin=b"X")
        self.assertEqual(run["status"], "ERROR")
        self.assertEqual(run["error"]["reason"], "UNSUPPORTED_STDIN")

    def test_trace_refused_by_backend(self):
        run = BACKEND.run_full(bytes.fromhex("01411000"), trace=True)
        self.assertEqual(run["status"], "ERROR")
        self.assertEqual(run["error"]["reason"], "UNSUPPORTED_TRACE")

    def test_trace_refused_by_dispatch(self):
        container = b2t.encode_bytes(bytes.fromhex("01411000")).container
        with self.assertRaises(DispatchError) as ctx:
            dispatch.dispatch_container(
                container, backend_id=a04_backend.BACKEND_ID, trace=True
            )
        self.assertIn("does not support tracing", str(ctx.exception))

    def test_execute_contract_shape(self):
        result = BACKEND.execute(bytes.fromhex("101000"))
        self.assertEqual(result.backend_id, a04_backend.BACKEND_ID)
        self.assertEqual(result.status, "ERROR")
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"UNSUPPORTED_PROFILE", result.stderr)

    def test_ref_envelope_has_no_backend_meta(self):
        # regression pin for the envelope change: the reference backend's
        # runs carry no meta, and dispatch must surface None, not invent it.
        container = b2t.encode_bytes(bytes.fromhex("01411000")).container
        envelope = dispatch.dispatch_container(
            container, backend_id=dispatch.DEFAULT_BACKEND
        )
        self.assertIsNone(envelope["backend_meta"])


class TestBudget(unittest.TestCase):
    """Pure: the MBIR-step to Malbolge-step translation."""

    def test_none_uses_default(self):
        self.assertEqual(
            a04_backend.malbolge_budget(None), a04_backend.DEFAULT_MALBOLGE_BUDGET
        )

    def test_translation(self):
        self.assertEqual(
            a04_backend.malbolge_budget(1),
            a04_backend.BASELINE_FLOOR + a04_backend.STEPS_PER_MBIR_STEP,
        )
        self.assertEqual(
            a04_backend.malbolge_budget(100),
            a04_backend.BASELINE_FLOOR + 100 * a04_backend.STEPS_PER_MBIR_STEP,
        )

    def test_capped_below_uint32(self):
        # the runner parses the step limit with strtoul into a uint32
        cap = a04_backend.malbolge_budget(10 ** 12)
        self.assertEqual(cap, a04_backend.RUNNER_BUDGET_CAP)
        self.assertLess(cap, 2 ** 32)


class TestRunnerHonesty(unittest.TestCase):
    """Pure: a broken override is an error, never a silent fallback."""

    def test_env_override_is_authoritative(self):
        saved = dict(os.environ)
        os.environ["A04_MALBOLGE_RUNNER"] = "/nonexistent/a04-test-malbolge"
        try:
            run = BACKEND.run_full(bytes.fromhex("01411000"))
        finally:
            os.environ.clear()
            os.environ.update(saved)
        self.assertEqual(run["status"], "ERROR")
        self.assertEqual(run["exit_code"], 1)
        self.assertEqual(run["error"]["reason"], "RUNNER_NOT_FOUND")
        self.assertIn("authoritative", run["error"]["detail"])


class TestCliBackends(unittest.TestCase):
    """Pure: the catalog listing names both substrates (no runner needed)."""

    def test_backends_listing_includes_a04(self):
        proc = subprocess.run(
            [sys.executable, str(Path(dispatch.__file__).resolve()), "backends"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(a04_backend.BACKEND_ID, proc.stdout)
        self.assertIn(dispatch.DEFAULT_BACKEND, proc.stdout)


@NEEDS_RUNNER
class TestMachineInstances(unittest.TestCase):
    """The committed instances reproduce their own evidence, case by case.

    Direct substrate calls (no router): several multicycle cases are only
    reachable this way, because the router prefers the LIFO image for every
    k <= 2 shape.  The LIMITATION_CONFIRMED control is included verbatim:
    the assertion is that the instance matches its RECORDED behavior
    (runner_hex 4354 — the push-push degradation), which is exactly the
    honesty this backend owes.  Through dispatch that shape routes to the
    LIFO machine (correct 4241), so the limitation can never surface there.
    """

    def test_lifo_instance_reproduces_all_evidence(self):
        for case in a04_vectors.machine_cases("lifo"):
            with self.subTest(case=case["input_hex"], note=case["description"]):
                result = BACKEND.run_machine("lifo", bytes.fromhex(case["input_hex"]))
                self.assertEqual(result["status"], "HALTED")
                self.assertEqual(result["output"].hex(), case["runner_hex"])
                self.assertEqual(result["steps"], case["runner_steps"])
                self.assertTrue(
                    result["meta"]["parity"].startswith("asserted ("),
                    result["meta"]["parity"],
                )

    def test_multicycle_instance_reproduces_all_evidence(self):
        for case in a04_vectors.machine_cases("multicycle"):
            with self.subTest(case=case["input_hex"], verdict=case["verdict"]):
                result = BACKEND.run_machine(
                    "multicycle", bytes.fromhex(case["input_hex"])
                )
                self.assertEqual(result["status"], "HALTED")
                self.assertEqual(result["output"].hex(), case["runner_hex"])
                self.assertEqual(result["steps"], case["runner_steps"])
                # oracle_classic emulates the machine faithfully, so the dual
                # assertion holds on the control vector too (4354 == 4354).
                self.assertEqual(result["meta"]["oracle_steps"], case["runner_steps"])


@NEEDS_RUNNER
class TestEndToEndRouter(unittest.TestCase):
    """Every machine-evidenced vector through containers and the router.

    The step count proves which machine ran: each routed instance carries
    its own recorded steps for the same input, so equality against the
    ROUTED machine's row verifies routing and execution at once.
    """

    def test_evidenced_vectors_route_and_execute(self):
        for machine in ("lifo", "multicycle"):
            for case in a04_vectors.machine_cases(machine):
                program = bytes.fromhex(case["input_hex"])
                routed = a04_backend.route_machine(program)
                expected = a04_vectors.case_by_input(routed, case["input_hex"])
                with self.subTest(source=machine, case=case["input_hex"], routed=routed):
                    envelope = _container_envelope(program)
                    self.assertEqual(envelope["status"], "HALTED")
                    self.assertEqual(envelope["exit_code"], 0)
                    self.assertEqual(envelope["backend_meta"]["machine"], routed)
                    self.assertEqual(envelope["stdout_hex"], expected["runner_hex"])
                    self.assertEqual(envelope["steps"], expected["runner_steps"])
                    self.assertTrue(
                        envelope["backend_meta"]["parity"].startswith("asserted ("),
                        envelope["backend_meta"]["parity"],
                    )
                    # cross-backend agreement: the reference VM must emit
                    # identical bytes for every in-profile shape
                    ref = dispatch.dispatch_container(
                        b2t.encode_bytes(program).container,
                        backend_id=dispatch.DEFAULT_BACKEND,
                    )
                    self.assertEqual(ref["status"], "HALTED")
                    self.assertEqual(ref["stdout_hex"], envelope["stdout_hex"])

    def test_extension_vectors(self):
        for machine, input_hex, expected_hex, expected_steps, note in (
            a04_vectors.EXTENSION_VECTORS
        ):
            with self.subTest(case=input_hex, note=note):
                envelope = _container_envelope(bytes.fromhex(input_hex))
                self.assertEqual(envelope["status"], "HALTED")
                self.assertEqual(envelope["exit_code"], 0)
                self.assertEqual(envelope["backend_meta"]["machine"], machine)
                self.assertEqual(envelope["stdout_hex"], expected_hex)
                self.assertEqual(envelope["steps"], expected_steps)
                ref = dispatch.dispatch_container(
                    b2t.encode_bytes(bytes.fromhex(input_hex)).container,
                    backend_id=dispatch.DEFAULT_BACKEND,
                )
                self.assertEqual(ref["stdout_hex"], expected_hex)


@NEEDS_RUNNER
class TestSubstrateBudget(unittest.TestCase):
    """max_steps translation semantics at the substrate seam."""

    def test_runner_timeout_maps_to_max_steps(self):
        with mock.patch.object(a04_backend, "malbolge_budget", return_value=1000):
            run = BACKEND.run_full(bytes.fromhex("01411000"))
        self.assertEqual(run["status"], "MAX_STEPS")
        self.assertEqual(run["exit_code"], 2)
        self.assertEqual(run["steps"], 1000)
        self.assertEqual(run["error"]["reason"], "MAX_STEPS")
        self.assertIn("skipped", run["meta"]["parity"])

    def test_small_mbir_budgets_still_complete(self):
        # documented, deliberate: the substrate's unit is the Malbolge step.
        # A 1-MBIR-step budget still translates to a 156,500-step Malbolge
        # budget, which carries the in-profile programs to completion —
        # substrate-level consumption inside an MBIR instruction is
        # invisible at MBIR granularity.
        envelope = _container_envelope(bytes.fromhex("01411000"), max_steps=1)
        self.assertEqual(envelope["status"], "HALTED")
        self.assertEqual(envelope["stdout_hex"], "41")
        self.assertEqual(envelope["steps"], 59752)
        self.assertEqual(envelope["backend_meta"]["malbolge_budget"], 156500)


@NEEDS_RUNNER
class TestCliRun(unittest.TestCase):
    def test_run_json_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.b2t"
            path.write_bytes(b2t.encode_bytes(bytes.fromhex("01411000")).container)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(Path(dispatch.__file__).resolve()),
                    "run",
                    "--backend",
                    a04_backend.BACKEND_ID,
                    "--json",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        envelope = json.loads(proc.stdout)
        self.assertEqual(envelope["status"], "HALTED")
        self.assertEqual(envelope["exit_code"], 0)
        self.assertEqual(envelope["stdout_hex"], "41")
        self.assertEqual(envelope["steps"], 59752)
        self.assertEqual(envelope["backend_meta"]["machine"], "lifo")
        self.assertEqual(envelope["backend_meta"]["runner_status"], "HALTED")

    def test_run_text_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "add.b2t"
            path.write_bytes(b2t.encode_bytes(bytes.fromhex("01020103061000")).container)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(Path(dispatch.__file__).resolve()),
                    "run",
                    "--backend",
                    a04_backend.BACKEND_ID,
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("UNSUPPORTED_OPCODE", proc.stdout)


if __name__ == "__main__":
    unittest.main()
