# epoch_xlat2_block_v1 — veredicto

Responde a las puertas de `GATES.md` (commit `2129a85`, pre-registrado antes de
este archivo y de `probe.py`). Repo MALBOLGE-MB-DATABASE, local sin push.
Handoff de `claude_code_a029a379be0f4681` (bridge seq 11995/11996, pedido de Danny),
base `bb4e204`.

## Dialecto y motores

Dialecto: **Classic permisivo (3^10)** — el mismo del oráculo y del intérprete
independiente. El cargador de Olmstead 1998 **rechaza** la imagen del bloque
(Q5), así que la imagen sólo corre en intérpretes permisivos. Motores usados:
oráculo del repo, intérprete independiente de `epoch_audit_v1`, un trazador local
con la misma semántica (validado contra el oráculo byte a byte en la ejecución
acotada), el runner C (`runners/malbolge-original/malbolge`, `stdin=DEVNULL`) y
Olmstead 1998 como cargador.

## La construcción

El bloque se calcula, no se escribe a mano: el probe deriva los ciclos de XLAT2,
elige para cada objetivo el par de desplazamientos buenos del ciclo de longitud 2
(el único: `[70, 74]`), y con ello las posiciones, el relleno, el trampolín, el
`JMP` y la tabla de destinos.

* Desplazamientos buenos: `OUT [25,29]`, `IN [43,47]`, `ROT [59,63]`,
  `DLOAD [60,64]`, `CRAZY [82,86]` — todos con tramo de 5 celdas.
* Las dos celdas `X` se siembran **con el mismo valor (74)**; el desfase sale del
  desplazamiento de 4 posiciones: en 119 el 74 decodifica `OUT` (5) y el 70
  decodifica 1 (inválido); en 123 es al revés (9 inválido / 5 `OUT`). Cada vuelta
  cifra las dos celdas un paso en el ciclo de longitud 2, así que los papeles se
  intercambian y hay exactamente una operación por vuelta.
* Las tres celdas de relleno se toman de un ciclo XLAT2 cuyo **ciclo entero** es
  inocuo en su posición (para OUT: el de longitud 6), así que el relleno es
  inocuo en todas las vueltas, no sólo en la primera.
* El bucle lo cierra un `JMP` en `124` (valor 68). El `JMP` cifra su destino, no su
  propia celda, así que la instrucción de control no se degrada nunca. Salta a un
  trampolín en `118` (valor imprimible; se cifra cada vuelta pero no se vuelve a
  ejecutar) y la ejecución sigue en el bloque.
* El destino lo da una tabla de celdas a partir de `d = 164`: `d` avanza una celda
  por instrucción, el `DLOAD` en la celda 0 lo fija en 40 para que esa tabla caiga
  fuera del cuerpo recorrido. Todas las celdas de la tabla apuntan al trampolín,
  así que el bucle es estable mientras `d` quede dentro de ella.

## Q1 — construcción

| X | posiciones (mód. 94) | tramo | relleno | trampolín | JMP | d en el 1.º JMP | largo | válidas al cargar |
|---|---|---|---|---|---|---|---|---|
| OUT | 25, 29 | 5 | 37, 37, 37 (ciclo 6) | 118 | 124 | 164 | 584 | 44 |
| IN | 43, 47 | 5 | 41, 41, 37 | 42 | 48 | 88 | 508 | 43 |
| ROT | 59, 63 | 5 | 37, 41, 41 | 58 | 64 | 104 | 524 | 43 |
| DLOAD | 60, 64 | 5 | 41, 41, 37 | 59 | 65 | 105 | 525 | 43 |
| CRAZY | 82, 86 | 5 | 37, 37, 37 | 81 | 99 | 139 | 1279 | 106 |

Para CRAZY el `JMP` necesitó 12 celdas extra de relleno inocuo: el valor del `JMP`
debe ser imprimible (posición mód. 94 en `[5,65]`), y la vuelta mide 18
instrucciones en lugar de 6. Las demás construcciones caben con tramo 5 y vuelta de
6 instrucciones.

## Q2 — OUT construido y ejecutado

`out_block.mb` (584 celdas, todas imprimibles): 60 vueltas, 479 pasos.

* exactamente **una** ejecución del opcode `5` (`OUT`) en cada una de las 60
  vueltas (`per_round` = 60 unos);
* los PCs del `OUT` alternan `119, 123, 119, 123, …` — una vuelta en la primera
  celda del par y la siguiente en la segunda, como predice el desfase;
* los únicos opcodes válidos decodificados en el cuerpo del bucle son `{4 (JMP),
  5 (OUT)}`: **nada perjudicial**;
* salida: 60 bytes `0x00` (`a` vale 0 durante toda la ejecución).

Acuerdo de motores en la ejecución acotada (479 pasos): oráculo 60 bytes
`MAX_STEPS`, intérprete independiente 60 bytes `MAX`, runner C 60 bytes
`TIMEOUT` en el límite impuesto. Los tres coinciden byte a byte con el trazador
(G1).

## Q3 — controles negativos

* **Control de desfase** (`out_block_ctrl_phase.mb`, segunda celda `X` en la otra
  fase, valor 70): el recuento por vuelta es `2, 0, 2, 0, …` — no hay exactamente
  una operación por vuelta. El criterio de Q2 rompe por el lado previsto.
* **Control de relleno no inocuo** (`out_block_ctrl_filler.mb`, celda 120 sembrada
  con el valor 107, que decodifica `ROT` (39) en su posición): el recuento de
  `OUT` por vuelta sigue pareciendo correcto, pero el cuerpo del bucle decodifica
  el opcode perjudicial `39`, que el criterio de Q2 rechaza.

## Q4 — ROT, CRAZY y DLOAD: el puntero `d`

