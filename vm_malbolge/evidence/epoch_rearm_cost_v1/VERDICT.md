# epoch_rearm_cost_v1 — coste real de `ROT` + un `CRAZY` y restore exacto en una ejecución

Responde a los dos `NOT_DEMONSTRATED` que dejó `epoch_audit_v1`:

- **H1**: el coste real de la vía `ROT` + un `CRAZY` de preparación (pasos,
  rutado de `d`, celdas auxiliares) frente a la tabla de 34 posiciones de
  `epoch_rearm_barrier_v1`.
- **H2**: M8 era un literal (`200`); aquí se mide desde la traza.

Además construye, en **una sola ejecución**, el restore exacto de una celda de
código ya ejecutada y su re-ejecución, con control negativo sin restauración.

## Dialecto

**Classic permisivo (3^10)**: cargador sin validación y valores no imprimibles
producidos en runtime. Los tres motores (oráculo del repo, trazador del pack y
runner C original) coinciden en las tres imágenes; el runner C **no** corta por
la guarda de imprimibilidad (las celdas ejecutadas son imprimibles).

## Mecanismo

La celda `X = 44` contiene `V = 55`; `(55 + 44) % 94 = 5` → `OUT`. Al ejecutarse,
la celda se cifra: `ENC[55] = 110`. La celda de caída `45` contiene `43`;
`(43 + 45) % 94 = 88` (NOP) y se cifra a `36`; en la segunda visita,
`(36 + 45) % 94 = 81` → `END`.

```
bootstrap   DLOAD, DLOAD, ROT, DLOAD, NOP, DLOAD, JMP        (pc 0..6)
X = 44      OUT  -> emite 42; la celda 44 pasa a 110
45          NOP  -> la celda 45 pasa a 36
rutina      DLOAD, DLOAD, ROT, DLOAD, CRAZY, DLOAD, CRAZY|NOP,
            DLOAD, DLOAD, JMP                                (pc 46..55)
            el CRAZY de pc 52 restaura la celda 44: 110 -> 55
X = 44      OUT  -> emite 55 (la celda 44 vuelve a 110)
45          END  -> HALTED
```

La palabra de control **no se escribe a mano**: `plan.derive()` enumera las
soluciones por trit de `crazy(ctrl, 110) = 55` y se queda con la primera
materializable como `crazy(rot(v1), v2)` con `v1, v2` imprimibles. Sale
`ctrl = 29552` con `(v1, v2) = (54, 74)`.

La imagen `rearm.mb` añade, después de la restauración, el rearm **ejecutado** de
la celda auxiliar 103 (`29552 -> 74`), con su propia palabra de control
`ctrl2 = 29505`, materializada por `(84, 45)`.

## C1 — coste de la carga de la palabra de control

Traza de `restore.mb`, pc 46..50:

| medición | valor |
|---|---|
| instrucciones | 5 (`DLOAD, DLOAD, ROT, DLOAD, CRAZY`) |
| pasos | 5 |
| hops de `d` (DLOAD) | 3: `46→88`, `89→99`, `101→102` |
| celdas auxiliares leídas | 4: `89, 100, 101, 103` |
| celdas auxiliares consumidas | 2: `100` (ROT, 54→18), `103` (CRAZY, 74→29552) |
| palabra de control | `29552` |

Las celdas `99` y `102` son **destinos de hop** (valores), no celdas: el conteo
de 6 celdas auxiliares del handoff incluía dos valores; la traza da 4 celdas
sembradas.

Comparación calculada con la tabla de `epoch_rearm_barrier_v1`:

| comprobación | resultado |
|---|---|
| celdas de la tabla | 34 |
| ¿celda 44 en la tabla? | **no** |
| `swap01(55)` | `29550` |
| ¿`swap01(55)` en la órbita de 55? | **no** (la órbita sólo tiene un valor imprimible: 55) |

Así que la tabla de 34 posiciones **no puede expresar** esta celda re-ejecutable;
la vía `ROT` + `CRAZY` la materializa en 5 instrucciones y 4 celdas auxiliares.
Es el punto de H1: la tabla era un límite del modelo de un `ROT`, no de Classic.

## C2 — restore exacto y control negativo

| | `restore.mb` | `no_restore.mb` |
|---|---|---|
| ejecuciones de 44 | 2 | 2 |
| opcodes | `5, 5` (`OUT`, `OUT`) | `5, 60` (`OUT`, NOP) |
| bytes emitidos | `42, 55` | `42` |
| CRAZY a 44 | 1: `110 -> 55` (paso 16) | 0 |
| salida | `2a37` | `2a` |
| pasos / estado | 21 / `HALTED` | 21 / `HALTED` |

La segunda visita a 44 en el control negativo encuentra `110` (el valor cifrado)
y decodifica el opcode 60, que no es `OUT`: no hay segunda emisión.

## C3 — M8 medido desde la traza

