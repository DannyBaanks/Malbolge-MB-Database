#!/usr/bin/env python3
"""crypto/bolgecrypt.py — BOLGE-CRYPT v0: cifrado cuyo backend corre en Malbolge.

ARQUITECTURA (ver crypto/SPEC.md para el diseno completo y los limites):

  - La operacion criptografica de cada byte -- la suma modular (x + k) mod 256
    y su inversa -- la ejecuta una MAQUINA MALBOLGE CLASSIC real: la imagen
    verificada de vm_malbolge/evidence/increment_circuit_loop_v1/
    run02/increment.mb (incremento de byte mod 256 con acarreo paralelo,
    HALT autonomo en EOF; 517 casos de paridad oraculo/BF16/Olmstead en su
    evidencia). Sumar k a un byte = aplicar esa maquina k veces; restar k =
    aplicarla (256 - k) veces (la maquina envuelve mod 256).
  - Python NO cifra: solo deriva el keystream desde la clave (key schedule,
    que es material secreto por diseno), alimenta la maquina byte a byte,
    recoge la salida y empaqueta el contenedor. gate G06.
  - La seguridad depende solo de la clave+nonce: la maquina y el algoritmo
    son publicos (Kerckhoffs). gate G08. keystream experimental, no auditado.
  - El criptograma se transporta en ASCII 33..126 (base-94, 2 chars/byte):
    el payload del contenedor es ademas sintacticamente un programa Malbolge
    valido. gate G05.

Contenedor BLC1:
    magic 'BLC1'(4) | version(1)=1 | nonce(8) | data_len(4 BE) |
    crc32_plain(4 BE) | payload_len(2 BE) | payload (base-94 ASCII 33..126)

v0.5 (orquestacion por lotes): la maquina incrementa todo el stream en una
pasada; en la pasada p viajan juntos todos los bytes con k_i >= p, asi que
un mensaje cuesta max(k) ~ 255 pasadas (no sum(k)). Medido: ~2,4 ms/byte
asintotico con Zigbolge.

CLI:
    bolgecrypt.py cipher   --key HEX --in F --out F.bc1
    bolgecrypt.py decipher --key HEX --in F.bc1 --out F
    bolgecrypt.py probe    --evidence crypto/evidence/bolgecrypt_v0.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import zlib

MAGIC_V1 = b"BLC1"     # span implicito 256
MAGIC_V2 = b"BLC2"     # lleva el span del keystream (1 byte)
MAGIC = MAGIC_V2
VERSION = 2
NONCE_LEN = 8
BASE = 94
ASCII_LO = 33

# maquina Classic verificada (incremento mod 256 con carry paralelo)
DEFAULT_IMAGE = (
    pathlib.Path(__file__).resolve().parents[0]
    / "vm_malbolge/evidence/increment_circuit_loop_v1/run02/increment.mb"
)


# ---------------- keystream (experimental, documentado) ----------------
def keystream_byte(key: bytes, nonce: bytes, index: int, span: int = 256) -> int:
    """SplitMix64 encadenado sobre semilla = SHA-256(key||nonce).

    Experimental: no es un PRNG auditado; la seguridad del sistema descansa
    en el secreto de la clave, no en la oscuridad de este esquema.
    """
    if index == 0:
        keystream_byte._h = None  # noqa: SLF001
    seed = int.from_bytes(hashlib.sha256(key + nonce).digest()[:8], "big")
    state = (seed + index * 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = state
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    z = z ^ (z >> 31)
    return (z & 0xFF) % span


def keystream(key: bytes, nonce: bytes, n: int, span: int = 256) -> list[int]:
    return [keystream_byte(key, nonce, i, span) for i in range(n)]


# ---------------- runner Malbolge ----------------
class Runner:
    def __init__(self, path: str):
        self.path = path

    def run(self, image: pathlib.Path, stdin_bytes: bytes, budget: int | None = None):
        # la maquina de incremento gasta ~60k de init + ~1,9k pasos/byte
        if budget is None:
            budget = 150_000 + 7_000 * len(stdin_bytes)
        t0 = time.perf_counter()
        p = subprocess.run(
            [self.path, str(image), str(budget)],
            input=stdin_bytes,
            capture_output=True,
            timeout=600,
        )
        wall = time.perf_counter() - t0
        err = p.stderr.decode(errors="replace")
        steps = -1
        status = ""
        for tok in err.replace("{", " ").replace("}", " ").replace(",", " ").split():
            if tok.startswith('"steps":'):
                pass
        import re

        m = re.search(r'"steps":\s*(\d+)', err) or re.search(r"steps:\s*(\d+)", err)
        if m:
            steps = int(m.group(1))
        m2 = re.search(r'"status":\s*"([A-Z_]+)"', err) or re.search(r"status:\s*([A-Z_]+)", err)
        if m2:
            status = m2.group(1)
        out = p.stdout
        if out.endswith(b"\n"):
            out = out[:-1]  # el runner emite bytes + un \n final
        return out, steps, status, wall


def resolve_runner(explicit: str | None = None) -> Runner:
    cands = []
    if explicit:
        cands.append(explicit)
    env = os.environ.get("A04_MALBOLGE_RUNNER")
    if env:
        cands.append(env)
    env2 = os.environ.get("BOLGE_RUNNER")
    if env2:
        cands.append(env2)
    root = pathlib.Path(__file__).resolve().parents[0]
    cands += [
        "/tmp/opencode/zigbolge/zig-out/bin/zigbolge",
        str(root / "runners/malbolge-original/malbolge"),
    ]
    for c in cands:
        if c and os.access(c, os.X_OK):
            return Runner(c)
    raise SystemExit("no hay runner Malbolge disponible (A04_MALBOLGE_RUNNER/BOLGE_RUNNER)")


# ---------------- transporte base-94 (G05: ASCII 33..126) ----------------
def b94_encode(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        out.append(ASCII_LO + b // BASE)
        out.append(ASCII_LO + b % BASE)
    return bytes(out)


def b94_decode(payload: bytes) -> bytes:
    if len(payload) % 2:
        raise ValueError("payload base-94 de longitud impar")
    out = bytearray()
    for i in range(0, len(payload), 2):
        hi = payload[i] - ASCII_LO
        lo = payload[i + 1] - ASCII_LO
        if not (0 <= hi < BASE and 0 <= lo < BASE):
            raise ValueError("byte fuera de ASCII 33..126")
        out.append(hi * BASE + lo)
    return bytes(out)


# ---------------- cifrado/descifrado: la suma la hace Malbolge ----------------
def apply_plus1(runner: Runner, image: pathlib.Path, byte: int, passes: int, stats: dict):
    """Aplica la maquina +1 `passes` veces a un byte (mod 256)."""
    b = byte
    for _ in range(passes):
        out, steps, status, wall = runner.run(image, bytes([b]))
        if len(out) != 1 or status not in ("HALTED", ""):
            raise RuntimeError(f"maquina devolvio {out!r} status={status}")
        b = out[0]
        stats["passes"] += 1
        stats["steps"] += max(steps, 0)
        stats["wall"] += wall
    return b


def _stream_batched(runner, image, data: bytes, ks: list[int], stats: dict) -> bytes:
    """v0.5: suma modular por LOTES. La maquina incrementa todo el stream en
    una pasada; en la pasada p viajan juntos todos los bytes con k_i >= p.
    Coste: max(k) procesos (no sum(k)). La aritmetica sigue siendo 100%
    Malbolge: cada +1 de cada byte lo hace la maquina."""
    vals = list(data)
    rem = list(ks)
    for _p in range(1, max(rem) + 1 if rem else 0):
        idx = [i for i, r in enumerate(rem) if r > 0]
        if not idx:
            break
        out, steps, status, wall = runner.run(image, bytes(vals[i] for i in idx))
        if len(out) != len(idx) or (status not in ("HALTED", "")):
            raise RuntimeError(f"maquina devolvio {len(out)} bytes para {len(idx)} (status={status})")
        for j, i in enumerate(idx):
            vals[i] = out[j]
            rem[i] -= 1
        stats["passes"] += 1
        stats["steps"] += max(steps, 0)
        stats["wall"] += wall
    return bytes(vals)


def cipher(runner, image, data: bytes, key: bytes, nonce: bytes, stats=None, span: int = 256):
    stats = stats or {"passes": 0, "steps": 0, "wall": 0.0}
    ks = keystream(key, nonce, len(data), span)
    return _stream_batched(runner, image, data, ks, stats), stats


def decipher(runner, image, cipher_bytes: bytes, key: bytes, nonce: bytes, stats=None, span: int = 256):
    stats = stats or {"passes": 0, "steps": 0, "wall": 0.0}
    ks = keystream(key, nonce, len(cipher_bytes), span)
    comp = [(256 - k) % 256 for k in ks]
    return _stream_batched(runner, image, cipher_bytes, comp, stats), stats


# ---------------- contenedor ----------------
def pack(runner, image, key: bytes, nonce: bytes, data: bytes, span: int = 256) -> bytes:
    cipher_bytes, _ = cipher(runner, image, data, key, nonce, span=span)
    payload = b94_encode(cipher_bytes)
    hdr = bytearray()
    hdr += MAGIC_V2
    hdr.append(VERSION)
    hdr += nonce
    hdr.append(span - 1)          # 1..256 -> 0..255
    hdr += len(data).to_bytes(4, "big")
    hdr += (zlib.crc32(data) & 0xFFFFFFFF).to_bytes(4, "big")
    hdr += len(payload).to_bytes(2, "big")
    return bytes(hdr) + payload


def unpack(runner, image, container: bytes, key: bytes):
    if container[:4] not in (MAGIC_V1, MAGIC_V2):
        raise ValueError("magic invalido")
    if container[4] != VERSION and container[:4] != MAGIC_V1:
        raise ValueError("version invalida")
    nonce = container[5:13]
    if container[:4] == MAGIC_V2:
        span = container[13] + 1
        rest = container[14:]
    else:
        span = 256
        rest = container[13:]
    data_len = int.from_bytes(rest[0:4], "big")
    crc = int.from_bytes(rest[4:8], "big")
    payload_len = int.from_bytes(rest[8:10], "big")
    payload = rest[10:10 + payload_len]
    if len(payload) != payload_len:
        raise ValueError("payload truncado")
    cipher_bytes = b94_decode(payload)
    data, _ = decipher(runner, image, cipher_bytes, key, nonce, span=span)
    if len(data) != data_len:
        raise ValueError("longitud no cuadra")
    if (zlib.crc32(data) & 0xFFFFFFFF) != crc:
        raise ValueError("CRC no cuadra: clave incorrecta o dato corrupto")
    return data, nonce


# ---------------- CLI ----------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="BOLGE-CRYPT v0 (backend Malbolge Classic)")
    ap.add_argument("--runner", help="ruta del runner (o A04_MALBOLGE_RUNNER/BOLGE_RUNNER)")
    ap.add_argument("--image", help="imagen .mb de la maquina +1 (default: la verificada del repo)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("cipher", "decipher"):
        p = sub.add_parser(name)
        p.add_argument("--key", required=True, help="clave en hex")
        p.add_argument("--nonce", help="nonce en hex (cipher: si se omite, aleatorio)")
        p.add_argument("--in", dest="inp", required=True)
        p.add_argument("--out", dest="out", required=True)
    args = ap.parse_args(argv)

    runner = resolve_runner(args.runner)
    image = pathlib.Path(args.image) if args.image else DEFAULT_IMAGE

    if args.cmd == "cipher":
        key = bytes.fromhex(args.key)
        nonce = bytes.fromhex(args.nonce) if args.nonce else os.urandom(NONCE_LEN)
        data = pathlib.Path(args.inp).read_bytes()
        container = pack(runner, image, key, nonce, data, span=args.span)
        pathlib.Path(args.out).write_bytes(container)
        print(f"cifrado: {len(data)} bytes -> contenedor {len(container)} bytes (nonce {nonce.hex()})")
    else:
        key = bytes.fromhex(args.key)
        container = pathlib.Path(args.inp).read_bytes()
        data, nonce = unpack(runner, image, container, key)
        pathlib.Path(args.out).write_bytes(data)
        print(f"descifrado: {len(data)} bytes (nonce {nonce.hex()})")


if __name__ == "__main__":
    main()