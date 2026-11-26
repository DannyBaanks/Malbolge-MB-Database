#!/usr/bin/env python3
"""crypto/machine_compile.py — de .hell a imagen Classic con instalador.

Bifurcacion de vm_malbolge/tools/increment_bf/compile.py (segunda mitad):
LMAO parcheado para dumpear el layout + instalador autonomo sintetizado con
BolgeForge + validacion del loader estricto. No copia imagenes previas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]          # raiz de MALBOLGE-MB-DATABASE (worktree)
FORGE = ROOT / "vm_malbolge/tools/increment_bf/backend"
LMAO = ROOT / "third_party/lmao"


def patch_layout_extractor(source: str) -> str:
    old = "int needs_initialization = 0;"
    if source.count(old) != 1:
        raise RuntimeError("unsupported LMAO source: initialization marker")
    source = source.replace(old, "int needs_initialization = 1;")
    needle = "\t\t\tupdate_offsets(memory_layout);\n\t\t\tif (generate_opcodes_from_memory_layout"
    replacement = '''\t\t\tupdate_offsets(memory_layout);
            if (getenv("DUMP_LAYOUT")) {
                FILE *dump = fopen(getenv("DUMP_LAYOUT"), "w");
                if (!dump || !generate_opcodes_from_memory_layout(memory_layout, last_preinitialized_position, opcodes, labeltree, 0, 1)) return 2;
                fprintf(dump, "ENTRY %d\\n", entrypoint->offset);
                for (i=0; i<=C2; i++) if (opcodes[i]>=0) fprintf(dump, "%u %d\\n", i, opcodes[i]);
                fclose(dump); return 0;
            }
\t\t\tif (generate_opcodes_from_memory_layout'''
    if source.count(needle) != 1:
        raise RuntimeError("unsupported LMAO source: layout marker")
    return source.replace(needle, replacement, 1)


def run(argv, **kwargs):
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300, **kwargs)
    if p.returncode:
        raise RuntimeError(f"{argv[0]} exited {p.returncode}: {p.stderr[-3000:]}")
    return p


def compile_hell(hell: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    for f in (FORGE / "constants.py", FORGE / "tools/resynthesize.py",
              FORGE / "bootstrap_1533.bin", LMAO / "src/main.c"):
        if not f.is_file():
            raise FileNotFoundError(f)
    with tempfile.TemporaryDirectory(prefix="cipher-compile-") as temp:
        t = Path(temp)
        src = t / "src"
        shutil.copytree(LMAO / "src", src)
        (t / "bin").mkdir()
        main = src / "main.c"
        main.write_text(patch_layout_extractor(main.read_text()))
        run(["make", "-C", str(src)])
        layout = t / "layout.txt"
        env = os.environ.copy()
        env["DUMP_LAYOUT"] = str(layout)
        run([str(t / "bin/lmao"), "-f", "-o", str(t / "unused.mb"), str(hell)], cwd=ROOT, env=env)
        lines = layout.read_text().splitlines()
        entry = int(lines[0].split()[1])
        values = {}
        for line in lines[1:]:
            a, b = map(int, line.split())
            if a in values:
                raise ValueError(f"duplicate layout cell {a}")
            values[a] = b
        if not values or min(values) < 1533:
            raise ValueError("layout conflicts with bootstrap")
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(FORGE))
        from constants import XLAT1  # noqa: PLC0415
        from tools.resynthesize import synthesize_preamble_ops  # noqa: PLC0415
        raw = (FORGE / "bootstrap_1533.bin").read_bytes()
        if len(raw) != 1535:
            raise ValueError("invalid bootstrap asset")
        template = list(raw[:1533]) + [33] * 45 + list(raw[-2:])
        length = min(values) - 20
        length -= (length - len(template)) % 94
        if length <= len(template):
            raise ValueError("layout leaves no bootstrap room")
        clean = template + [33] * (length - len(template))
        ops = synthesize_preamble_ops(clean, values, entry, 9003, 0, template_clean=template,
                                      boot="original", direct_gap=60, borrow_penalty=1,
                                      rng=random.Random(14), restart_p1=0.9, restart_p2=0.95)
        end = 99 + len(ops)
        if end > length - 2:
            raise ValueError(f"installer too large: {end} > {length - 2}")
        image = bytearray(template[:99])
        image.extend(33 + ((XLAT1.index(ch) - i) % 94) for i, ch in enumerate(ops, 99))
        while len(image) < length - 2:
            image.append(33 + ((XLAT1.index("o") - len(image)) % 94))
        image.extend(template[-2:])
        if not all(XLAT1[(v - 33 + i) % 94] in "ji*p</vo" for i, v in enumerate(image)):
            raise AssertionError("not accepted by strict loader")
        with output.open("xb") as f:
            f.write(image)
        return {
            "image_sha256": hashlib.sha256(image).hexdigest(),
            "image_bytes": len(image),
            "layout_cells": len(values),
            "entry": entry,
            "installer_ops": len(ops),
            "hell_sha256": hashlib.sha256(hell.read_bytes()).hexdigest(),
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hell", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    meta = compile_hell(args.hell, args.out)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()