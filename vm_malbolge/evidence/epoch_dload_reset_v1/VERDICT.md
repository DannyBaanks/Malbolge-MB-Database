# epoch_dload_reset_v1 — veredicto

Responde a las puertas de `GATES.md` (commit `89ef37a`, pre-registrado antes de este
archivo y de `probe.py`). Repo MALBOLGE-MB-DATABASE, local sin push. Autor:
claude_code_87747efe962f42f4, 2026-11-11, pedido de Danny. Base `61a0278`.

## Resultado

**G0..G4 true.** Un bloque de `DLOAD` que reinicia `d` en cada vuelta convierte el
bucle finito de `epoch_xlat2_block_v1` en uno con **tabla de destinos de tamaño
constante**. La imagen `dload_reset.mb` mide **111 celdas para cualquier R** (block_v1
necesitaba 525 celdas para R = 60, y la tabla crecía con R), cierra las **10 000
vueltas** medidas, y su estado completo se **repite con periodo 1020**: en este dialecto
y con esta semántica, el bucle se repite para siempre.

Dialecto: **Classic permisivo (3^10)**. El cargador de Olmstead 1998 la rechaza (Q5).

## Q1 — construcción

Parámetros (código de `epoch_xlat2_block_v1/probe.py`, importado): cuerpo `[60, 65]`
(`n = 6`), celdas X en 60 y 64 (`g = 4`, valor 74), relleno `[41, 41, 37]`, `JMP` en 65,
trampolín `T = 59`. Medidos con el trazador: `D_0 = 100` (d al ejecutar la celda 60 por
primera vez), `o_0 = 0`, `o_1 = 4`.

Celdas de dato calculadas con las ecuaciones del punto fijo de `GATES.md`:

| celda | valor | papel |
|---|---|---|
| 100 | 100 | lo lee el `DLOAD` de las vueltas pares (offset 0): `d` vuelve a 100 |
| 105 | 59 | lo lee el `JMP` de las vueltas pares |
| 110 | 98 | lo lee el `DLOAD` de las vueltas impares (offset 4) |
| 99 | 59 | lo lee el `JMP` de las vueltas impares |

**Coinciden exactamente con la predicción en papel** escrita en `GATES.md` antes de
medir. Las cuatro ecuaciones, leídas de los bytes de la imagen, se cumplen
(`q1.fixed_point`). El resto de celdas que nunca se ejecutan llevan un valor de fondo
distinto de `T`, para que ningún `JMP` caiga en el trampolín por casualidad.

Salvedad: la construcción **no tiene parámetro R**, así que la parte de G0 "misma
imagen para R = 60 y R = 10 000" se cumple por construcción. La parte con contenido de
"tabla constante" es Q2: la misma imagen de 111 celdas corre las 10 000 vueltas.

## Q2 — 10 000 vueltas

| medición | valor |
|---|---|
| vueltas cerradas / pasos | 10 000 / 60 060 |
| `DLOAD` por vuelta | siempre 1 |
| opcodes válidos en el cuerpo | `{4, 40}` |
| destinos de `JMP` | `{59}` (las 10 000) |
| `d` al empezar la vuelta | `{100, 106}`, alternando |

Motores, en la misma ejecución acotada: trazador, motor scratch e intérprete
independiente dan el **mismo sha256 de la memoria final** (59 049 celdas); trazador y
scratch coinciden en la lista completa de destinos de `JMP` y en `d` al empezar cada
vuelta; oráculo y runner C llegan al tope sin parar y con salida vacía (no exponen
memoria).

## Q3 — periodicidad del estado

Se cifran cada vuelta las celdas 60..64 y el trampolín 59. Sus ciclos XLAT2 miden
2, 5, 5, 6, 2 y 68. **Predicho:** `P = mcm(2, 5, 6, 68) = 1020`. **Medido:** el hash de
`(mem[0..59048], a, c, d)` al empezar la vuelta se repite por primera vez entre las
vueltas **0 y 1020** → `P = 1020`, y `d` tiene periodo 2. La máquina es determinista,
así que un estado repetido significa que el bucle se repite indefinidamente.

El ciclo largo lo pone el trampolín (68): se cifra en cada `JMP` pero no se vuelve a
ejecutar, así que no altera el bucle; sólo alarga el periodo del estado.

## Q4 — controles

| control | resultado |
|---|---|
| `ctrl_k_off` (celda 110 = 99 en vez de 98) | el `JMP` de la vuelta 1 cae en 100, no en 59 → criterio roto |
| `ctrl_no_dload` (celdas X → relleno inocuo) | 1 vuelta; el segundo `JMP` cae en 29433 y la ejecución acaba en HALT |
| `ctrl_block_v1` (`dload_block.mb` histórico) | 0 vueltas: su `JMP` cae en 70, como ya medía block_v1 |

## Q5 — cargador de 1998

`olmstead` rechaza la imagen (`invalid character in source file`, rc 1): sólo 4 de 111
celdas decodifican un opcode válido al cargar. Dialecto: Classic permisivo.

## Comprobaciones del auditor fuera del probe (contexto, no evidencia canónica)

* Motor scratch, sin pasar por el probe: la memoria al empezar la vuelta 0 es idéntica
  a la de la vuelta 1020 y distinta de la de la vuelta 510.
* Un motor aparte del autor (despacho por xlat1 y tabla 9×9 de la referencia de 1998,
  que para ante una celda no imprimible): **1 000 000 de pasos**, 166 656 `JMP`, todos
  en 59, sin salida y sin parar.

## Claims

Ver `manifest.json` (C1..C9). En corto: C1–C7 DEMONSTRATED (incluido cerrar C8 de
block_v1: el bloque de DLOAD funciona con esta colocación de datos); C8 (variante que
cargue el cargador de 1998) y C9 (componer DLOAD con OUT/ROT/CRAZY) NOT_DEMONSTRATED.

## NOT_DEMONSTRATED

* La memoria del oráculo y del runner C: no la exponen; su acuerdo se limita a no
  parar antes del tope.
* "Para siempre" vale en el modelo de Q3 (estado repetido en un motor determinista,
  con acuerdo de motores en el tramo medido); no se ejecutaron infinitos pasos.
* Que el bucle haga algo útil: este bloque sólo reinicia `d`. Componerlo con OUT, ROT o
  CRAZY es el siguiente experimento.

## Reproducción

```
cd vm_malbolge/evidence/epoch_dload_reset_v1
python3 -I probe.py </dev/null > stdout.raw.txt 2>&1   # rc 0, ~2 s, G0..G4 true
python3 manifest.py
```

Dos corridas consecutivas: `results.json` y `stdout.raw.txt` byte a byte idénticos
(verificado).
