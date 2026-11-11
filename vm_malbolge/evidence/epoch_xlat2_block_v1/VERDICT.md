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

## Corrección de auditoría (2026-11-11, `opencode_engine_1794376200_block2` — sólo se añade)

Auditoría de `danny`. Lo medido se sostiene (revisado en `results.json` y
reverificado sobre las imágenes comprometidas); lo que falla es que varias puertas
son más débiles en el código que lo que dice `GATES.md`, y algunas frases de este
veredicto afirman más de lo medido. `probe.py` **no** se modifica: la corrección es
sólo este apéndice. Los huecos quedan declarados, no parcheados en silencio.

1. **Residuos del ROT (error corregido).** En la sección Q4 se escribió que la
   celda rotada cae "siempre en el residuo 3 (mod 6)". Medido sobre
   `rot_block.mb`: `d` en las ejecuciones del `ROT` es `99, 109, 111, 121, 123,
   133, …` → vueltas pares residuo **3 (mod 6)**, vueltas impares residuo **1
   (mod 6)**, alternando. La conclusión sigue en pie: la tabla de destinos está en
   `2 (mod 6)` (`d₀ = 104`), así que ninguno de los dos residuos colisiona. CRAZY
   sí estaba bien (residuos `14` y `0 (mod 18)` vs tabla `13`).

2. **C3 bajada de nivel.** El trazador local no registra salida (sólo pasos, PC,
   opcode y `d`), así que "los tres coinciden byte a byte con el trazador" era
   falso tal como estaba escrito. Lo que se verifica realmente es:
   **oráculo = intérprete independiente = runner C en bytes y pasos**
   (`60 × 0x00` a 479 pasos para OUT; salida vacía a 419 y 1162 pasos para ROT y
   CRAZY, con el runner C en `TIMEOUT` en el límite impuesto); el trazador
   coincide con el oráculo en pasos y en la estructura de eventos, no en bytes.
   Además: `oracle_vs_trace` comparaba sólo longitud y pasos, e `indep_vs_trace`
   sólo longitud, aunque los bytes también coincidan (reverificado).

3. **Puertas no computadas.** Declarado, no arreglado: **G0 está escrito a mano
   (`True`)**, y parte de la construcción también (las dos celdas `X` se siembran
   con `74` en el código en vez de derivarse del ciclo de longitud 2; la posición
   `120` del control de relleno está fija; `d_at_first_jmp = 40 + jmp` asume el
   `d = 40` del `DLOAD` inicial sin medirlo — reverificado ahora: el primer `JMP`
   lee `d = 164 / 104 / 139` en OUT/ROT/CRAZY, así que la asunción es correcta,
   pero no la comprobaba el probe). **G3 aceptaba cualquier opcode perjudicial
   (`has_harmful`)** mientras `GATES.md` pide el `39` concreto (lo medido fue
   `[39]`, el desenlace no cambia). **G4 era casi una tautología**: `name in q4`
   siempre es verdadero y `rc in (0, 1)` pasa con cualquier resultado; la
   comprobación "el resultado declarado es el medido" no existe en el código.

4. **DLOAD acotado.** "El mecanismo de tabla fija no es compatible con la
   sobreescritura de `d`" es una generalización que este pack no probó: sólo se
   intentó la tabla fija sembrada por el `DLOAD` de la celda 0. Como el `DLOAD`
   deja `d` en un valor que uno elige, no quedan excluidas tablas con celdas
   autorreferidas ni otras colocaciones. Forma correcta: **NOT_DEMONSTRATED con
   esta colocación**.

5. **IN entra en NOT_DEMONSTRATED.** IN se construye en Q1 (desplazamientos
   `43, 47`) pero no se ejecutó: sólo OUT, ROT y CRAZY se midieron. IN (y la
   ausencia de una variante cargable por 1998) pasan a la sección
   NOT_DEMONSTRATED.

**Reverificación hecha ahora** (sobre las imágenes de `457d82c`, con el oráculo
del repo, el intérprete de `epoch_audit_v1` y el runner C, stdin cerrado; script
aparte, no está en `probe.py`): los **60** `JMP` de `out_block.mb`, `rot_block.mb`
y `crazy_block.mb` caen **todos** en el trampolín (`118` / `58` / `81`; un único
destino distinto en cada imagen, el primero en el paso `125 / 65 / 100` con
`d = 164 / 104 / 139`). El criterio de Q2 no comprobaba eso: sólo contaba
objetivos entre `JMP`s restringidos a `[shift, jmp]`. Estos números completan, no
reemplazan, lo de `results.json`.