| medición | valor |
|---|---|
| M8 (celdas de código del cuerpo) | **12** |
| celdas | `44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55` |
| re-ejecutadas (≥2 veces) | `44, 45` |
| conteo independiente (`no_restore`) | 12 |
| celdas del `code_map` 44..55 | 12 |
| literal `200` en `probe.py` | no |

M8 es el número de celdas de código distintas que el cuerpo ejecuta por
iteración. Para este micro-bucle son 12, no 200. El `200` de la barrera sigue
siendo un literal no medido: este pack **no** demuestra que el cuerpo del bucle
de la época tenga 12 celdas, sólo que el micro-bucle medido tiene 12.

Matiz medido: la celda 55 (`JMP`) se ejecuta pero **no** se cifra, porque el
`JMP` cifra la celda destino (`mem[mem[d]] = mem[43]`), no la suya. Por eso el
rearm del bucle cubre **11** celdas de código (44..54), no 12; la 55 queda
intacta y no necesita rearm. La celda 43 la cifra el `JMP` y sólo la usa el
bootstrap.

## C4 — rearm de las celdas auxiliares

Celdas escritas por el cuerpo (traza de `restore.mb`, desde la primera visita a
44 hasta el `END`): **14** (12 de código + `100` + `103`; la celda `43` la cifra
el `JMP` de la 55 por el quirk `mem[mem[d]]` y sólo la usa el bootstrap).

Mínimo de `CRAZY`s por celda (búsqueda exhaustiva por trit sobre los 3 estados):

| conjunto | celdas | CRAZYs mínimos | instrucciones (7/CRAZY) |
|---|---|---|---|
| conservador (todas las escrituras) | 14 | 25 | 175 |
| sólo bucle (sin la celda 43) | 13 (11 código + 100 + 103) | 23 | 161 |

La celda 55 no aparece en la tabla de rearm porque el `JMP` no la cifra; las 11
celdas de código rearmables son 44..54.

Rearm **ejecutado** de la celda 103 en `rearm.mb`:

| medición | valor |
|---|---|
| escritura | `29552 -> 74` (objetivo `74`) |
| segmento | pc 56..62, 7 pasos |
| celdas nuevas consumidas | 2: `90` (ROT, 84→28), `92` (CRAZY, 45→29505) |
| coste por celda | 7 instrucciones + 2 celdas nuevas |

Cada carga de palabra de control consume una celda `ROT`; `ROT` no tiene punto
fijo imprimible (`rot(v) = v` sólo para `v = 0`), así que el rearm de una celda
consume celdas nuevas y el ciclo cerrado no se construyó: **NOT_DEMONSTRATED**
con la cota inferior medida (7 instrucciones y 2 celdas por celda rearmada).

## Tabla de afirmaciones

| afirmación | estado |
|---|---|
| C1: la palabra de control se carga con 5 instrucciones, 3 hops y 4 celdas auxiliares (2 consumidas) | **DEMONSTRATED** (traza + 3 motores) |
| C1: la tabla de 34 posiciones no contiene la celda 44 y no puede expresar este restore | **DEMONSTRATED** (tabla + órbita calculadas) |
| C2: una celda de código ya ejecutada se restaura exactamente y se re-ejecuta en una sola ejecución | **DEMONSTRATED** (`2a37`, 21 pasos, `HALTED`) |
| C2: sin el CRAZY la segunda visita no es `OUT` | **DEMONSTRATED** (`2a`, opcode 60, sin CRAZY a 44) |
| C3: M8 = 12 celdas de código medidas desde la traza (no 200) | **DEMONSTRATED** para este micro-bucle |
| C4: el rearm de una celda auxiliar se ejecuta (29552→74) en 7 instrucciones y 2 celdas nuevas | **DEMONSTRATED** |
| C4: el ciclo cerrado de rearm | **NOT_DEMONSTRATED** (no construido; cada carga consume una celda ROT) |
| el cuerpo del bucle de la época tiene 200 celdas | **NOT_DEMONSTRATED** (el 200 de la barrera era un literal; aquí se mide 12 para el micro-bucle) |
| el runner C corta por la guarda de imprimibilidad en estas imágenes | **NOT_DEMONSTRATED** (no ocurre; las tres imágenes terminan en el C) |

## Reproducción

```bash
cd vm_malbolge/evidence/epoch_rearm_cost_v1
python3 build.py      # escribe las tres imágenes y build_index.json
python3 probe.py      # mide C1..C4, aplica G0..G6, escribe results.json
python3 manifest.py   # escribe manifest.json
```

## Relación con la auditoría

- H1 queda cerrada en su parte de coste: la vía `ROT` + un `CRAZY` cuesta 5
  instrucciones y 4 celdas auxiliares, y la tabla de 34 posiciones no contiene
  la celda 44 (no es una barrera de Classic).
- H2 queda cerrada para el micro-bucle: M8 se mide desde la traza (12), no se
  escribe a mano. El `200` del cuerpo completo de la época sigue sin medirse.
- H3: el dialecto se declara (Classic permisivo) y los tres motores coinciden.
- H7: los blobs van en LF; el runner C está en `.gitignore` y se declara como
  dependencia no reproducible desde un clon limpio.
