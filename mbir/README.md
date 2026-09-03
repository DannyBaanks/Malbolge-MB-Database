# MBIR — Shared Semantic Runtime Contract

Language-neutral intermediate representation executed by a shared runtime,
ultimately hosted on Malbolge.

- `mbir.py` — encoder/decoder + static validation (MBIR_VERSION 0)
- `mbir_ref.py` — reference VM implementing the full MBIR semantic model (A03)
- `tests/test_mbir.py` — contract conformance suite (23/23 PASS)
- `tests/test_mbir_ref.py` — reference VM conformance suite (28/28 PASS)
- Contract spec: `docs/MBIR_CONTRACT.md`

## Quick use

```python
import sys; sys.path.insert(0, "mbir")
import mbir
blob = mbir.encode([
    (mbir.PUSH_CONST, 2), (mbir.PUSH_CONST, 3),
    (mbir.ADD, ()), (mbir.OUT_BYTE, ()), (mbir.HALT, ()),
])
print(mbir.decode(blob))
```

## Version

`MBIR_VERSION = 0` — frozen. Never change semantics in place; increment version.