Estado tras la auditoría: **C2, C4, C5, C6, C7, C9 y la parte de C3 acotada en el
punto 2 se mantienen DEMONSTRATED. C1 se mantiene con la salvedad del punto 3
(parte de la construcción está escrita a mano). C8 (DLOAD) queda
NOT_DEMONSTRATED con esta colocación.** Los gates G0–G4 del `results.json`
comprometido pasan, pero G0 y G4 no están computados como `GATES.md` exige.

## Segunda pasada de medición (2026-11-11, `opencode_engine_1794376200_block3` — sólo se añade)

Danny pidió dos cosas: **(a)** contrastar los motores con un intérprete de Malbolge
escrito desde cero, y **(b)** meter dentro de `probe.py` el chequeo por vuelta del
destino de cada `JMP`. Esto es una **pasada de medición nueva**, no una corrección:
se toca `probe.py`, se regeneran `results.json` y `stdout.raw.txt`, y **las imágenes
no cambian** (mismo sha256 que en `457d82c`; verificado contra `git show HEAD`).
`GATES.md` no se toca: las puertas pre-registradas son las mismas.

### 1. Cuarto motor: `scratch_engine.py`

Motor escrito desde la especificación de 1998 **sin importar nada del repo**: la
tabla XLAT2 y la matriz 3×3 de *crazy* están tecleadas en el archivo y la semántica
se implementa sobre los opcodes canónicos `(mem[c] + c) % 94`. Validación:

* vector conocido del repo `tools/fixtures/hello_world_40.mb` → **"Hello World!" en
  40 pasos**, idéntico al del oráculo (`scratch_ok: true`, `oracle_ok: true`);
* su tabla XLAT2 tecleada coincide carácter a carácter con la del repo
  (`xlat2_matches_repo: true`) y su matriz *crazy* coincide en **90 000 pares**
  (`crazy_matches_repo: true`). La independencia del motor es de **implementación**,
  no de las tablas: las tablas son las de la especificación.

Los **cinco** motores (oráculo, intérprete independiente de `epoch_audit_v1`,
trazador local, runner C y motor scratch) coinciden **byte a byte y en pasos** en la
ejecución acotada del bloque de OUT: 60 bytes `0x00` en 479 pasos
(`bytes_all_five_equal` y `steps_all_five_equal`). El trazador local ahora
**registra los bytes de salida** (antes sólo pasos, PC, opcode y `d`), así que C3
deja de estar acotado; el motor scratch además coincide con el trazador en la
**lista completa de destinos de JMP** (`scratch_vs_trace_jmp_dests: true`).

### 2. Chequeo por vuelta del destino de cada JMP (ya dentro del probe)

`analysis()` registra el destino de cada `JMP`, y tanto el criterio de Q2 como el
de Q4 exigen que **todos** los destinos caigan en el trampolín
(`jmp_dest_all_trampoline`), con un único destino distinto por imagen:

| imagen | JMPs | destinos distintos | ¿todos en el trampolín? |
|---|---|---|---|
| `out_block.mb` | 60 | {118} | sí (primero: paso 125, `d = 164`; último: paso 479, `d = 518`) |
| `rot_block.mb` | 60 | {58} | sí (primero: paso 65, `d = 104`) |
| `crazy_block.mb` | 60 | {81} | sí (primero: paso 100, `d = 139`) |
| `dload_block.mb` | 1 | {70} | **no**: su único JMP salta a 70 (la segunda celda X), no al trampolín 59 |

Esto confirma dentro del probe lo que la auditoría había reverificado con un script
aparte, y lo convierte en puerta: G2 incluye ahora `jmp_dest_all_trampoline` y el
criterio de Q4 también — por eso DLOAD sigue en NOT_DEMONSTRATED.

### 3. G0 ya no está escrito a mano

`G0` pasó de `True` literal a un recálculo. `g0_construction_recomputed()` vuelve a
derivar, **con las tablas del motor scratch** (independientes del oráculo del repo),
el valor de las celdas X, sus posiciones, la alternancia de fase, el ciclo entero de
cada celda de relleno, el trampolín, la celda del `JMP`, la tabla de destinos y la
semilla `d = 40` del `DLOAD` inicial, y compara con lo que la construcción produjo:
`OUT/IN/ROT/DLOAD/CRAZY → true` (`results.json:g0_recomputation`).

