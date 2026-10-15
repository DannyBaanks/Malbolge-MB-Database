"""Milestone M2 CF + CMP_EQ differential test harness.

Tests stored-program control flow across all 7 vectors:
  - Vector 1: JMP skip HALT (exp 41)
  - Vector 2: JMP other immediate (exp 58)
  - Vector 3: JZ taken (exp 42)
  - Vector 4: JZ not taken (exp 43)
  - Vector 5: CALL then return (exp 4241)
  - Vector 6: CMP_EQ taken 1==1 (exp 42)
  - Vector 7: CMP_EQ not taken 1!=2 (exp 43)

Usage:
    python3 vm_malbolge/tests/m2_cf_cmp_harness.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic

RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"
MB_PATH = REPO / "vm_malbolge/src/mbir_m2_cf_cmp.mb"

VECTORS = [
    ("Vector 1: JMP skip HALT", "0c05000000014110000000", "41"),
    ("Vector 2: JMP other immediate", "0c05000000015810000000", "58"),
    ("Vector 3: JZ taken", "01000d0700000001421000", "42"),
    ("Vector 4: JZ not taken", "01010d0900000143100000", "43"),
    ("Vector 5: CALL then return", "0e0700014110000142100f", "4241"),
    ("Vector 6: CMP_EQ taken (1==1)", "0401000001000043420000", "42"),
    ("Vector 7: CMP_EQ not taken (1!=2)", "0401000002000043420000", "43"),
]


def run_all() -> bool:
    if not MB_PATH.exists():
        sys.exit(f"Binary not found: {MB_PATH}")
    if not RUNNER.exists():
        sys.exit(f"Native runner not found: {RUNNER}")

    size = MB_PATH.stat().st_size
    headroom = 59049 - size
    print(f"Testing {MB_PATH.name} ({size} bytes, headroom={headroom} bytes)")
    if size > 59049:
        sys.exit(f"FAIL: Size {size} exceeds 59049 limit!")

    mb_content = MB_PATH.read_text(encoding="latin-1")
    all_ok = True

    for name, hex_in, exp in VECTORS:
        inp = bytes.fromhex(hex_in).decode("latin-1")

        # Python reference oracle
        out_o, steps_o, status_o = oracle_classic.run(
            mb_content, max_steps=500000, stdin_data=inp
        )
        out_o_hex = out_o.encode("latin-1").hex()

        # Native C runner
        run_res = subprocess.run(
            [str(RUNNER), str(MB_PATH)],
            input=bytes.fromhex(hex_in),
            capture_output=True,
        )
        out_r_hex = run_res.stdout.hex().strip()
        if out_r_hex.endswith("0a"):
            out_r_hex = out_r_hex[:-2]

        match = (out_o_hex == exp and out_r_hex == exp)
        parity = (out_o_hex == out_r_hex)
        verdict = "PASS" if match else "FAIL"
        print(
            f"  {name}: exp={exp} oracle={out_o_hex} runner={out_r_hex} (steps={steps_o}) parity={parity} -> {verdict}"
        )
        if not match:
            all_ok = False

    if all_ok:
        print("ALL 7 VECTORS PASSED WITH 100% BIT-EXACT DUAL PARITY")
    else:
        print("FAIL: Some vectors did not match expected output or lacked parity")
    return all_ok


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
