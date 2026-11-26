# BOLGE-CRYPT v0 — sistema de cifrado cuyo backend corre en Malbolge Classic

> Milestone `malbolge-mb-db/bolge-crypt-v0`. Trabajo en `crypto/`, rama
> `feat/bolge-crypt-v0`. MBIR v0 sigue congelado: codec/dispatcher/backends
> son consumidores, nunca al revés.

## 1. Objetivo y forma

Un sistema de cifrado donde **las operaciones criptográficas ocurren dentro de
la máquina Malbolge Classic**, ejecutadas por intérpretes independientes:

- El **frontend Python** solo orquesta: empaqueta entradas, invoca al runner,
  verifica round-trip. **No cifra ni descifra** (gate G06).
- El **backend** son imágenes `.mb` Malbolge Classic puras, generadas por
  compiladores de este repo (ruta HeLL/LMAO + circuito + instalador).
- Cifrador y descifrador son **privados** (decisión del operador: seguridad
  por obscuridad + clave; queda documentado como tal, no como criptografía
  auditada). La clave viaja separada del .mb (nunca incrustada en el
  programa): el generador la consume, el .mb resultante es el artefacto.

## 2. Estado auditado (hechos medidos, no recuerdos)

| Pieza | Estado | Evidencia |
|---|---|---|
| Runner rápido | Zigbolge con stdin arreglado hoy: **~667M pasos/s** (100M pasos en 0.15 s), paridad bit-exact vs Engine: hello 4475 pasos, lifo 59752 pasos + salida `41` | PR DannyBaanks/Zigbolge#1 |
| Runner de referencia | Olmstead/Engine, ~31,3k pasos/s | `runners/malbolge-original` |
| Intérpretes cruzados | 15 runners registrados (`runners/*/manifest.json`) para G03 | repo |
| **Incremento de byte mod 256 con carry paralelo** | **YA DEMOSTRADO**: `increment_circuit_loop_v1` (517 casos, paridad oráculo Python/BF16/Olmstead, 10.000 bytes en una ejecución, HALT autónomo en EOF Olmstead). Imagen `run02/increment.mb`, reverificada hoy también con Zigbolge: `ABCD`→`BCDE` HALTED | `vm_malbolge/evidence/increment_circuit_loop_v1/` |
| Suma de dos operandos (a+b) | **NO demostrada**: kernels P0(ADD)/P1(SUB) y ALU operan sobre dominio chico; medido hoy: 1/10 pares de bytes correctos, hasta 4+4 falla | `vm_malbolge/P0_STATUS.md`, medición propia |
| Primitivas de circuito | `circuit.py`: `bool_and/or`, `add_bit(x,y)` (medio sumador), carry paralelo CRAZY+ROT | `vm_malbolge/tools/increment_bf/circuit.py` |
| Coste del incremento | ~78-80k pasos / 4 bytes (init + stream) | medición propia hoy |

## 3. Diseño del cifrador v0

Esquema simétrico autoinverso sobre bytes:

```
cifrado:   out_i = (data_i + ks_i) mod 256
descifrado: data_i = (out_i - ks_i) mod 256
```

- `ks` = keystream derivado de (clave, nonce). En v0 el keystream vive en la
  sección DATA por posición: el generador (privado, con la clave) especializa
  una imagen .mb concreta. Extensión siguiente: ks derivado en runtime.
- El cifrado de bytes se transporta en un **contenedor** estilo `.b2t`
  (magic, versión, nonce, longitud, CRC-32) cuya carga útil va codificada en
  ASCII 33..126 — por eso el artefacto distribuido es además un programa
  **sintácticamente válido** (gate G05) sin que el transporte toque la
  criptografía (G06 sigue intacto).
- HALT en EOF Olmstead (a=59048), como la máquina de incremento ya hace.

## 4. Plan de construcción (milestones verificables)

- **M1 — sumador de dos bytes** (`crypto/gen_adder.py` + host oracle):
  extender `increment(x)` a `add(x, y)` con carry chain sobre el ancho del
  byte; verificación exhaustiva 256×256 = 65.536 pares en host. Salida:
  `crypto/evidence/adder_host.json`.
- **M2 — emisión de imagen**: circuito → HeLL → LMAO → layout → instalador →
  check del loader estricto. Paridad Olmstead vs Zigbolge vs oráculo;
  `steps` por byte medidos. `crypto/evidence/adder_image.json`.
- **M3 — máquina cifradora** stream+ks(DATA)+HALT-EOF: round-trip contra
  oráculo Python, pasos/byte, tamaño de imagen (< 59.049 palabras).
- **M4 — máquina restadora** (descifrador, privada): misma estructura con SUB.
- **M5 — contenedor + CLI + probe de evidencia** con los gates G01..G08 de
  GPT explícitos (G01/G02 cifrado/descifrado en Classic; G03 intérpretes
  independientes; G04 vectores de referencia; G05 artefacto ASCII válido;
  G06 Python no cifra; G07 pasos/byte reproducibles; G08 seguridad = clave,
  aquí por obscuridad documentada) + job CI.

## 5. Límites honestos (por escrito, no por omisión)

- Seguridad por obscuridad + clave: no sustituye criptografía auditada; un
  reversing del .mb revela el keystream. Elegido por el operador con ese
  conocimiento.
- Rendimiento estimado v0: ~20k pasos/byte → ~30 KB/s con Zigbolge. Mensajes
  pequeños (credenciales, tokens, instrucciones), no streaming masivo.
- Tope duro de Classic: imagen < 59.049 palabras; el ks incrustado acota el
  número de posiciones cifrables por .mb (streams largos ⇒ ks derivado en
  runtime, milestone posterior).
- Los `steps` entre Olmstead y Zigbolge pueden diferir en una constante de
  arranque (medido hoy: 80.745 vs 77.999 en la misma imagen de incremento);
  la paridad funcional byte a byte es la que se exige.