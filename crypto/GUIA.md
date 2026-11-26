# GUIA — BOLGE-CRYPT v0

## Requisitos

Un runner Malbolge que acepte `malbolge <imagen.mb> <presupuesto>` con el
programa por stdin. Se resuelve en este orden:

1. `--runner RUTA`
2. `A04_MALBOLGE_RUNNER` / `BOLGE_RUNNER`
3. `/tmp/opencode/zigbolge/zig-out/bin/zigbolge` (si existe)
4. `runners/malbolge-original/malbolge` del repo

La maquina (imagen) vive en el repo:
`vm_malbolge/evidence/increment_circuit_loop_v1/run02/increment.mb`.

## Uso

```bash
cd crypto

# cifrar (el nonce se genera aleatorio si no se pasa)
python3 bolgecrypt.py --runner /ruta/al/runner cipher \
    --key 000102030405060708090a0b0c0d0e0f \
    --in secreto.txt --out secreto.txt.bc1

# descifrar
python3 bolgecrypt.py --runner /ruta/al/runner decipher \
    --key 000102030405060708090a0b0c0d0e0f \
    --in secreto.txt.bc1 --out secreto.restored
```

La salida de `cipher` imprime el nonce en hex (guardalo junto al contenedor;
tambien esta dentro). `decipher` verifica longitud y CRC-32: con clave
incorrecta falla con "CRC no cuadra".

## Evidencia

```bash
python3 probe_bolgecrypt.py     # escribe evidence/bolgecrypt_v0.json
```

Comprueba: vectores de referencia contra la formula pura, round-trip con
contenedor, los 256 bytes con +1, paridad entre runners si hay dos,
payload ASCII 33..126, pasos/byte medidos y rechazo de clave incorrecta.
El probe se niega a escribir si algo falla.

## Advertencias honestas

- Keystream experimental (splitmix64): no es criptografia auditada.
- Velocidad: ~0,2 s/byte con Zigbolge; ~30 s/byte con Olmstead. Para
  mensajes pequenos. No uses esto para streaming masivo.
- M6 (maquina propia con LOOP y keystream crazy-chain) está diseñada en
  SPEC.md; falta resolver el presupuesto del instalador (numeros medidos
  incluidos ahi).
