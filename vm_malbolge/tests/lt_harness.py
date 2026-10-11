"""CMP_LT differential harness: 9 ordered pairs over {0,1,2} + 3 baselines.

Usage (from repo root):
    python3 vm_malbolge/tests/lt_harness.py [path/to/mbir_cmp_lt.mb]

Runs each vector on tools/oracle_classic.py and runners/malbolge-original/malbolge,
prints outputs and verdict.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic

RUNNER = REPO / "runners" / "malbolge-original" / "malbolge"

VECTORS = []
for a in (0, 1, 2):
    for b in (0, 1, 2):
        want = "01" if a < b else "00"
        VECTORS.append((f"cmp_lt({a},{b})", f"01{a:02x}01{b:02x}021000", want))
VECTORS += [
    ("baseline1 push+out", "01411000", "41"),
    ("baseline2 lifo", "01410142101000", "4241"),
    ("baseline3 halt", "00", ""),
]


def run_oracle(path, stdin_bytes, max_steps=600000):
    src = open(path, encoding="latin-1").read()
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=stdin_bytes.decode("latin-1"))
    return text.encode("latin-1").hex(), steps


def run_runner(path, stdin_bytes, max_steps=600000):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(stdin_bytes)
        name = f.name
    try:
        with open(name, "rb") as fin:
            r = subprocess.run([str(RUNNER), str(path), str(max_steps)],
                               stdin=fin, capture_output=True)
        out = r.stdout
        if out.endswith(b"\r\n"):
            out = out[:-2]
        elif out.endswith(b"\n"):
            out = out[:-1]
        return out.hex()
    finally:
        os.unlink(name)


def main():
    mb = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "vm_malbolge/src/mbir_cmp_lt.mb"
    passed = 0
    for label, hexin, want in VECTORS:
        stdin_bytes = bytes.fromhex(hexin)
        ohex, osteps = run_oracle(mb, stdin_bytes)
        rhex = run_runner(mb, stdin_bytes)
        ok = ohex == want and rhex == want
        passed += ok
        print(f"{label:20s} in={hexin:16s} want={want or '(empty)':6s} "
              f"oracle={ohex or '(empty)':6s} runner={rhex or '(empty)':6s} "
              f"steps={osteps} {'PASS' if ok else 'FAIL'}")
    print(f"== {passed}/{len(VECTORS)}")
    sys.exit(0 if passed == len(VECTORS) else 1)


if __name__ == "__main__":
    main()
