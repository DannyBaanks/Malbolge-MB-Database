"""Audit existing sweep evidence without rewriting it. Usage: verify.py PACK [REPEAT]."""
import hashlib
import itertools
import json
import pathlib
import sys

pack = pathlib.Path(sys.argv[1]).resolve()
repeat = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv)>2 else None
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected = set(itertools.permutations(('lll','llr','lr','rl','rr')))
roots = [pack/'run01', pack/'run02'] + ([repeat] if repeat else [])
images = {}
for root in roots:
    doc = json.loads((root/'sweep.json').read_text())
    orders = [tuple(r['order']) for r in doc['runs']]
    assert len(orders)==len(expected) and set(orders)==expected
    hashes = {}
    for row in doc['runs']:
        order = tuple(row['order'])
        folder = root/'-'.join(order)
        image = folder/'positive.mb'
        result = json.loads((folder/'probe.stdout.raw.json').read_text())['run']
        assert sha(image)==row['image_sha256']==result['image_sha256']
        assert result['call_order']==row['order']
        assert row['native_rc']==0 and row['independent_status']=='end' and row['local_trace_status']=='halt'
        assert row['shared_calls']==len(result['shared_calls'])==5
        assert row['continuation_visits']==result['continuation_visits']==[15000,15004,15008,15012,15016]
        assert row['output_hex']==result['output_hex']=='62e66ee66e'
        assert (folder/'positive.mb.native.stdout.raw').read_bytes()==bytes.fromhex(row['output_hex'])
        assert result['tails_unchanged']
        hashes[order]=sha(image)
    assert len(set(hashes.values()))==len(expected)
    if images: assert hashes==images
    images=hashes
rea=json.loads((pack/'rea.json').read_text())['records']
assert len(rea)==len(expected) and {tuple(r['order']) for r in rea}==expected
assert all(r['site_calls']==5 and r['equivalence'] and r['output_hex']=='62e66ee66e' for r in rea)
print(json.dumps({'result':'PASS','orders':len(expected),'distinct_images':len(set(images.values())),'identical_sweeps':len(roots),'rea_orders':len(rea)}))