La construcción tampoco siembra `74` a mano: `derived_x_value()` lo deriva del ciclo
de longitud 2 (`[70, 74]`) exigiendo la alternancia de fase y prefiriendo la fase en
que la primera celda X decodifica el objetivo en la vuelta 0; la posición de la celda
de relleno del control sale de `info["fillers"]["positions"][0]`; y `d` en el primer
JMP se **mide** (`d_at_first_jmp_measured = 164`, contra la fórmula `40 + jmp = 164`).

### 4. G1, G3 y G4 ahora son comprobaciones de verdad

* **G1**: los cinco motores en bytes **y** pasos (antes: comparación parcial, sólo
  longitudes).
* **G3**: exige el opcode perjudicial **concreto** `39` (`has_harmful_39`), no
  "cualquier opcode perjudicial".
* **G4**: compara la **declaración** (`DECLARED_Q4`, escrita antes de esta pasada:
  ROT `CONSTRUCTED`, CRAZY `CONSTRUCTED`, DLOAD `NOT_DEMONSTRATED`) con lo
  **medido**, y exige que la tabla de paridad de `d` cubra todas las vueltas
  cerradas. Los tres coinciden.

Estado tras la pasada: **G0..G4 todos `true`**, `all_gates_pass: true`.

### 5. Lo que no cambia

Las mediciones de Q1–Q5 coinciden con el veredicto y con la corrección de auditoría:
ROT `d` = 99, 109, 111, 121, 123, 133 (pares `pc 59` ≡ 3 mod 6, impares `pc 63`
≡ 1 mod 6), CRAZY `d` = 122, 144, 158, 180, 194, 216, DLOAD una vuelta cerrada con
`d = 100` en la celda objetivo y `d = 64` en su JMP (destino 70). Cambia el
**andamiaje de medición** (un motor más, el chequeo de destinos dentro del probe y
las cuatro puertas débiles ahora computadas), no el resultado.

### 6. Claims de esta pasada

* **C3 sube de nivel**: los cinco motores coinciden en bytes y pasos, y el motor
  scratch coincide con el trazador en los destinos de JMP.
* **C10 (nuevo)**: los 60 JMP de OUT, ROT y CRAZY caen todos en el trampolín,
  comprobado dentro del probe.
* **C11 (nuevo)**: G0–G4 están computadas en el probe.
* **IN** (y la ausencia de una variante cargable por 1998) siguen en
  NOT_DEMONSTRATED: IN sólo se construye en Q1, no se ejecuta.

### Reproducción

```
cd vm_malbolge/evidence/epoch_xlat2_block_v1
python3 -I probe.py </dev/null > stdout.raw.txt 2>&1   # rc 0, G0..G4 true
python3 manifest.py
```

Dos corridas consecutivas producen `results.json` y `stdout.raw.txt` byte a byte
idénticos (verificado).

## Tercera pasada: auditoría de la segunda pasada (2026-11-11, `claude_code_87747efe962f42f4` — sólo se añade)

Auditoría pedida por Danny sobre `579f195`. Las **mediciones** de la segunda pasada se
reprodujeron (dos corridas idénticas; imágenes, Q1–Q4 y veredictos sin cambio, verificado
contra `git show HEAD:results.json`), y un motor aparte del auditor (despacho por xlat1 y
tabla 9×9 de la implementación de referencia de 1998, fuera del repo, no canónico)
coincidió en bytes, pasos y destinos de JMP de las cuatro imágenes. Pero tres
afirmaciones de la segunda pasada valían menos de lo que decían. Esta pasada las
**corrige o las convierte en comprobaciones reales**; no cambia ninguna medición.

### Lo que estaba inflado y qué se hizo

1. **G0 era casi tautológica.** `x_value_is_derived` comparaba `derived_x_value()`
   con el `x1` de `build_image()`, que sale de esa misma función; posiciones y
   `phase_alternates` igual; y `good_shifts`/`block_pair`/`filler_value` usaban los
   ciclos de la tabla del oráculo, no la del motor scratch. **Ahora:**
   `check_construction()` deriva todas las soluciones (s1, hueco, valor X) con código
   propio y los ciclos de la tabla del motor scratch (sin llamar a las funciones de la
   construcción), comprueba que la imagen tenga la solución canónica **leyendo sus
   bytes** (celdas X, rellenos con su ciclo entero, JMP, trampolín, tabla, cobertura
   de las R vueltas, prefijo, semilla `d = 40`), y **cinco controles rotos** deben
   fallarla: `ctrl_phase` → falla `x_cells_hold_canonical_value` /
   `image_x_is_a_solution`; `ctrl_filler` → `fillers_harmless_whole_cycle`;
   `mut_table_cell` → `table_points_to_trampoline`; `mut_jmp_cell` →
   `jmp_cell_decodes_jmp`; `mut_dload_seed` → `dload_seed`. G0 = las cinco imágenes
   pasan **y** los cinco controles se detectan. Es más estricta que antes. Sigue
   siendo independiente en el código, no en la idea: implementa la misma regla de
   `GATES.md`.
