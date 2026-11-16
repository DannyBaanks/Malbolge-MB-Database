#!/usr/bin/env python3
"""G5b-2 P1: ensamblador independiente a partir del plan en JSON de plan.zig.

Uso: python3 assemble.py <ruta-binario-plan> <dir-salida-vacio>
Lee los planes para positive / control_a / control_b, valida la disposicion
y legalidad contra xlat1/xlat2 de BolgeForge, sintetiza el preambulo y emite
las imagenes .mb listas para verificacion.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
MODES = ('positive', 'control_a', 'control_b')
VALID = set('ji*p</vo')
EFFECTS = {4, 5, 23, 39, 40, 62, 81}

if len(sys.argv) != 3:
    raise SystemExit('uso: python3 assemble.py <plan-bin> <dir-salida-vacio>')

PLAN_BIN = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
if any(OUT.iterdir()):
    raise SystemExit(f'output directory is not empty: {OUT}')

source = ROOT.parent / 'BolgeForge'
forge = pathlib.Path(tempfile.mkdtemp(prefix='g5b-p1-'))
try:
    (forge / 'tools').mkdir()
    (forge / 'reference/malbolge_org').mkdir(parents=True)
    for name in ('constants.py', 'tools/resynthesize.py', 'reference/malbolge_org/cat.mal'):
        shutil.copyfile(source / name, forge / name)
    sys.path.insert(0, str(forge))
    from constants import XLAT1, XLAT2  # noqa: E402
    from tools.resynthesize import synthesize_preamble_ops  # noqa: E402

    raw = (forge / 'reference/malbolge_org/cat.mal').read_bytes()
    template = [v for v in raw if 33 <= v <= 126]
    k94 = 325
    source_len = len(template) + 94 * k94

    def loads(pc: int, w: int) -> bool:
        return 33 <= w <= 126 and XLAT1[(w - 33 + pc) % 94] in VALID

    def succ(w: int) -> int:
        return ord(XLAT2[w - 33])

    reports = {}
    for mode in MODES:
        proc = subprocess.run([str(PLAN_BIN), mode], capture_output=True, text=True, check=True)
        plan = json.loads(proc.stdout)
        assert plan['mode'] == mode

        code = {int(k): int(v) for k, v in plan['code'].items()}
        targets = {int(k): int(v) for k, v in plan['targets'].items()}
        handoff = int(plan['handoff'])
        islands = {k: int(v) for k, v in plan['islands'].items()}

        # Validacion independiente de las islas contra xlat1/xlat2 del vendor
        assert islands['K'] % 94 == 2 and code[islands['K']] == 66
        assert islands['F'] % 94 == 60 and code[islands['F']] == 74
        for name, expected_op in (('MOVD_V', 40), ('ROT_V', 39), ('OUT', 5), ('MOVD_LOOP', 40)):
            x = islands[name]
            w = code[x]
            assert w in (70, 74), (name, w)
            assert (w + x) % 94 == expected_op, (name, x, w)
            assert (succ(w) + x) % 94 not in EFFECTS, (name, x, w)
        for name, x in islands.items():
            assert (code[x + 1] + (x + 1)) % 94 == 4, (name, x)
            assert loads(x, code[x]) and loads(x + 1, code[x + 1]), (name, x)

        assert source_len < min(targets), min(targets)

        clean = template + [33] * (source_len - len(template))
        t0 = time.monotonic()
        ops = synthesize_preamble_ops(
            clean, targets, handoff, 9003, 0, template_clean=template, boot='original'
        )
        end_ops = 99 + len(ops)
        if end_ops >= min(code):
            raise ValueError(f'{mode}: preamble {end_ops} overlaps code {min(code)}')
        if max(code) >= source_len - 2:
            raise ValueError(f'{mode}: code {max(code)} overlaps tail {source_len - 2}')

        prog = bytearray(template[:99])
        prog.extend(33 + ((XLAT1.index(ch) - i) % 94) for i, ch in enumerate(ops, 99))
        while len(prog) < source_len - 2:
            prog.append(33 + ((XLAT1.index('o') - len(prog)) % 94))
        prog.extend(template[-2:])
        for pc, w in code.items():
            prog[pc] = w

        assert all(loads(i, v) for i, v in enumerate(prog)), f'{mode}: loader failed'

        mb_path = OUT / f'{mode}.mb'
        mb_path.write_bytes(prog)
        (OUT / f'{mode}.plan.json').write_text(json.dumps(plan, indent=2) + '\n')
        (OUT / f'{mode}.ops').write_text(''.join(ops) + '\n')
        (OUT / f'{mode}.targets.json').write_text(
            json.dumps({str(k): v for k, v in sorted(targets.items())}, indent=2) + '\n'
        )
        reports[mode] = {
            'sha256': hashlib.sha256(prog).hexdigest(),
            'image_len': len(prog),
            'preamble_end': end_ops,
            'plan_length': len(ops),
            'targets': len(targets),
            'code_cells': len(code),
            'islands': islands,
            'elapsed_seconds': round(time.monotonic() - t0, 3),
        }

    summary = {'source_len': source_len, 'programs': reports}
    (OUT / 'assembly.results.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
finally:
    shutil.rmtree(forge, ignore_errors=True)
