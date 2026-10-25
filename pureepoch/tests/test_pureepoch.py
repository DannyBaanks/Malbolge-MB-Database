"""
Test suite for the PureEpoch track in MALBOLGE-MB-DATABASE.

Verifies SHA-256 integrity and executes the 12 canonical PureEpoch artifacts
against the native Malbolge runner (runners/malbolge-original/malbolge).
"""
import hashlib
import json
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNNER = REPO_ROOT / "runners" / "malbolge-original" / "malbolge"
PROGS_DIR = REPO_ROOT / "pureepoch" / "programs"
EVIDENCE_DIR = REPO_ROOT / "pureepoch" / "evidence"


def run_malbolge(prog_name: str, stdin_bytes: bytes = b"", max_steps: int = 100000):
    prog_path = PROGS_DIR / prog_name
    assert prog_path.exists(), f"Program not found: {prog_path}"
    assert RUNNER.exists(), f"Runner not found: {RUNNER}"

    proc = subprocess.run(
        [str(RUNNER), str(prog_path), str(max_steps)],
        input=stdin_bytes,
        capture_output=True,
    )
    return proc


def test_01_sha256_integrity():
    hashes_file = EVIDENCE_DIR / "hashes.json"
    assert hashes_file.exists(), "hashes.json missing"
    with open(hashes_file) as f:
        data = json.load(f)

    for filename, expected_hash in data["hashes"].items():
        p = PROGS_DIR / filename
        assert p.exists(), f"File {filename} missing"
        actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {filename}: {actual_hash} != {expected_hash}"


def test_02_m1a_reversible_mutation():
    proc = run_malbolge("m1a_rot10.mal")
    assert proc.returncode == 0
    assert proc.stdout == b"%\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 43" in proc.stderr


def test_03_m1b_checkpoint_journal():
    proc = run_malbolge("m1b_normal.mal")
    assert proc.returncode == 0
    assert proc.stdout == b"\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 14" in proc.stderr


def test_04_m1c_in_band_decision_rollback():
    proc = run_malbolge("m1c_normal.mal", stdin_bytes=b"1")
    assert proc.returncode == 0
    assert proc.stdout == b"\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 66" in proc.stderr


def test_05_m1e_prior_dependent_recovery():
    proc = run_malbolge("m1e_normal.mal", stdin_bytes=b"1")
    assert proc.returncode == 0
    assert proc.stdout == b"\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 570" in proc.stderr


def test_06_m2_two_epoch_continuation():
    proc = run_malbolge("m2_normal.mal", stdin_bytes=b"11")
    assert proc.returncode == 0
    assert proc.stdout == b"Q\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 1276" in proc.stderr


def test_07_m3_three_epoch_chain():
    proc = run_malbolge("m3_normal.mal", stdin_bytes=b"111")
    assert proc.returncode == 0
    assert proc.stdout == b"\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 7349" in proc.stderr


def test_08_quine94_ceiling_probe():
    proc = run_malbolge("quine94_ceiling_probe.mal")
    assert proc.returncode == 0
    assert proc.stdout == b"Q\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 36" in proc.stderr


def test_09_torus_borrow_e_t2():
    proc = run_malbolge("torus_borrow_e_t2.mal")
    assert proc.returncode == 0
    assert proc.stdout == b"\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 203" in proc.stderr


def test_10_torus_e_t3_normal():
    proc = run_malbolge("torus_e_t3_normal.mal")
    assert proc.returncode == 0
    assert proc.stdout == b"\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 260" in proc.stderr


def test_11_boss1_byzantine_cascade():
    proc = run_malbolge("boss1_byzantine.mal", stdin_bytes=b"11")
    assert proc.returncode == 0
    assert proc.stdout == b"Q\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 1286" in proc.stderr


def test_12_boss2_turing_brainfuck():
    proc = run_malbolge("boss2_brainfuck.mal")
    assert proc.returncode == 0
    assert proc.stdout == b"\x01\x01\x02\x01\x02\n"
    assert b"status: HALTED" in proc.stderr
    assert b"steps: 1205" in proc.stderr


@pytest.mark.parametrize(
    "inp,expected_out,expected_steps",
    [
        (b"0", b"\n", 9),
        (b"1", b"1\n", 15),
        (b"2", b"11\n", 16),
        (b"3", b"111\n", 17),
        (b"7", b"1111111\n", 23),
        (b"", b"\n", 2),
    ],
)
def test_13_boss3_autonomous_loop_all_cases(inp, expected_out, expected_steps):
    proc = run_malbolge("boss3_autonomous_loop.mal", stdin_bytes=inp)
    assert proc.returncode == 0
    assert proc.stdout == expected_out
    assert b"status: HALTED" in proc.stderr
    assert f"steps: {expected_steps}".encode() in proc.stderr
