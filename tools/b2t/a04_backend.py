#!/usr/bin/env python3
"""A04 backend — the Malbolge-hosted fetch-loop runtime as a real substrate.

This module registers the second real execution backend of the b2t
dispatcher: the verified Malbolge machines of the A04/A05 program
(vm_malbolge/), driven through the recorded C runner
(runners/malbolge-original/malbolge, the "original" Malbolge-Engine build).

Pipeline position (tools/b2t/README.md):

    .b2t container --b2t--> MBIR bytes --[profile route]--> Malbolge machine
                                                        |          |
                                                        '-- oracle_classic
                                                        (byte+step parity is
                                                         asserted on every
                                                         single execution)

Machines (committed, evidence-verified instances):

    lifo        vm_malbolge/src/mbir_a05_lifo.mb
                (vm_malbolge/evidence/mbir_a05_lifo_smoke.json, 7/7 PASS)
                two-slot LIFO: push/push/out orderings and <= 2 sequential
                push/out cycles.

    multicycle  vm_malbolge/src/mbir_a05_multicycle.mb
                (vm_malbolge/evidence/mbir_a05_multicycle_smoke.json,
                8 PASS + 1 LIMITATION_CONFIRMED control)
                strictly alternating (PUSH, OUT)^k cycles, k >= 1.

Honesty contract
----------------
The capability envelope is the union of the shapes demonstrated in the
machine evidence, plus each machine's own data-generality claim (arbitrary
operand bytes; arbitrary sequential cycles) — and every execution re-verifies
that claim live:

    opcodes         {HALT 0x00, PUSH_CONST 0x01, OUT_BYTE 0x10} only
    trailing HALT   required (the machines EOF-halt; the profile refuses
                    instead of relying on that accident)
    after-HALT      nothing
    stdin           must be empty (the machines consume the program itself
                    from stdin as raw bytes; MBIR IN_BYTE is out of profile)
    stack shape     one of the demonstrated families below

Anything else is refused with an explicit UNSUPPORTED_* error envelope —
never an exception, never a crash, never a silent fallback.  Dir presence
is not engine presence.

Every executed run is a differential probe: the C runner's output and step
count are asserted byte-for-byte and step-for-step against
tools/oracle_classic.py running the same normalized machine image and the
same program; divergence surfaces as ENGINE_PARITY_MISMATCH and the run is
an ERROR.  The multicycle limitation control (LIMITATION_CONFIRMED in the
machine evidence: push-push degrades to 0x4354) can never surface through
dispatch, because that shape routes to the LIFO machine, which implements
it correctly.

max_steps is denominated in MBIR steps (like every backend); it is
translated into a Malbolge-step budget (baseline floor + a measured ~6,046
substrate steps per MBIR instruction, with margin), capped below the
runner's uint32 argv parse limit.  Runner `status: TIMEOUT` maps to
MAX_STEPS (exit code 2).

Runner channel (recorded contract, see the runner_contract block of
vm_malbolge/evidence/mbir_a04_backend_bridge.json): program as RAW bytes on
stdin — never an ASCII hex string, which feeds the machines' unknown-opcode
guard (constant 0x54 per byte) —; emitted bytes on stdout plus ONE trailing
newline (stripped once); ``steps: <N> | status: HALTED|TIMEOUT`` on stderr;
exit code 0 either way.

Tracing is not supported (trace_supported = False): the substrate executes
tens of thousands of Malbolge steps per MBIR opcode; per-step annotation is
mbir-ref-python --trace, not this substrate.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
_TOOLS = _REPO_ROOT / "tools"
for _path in (_HERE, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from mbir import MBIRDecodeError, backends
from mbir import decode as mbir_decode

BACKEND_ID = "a04-malbolge"

# Runner resolution: A04_MALBOLGE_RUNNER overrides authoritatively (a set
# but missing path is an honest error, never a silent fallback); without it
# the recorded repository binary is used when present.
DEFAULT_RUNNER_REL = "runners/malbolge-original/malbolge"

# max_steps=None translates to this Malbolge-step budget: comfortably above
# every evidenced vector (the largest, the 5-cycle hello string, halts at
# 72,885 steps).
DEFAULT_MALBOLGE_BUDGET = 600_000

# Measured substrate cost per executed MBIR instruction is ~6,046-6,052
# Malbolge steps (A05/A05b evidence); the floor covers the machine
# baselines (42,655-53,700 steps before the first opcode lands).
BASELINE_FLOOR = 150_000
STEPS_PER_MBIR_STEP = 6_500

# The runner parses the step limit with strtoul into a uint32; stay below it.
RUNNER_BUDGET_CAP = 4_000_000_000

# Wall-clock ceiling for one runner invocation (the machines always halt
# inside the profile; this guards against a broken runner build).
WALL_TIMEOUT_DEFAULT = 120.0

MACHINES = {
    "lifo": {
        "image": "vm_malbolge/src/mbir_a05_lifo.mb",
        "evidence": "vm_malbolge/evidence/mbir_a05_lifo_smoke.json",
        "label": "A05 2-slot LIFO (mbir_a05_lifo.mb)",
    },
    "multicycle": {
        "image": "vm_malbolge/src/mbir_a05_multicycle.mb",
        "evidence": "vm_malbolge/evidence/mbir_a05_multicycle_smoke.json",
        "label": "A05b multicycle alternator (mbir_a05_multicycle.mb)",
    },
}

# Body shapes (everything before the mandatory trailing HALT) demonstrated
# on the committed LIFO instance.  Descriptions are verbatim intent from the
# machine evidence; operands are arbitrary u8.
LIFO_BODIES = {
    (): "bare HALT",
    ("P",): "single PUSH, no OUT",
    ("P", "O"): "one PUSH/OUT cycle",
    ("P", "O", "P", "O"): "two sequential PUSH/OUT cycles",
    ("P", "P", "O", "O"): "push, push, out, out (LIFO order)",
    ("P", "P", "O"): "push, push, out (top pop)",
}


class _Refusal(Exception):
    """Internal: a program-level refusal with its reason and detail.

    Never escapes this module: run_full converts these into ERROR run
    records.  pc stays -1 unless a concrete instruction offset is known
    (the CLI prints ``pc=%d``, so it must always be an int).
    """

    def __init__(self, reason: str, detail: str, pc: int = -1):
        super().__init__("%s: %s" % (reason, detail))
        self.reason = reason
        self.detail = detail
        self.pc = pc


# ---------------------------------------------------------------------------
# Capability profile: tokenize + route
# ---------------------------------------------------------------------------


def _tokenize(blob: bytes) -> tuple[str, ...]:
    """Decode MBIR and map instructions to P (PUSH_CONST), O (OUT_BYTE), H (HALT)."""
    try:
        decoded = mbir_decode(blob)
    except MBIRDecodeError as exc:
        raise _Refusal(
            "UNSUPPORTED_MBIR", "MBIR decode refused the stream: %s" % exc, -1
        ) from exc
    tokens = []
    for mnemonic, _operands, offset in decoded:
        if mnemonic == "HALT":
            tokens.append("H")
        elif mnemonic == "PUSH_CONST":
            tokens.append("P")
        elif mnemonic == "OUT_BYTE":
            tokens.append("O")
        else:
            raise _Refusal(
                "UNSUPPORTED_OPCODE",
                "opcode %s at offset %d is outside the A04 demonstrated subset "
                "{HALT 0x00, PUSH_CONST 0x01, OUT_BYTE 0x10}" % (mnemonic, offset),
                offset,
            )
    return tuple(tokens)


def _is_alternating(body: tuple[str, ...]) -> bool:
    """True for strict (P, O)^k bodies with k >= 1."""
    if not body or len(body) % 2 != 0:
        return False
    return all(
        body[index] == "P" and body[index + 1] == "O"
        for index in range(0, len(body), 2)
    )


def _route(tokens: tuple[str, ...]) -> str:
    """Route a token stream to the machine whose evidence covers it."""
    if not tokens or tokens[-1] != "H":
        raise _Refusal(
            "UNSUPPORTED_PROFILE",
            "the A04 machines require an explicit trailing HALT (0x00): the "
            "machines EOF-halt and the reference VM errors on end-of-stream, "
            "so the profile sides with the stricter reading and refuses",
            -1,
        )
    body = tokens[:-1]
    if "H" in body:
        raise _Refusal(
            "UNSUPPORTED_PROFILE",
            "instructions after HALT are not accepted by the A04 profile",
            -1,
        )
    if body in LIFO_BODIES:
        return "lifo"
    # Complete these sets for the multicycle machine's own demonstrated
    # coverage; unreachable while every k<=2 shape sits in LIFO_BODIES, but
    # kept explicit so the routing class of each machine documents itself.
    if body == ("P",) or _is_alternating(body):
        return "multicycle"
    # Richer refusal diagnostics for the common near-miss shapes.
    depth = 0
    for index, token in enumerate(body):
        if token == "P":
            depth += 1
        else:
            depth -= 1
            if depth < 0:
                raise _Refusal(
                    "UNSUPPORTED_PROFILE",
                    "OUT_BYTE with an empty stack at instruction %d matches no "
                    "demonstrated machine profile" % index,
                    -1,
                )
    if depth > 2:
        raise _Refusal(
            "UNSUPPORTED_PROFILE",
            "peak stack depth %d exceeds the 2-slot machines (deeper stacks "
            "are the A06 frontier, not demonstrated)" % depth,
            -1,
        )
    raise _Refusal(
        "UNSUPPORTED_PROFILE",
        "opcode ordering %r matches no demonstrated machine shape (the six "
        "LIFO bodies or strictly alternating PUSH/OUT cycles)" % ("".join(body),),
        -1,
    )


def route_machine(blob: bytes) -> str:
    """Decode `blob` and return the machine name whose evidence covers it.

    Raises _Refusal (UNSUPPORTED_*) for anything outside the capability
    profile.  Routing is lifo-first: k <= 2 alternation and single pushes
    run on the committed LIFO image; k >= 3 runs on multicycle.
    """
    return _route(_tokenize(blob))


# ---------------------------------------------------------------------------
# Budget translation
# ---------------------------------------------------------------------------


def malbolge_budget(max_steps: int | None) -> int:
    """Translate an MBIR-step budget into a Malbolge-step runner budget.

    None -> DEFAULT_MALBOLGE_BUDGET.  With an explicit MBIR budget the
    translation is BASELINE_FLOOR + STEPS_PER_MBIR_STEP per step, capped
    below the runner's uint32 argv limit.  Substrate step consumption inside
    a single MBIR instruction is invisible at MBIR granularity; a runner
    TIMEOUT therefore reports MAX_STEPS, and small MBIR budgets can still
    complete (documented, deliberate: the substrate's unit is the Malbolge
    step, the contract's unit is the MBIR step).
    """
    if max_steps is None:
        return DEFAULT_MALBOLGE_BUDGET
    budget = BASELINE_FLOOR + STEPS_PER_MBIR_STEP * int(max_steps)
    return min(budget, RUNNER_BUDGET_CAP)


# ---------------------------------------------------------------------------
# Runner channel
# ---------------------------------------------------------------------------


def wall_timeout() -> float:
    env = os.environ.get("A04_MALBOLGE_WALL_TIMEOUT")
    if env:
        try:
            return max(float(env), 1.0)
        except ValueError:
            pass
    return WALL_TIMEOUT_DEFAULT


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_machine(machine: str) -> bytes:
    """Read a committed machine image as bytes, CRLF-normalized.

    autocrlf checkouts rewrite the image's line endings (worktree copies of
    the committed blobs are CRLF-tailed); the real engine and the parity
    oracle must always consume identical bytes, so every consumer of this
    module normalizes first.
    """
    if machine not in MACHINES:
        raise _Refusal("MACHINE_IMAGE_NOT_FOUND", "unknown machine %r" % machine, -1)
    relative = MACHINES[machine]["image"]
    path = _REPO_ROOT / relative
    if not path.is_file():
        raise _Refusal(
            "MACHINE_IMAGE_NOT_FOUND",
            "machine image %s is not present in this checkout" % relative,
            -1,
        )
    return path.read_bytes().replace(b"\r\n", b"\n")


_RUNNER_STATUS_RE = re.compile(rb"steps:\s*(\d+)\s*\|\s*status:\s*([A-Za-z_-]+)")


def parse_runner_result(stdout: bytes, stderr: bytes) -> tuple[bytes, int, str]:
    """Parse the recorded (stdout, stderr) channel of the original runner.

    Contract: emitted bytes on stdout plus ONE trailing newline (strip
    once); ``steps: <N> | status: HALTED|TIMEOUT`` on stderr; exit code 0
    either way (TIMEOUT means the step budget ran out).
    """
    match = _RUNNER_STATUS_RE.search(stderr)
    if match is None:
        raise _Refusal(
            "RUNNER_FAILED",
            "unrecognized runner output (stderr=%r)" % stderr[:200],
            -1,
        )
    steps = int(match.group(1))
    status = match.group(2).decode("ascii", "replace")
    out = stdout
    if out.endswith(b"\r\n"):
        out = out[:-2]
    elif out.endswith(b"\n"):
        out = out[:-1]
    return out, steps, status


def _oracle_parity(image: bytes, program: bytes, budget: int) -> tuple[bytes, int, str]:
    """Run tools/oracle_classic.py on the same image+program (parity oracle)."""
    if str(_TOOLS) not in sys.path:
        sys.path.insert(0, str(_TOOLS))
    import oracle_classic

    try:
        text, steps, status = oracle_classic.run(
            image.decode("latin-1"),
            max_steps=budget,
            stdin_data=program.decode("latin-1"),
        )
    except Exception as exc:  # the oracle is a measurement instrument: any failure is parity-breaking
        raise _Refusal(
            "ENGINE_PARITY_MISMATCH",
            "oracle_classic failed on the machine image: %r" % (exc,),
            -1,
        ) from exc
    return text.encode("latin-1"), int(steps), str(status)


# ---------------------------------------------------------------------------
# Backend adapter
# ---------------------------------------------------------------------------


class A04MalbolgeBackend:
    """BackendAdapter (structural, mbir/backends.py) over the real machines."""

    backend_id = BACKEND_ID
    trace_supported = False

    def resolve_runner(self) -> Path:
        """Resolve the C runner path or raise RUNNER_NOT_FOUND.

        A04_MALBOLGE_RUNNER is authoritative when set: a set-but-missing path
        is an honest error, never a silent fallback to the repo binary.
        """
        env = os.environ.get("A04_MALBOLGE_RUNNER")
        if env:
            candidate = Path(env)
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate
            raise _Refusal(
                "RUNNER_NOT_FOUND",
                "A04_MALBOLGE_RUNNER points to %s, which is not an executable "
                "file (the override is authoritative: no fallback)" % env,
                -1,
            )
        candidate = _REPO_ROOT / DEFAULT_RUNNER_REL
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise _Refusal(
            "RUNNER_NOT_FOUND",
            "no executable Malbolge runner at %s; build the original variant "
            "from Malbolge-Engine (make) or point A04_MALBOLGE_RUNNER at one"
            % DEFAULT_RUNNER_REL,
            -1,
        )

    def _invoke_runner(self, runner: Path, image: bytes, program: bytes, budget: int):
        """Run the real machine once: image on disk, program as raw stdin bytes."""
        with tempfile.NamedTemporaryFile(suffix=".mb") as image_file:
            image_file.write(image)
            image_file.flush()
            try:
                return subprocess.run(
                    [str(runner), image_file.name, str(budget)],
                    input=program,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=wall_timeout(),
                )
            except subprocess.TimeoutExpired as exc:
                raise _Refusal(
                    "RUNNER_WALL_TIMEOUT",
                    "the real runner exceeded the %.0fs wall limit (budget=%d "
                    "Malbolge steps)" % (wall_timeout(), budget),
                    -1,
                ) from exc
            except OSError as exc:
                raise _Refusal(
                    "RUNNER_FAILED", "executing the runner failed: %s" % exc, -1
                ) from exc

    def run_machine(self, machine: str, program: bytes, budget: int | None = None) -> dict:
        """Execute `program` on `machine` through the real runner.

        The public substrate seam: run_full uses it for routed programs,
        tests and probes use it directly to assert the committed instances
        against their evidence.  Dual-engine parity is asserted on every
        HALTED run; a runner TIMEOUT maps to status MAX_STEPS here.
        """
        if budget is None:
            budget = DEFAULT_MALBOLGE_BUDGET
        runner = self.resolve_runner()
        image = load_machine(machine)
        proc = self._invoke_runner(runner, image, program, budget)
        out, steps, status = parse_runner_result(proc.stdout, proc.stderr)
        meta = {
            "machine": machine,
            "machine_image": MACHINES[machine]["image"],
            "machine_image_sha256": _sha256(image),
            "runner": str(runner),
            "runner_sha256": _sha256_file(runner),
            "malbolge_budget": int(budget),
            "runner_status": status,
        }
        if status == "TIMEOUT":
            meta["parity"] = "skipped (runner hit the step budget)"
            return {"status": "MAX_STEPS", "output": out, "steps": steps, "meta": meta}
        if status != "HALTED":
            raise _Refusal(
                "RUNNER_FAILED",
                "unrecognized runner status %r on machine %s" % (status, machine),
                -1,
            )
        oracle_out, oracle_steps, oracle_status = _oracle_parity(image, program, budget)
        meta["oracle_steps"] = oracle_steps
        meta["parity"] = "asserted (oracle_classic: output + steps equal)"
        if oracle_status != "HALTED" or oracle_out != out or oracle_steps != steps:
            raise _Refusal(
                "ENGINE_PARITY_MISMATCH",
                "runner(out=%s steps=%s status=%s) diverged from oracle_classic"
                "(out=%s steps=%s status=%s) on machine %s; the substrate's "
                "differential assertion tripped"
                % (
                    out.hex(),
                    steps,
                    status,
                    oracle_out.hex(),
                    oracle_steps,
                    oracle_status,
                    machine,
                ),
                -1,
            )
        return {"status": "HALTED", "output": out, "steps": steps, "meta": meta}

    # -- run_full contract (mirrors MBIRRefBackend.run_full's shape) --------

    def run_full(self, blob: bytes, stdin: bytes = b"", max_steps=None, trace=False) -> dict:
        """Execute an MBIR blob; return a run record or an honest refusal.

        Refusals are ERROR records with error.reason ∈ {UNSUPPORTED_*,
        RUNNER_*, ENGINE_PARITY_MISMATCH, MAX_STEPS context}; executed runs
        carry status HALTED (exit 0) or MAX_STEPS (exit 2, translated
        runner TIMEOUT).
        """
        if trace:
            return _refuse(
                "UNSUPPORTED_TRACE",
                "the A04 substrate executes tens of thousands of Malbolge "
                "steps per MBIR opcode; per-step annotation lives in "
                "mbir-ref-python --trace",
                -1,
                None,
            )
        if stdin:
            return _refuse(
                "UNSUPPORTED_STDIN",
                "the A04 machines consume the program itself from stdin as "
                "raw bytes; MBIR-level stdin (IN_BYTE) is outside the "
                "demonstrated profile",
                -1,
                None,
            )
        try:
            machine = route_machine(blob)
        except _Refusal as refusal:
            return _refuse_from(refusal, None)
        budget = malbolge_budget(max_steps)
        try:
            result = self.run_machine(machine, blob, budget)
        except _Refusal as refusal:
            return _refuse_from(refusal, {"machine": machine, "malbolge_budget": budget})
        if result["status"] == "MAX_STEPS":
            return {
                "status": "MAX_STEPS",
                "exit_code": 2,
                "steps": result["steps"],
                "output": result["output"],
                "trace_events": [],
                "in_cursor": 0,
                "error": {
                    "reason": "MAX_STEPS",
                    "pc": -1,
                    "detail": "the Malbolge machine exhausted the translated "
                    "step budget (%d substrate steps)" % budget,
                },
                "meta": result["meta"],
            }
        return {
            "status": "HALTED",
            "exit_code": 0,
            "steps": result["steps"],
            "output": result["output"],
            "trace_events": [],
            "in_cursor": 0,
            "error": None,
            "meta": result["meta"],
        }

    def execute(self, blob: bytes, stdin: bytes = b"") -> backends.BackendResult:
        """MBIR backend contract surface (mbir/backends.py)."""
        run = self.run_full(blob, stdin)
        stderr = b""
        if run["error"]:
            message = "%s at pc=%d" % (run["error"]["reason"], run["error"]["pc"])
            if run["error"].get("detail"):
                message += ": %s" % run["error"]["detail"]
            stderr = message.encode()
        return backends.BackendResult(
            backend_id=self.backend_id,
            status=run["status"],
            stdout=run["output"],
            stderr=stderr,
            exit_code=run["exit_code"],
        )


def _refuse(reason: str, detail: str, pc: int, meta) -> dict:
    """ERROR run record for a program-level refusal (exit code 1)."""
    return {
        "status": "ERROR",
        "exit_code": 1,
        "steps": 0,
        "output": b"",
        "trace_events": [],
        "in_cursor": 0,
        "error": {"reason": reason, "pc": pc, "detail": detail},
        "meta": meta,
    }


def _refuse_from(refusal: _Refusal, meta) -> dict:
    return _refuse(refusal.reason, refusal.detail, refusal.pc, meta)


def register(catalog: backends.BackendCatalog) -> None:
    """Register this substrate alongside the reference backend."""
    catalog.register(A04MalbolgeBackend())
