# BOLGE-CRYPT — cifrado con backend en Malbolge Classic

Sistema de cifrado donde **las operaciones criptográficas ocurren dentro de
una maquina Malbolge Classic real**. Python (frontend) solo deriva el
keystream desde la clave, alimenta la maquina byte a byte, recoge la salida
y empaqueta el contenedor. Los gates G01..G08 estan mapeados uno a uno en
`evidence/bolgecrypt_v0.json`.

- Maquina: `vm_malbolge/evidence/increment_circuit_loop_v1/run02/increment.mb`
  (incremento mod 256 con acarreo paralelo, HALT autonomo en EOF).
- Sumar k a un byte = aplicar la maquina k veces; restar k = (256-k) veces.
- Contenedor `BLC1`: magic + version + nonce(8) + data_len + crc32(claro) +
  payload base-94 ASCII 33..126 (el criptograma es ademas sintacticamente un
  programa Malbolge valido).
- Keystream: splitmix64 sobre SHA-256(clave||nonce). Experimental, no auditado.
- Seguridad = solo la clave+nonce (maquina y algoritmo son publicos).

Guia de operacion: `GUIA.md`. Diseno y limites: `SPEC.md`.

## Rendimiento (medido, v0.5 por lotes)

| Runner | Pasos/s | 64 B | 1 KB | 4 KB |
|---|---|---|---|---|
| Zigbolge (Zig, stdin arreglado) | ~667M | 0,5 s | 2,8 s | 9,7 s |
| Olmstead original (C) | ~31k | ~10 s | ~1 min | ~3,5 min (extrapolado) |

v0.5: en la pasada p viajan juntos todos los bytes con k_i >= p — 255 pasadas
por mensaje, no sum(k). La maquina gasta ~59k pasos de init + ~5,5k por byte.
