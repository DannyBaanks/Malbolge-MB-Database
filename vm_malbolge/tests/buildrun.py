"""Build-and-run harness for HeLL sources against oracle + real LMAO-compiled binary.

Usage (from repo root):
    py vm_malbolge/tests/buildrun.py <file.hell> <hex-input> [--expect=<hex>]
    py vm_malbolge/tests/buildrun.py <file.hell> <hex-input> [--fast-layout]

- Compiles with LMAO normal layout by default; --fast-layout opts into -f.
- Simulates with oracle_classic
- Executes on runners/malbolge-original/malbolge.exe
- Prints both outputs + verdict
"""
import os
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LMAO = os.path.join(REPO, "third_party", "lmao", "bin", "lmao.exe")
RUNNER = os.path.join(REPO, "runners", "malbolge-original", "malbolge.exe")
sys.path.insert(0, os.path.join(REPO, "tools"))
import oracle_classic


def exe_command(path_str):
    if os.name == "nt":
        return [path_str]
    path = Path(path_str)
    native = path.with_suffix("")
    if native.is_file() and os.access(native, os.X_OK):
        return [str(native)]
    wine = shutil.which("wine")
    if wine is not None:
        return [wine, str(path)]
    return [str(path)]


def compile_hell(src_path, out_mb, fast_layout=False):
    cmd = [*exe_command(LMAO)]
    if fast_layout:
        cmd.append("-f")
    cmd.extend(["-o", out_mb, src_path])
    r = subprocess.run(cmd,
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
            r = subprocess.run([*exe_command(RUNNER), path, str(max_steps)],
                               stdin=fin, capture_output=True)
        out_bytes = r.stdout
        if out_bytes.endswith(b"\r\n"):
            out_bytes = out_bytes[:-2]
        elif out_bytes.endswith(b"\n"):
            out_bytes = out_bytes[:-1]
        return out_bytes, r.returncode, r.stderr.decode("latin-1")
    finally:
        os.unlink(stdin_file)


def main():
    args = sys.argv[1:]
    fast_layout = "--fast-layout" in args
    args = [arg for arg in args if arg != "--fast-layout"]
    if not args:
        raise SystemExit("usage: buildrun.py <file.hell> <hex-input> [--expect=<hex>] [--fast-layout]")
    src = args[0]
    hexin = args[1] if len(args) > 1 else ""
    stdin_bytes = bytes.fromhex(hexin) if hexin else b""
    expect = None
    for arg in args[2:]:
        if arg.startswith("--expect="):
            expect = bytes.fromhex(arg.split("=", 1)[1])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mb") as f:
        out_mb = f.name
    try:
        ok, log = compile_hell(src, out_mb, fast_layout=fast_layout)
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
