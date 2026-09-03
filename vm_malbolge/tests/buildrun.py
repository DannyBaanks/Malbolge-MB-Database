"""Build-and-run harness for HeLL sources against oracle + real LMAO-compiled binary.

Usage (from repo root):
    py vm_malbolge/tests/buildrun.py <file.hell> <hex-input> [--expect=<hex>]

- Compiles with LMAO (fast mode) to a temp .mb
- Simulates with oracle_classic
- Executes on runners/malbolge-original/malbolge.exe
- Prints both outputs + verdict
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LMAO = os.path.join(REPO, "third_party", "lmao", "bin", "lmao.exe")
RUNNER = os.path.join(REPO, "runners", "malbolge-original", "malbolge.exe")
sys.path.insert(0, os.path.join(REPO, "tools"))
import oracle_classic


def compile_hell(src_path, out_mb):
    r = subprocess.run([LMAO, "-f", "-o", out_mb, src_path],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out_mb):
        return False, r.stdout + r.stderr
    return True, r.stdout


def run_oracle(path, stdin_bytes, max_steps=600000):
    src = open(path, encoding="latin-1").read()
    text, steps, status = oracle_classic.run(
        src, max_steps=max_steps, stdin_data=stdin_bytes.decode("latin-1"))
    return text, steps, status


def run_runner(path, stdin_bytes, max_steps=600000):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(stdin_bytes)
        stdin_file = f.name
    try:
        with open(stdin_file, "rb") as fin:
            r = subprocess.run([RUNNER, path, str(max_steps)],
                               stdin=fin, capture_output=True)
        out_bytes = r.stdout
        if out_bytes.endswith(b"\r\n"):
            out_bytes = out_bytes[:-2]
        return out_bytes, r.returncode, r.stderr.decode("latin-1")
    finally:
        os.unlink(stdin_file)


def main():
    src = sys.argv[1]
    hexin = sys.argv[2] if len(sys.argv) > 2 else ""
    stdin_bytes = bytes.fromhex(hexin) if hexin else b""
    expect = None
    for arg in sys.argv[3:]:
        if arg.startswith("--expect="):
            expect = bytes.fromhex(arg.split("=", 1)[1])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mb") as f:
        out_mb = f.name
    try:
        ok, log = compile_hell(src, out_mb)
        print("== LMAO compile:", "OK" if ok else "FAIL")
        if not ok:
            print(log)
            sys.exit(1)
        ot, osteps, ostatus = run_oracle(out_mb, stdin_bytes)
        print(f"== oracle: out={ot.encode('latin-1').hex()} steps={osteps} status={ostatus}")
        rout, rc, rerr = run_runner(out_mb, stdin_bytes)
        rerr_first = rerr.strip().splitlines()[0] if rerr.strip() else ""
        print(f"== runner: out={rout.hex()} rc={rc} stderr={rerr_first!r}")
        if expect is not None:
            print(f"== expect: {expect.hex()}, runner={rout.hex()}",
                  "MATCH" if rout == expect else "MISMATCH")
            if rout != expect:
                sys.exit(2)
    finally:
        os.unlink(out_mb)


if __name__ == "__main__":
    main()