`d` avanza una celda por instrucción ejecutada; en una vuelta de tramo 5 eso
significa que la primera y la segunda celda `X` ven `d` en valores distintos, y
que vueltas pares e impares quedan separadas por el largo de la vuelta. Medido
(primeras ejecuciones del objetivo):

| X | vueltas cerradas | `d` en vueltas pares (pc) | `d` en vueltas impares (pc) | resultado |
|---|---|---|---|---|
| ROT | 60 | 99, 111, 123 (pc 59) | 109, 121, 133 (pc 63) | **CONSTRUIDO** |
| CRAZY | 60 | 122, 158, 194 (pc 82) | 144, 180, 216 (pc 86) | **CONSTRUIDO** |
| DLOAD | 1 | 100 (pc 60) | — | **NOT_DEMONSTRATED** |

* **ROT**: la celda que rota el `ROT` cae siempre en el residuo `3 (mod 6)` y las
  celdas de destino del `JMP` en el residuo `2 (mod 6)`: nunca coinciden, así que
  el bucle sobrevive 60 vueltas con exactamente un `ROT` por vuelta y sin ningún
  otro opcode válido en el cuerpo. Oráculo y runner C coinciden (419 pasos, salida
  vacía).
* **CRAZY**: con tramo 18 el mismo chequeo: los objetivos del `CRAZY` caen en los
  residuos `14` y `0 (mod 18)`, la tabla en el `13`: sin colisión, 60 vueltas, un
  `CRAZY` por vuelta, sin opcodes perjudiciales. Oráculo y runner C coinciden
  (1162 pasos, salida vacía).
* **DLOAD**: el `DLOAD` **sobrescribe** `d` (`d = mem[d]`, no un incremento). En la
  vuelta 0, la celda 60 se ejecuta con `d = 100` y deja `d = mem[100] = 59` (el
  valor del trampolín); tras el avance normal el `JMP` de la vuelta lee
  `d = 64`, y `mem[64]` es la segunda celda `X` (valor 70), no el trampolín: el
  bucle sale de la tabla. Medido: **1 vuelta cerrada** y el programa deambulando
  hasta detenerse en el paso 112 (oráculo y runner C coinciden en ese paso, ambos
  `HALTED`). El mecanismo de tabla fija no es compatible con la sobreescritura de
  `d`: se declara **NOT_DEMONSTRATED**.

## Q5 — cargador de Olmstead 1998

`olmstead` sobre `out_block.mb`: **rc 1**, `stderr = "invalid character in source
file"`. De las 584 celdas cargadas, sólo **44** decodifican un opcode válido: el
cargador de 1998 exige un opcode válido en todas (`vendor/olmstead_original.c:78`).
Declaración de dialecto: **Classic permisivo (3^10)**; el bloque usa opcodes no
válidos como relleno inocuo y no es cargable por el intérprete de 1998.

## Claims

| claim | estado |
|---|---|
| C1: el cálculo del bloque (posiciones, valores, relleno, trampolín, `JMP`, tabla) se deriva en el probe de los ciclos de XLAT2 | DEMONSTRATED |
| C2: `out_block.mb` hace la operación exactamente una vez por vuelta durante 60 vueltas, con PCs alternantes 119/123 y sin ningún opcode perjudicial en el cuerpo | DEMONSTRATED |
| C3: oráculo, intérprete independiente, trazador y runner C coinciden en la salida y los pasos de la ejecución acotada | DEMONSTRATED |
| C4: el control de desfase produce 2 y 0 operaciones por vuelta alternadas | DEMONSTRATED |
| C5: el control de relleno no inocuo decodifica el opcode perjudicial `39` en el cuerpo del bucle | DEMONSTRATED |
| C6: el bloque de ROT se construye y ejecuta exactamente una vez por vuelta durante 60 vueltas, con el `d` medido por paridad | DEMONSTRATED |
| C7: el bloque de CRAZY se construye y ejecuta exactamente una vez por vuelta durante 60 vueltas, con el `d` medido por paridad | DEMONSTRATED |
| C8: el bloque de DLOAD se construye y ejecuta | NOT_DEMONSTRATED (el `DLOAD` sobrescribe `d`; medido 1 vuelta cerrada) |
| C9: una variante del bloque que pase el cargador de Olmstead 1998 | NOT_DEMONSTRATED |

## Consecuencia

La corrección de `epoch_xlat2_phase_census_v1` (commit `bb4e204`) dejó el bloque
como "calculado, no ejecutado". Este pack lo ejecuta: **el cuerpo de bucle de
tamaño constante existe y hace su operación exactamente una vez por vuelta** para
OUT, ROT y CRAZY, en Classic permisivo. Lo que sigue abierto de la línea de
épocas no es el tamaño del cuerpo sino (a) el dialecto — el cargador de 1998 lo
rechaza —, (b) `DLOAD`, que rompe el puntero `d`, y (c) usar estos bloques dentro
de un programa que calcule algo elegido por la petición, que este pack no construye.

## Reproducción

```
cd vm_malbolge/evidence/epoch_xlat2_block_v1
python3 -I probe.py </dev/null > stdout.raw.txt 2>&1   # rc 0, G0..G4 true
python3 manifest.py
```

## NOT_DEMONSTRATED

- el bloque de DLOAD (el `DLOAD` sobrescribe `d`; ver Q4);
- una imagen del bloque que pase el cargador de Olmstead 1998;
- la ejecución del bloque fuera de la tabla de destinos: el bucle es exacto
  mientras `d` queda dentro de la tabla (60 vueltas medidas); más allá, los
  motores divergen (el runner C para en la primera celda no imprimible y el
  oráculo deambula), y eso no se mide aquí;
- cualquier uso del bloque dentro de un programa que haga otra cosa.
