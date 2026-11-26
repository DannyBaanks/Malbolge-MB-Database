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

## 6. Arquitectura v0 DESPLEGADA (con evidencia)

El plan original (imagen especializada por mensaje, keystream en .DATA por
posicion, netlist completo de suma/resta) quedo **bloqueado por un muro medido**:

| Ruta | Resultado medido |
|---|---|
| Emision straight-line N=1 (machine_hell.py, netlist verificado) | 5.397 celdas de layout (140 ops) |
| Instalador BolgeForge (seed 14 y barrido 0..2024) | ~287k ops vs presupuesto ~51,5k (53 ops/celda, plano en semillas) |
| Capacidad implícita del instalador | ~1.050 celdas de programa |
| LMAO nativo sobre el mismo .hell | "Memory usage conflict while generating initialization code" |

Con ese presupuesto no cabe un sumador completo (~53 gates minimos, closure
completo demostrado: 19.683/19.683 tablas alcanzables por crazy; gadgets
minimales D=9, G=6, P=11, DS=13, B=6, Q=12; ripple Kogge-Stone de 3 pasos
verificado exhaustivo 65.536 casos add + sub256, 0 fallos).

**v0 desplegado (todo medido, evidencia en evidence/bolgecrypt_v0.json):**
la operacion criptograica de cada byte la ejecuta la maquina Classic
**verificada** `vm_malbolge/evidence/increment_circuit_loop_v1/run02/
increment.mb` (incremento mod 256 con acarreo paralelo; 517 casos de paridad
en su evidencia; reverificada hoy tambien contra Zigbolge). Sumar k a un
byte = aplicar la maquina k veces; restar k = aplicarla (256-k) veces. La
suma modular la hace Malbolge en cada paso (G01/G02/G06); Python solo
deriva el keystream (splitmix64 sobre SHA-256(clave||nonce), experimental
y documentado) y orquesta. Contenedor BLC1 con nonce por mensaje, CRC-32
del claro y payload base-94 ASCII 33..126 (G05, sintacticamente valido).

Coste medido: ~9,3M pasos por byte de mensaje (~144 pasadas de maquina por
byte, ~64,5k pasos por pasada incluyendo init); ~0,2 s/byte con Zigbolge
(667M pasos/s), ~30 s/byte con el Olmstead original (~31k pasos/s).
Mensajes pequenos (credenciales, tokens): un bloque de 64 B tarda ~13 s.

## 6b. v0.5 — orquestacion por lotes (desplegado, medido)

El cuello de v0 no era la VM: era el spawn de proceso por pasada. La maquina
incrementa TODO un stream por pasada, asi que en la pasada p viajan juntos
todos los bytes con k_i >= p: coste max(k) procesos en vez de sum(k).
La aritmetica sigue siendo 100% Malbolge (cada +1 lo hace la maquina).

Medido (Zigbolge, ~667M pasos/s):

| Pasos de la maquina | valor |
|---|---|
| init por ejecucion | ~59k pasos |
| por byte de stream | ~5,5k pasos |
| pasadas por mensaje | max(k) ~ 255 (independiente de N) |

| Mensaje | wall | ms/byte |
|---|---|---|
| 64 B | 0,5 s | 8,6 |
| 256 B | 1,0 s | 4,0 |
| 1024 B | 2,8 s | 2,7 |
| 4096 B | 9,7 s | 2,4 (asintota: spawn + VM) |

Correcto y round-trip verificado en todos los tamanos; presupuesto del runner
escalado a 150k + 7k·N pasos (la maquina TIMEOUTea con presupuesto fijo).

## 7. M6 — siguiente hito (maquina propia, LOOP con keystream crazy-chain)

Con el emisor listo y el netlist verificado (adder_netlist/adder_full/
gadget_min + el emisor machine_hell/machine_compile), lo que falta para la
maquina especializada es resolver el presupuesto del instalador:
  (a) maquina de encapsulation LOOP con estado (keystream crazy-chain en una
      celda, avance = 1 crazy/byte) en vez de especializacion por mensaje;
  (b) despacho EOF con bloques propios (sin las @ fijas) para recuperar
      ~19k ops de presupuesto;
  (c) o acceptance de imagenes multi-imagen por contenedor.
Estimacion: ~39-45 gates de encapsulación (circuitos +1/-1 duales + test de
contador) => ~1.000-1.300 celdas, en el filo del presupuesto medido.
