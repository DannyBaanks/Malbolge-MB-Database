# epoch_rearm_cost_v1 — puertas pre-registradas

Este archivo se commitea **antes** de `plan.py`, `build.py`, `probe.py` y de
cualquier medición del pack. Las puertas no se ajustan después de ver los
resultados; toda corrección posterior va como adición fechada al final de este
archivo, con el motivo, y no borra la versión pre-registrada.

Contexto: `epoch_audit_v1` (H1) dejó **NOT_DEMONSTRATED** el coste real de la
vía `ROT` + un `CRAZY` de preparación (pasos, rutado de `d`, celdas auxiliares),
y (H2) señaló que M8 era un literal (`200`). Este pack mide esas dos cosas y
construye, en una sola ejecución, el restore exacto de una celda de código ya
ejecutada con su control negativo.

## Dialecto declarado

**Classic permisivo (3^10)**: cargador sin validación (acepta celdas de dato que
no decodifican a un opcode en su posición) y valores no imprimibles producidos
en runtime. El runner C original es el tercer motor; si su guarda de
imprimibilidad corta una imagen, se registra como `DIALECT_LIMIT` con el paso
exacto, no como fallo de la imagen.

## Definiciones

- **C1** — coste de cargar la palabra de control `CTRL` con `ROT` + un `CRAZY`
  de preparación, medido en la traza: instrucciones, pasos, hops de `d`, celdas
  auxiliares leídas y celdas auxiliares escritas (consumidas).
- **C2** — restaurar exactamente una celda de código ya ejecutada y
  re-ejecutarla en una sola ejecución, con control negativo sin restauración.
- **C3 (M8)** — número de celdas de código distintas que el cuerpo ejecuta por
  iteración, contado desde la traza; se reporta también el subconjunto
  re-ejecutado (pc con ≥2 ejecuciones en la misma ejecución).
- **C4** — coste de rearmar las celdas auxiliares que el cuerpo modifica. Si no
  se construye un ciclo cerrado, se declara `NOT_DEMONSTRATED` con la razón y
  la cota inferior medida.

## Puertas

**G0 INTEGRIDAD.** Cada imagen es ASCII imprimible (33..126), sin whitespace y
es una sola imagen; `build.py` es determinista (dos builds consecutivos dan el
mismo SHA-256). PASA si las tres imágenes lo cumplen; FALLA si no.

**G1 TRES MOTORES.** Para cada imagen, el oráculo del repo
(`tools/oracle_classic.py`), el trazador del pack y el runner C
(`runners/malbolge-original/malbolge`) coinciden en bytes de salida, número de
pasos y estado. PASA si coinciden en las tres imágenes; FALLA con
`DIALECT_LIMIT` si el runner C corta por la guarda (se registra el paso exacto).

**G2 PALABRA DE CONTROL.** En la traza de `restore`, `a = CTRL` se produce con
exactamente 5 instrucciones (`DLOAD,DLOAD,ROT,DLOAD,CRAZY`); la traza muestra la
celda del `ROT` y la celda del `CRAZY` con sus valores viejo→nuevo. La
comparación con la tabla de 34 posiciones de `epoch_rearm_barrier_v1` se
**calcula**, no se afirma: se comprueba si la celda de código re-ejecutada está
en esa tabla y se reporta. PASA si la traza muestra el valor exacto y el coste
se cuenta desde la traza; FALLA si no.

**G3 RESTORE EXACTO.** En la traza de `restore` hay exactamente un `CRAZY` con
`addr` = la celda de código, `old` = valor cifrado, `new` = valor original; esa
celda se ejecuta dos veces con el mismo opcode (`OUT`); la salida son los dos
bytes de los dos `OUT` (el primero y el segundo) y el estado es `HALTED`. PASA
si todo; FALLA si no.

**G4 CONTROL NEGATIVO.** En la traza de `no_restore`, la celda de código se
ejecuta dos veces, la segunda con un opcode distinto de `OUT`, no hay ningún
`CRAZY` a esa celda, la salida tiene un solo byte y el estado es `HALTED`. PASA
si todo; FALLA si no.

**G5 M8 MEDIDO.** El probe calcula M8 desde la traza; el código del probe no
contiene el literal `200` ni un tamaño de cuerpo escrito a mano. PASA si M8 > 0
y coincide con el conteo independiente de la traza; FALLA si no.

**G6 REARM.** Para cada celda escrita por el cuerpo se calcula el mínimo de
`CRAZY`s necesario para restaurarla (búsqueda exhaustiva por trit sobre los 3
estados) y se mide en una ejecución real el rearm de al menos una celda
auxiliar (valor viejo→nuevo en la traza). PASA si el rearm medido deja la celda
en el valor original y el coste se reporta; el ciclo cerrado se declara
`NOT_DEMONSTRATED` si no se construye, con la razón (cada carga de palabra de
control consume una celda `ROT`; no hay punto fijo `ROT` imprimible).
