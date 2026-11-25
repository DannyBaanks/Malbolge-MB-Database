"""Record trusted-fixture differential evidence; this is not part of the compiler."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = (
    Path(os.environ["MALBOLGE_MB_DATABASE_ROOT"])
    if "MALBOLGE_MB_DATABASE_ROOT" in os.environ
    else Path(__file__).resolve().parents[3]
)
SRC = Path(os.environ.get("CLASSIC_COMPILER_SRC", ROOT / "python/src"))
sys.path.insert(0, str(SRC))
from classic_compiler import compile_text


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


test_path = (
    SRC / "test_classic_compiler.py"
    if (SRC / "test_classic_compiler.py").exists()
    else ROOT / "python/tests/test_classic_compiler.py"
)
CORPUS = load("classic_cases", test_path).CORPUS
p5 = load(
    "classic_trace_primitives",
    ROOT / "vm_malbolge/evidence/g5b_flag_return_v5/probe.py",
)
SE = p5.SE


def trace(image, mapping):
    mem = list(image) + [0] * (59049 - len(image))
    for i in range(len(image), 59049):
        mem[i] = SE.crazy(mem[i - 1], mem[i - 2])
    a = c = d = 0
    stack = []
    events = []
    jumps = []
    counts = {}
    output = []
    active = False
    status = "limit"
    instances = {i["id"]: i for i in mapping["instances"]}

    def slots():
        return {
            depth: {"value": mem[s["slot"]], "journal": mem[s["journal"]]}
            for depth, s in mapping["slots"].items()
        }

    for step in range(1, 200000):
        if c == mapping["main_entry"]:
            active = True
        if active:
            counts[c] = counts.get(c, 0) + 1
            for mark in mapping["markers"].get(str(c), []):
                event = {
                    **mark,
                    "step": step,
                    "pc": c,
                    "d": d,
                    "a": a,
                    "slots": slots(),
                }
                events.append(event)
                if mark["kind"] == "call":
                    item = instances[mark["instance"]]
                    assert (
                        mem[d] == item["entry"] - 1
                        and mem[item["slot"]] == item["continuation"] - 1
                    )
                    assert item["depth"] == len(stack) + 1
                    stack.append(item["id"])
                elif mark["kind"] == "function_entry":
                    assert stack[-1] == mark["instance"]
                elif mark["kind"] == "return":
                    assert stack.pop() == mark["instance"]
                    assert mem[d] == instances[mark["instance"]]["continuation"] - 1
                elif mark["kind"] == "main_halt":
                    assert not stack
            for ancestor in stack[:-1]:
                item = instances[ancestor]
                assert mem[item["slot"]] == item["continuation"] - 1
        if not 33 <= mem[c] <= 126:
            status = "frozen"
            break
        op = (mem[c] + c) % 94
        if active and op == 4:
            jumps.append(
                {
                    "step": step,
                    "pc": c,
                    "d": d,
                    "stored": mem[d],
                    "next_pc": (mem[d] + 1) % 59049,
                }
            )
        if op == 4:
            c = mem[d]
        elif op == 5:
            output.append(a % 256)
        elif op == 23:
            raise AssertionError("unexpected input")
        elif op == 39:
            a = mem[d] = SE.rot(mem[d])
        elif op == 40:
            d = mem[d]
        elif op == 62:
            a = mem[d] = SE.crazy(a, mem[d])
        elif op == 81:
            status = "halt"
            break
        if 33 <= mem[c] <= 126:
            mem[c] = SE.encrypt(mem[c])
        c = (c + 1) % 59049
        d = (d + 1) % 59049
    assert status == "halt" and not stack and all(n == 1 for n in counts.values())
    assert len(jumps) == 2 * len(instances)
    assert all(
        mem[s["slot"]] == mem[s["journal"]] == 29524 for s in mapping["slots"].values()
    )
    return {
        "status": status,
        "steps": step,
        "output_hex": bytes(output).hex(),
        "events": events,
        "jumps": jumps,
        "compiled_code_visits_max": max(counts.values()),
        "final_slots": slots(),
    }


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    results = {}
    for name, source in CORPUS.items():
        folder = out / name
        folder.mkdir()
        (folder / "source.py").write_text(source)
        artifact = compile_text(source)
        (folder / "program.mb").write_bytes(artifact.image)
        (folder / "map.json").write_text(
            json.dumps(artifact.mapping, indent=2, ensure_ascii=False) + "\n"
        )
        py = subprocess.run(
            [sys.executable, str(folder / "source.py")],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            capture_output=True,
            check=True,
            timeout=10,
        )
        native = subprocess.run(
            [str(p5.OLM), str(folder / "program.mb")],
            input=b"",
            capture_output=True,
            check=True,
            timeout=10,
        )
        for prefix, result in [("python", py), ("native", native)]:
            (folder / (prefix + ".stdout.raw")).write_bytes(result.stdout)
            (folder / (prefix + ".stderr.raw")).write_bytes(result.stderr)
        independent = p5.cb.execute(artifact.image, b"", max_steps=200000)
        local = trace(artifact.image, artifact.mapping)
        assert (
            native.stdout
            == py.stdout
            == independent.output
            == bytes.fromhex(local["output_hex"])
            and independent.status == "end"
        )
        (folder / "trace.json").write_text(json.dumps(local, indent=2) + "\n")
        results[name] = {
            "image_sha256": hashlib.sha256(artifact.image).hexdigest(),
            "output_hex": py.stdout.hex(),
            "native_rc": native.returncode,
            "python_rc": py.returncode,
            "clasesbolge_status": independent.status,
            "clasesbolge_steps": independent.steps,
            "local_steps": local["steps"],
            "call_instances": len(artifact.mapping["instances"]),
        }
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
