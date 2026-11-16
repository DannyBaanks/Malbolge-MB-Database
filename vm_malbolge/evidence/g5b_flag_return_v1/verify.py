#!/usr/bin/env python3
"""G5b-2 P1: verificador independiente de puertas G0..G4.

Uso: python3 verify.py <dir-run01> [<dir-run02>]
Ejecuta las imagenes .mb en:
  1. Olmstead nativo (Malbolge-PureEpoch/build/olmstead) con entrada vacia;
  2. Trazador scratch del repo (epoch_dload_compose_v1/probe.py SE);
  3. Tercer interprete independiente (clasesbolge/tools/malbolge.py).
Comprueba G0..G3 y, si se pasa <dir-run02>, G4 (identidad byte a byte).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
MODES = ('positive', 'control_a', 'control_b')
VALID = set('ji*p</vo')

if len(sys.argv) not in (2, 3):
    raise SystemExit('uso: python3 verify.py <dir-run01> [<dir-run02>]')

OUT1 = pathlib.Path(sys.argv[1]).resolve()
OUT2 = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else None

OLMSTEAD = ROOT.parent / 'Malbolge-PureEpoch/build/olmstead'
CLASES_DIR = pathlib.Path(os.environ['CLASESBOLGE_DIR']) if 'CLASESBOLGE_DIR' in os.environ else ROOT.parents[1] / 'clasesbolge'
CLASES_MALBOLGE = CLASES_DIR / 'tools/malbolge.py'

spec_se = importlib.util.spec_from_file_location(
    'compose_probe', ROOT / 'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py'
)
mod_se = importlib.util.module_from_spec(spec_se)
spec_se.loader.exec_module(mod_se)
SE = mod_se.SE

spec_cb = importlib.util.spec_from_file_location('clasesbolge_malbolge', CLASES_MALBOLGE)
mod_cb = importlib.util.module_from_spec(spec_cb)
sys.path.insert(0, str(CLASES_MALBOLGE.parent))
spec_cb.loader.exec_module(mod_cb)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def trace_scratch(image: bytes, plan: dict) -> dict:
    n = 59049
    mem = list(image) + [0] * (n - len(image))
    for i in range(len(image), n):
        mem[i] = SE.crazy(mem[i - 1], mem[i - 2])

    islands = {k: int(v) for k, v in plan['islands'].items()}
    k_pc = islands['K']
    f_pc = islands['F']
    v_addr = int(plan['data']['V'])
    jmp_pcs = [pc + 1 for pc in islands.values()]
    jmp_init = {pc: mem[pc] for pc in jmp_pcs}

    a = c = d = 0
    out = []
    in_loop = False
    f_at_k = []
    v_write_sites = []
    jmp_changed = False
    status = 'limit'

    for steps in range(1, 2_000_000):
        if c == k_pc:
            in_loop = True
            f_at_k.append(mem[f_pc])
        if not 33 <= mem[c] <= 126:
            status = 'frozen'
            break
        op = (mem[c] + c) % 94
        if op == 4:
            c = mem[d]
        elif op == 5:
            out.append(a % 256)
        elif op == 23:
            a = 59048
        elif op == 39:
            if in_loop and d == v_addr:
                v_write_sites.append(c)
            a = mem[d] = SE.rot(mem[d])
        elif op == 40:
            d = mem[d]
        elif op == 62:
            if in_loop and d == v_addr:
                v_write_sites.append(c)
            a = mem[d] = SE.crazy(a, mem[d])
        elif op == 81:
            status = 'halt'
            break
        if 33 <= mem[c] <= 126:
            mem[c] = SE.encrypt(mem[c])
        c = (c + 1) % n
        d = (d + 1) % n
        if in_loop and any(mem[pc] != jmp_init[pc] for pc in jmp_pcs):
            jmp_changed = True

    return {
        'status': status,
        'steps': steps,
        'output': bytes(out),
        'f_at_k': f_at_k,
        'v_write_sites': sorted(set(v_write_sites)),
        'jmp_changed': jmp_changed,
    }


def run_olmstead(mb_path: pathlib.Path) -> dict:
    proc = subprocess.run(
        [str(OLMSTEAD), str(mb_path)],
        input=b'',
        capture_output=True,
        timeout=15,
    )
    return {'rc': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}


def expected_outputs(v0: int) -> dict[str, bytes]:
    rs = [v0]
    for _ in range(6):
        rs.append(SE.rot(rs[-1]))
    r = [x % 256 for x in rs[1:]]
    return {
        'positive': bytes([r[0], r[0], r[1], r[2], r[2], r[3], r[4], r[4], r[5]]),
        'control_a': bytes([r[0], r[1], r[2]]),
        'control_b': bytes([r[0], r[0], r[1], r[2], r[3]]),
    }


v0_ref = json.loads((OUT1 / 'positive.plan.json').read_text())['v0']
expected = expected_outputs(int(v0_ref))

results = {
    'olmstead_sha256': sha256_bytes(OLMSTEAD.read_bytes()),
    'clasesbolge_malbolge_sha256': sha256_bytes(CLASES_MALBOLGE.read_bytes()),
    'v0': v0_ref,
    'expected_hex': {k: v.hex() for k, v in expected.items()},
    'modes': {},
}

for mode in MODES:
    mb_path = OUT1 / f'{mode}.mb'
    plan = json.loads((OUT1 / f'{mode}.plan.json').read_text())
    image = mb_path.read_bytes()

    loader_ok = all((v + i) % 94 in mod_se.VALID for i, v in enumerate(image))
    native = run_olmstead(mb_path)
    scratch = trace_scratch(image, plan)
    cb_res = mod_cb.execute(image, b'', max_steps=2_000_000)

    exp = expected[mode]
    assert loader_ok, f'{mode}: loader_ok failed'
    assert native['rc'] == 0, f'{mode}: olmstead rc={native["rc"]}'
    assert native['stdout'] == exp, (mode, native['stdout'].hex(), exp.hex())
    assert scratch['status'] == 'halt' and scratch['output'] == exp, (mode, scratch)
    assert cb_res.status == 'end' and cb_res.output == exp, (mode, cb_res.report(), cb_res.output.hex())

    rot_v = int(plan['islands']['ROT_V'])
    assert scratch['v_write_sites'] == [rot_v], (mode, scratch['v_write_sites'], rot_v)
    assert not scratch['jmp_changed'], (mode, 'jmp_changed')
    if mode == 'positive':
        assert scratch['f_at_k'] == [74, 74, 74, 74], scratch['f_at_k']
    if mode == 'control_b':
        assert scratch['f_at_k'][0] == 74 and 70 in scratch['f_at_k'][1:], scratch['f_at_k']
        assert native['stdout'][:3] == expected['positive'][:3]
        assert native['stdout'] != expected['positive']

    results['modes'][mode] = {
        'image_sha256': sha256_bytes(image),
        'loader_ok': loader_ok,
        'olmstead_rc': native['rc'],
        'olmstead_stdout_hex': native['stdout'].hex(),
        'scratch_status': scratch['status'],
        'scratch_steps': scratch['steps'],
        'scratch_output_hex': scratch['output'].hex(),
        'f_at_k': scratch['f_at_k'],
        'v_write_sites': scratch['v_write_sites'],
        'jmp_changed': scratch['jmp_changed'],
        'clasesbolge_status': cb_res.status,
        'clasesbolge_steps': cb_res.steps,
        'clasesbolge_output_hex': cb_res.output.hex(),
        'expected_hex': exp.hex(),
        'all_interpreters_match': True,
    }

if OUT2 is not None:
    repro = {}
    for mode in MODES:
        for ext in ('mb', 'ops', 'plan.json', 'targets.json'):
            fname = f'{mode}.{ext}'
            b1 = (OUT1 / fname).read_bytes()
            b2 = (OUT2 / fname).read_bytes()
            assert b1 == b2, f'G4 mismatch on {fname}'
            repro[fname] = sha256_bytes(b1)
    results['g4_reproducible'] = True
    results['g4_sha256'] = repro

(OUT1 / 'verification.results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
