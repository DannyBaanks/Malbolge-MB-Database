#!/usr/bin/env python3
"""L1: un JMP no cifra su propia celda (vendor Olmstead instrumentado).

Uso: python3 lemma_jmp.py <dir-nuevo-vacio>
Construye en <dir> tres binarios desde vendor/olmstead_original.c:
  plain  - fuente sin tocar (control de paridad con build/olmstead)
  instr  - registra en stderr cada JMP (pc, palabra) y cada escritura de datos
  mutant - ademas cifra la celda JMP ejecutada (control G3a)
"""
import collections
import hashlib
import json
import pathlib
import subprocess
import sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
GIT = ROOT.parent
OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
if any(OUT.iterdir()):
    raise SystemExit(f'output directory is not empty: {OUT}')
VENDOR = GIT / 'Malbolge-PureEpoch/vendor/olmstead_original.c'
NATIVE = GIT / 'Malbolge-PureEpoch/build/olmstead'
src = VENDOR.read_text()
sha = lambda b: hashlib.sha256(b).hexdigest()

# G0: la asignacion de c en 'i' precede a la linea de cifrado.
lines = src.splitlines()
jmp_line = next(i for i, l in enumerate(lines, 1) if "case 'i': c = mem[d]; break;" in l)
enc_line = next(i for i, l in enumerate(lines, 1) if 'mem[c] = xlat2[mem[c] - 33];' in l)
assert jmp_line < enc_line

HEAD = "    switch ( xlat1[( mem[c] - 33 + c ) % 94] )"
JMP = "      case 'i': c = mem[d]; break;"
ROTW = "      case '*': a = mem[d] = mem[d] / 3 + mem[d] % 3 * 19683; break;"
CRZW = "      case 'p': a = mem[d] = op( a, mem[d] ); break;"
for s in (HEAD, JMP, ROTW, CRZW):
    assert src.count(s) == 1, s
pre = "    { unsigned short pc0 = c; (void)pc0;\n"
instr = (src.replace(HEAD, pre + HEAD)
         .replace(JMP, "      case 'i': fprintf(stderr, \"J %u %u\\n\", pc0, mem[pc0]); c = mem[d]; break;")
         .replace(ROTW, "      case '*': fprintf(stderr, \"W %u\\n\", d); a = mem[d] = mem[d] / 3 + mem[d] % 3 * 19683; break;")
         .replace(CRZW, "      case 'p': fprintf(stderr, \"W %u\\n\", d); a = mem[d] = op( a, mem[d] ); break;"))
mutant = (src.replace(HEAD, pre + HEAD)
          .replace(JMP, "      case 'i': c = mem[d]; if (mem[pc0] >= 33 && mem[pc0] <= 126) mem[pc0] = xlat2[mem[pc0] - 33]; break;"))
# cerrar el bloque abierto por pre: tras el switch (antes del cifrado)
ENC = "    mem[c] = xlat2[mem[c] - 33];"
instr = instr.replace(ENC, "    }\n" + ENC)
mutant = mutant.replace(ENC, "    }\n" + ENC)

bins = {}
for name, text in (('plain', src), ('instr', instr), ('mutant', mutant)):
    c = OUT / f'olmstead_{name}.c'
    c.write_text(text)
    b = OUT / f'olmstead_{name}'
    subprocess.run(['gcc', '-O2', '-w', '-o', str(b), str(c)], check=True)
    bins[name] = b
(OUT / 'instr.diff').write_text(subprocess.run(
    ['diff', '-u', '--label', 'Malbolge-PureEpoch/vendor/olmstead_original.c', '--label', 'olmstead_instr.c',
     str(VENDOR), str(OUT / 'olmstead_instr.c')], capture_output=True, text=True).stdout)
(OUT / 'mutant.diff').write_text(subprocess.run(
    ['diff', '-u', '--label', 'Malbolge-PureEpoch/vendor/olmstead_original.c', '--label', 'olmstead_mutant.c',
     str(VENDOR), str(OUT / 'olmstead_mutant.c')], capture_output=True, text=True).stdout)

EV = ROOT / 'vm_malbolge/evidence'
cases = {
    'increment': (EV / 'increment_circuit_loop_v1/run02/increment.mb', bytes(range(256))),
    'phase_loop': (EV / 'g5_phase_loop_20261112/run01/positive.mb', b'ABCD'),
}


