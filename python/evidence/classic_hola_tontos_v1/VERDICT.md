# Hola Tontos — Classic v0 official greeting

DEMONSTRATED for this fixture. The host compiler compiles `python/examples/hola_tontos.py`; the resulting standalone strict Classic image executes a physical function call and numeric return. Exact output is `Hola Tontos :P Jajajaja` followed by LF. CPython, Olmstead, clasesbolge, the local trace and REA agree on output; two independent compilations reproduce identical images, maps, traces and REA reports. No change to the compiler or the historical corpus. This is a new example, not an extension of the supported Python subset.

- Image: [program.mb](run01/hola_tontos/program.mb), 39932 bytes.
- SHA-256: `d6685c83a11d6c951087cc891769118d2ee5113b8ed39a17635360ccc4c2a07d`.
- REA and local trace: 6904 steps including HALT. Clasesbolge: 6903 steps (excludes HALT).
- CALL at PC 20048 → 20069; RET at PC 20606 → 20050.

## Reproduce

From the repository root with the existing Classic dependencies and REA available (use a fresh directory):

```sh
out=$(mktemp -d)
python3 -B python/evidence/classic_hola_tontos_v1/reproduce.py "$out/run"
node python/evidence/classic_compiler_v0/rea.mjs /home/danny/Development/rea/dist "$out/run"
```

The reproducer uses the previously committed differential harness with a one-fixture corpus. The input, output, map, trace, results and SHA-256 are preserved in each run. See `environment.txt` for the dependencies used. No claim of general Python support or self-hosting.
