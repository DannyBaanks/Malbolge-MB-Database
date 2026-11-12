#!/usr/bin/env python3
"""Verify the reference cat's EOF discriminator over the full byte domain."""
import importlib.util
import json
import pathlib

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
spec = importlib.util.spec_from_file_location('compose', ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
crazy = m.SE.crazy

def discriminate(value):
    return crazy(crazy(59048, value), 29524)

values = [discriminate(n) for n in range(256)]
eof = discriminate(59048)
trits = [{(v // (3 ** p)) % 3 for v in range(256)} for p in range(10)]
result = {'formula': 'crazy(crazy(59048, value), 29524)',
          'orientation': 'crazy(accumulator, cell)',
          'eof_result': eof,
          'byte_collisions_with_eof': [v for v, d in enumerate(values) if d == eof],
          'distinct_byte_results': len(set(values)),
          'distinctive_trits': [p for p, vs in enumerate(trits) if 2 not in vs],
          'byte_trit_sets': [sorted(vs) for vs in trits],
          'control_wrong_eof_255_does_not_halt': discriminate(255) != eof,
          'scope': 'pure algebra; does not install or rearm a relocated loop'}
assert eof == 0 and not result['byte_collisions_with_eof']
assert result['distinctive_trits'] == [5, 6, 7, 8, 9]
(P/'algebra.results.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True, indent=2))