def run(binary, image, data, stderr_path=None, timeout=120):
    err = open(stderr_path, 'wb') if stderr_path else subprocess.DEVNULL
    try:
        p = subprocess.run(['stdbuf', '-o0', str(binary), str(image)], input=data, stdout=subprocess.PIPE,
                           stderr=err, timeout=timeout)
        return {'rc': p.returncode, 'stdout': p.stdout, 'timeout': False}
    except subprocess.TimeoutExpired as e:
        return {'rc': None, 'stdout': e.stdout or b'', 'timeout': True}
    finally:
        if stderr_path:
            err.close()


report = {'vendor_sha256': sha(VENDOR.read_bytes()), 'native_sha256': sha(NATIVE.read_bytes()),
          'g0': {'jmp_line': jmp_line, 'encrypt_line': enc_line,
                 'jmp_text': lines[jmp_line - 1].strip(), 'encrypt_text': lines[enc_line - 1].strip()},
          'cases': {}}
for tag, (image, data) in cases.items():
    # phase_loop no hace HALT tras EOF (documentado): se acota por timeout.
    t = 120 if tag == 'increment' else 2
    native = run(NATIVE, image, data, timeout=t)
    plain = run(bins['plain'], image, data, timeout=t)
    log = OUT / f'{tag}.instr.stderr.raw.txt'
    ins = run(bins['instr'], image, data, log, timeout=t)
    mut = run(bins['mutant'], image, data, timeout=t)
    last = {}            # pc -> palabra en la visita JMP previa
    writes = collections.Counter()   # escrituras de datos por direccion
    writes_since = {}    # pc -> numero de escrituras a pc vistas al ultimo JMP
    visits = collections.Counter()
    same = changed_with_write = changed_without_write = 0
    examples = []
    with open(log) as fh:
        for line in fh:
            k, *v = line.split()
            if k not in ('J', 'W') or len(v) != (2 if k == 'J' else 1) or not line.endswith('\n'):
                continue  # linea truncada por el timeout (solo phase_loop)
            if k == 'W':
                writes[int(v[0])] += 1
                continue
            pc, w = int(v[0]), int(v[1])
            visits[pc] += 1
            if pc in last:
                if w == last[pc]:
                    same += 1
                elif writes[pc] != writes_since[pc]:
                    changed_with_write += 1
                else:
                    changed_without_write += 1
                    if len(examples) < 5:
                        examples.append({'pc': pc, 'before': last[pc], 'after': w})
            last[pc] = w
            writes_since[pc] = writes[pc]
    # Con timeout, la ultima linea puede quedar truncada; solo afecta a phase_loop.
    # phase_loop no termina: comparar solo el prefijo verificado en g5_phase_loop.
    n = None if tag == 'increment' else 5
    cut = lambda r: r['stdout'][:n] if n else r['stdout']
    report['cases'][tag] = {
        'compared_stdout_prefix_bytes': n, 'compared_prefix_hex': cut(native).hex() if n else None,
        'image_sha256': sha(image.read_bytes()), 'input_sha256': sha(data), 'input_len': len(data),
        'native': {'rc': native['rc'], 'timeout': native['timeout'], 'stdout_sha256': sha(native['stdout']), 'stdout_len': len(native['stdout'])},
        'plain_equals_native': cut(plain) == cut(native),
        'instr_equals_native': cut(ins) == cut(native),
        'instr_log_sha256': sha(log.read_bytes()),
        'jmp_cells': len(visits), 'jmp_executions': sum(visits.values()),
        'revisits_same_word': same, 'revisits_changed_after_data_write': changed_with_write,
        'revisits_changed_without_write': changed_without_write, 'examples_changed_without_write': examples,
        'mutant': {'rc': mut['rc'], 'timeout': mut['timeout'], 'stdout_sha256': sha(mut['stdout']),
                   'stdout_len': len(mut['stdout']), 'diverges_from_native': mut['stdout'] != native['stdout'] or mut['timeout'] != native['timeout']},
    }
inc = report['cases']['increment']
assert inc['native']['rc'] == 0 and not inc['native']['timeout']
assert inc['native']['stdout_len'] == 256
for tag, r in report['cases'].items():
    assert r['plain_equals_native'] and r['instr_equals_native'], tag
    assert r['revisits_changed_without_write'] == 0, tag
    assert r['revisits_same_word'] > 0, tag
assert inc['mutant']['diverges_from_native']
assert report['cases']['phase_loop']['compared_prefix_hex'] == '41424344a8'
print(json.dumps(report, indent=2))