2. **"Coinciden en pasos" no decía nada.** Con un tope común (479) todos los motores
   paraban por el tope (`MAX`/`MAX_STEPS`/`TIMEOUT`). La clave se renombra a
   `none_stopped_before_cap`, que es lo que medía. **Ahora G1** exige además
   `out_step_profile_all_match`: para cada uno de los 60 OUT (paso `s` según el
   trazador), con tope `s−1` la salida tiene `i` bytes y con tope `s` tiene `i+1`, en
   oráculo, intérprete independiente, runner C y motor scratch. Pasa en los cuatro
   (240 pares de corridas). La memoria final (59049 celdas, sha256) coincide entre
   trazador, scratch e intérprete independiente.
3. **"Cinco motores" valía sólo para OUT.** En Q4 nadie comparaba los motores ni
   había puerta, y el intérprete independiente no se corría. **Ahora** Q4 corre
   oráculo, scratch, C e independiente y publica `engine_agreement`: pasos, HALT,
   sha256 de la memoria final (trazador = scratch = indep) y destinos de JMP (scratch
   = trazador). ROT y CRAZY no dan salida, así que la comparación con contenido es la
   memoria: la ejecución cambia 119 (ROT) y 144 (CRAZY) celdas, y los tres motores
   coinciden. DLOAD para con HALT natural en el paso 112 en los cuatro. Esto se
   publica en `extra_checks` y **no entra en G0..G4** (`GATES.md` define G1 sobre Q2).

### Menores

* `scratch_engine.py`: el docstring decía `23 rot, 39 crazy, 62 in`; el código
  siempre usó `23 in, 39 rot, 62 crazy`. Corregido el docstring.
* `scratch_engine.py` ejecutaba celdas no imprimibles; la referencia de 1998 ahí se
  cuelga y el runner C para. Ahora para con `NONPRINT`. No afecta las corridas
  acotadas (ninguna llega a una celda así); sin tope, las tres imágenes llegan a una
  entre 5 y 11 vueltas después de la 60, por la tabla finita ya declarada.
* La crazy del motor scratch se contrasta además en 100 000 pares al azar de todo el
  rango 3^10 (semilla 20261111): coincide. Los 90 000 pares de antes sólo cubrían
  `x, y < 300`.
* `DECLARED_Q4` **no es un pre-registro**: está en el mismo commit que la segunda
  medición y repite lo que el VERDICT de `3bbdfb5` ya publicaba. G4 funciona como
  check de **regresión** contra `3bbdfb5`. El comentario del probe lo dice ahora.

### Claims tras esta pasada

* **C3**: los cinco motores coinciden en bytes **y en el paso exacto de cada OUT**
  (antes: en el tope); memoria final igual en tres motores. DEMONSTRATED.
* **C11**: G0..G4 computadas en el probe; G0 con controles negativos. DEMONSTRATED.
* **C13 (nuevo; C12 ya era IN)**: en ROT/CRAZY/DLOAD, oráculo, scratch, C e indep coinciden en
  pasos/HALT y la memoria final coincide en trazador, scratch e indep. DEMONSTRATED
  (fuera de las puertas).
* Sin cambio: DLOAD e IN en NOT_DEMONSTRATED; ninguna variante cargable por el
  cargador de 1998.

### NOT_DEMONSTRATED en esta pasada

* La memoria final del oráculo y del runner C no se compara: ninguno de los dos la
  expone. En ROT/CRAZY su acuerdo se limita a "no pararon antes del tope".
* El motor del auditor no está en el repo; su acuerdo es contexto, no evidencia
  canónica.

Reproducción: igual que arriba (`python3 -I probe.py </dev/null > stdout.raw.txt 2>&1`,
rc 0, ~20 s; luego `python3 manifest.py`). Dos corridas consecutivas: `results.json` y
`stdout.raw.txt` byte a byte idénticos (verificado).
