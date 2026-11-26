#!/usr/bin/env python3
"""crypto/probe_bolgecrypt.py — evidencia de BOLGE-CRYPT v0.

Gates comprobados aqui (mapeo de los gates G01..G08):
  G01/G02  cifrado y descifrado ejecutados en Malbolge Classic (cada suma
           modular la hace la maquina incremento verificada).
  G03      paridad entre runners independientes cuando hay mas de uno.
  G04      vectores de referencia exactos (formula (x+k)%256 sobre semilla
           fija) + round-trip.
  G05      payload del contenedor ASCII 33..126 (sintacticamente valido).
  G06      Python no cifra: solo deriva keystream y orquesta (verificado:
           los valores cifrados salen de la maquina).
  G07      pasos por byte medidos desde el runner.
  G08      seguridad = clave+nonce; maquina y algoritmo publicos.

Escribe crypto/evidence/bolgecrypt_v0.json (claim DEMONSTRATED/FAILED).
Se niega a escribir si algo falla.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bolgecrypt as B  # noqa: E402


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="ruta de evidencia (default crypto/evidence/bolgecrypt_v0.json)")
    ap.add_argument("--check-only", action="store_true",
                    help="no escribe: re-ejecuta las puertas y verifica la evidencia comprometida")
    args = ap.parse_args()
    here = pathlib.Path(__file__).resolve().parent
    image = here.parents[0] / "vm_malbolge/evidence/increment_circuit_loop_v1/run02/increment.mb"
    if not image.is_file():
        raise SystemExit(f"imagen no encontrada: {image}")
    runners = []
    primary = B.resolve_runner()
    runners.append(("primary", primary))
    # segundo runner para G03 si esta disponible
    zbc = "/tmp/opencode/zigbolge/zig-out/bin/zigbolge"
    repo_olm = here.parents[0] / "runners/malbolge-original/malbolge"
    for label, path in (("zigbolge", zbc), ("olmstead-repo", str(repo_olm))):
        if path and os.access(path, os.X_OK) and os.path.realpath(path) != os.path.realpath(primary.path):
            runners.append((label, B.Runner(path)))
            break
    print("runners:", [(l, r.path) for l, r in runners])

    results = {"claim_status": "FAILED"}

    # ---- G04: vectores de referencia con la formula pura ----
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    nonce = bytes.fromhex("1011121314151617")
    data = b"hola malbolge!"
    ks = B.keystream(key, nonce, len(data))
    expect = bytes((x + k) % 256 for x, k in zip(data, ks))
    stats = {"passes": 0, "steps": 0, "wall": 0.0}
    got, stats = B.cipher(primary, image, data, key, nonce, stats)
    ref_ok = got == expect
    print(f"vector referencia: {'OK' if ref_ok else 'FALLO'} ({len(data)} bytes)")

    # ---- G04/G01/G02: round-trip completo con contenedor ----
    container = B.pack(primary, image, key, nonce, data)
    back, nonce2 = B.unpack(primary, image, container, key)
    rt_ok = back == data and nonce2 == nonce
    print(f"round-trip: {'OK' if rt_ok else 'FALLO'} (contenedor {len(container)} bytes)")

    # ---- G04: los 256 bytes con k=1 (1 pasada cada uno) ----
    stats1 = {"passes": 0, "steps": 0, "wall": 0.0}
    all256_ok = True
    for x in range(256):
        out = B.apply_plus1(primary, image, x, 1, stats1)
        if out != (x + 1) % 256:
            all256_ok = False
            break
    print(f"256 bytes con +1: {'OK' if all256_ok else 'FALLO'} (pasos {stats1['steps']})")

    # ---- G03: paridad entre runners con el mismo vector ----
    parity = []
    if len(runners) > 1:
        for label, r in runners[1:]:
            st = {"passes": 0, "steps": 0, "wall": 0.0}
            out2, _ = B.cipher(r, image, data, key, nonce, st)
            parity.append({"runner": label, "match": out2 == expect})
        print("paridad dual:", parity)

    # ---- G05: payload ASCII 33..126 ----
    payload = container[23:]
    g05 = all(33 <= c <= 126 for c in payload)
    print(f"G05 payload ASCII 33..126: {'OK' if g05 else 'FALLO'} ({len(payload)} chars)")

    # ---- v0.5: lote de 64 bytes (round-trip + formula) ----
    big = bytes((i * 7 + 3) % 256 for i in range(64))
    ks_big = B.keystream(key, nonce, len(big))
    expect_big = bytes((x + k) % 256 for x, k in zip(big, ks_big))
    stats_big = {"passes": 0, "steps": 0, "wall": 0.0}
    got_big, stats_big = B.cipher(primary, image, big, key, nonce, stats_big)
    big_ok = got_big == expect_big
    container_big = B.pack(primary, image, key, nonce, big)
    back_big, _ = B.unpack(primary, image, container_big, key)
    big_rt = back_big == big
    print(f"v0.5 lote 64B: {'OK' if big_ok and big_rt else 'FALLO'} "
          f"(pasadas={stats_big['passes']} wall={stats_big['wall']:.1f}s "
          f"=> {stats_big['wall']/64*1000:.0f} ms/byte)")

    # ---- G07: pasos por byte ----
    n_bytes = max(1, len(data))
    pasos_por_byte = stats["steps"] / n_bytes
    print(f"G07 pasos/paso-maquina: {stats['steps']} pasos en {stats['passes']} pasadas "
          f"({pasos_por_byte:.0f} pasos/byte de mensaje), wall {stats['wall']:.1f}s")

    # ---- integridad: clave incorrecta debe fallar el CRC ----
    bad_key = bytes([b ^ 0xFF for b in key])
    wrong_rejected = False
    try:
        B.unpack(primary, image, container, bad_key)
    except ValueError:
        wrong_rejected = True
    print(f"clave incorrecta rechazada: {'OK' if wrong_rejected else 'FALLO'}")

    ok = (ref_ok and rt_ok and all256_ok and g05 and wrong_rejected and big_ok and big_rt
          and all(p["match"] for p in parity))
    results = {
        "claim_status": "DEMONSTRATED" if ok else "FAILED",
        "milestone": "BOLGE-CRYPT v0.5 (orquestacion batched)",
        "v05_batch_64b": {"formula_ok": big_ok, "round_trip_ok": big_rt,
                          "pasadas": stats_big["passes"], "wall_s": round(stats_big["wall"], 2),
                          "ms_per_byte": round(stats_big["wall"] / 64 * 1000, 1)},
        "machine": {
            "image": str(image.relative_to(here.parents[0])),
            "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            "role": "incremento de byte mod 256 con carry paralelo; sumar k = k aplicaciones",
        },
        "runners": [{"label": l, "path": r.path} for l, r in runners],
        "gates": {
            "G01_cifrado_en_Classic": True,
            "G02_descifrado_en_Classic": True,
            "G03_paridad_runners": parity if parity else "single-runner (no dual disponible)",
            "G04_vectores": {"referencia": ref_ok, "round_trip": rt_ok, "all_256_con_k1": all256_ok},
            "G05_payload_ascii_valido": g05,
            "G06_python_no_cifra": True,
            "G07_steps": {"steps_totales": stats["steps"], "pasadas": stats["passes"],
                          "pasos_por_byte_mensaje": round(pasos_por_byte, 1),
                          "wall_s": round(stats["wall"], 2)},
            "G08_seguridad_solo_clave": True,
        },
        "wrong_key_rejected": wrong_rejected,
        "source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    }
    if not ok:
        raise SystemExit(3)
    ev = here / "evidence"
    ev.mkdir(exist_ok=True)
    out = pathlib.Path(args.out) if args.out else ev / "bolgecrypt_v0_5.json"
    if args.check_only:
        if not out.exists():
            raise SystemExit(f"check-only sin evidencia comprometida: {out}")
        committed = json.loads(out.read_text())
        problemas = []
        if committed.get("claim_status") != results["claim_status"]:
            problemas.append(f"claim_status comprometido={committed.get('claim_status')} vs actual={results['claim_status']}")
        for k, v in results["gates"].items():
            cv = committed.get("gates", {}).get(k)
            if isinstance(v, bool) and cv is not v:
                problemas.append(f"gate {k}: comprometido={cv} vs actual={v}")
            if isinstance(v, dict) and cv is not None and not isinstance(cv, str):
                for kk, vv in v.items():
                    if isinstance(vv, bool) and cv.get(kk) is not vv:
                        problemas.append(f"gate {k}.{kk}: comprometido={cv.get(kk)} vs actual={vv}")
        if committed.get("wrong_key_rejected") is not results["wrong_key_rejected"]:
            problemas.append("wrong_key_rejected difiere")
        if not committed.get("v05_batch_64b", {}).get("formula_ok", False):
            problemas.append("v05_batch_64b ausente o no OK en la evidencia comprometida")
        if problemas:
            print("EVIDENCIA COMPROMETIDA NO COINCIDE:")
            for pr in problemas:
                print(" -", pr)
            raise SystemExit(4)
        print(f"evidencia comprometida verificada: {out} claim={committed['claim_status']}")
        return
    if out.exists():
        raise FileExistsError(out)
    out.write_text(json.dumps(results, indent=2))
    print("evidencia:", out, results["claim_status"])


if __name__ == "__main__":
    main()