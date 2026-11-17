#!/usr/bin/env python3
"""Verify G5b P5 artifacts and write a hashed result manifest."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

PACK = pathlib.Path(__file__).resolve().parent
EXPECTED_ORDER = ['lll', 'rr', 'lr', 'rl', 'llr']
EXPECTED_CALLS = [12130, 21990, 7534, 21990, 7534]
EXPECTED_OUTPUT = '62e66ee66e'
EXPECTED_CONTINUATIONS = [15000, 15004, 15008, 15012, 15016]


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_positive(run_dir: pathlib.Path) -> dict:
    result = read_json(run_dir / 'probe.stdout.raw.json')
    run = result['run']
    image = (run_dir / 'positive.mb').read_bytes()
    assert result['all_five_sequential_calls_match'] is True
    assert run['call_order'] == EXPECTED_ORDER
    assert run['shared_op_address'] == 38058 and run['variable_address'] == 40006
    assert run['continuation_visits'] == EXPECTED_CONTINUATIONS
    assert [call['value_after'] for call in run['shared_calls']] == EXPECTED_CALLS
    assert [call['d'] for call in run['shared_calls']] == [40006] * 5
    assert run['output_hex'] == EXPECTED_OUTPUT and run['output_length'] == 5
    assert run['native_rc'] == 0
    assert run['independent_status'] == 'end' and run['local_trace_status'] == 'halt'
    assert run['tails_unchanged']
    assert all(state['flags'] == [74, 74, 74, 74] and state['shared_op'] == 74
               for state in run['states_at_cont'])
    assert len(image) == 39932 and sha256(image) == run['image_sha256']
    assert (run_dir / 'positive.mb.native.stdout.raw').read_bytes() == bytes.fromhex(EXPECTED_OUTPUT)
    assert (run_dir / 'positive.mb.native.stderr.raw').read_bytes() == b''
    assert (run_dir / 'probe.stderr.raw.txt').read_bytes() == b''
    return run


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit('uso: python3 verify.py <run01-dir> <run02-dir>')
    run01, run02 = (pathlib.Path(arg).resolve() for arg in sys.argv[1:])
    positive1 = verify_positive(run01)
    positive2 = verify_positive(run02)
    image1 = (run01 / 'positive.mb').read_bytes()
    image2 = (run02 / 'positive.mb').read_bytes()
    assert image1 == image2, 'independent positive images differ'

    control = read_json(run01 / 'control/control.stdout.raw.json')['run']
    assert control['call_order'] == EXPECTED_ORDER
    assert control['fault'] == 'first lll caller incorrectly toggles f_extra and selects llr'
    assert control['shared_op_address'] == 38058 and control['variable_address'] == 40006
    assert control['observed_return_order'] == [15016]
    assert control['output_hex'] == '62' and control['native_rc'] == 0
    assert control['independent_status'] == 'end' and control['local_trace_status'] == 'halt'
    assert len(control['shared_calls']) == 1 and control['negative_control_detected']
    assert control['shared_calls'][0]['d'] == 40006
    assert control['shared_calls'][0]['value_after'] == 12130
    assert (run01 / 'control/negative.mb.native.stdout.raw').read_bytes() == b'\x62'
    assert (run01 / 'control/negative.mb.native.stderr.raw').read_bytes() == b''
    assert (run01 / 'control/control.stderr.raw.txt').read_bytes() == b''

    rea = read_json(PACK / 'rea_summary.json')
    assert rea['runs'][0]['evidence_id'] and rea['runs'][1]['evidence_id']
    assert rea['runs'][0]['status'] == rea['runs'][1]['status'] == 'HALTED'
    assert rea['runs'][0]['output_bytes'] == [98, 230, 110, 230, 110]
    assert rea['runs'][1]['output_bytes'] == [98]
    assert rea['runs'][0]['events_truncated'] and rea['runs'][1]['events_truncated']
    assert rea['runs'][0]['captured_shared_site_events'] == 0
    assert rea['runs'][1]['captured_shared_site_events'] == 0

    verification = {
        'schema': 'g5b_p5_verification_v1',
        'positive_order': EXPECTED_ORDER,
        'positive_images_identical': True,
        'positive_image_sha256': sha256(image1),
        'positive_image_bytes': len(image1),
        'positive_shared_op_address': 38058,
        'positive_variable_address': 40006,
        'positive_continuations': EXPECTED_CONTINUATIONS,
        'positive_call_values': EXPECTED_CALLS,
        'positive_output_hex': EXPECTED_OUTPUT,
        'positive_steps_local': [positive1['local_trace_steps'], positive2['local_trace_steps']],
        'control_output_hex': control['output_hex'],
        'control_return_order': control['observed_return_order'],
        'control_calls': len(control['shared_calls']),
        'rea_positive_status': rea['runs'][0]['status'],
        'rea_positive_steps': rea['runs'][0]['steps'],
        'rea_positive_events_truncated': rea['runs'][0]['events_truncated'],
        'rea_control_status': rea['runs'][1]['status'],
        'rea_control_steps': rea['runs'][1]['steps'],
        'rea_control_events_truncated': rea['runs'][1]['events_truncated'],
        'rea_site_event_coverage': 'NOT_DEMONSTRATED: both 4096-event prefixes stop before the shared-code region',
        'gates': {'G0': 'PASS', 'G1': 'PASS', 'G2': 'PASS', 'G3': 'PASS', 'G4': 'PASS',
                  'REA_runtime_and_output': 'PASS', 'REA_site_event_coverage': 'NOT_DEMONSTRATED'},
    }
    (PACK / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')

    artifacts = []
    for path in sorted(PACK.rglob('*')):
        if not path.is_file() or path.name in {'manifest.json', 'hashes.sha256'}:
            continue
        data = path.read_bytes()
        artifacts.append({'path': path.relative_to(PACK).as_posix(),
                          'bytes': len(data), 'sha256': sha256(data)})
    manifest = {
        'schema': 'g5b_p5_manifest_v1',
        'pack': 'G5b P5 — cinco llamadores secuenciales',
        'artifact_count': len(artifacts),
        'artifacts': artifacts,
    }
    (PACK / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

    hash_rows = []
    for path in sorted(PACK.rglob('*')):
        if not path.is_file() or path.name == 'hashes.sha256':
            continue
        hash_rows.append(f"{sha256(path.read_bytes())}  {path.relative_to(PACK).as_posix()}")
    (PACK / 'hashes.sha256').write_text('\n'.join(hash_rows) + '\n')

    for line in (PACK / 'hashes.sha256').read_text().splitlines():
        expected_hash, relpath = line.split('  ', 1)
        assert sha256((PACK / relpath).read_bytes()) == expected_hash, relpath
    assert len(image1) == 39932
    print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    main()
