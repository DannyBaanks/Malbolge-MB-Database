# epoch_dload_compose_v1 — puertas pre-registradas

Se commitea **antes** de `probe.py` y de medir nada. Correcciones posteriores: sólo
como adición fechada al final, con el motivo.

Autor: `opencode_handoff_mbdb_1794xxxxx` (handoff de `claude_code_87747efe962f42f4`,
bridge seq 12135/12136, pedido de Danny), 2026-11-11. Base: MALBOLGE-MB-DATABASE
`f161c8a`, local sin push.

## Contexto

`epoch_xlat2_block_v1` construyó el bloque de 5 celdas que ejecuta OUT, ROT o CRAZY
exactamente una vez por vuelta dentro de un bucle cerrado por `JMP`, pero con una
tabla de destinos que **crece con R**: `d` avanza una celda por instrucción y cada
`JMP` lee una celda nueva.

`epoch_dload_reset_v1` construyó el bloque de `DLOAD` que **reinicia `d` cada
vuelta** con una tabla constante de dos celdas (periodo de estado 1020), pero ese
bloque no hace ninguna otra operación. Su `VERDICT` dejó C9 `NOT_DEMONSTRATED`:
componer el `DLOAD` con OUT, ROT o CRAZY.

Este pack construye y ejecuta esa composición: un cuerpo contiguo que contiene el
par de `DLOAD` (que reinicia `d`) y el par de la operación X (que la ejecuta una vez
por vuelta), con la misma tabla constante de dos celdas.

## Modelo (cálculo en papel, NO medido)

Cuerpo contiguo `[s .. J]`; `s = 60`, `T = 59` (la colocación de `DLOAD` de
`epoch_xlat2_block_v1`: `s ≡ 60 (mod 94)`, `T = s - 1` imprimible y mínimo).

- **Par de DLOAD** en los offsets `0` y `4`: ambos valen `74`; `(74 + 60) % 94 = 40`.
  En la vuelta 0 dispara la celda `s`; en la 1, la celda `s+4`; la otra decodifica 36
  o 44 (inválidos), y el par alterna para siempre.
- **Par de la operación X** en los offsets `δ` y `δ+4`, con `δ ≥ 5` el menor tal que
  `(s + δ) % 94 ≡ op - 74 (mod 94)`; `op ∈ {5 OUT, 39 ROT, 62 CRAZY}`. Ambos valen
  74: la misma alternancia da exactamente una X por vuelta.
- **Relleno** en el resto del cuerpo: valor cuyo ciclo XLAT2 **entero** es inocuo en
  su posición.
- **`JMP`** en `J = s + δ + 5 + e`, con `e ≥ 0` el menor que hace imprimible el valor
  `(4 - J) % 94` (`33..93`). `n = δ + 6 + e` celdas de cuerpo (`J - s + 1`).

Punto fijo de periodo 2 (`o_0 = 0`, `o_1 = 4` son los offsets del `DLOAD`):

| magnitud | ecuación |
|---|---|
| `D_0` | d al empezar la vuelta 0 (fijado por la semilla del prefijo) |
| `V_0` | `mem[D_0]` — lo lee el `DLOAD` de las vueltas pares |
| `D_1` | `V_0 + n` |
| `V_1` | `mem[D_1 + 4]` — lo lee el `DLOAD` de las vueltas impares |
| cierre | `D_2 = V_1 + n - 4 = D_0`, es decir `V_1 = D_0 - n + 4` |
| tabla par | `mem[V_0 + n - 1] = T` |
| tabla impar | `mem[D_0 - 1] = T` |

**Semilla del prefijo.** La celda `0` es `DLOAD` (`d = mem[0] = 40`, único valor
imprimible que decodifica 40 en 0). La celda `1` es `DLOAD` y lee `mem[41] = W`
(`d = W`); caminando hasta `s` queda `D_0 = W + s - 1`, con `W = D_0 - s + 1`
imprimible y `mem[41] = W` inocuo en 41.

**Regla de selección.** El menor `D_0 ≥ J + 2` con `V_1 = D_0 - n + 4` imprimible, y
el menor `V_0 > max(s, J - δ)` tal que las cuatro celdas de dato `D_0`, `V_0+n-1`,
`V_0+n+4`, `D_0-1` sean distintas, queden fuera de `[0..J]` y los `d` de la X
(`V_0+δ`, `V_1+δ`) queden fuera del código y de esas cuatro celdas. El probe
**calcula** todo esto desde los ciclos de XLAT2 y los parámetros medidos; no copia
la tabla de abajo. Si lo calculado difiere, se publica la diferencia.

**Predicción con los parámetros de papel** (medidos en los dos packs anteriores):

| X | δ | e | J | n | D_0 | V_0 | V_1 | celdas de dato (A,B,C,D) | d en la X | largo |
|---|---|---|---|---|---|---|---|---|---|---|
| OUT | 59 | 0 | 124 | 65 | 127 | 66 | 66 | 127, 130, 135, 126 | 125 | 137 |
| ROT | 93 | 0 | 158 | 99 | 161 | 66 | 66 | 161, 164, 169, 160 | 159 | 171 |
| CRAZY | 22 | 12 | 99 | 40 | 114 | 78 | 78 | 114, 117, 122, 113 | 100 | 124 |

`W` predicho: 68 (OUT), 102 (ROT), 55 (CRAZY); `r = 1` en los tres.

**Predicción de periodo.** Como en `epoch_dload_reset_v1`, el estado completo
`(mem[0..59048], a, c, d)` debe repetirse: `d` con periodo 2 y el estado con periodo
`P = mcm` de las longitudes de ciclo XLAT2 de **todas** las celdas cifradas cada
vuelta (cuerpo + trampolín, que se cifra en cada `JMP`). Con los ciclos de estas
imágenes: `mcm(2,4,5,6,9,68) = 3060` en los tres casos (predicción de papel).

## Dialecto y motores

Classic permisivo 3^10. Motores: oráculo (`tools/oracle_classic.py`), intérprete
independiente (`epoch_audit_v1/indep_interpreter.py`), motor scratch
(`epoch_xlat2_block_v1/scratch_engine.py`), runner C
(`runners/malbolge-original/malbolge`, stdin cerrado), un trazador local y el
cargador de Olmstead 1998 (`Malbolge-PureEpoch/build/olmstead`).

## Preguntas

**Q1 — construcción.** Para cada X ∈ {OUT, ROT, CRAZY}: parámetros derivados
(`s`, `δ`, `e`, `J`, `n`, `D_0`, `V_0`, `V_1`, semilla `W`), celdas de dato
(A,B,C,D) y largo de la imagen. Las cuatro ecuaciones del punto fijo se comprueban
**leyendo los bytes** de la imagen. Se compara con la tabla de predicción.

**Q2 — bucle compuesto.** `R = 10 000` vueltas por X. Por vuelta: número de
ejecuciones de la X y de `DLOAD` en el cuerpo, conjunto de opcodes válidos del
cuerpo, destino de cada `JMP`, `d` al empezar la vuelta y `d` al ejecutarse la X
(separado por paridad). Se exige exactamente una X y un `DLOAD` por vuelta.

**Q3 — periodicidad del estado.** Hash del estado completo al empezar cada vuelta;
primer par de vueltas con el mismo estado (pre-periodo y periodo). Se compara
`P` medido con el predicho por el mcm de los ciclos.

**Q4 — controles negativos.** Cuatro por X (doce en total), construidos desde la
misma imagen:

- `k_off`: la celda `D_0-1` (tabla impar) lleva `T+1`. Debe romper el criterio:
  algún destino de `JMP` distinto de `T` en las primeras 2 vueltas.
- `no_dload`: las dos celdas del par de `DLOAD` se sustituyen por relleno inocuo.
  Debe romper el criterio por `DLOAD` por vuelta = 0.
- `op_phase`: la segunda celda del par de X se siembra en la otra fase (`70` en vez
  de `74`). Debe romper el criterio con recuentos de X por vuelta `2, 0, 2, 0, …`.
- `dload_phase`: la segunda celda del par de `DLOAD` se siembra con `70`. Debe
  romper el criterio con recuentos de `DLOAD` por vuelta `2, 0, 2, 0, …`.

**Q5 — cargador de 1998.** Se prueba cada composición en `olmstead` y se declara el
dialecto.

## Puertas

- **G0 — construcción.** Los parámetros y las celdas de dato salen de calcularlos en
  el probe desde los ciclos y los parámetros medidos (no de tablas escritas a mano);
  las celdas del par de `DLOAD`, del par de X, del `JMP`, de la tabla y de las
  semillas se comprueban **leyendo los bytes** de la imagen; los cuatro controles
  mutantes de cada X se detectan (fallan la comprobación estructural o el criterio
  de G2). Las tres imágenes son imprimibles.
- **G1 — acuerdo de motores.** En la ejecución acotada de Q2 (tope = paso del
  `JMP` número `R` según el trazador): oráculo, intérprete independiente, motor
  scratch y runner C no paran antes del tope; para OUT los cuatro coinciden en los
  `R` bytes de salida; el sha256 de la memoria final coincide en trazador, scratch e
  intérprete independiente; los destinos de `JMP` y `d` al empezar cada vuelta
  coinciden en trazador y scratch.
- **G2 — criterio de Q2.** Para **cada** X, en las `R = 10 000` vueltas: exactamente
  una ejecución de la X y exactamente un `DLOAD` por vuelta; los únicos opcodes
  válidos del cuerpo son `{4, 40, op}`; todos los `JMP` caen en `T`; `d` al empezar
  la vuelta toma exactamente 2 valores; `d` en la X toma a lo sumo 2 valores, todos
  fuera del código y de las cuatro celdas de dato.
- **G3 — periodicidad.** Para cada X se encuentra un estado repetido dentro de las
  `R` vueltas, `d` tiene periodo 2 y el periodo medido es el `P` predicho por el mcm
  de los ciclos de las celdas cifradas.
- **G4 — controles y cargador.** Los doce controles de Q4 rompen el criterio por el
  motivo declarado, y Q5 publica el resultado del cargador y la declaración de
  dialecto.

## Fuera de alcance

- Componer `IN` (sólo OUT, ROT y CRAZY; `IN` sigue `NOT_DEMONSTRATED` desde
  `epoch_xlat2_block_v1`).
- Una variante que pase el cargador de Olmstead 1998.
- "Ilimitado" se demuestra sólo en el sentido de Q3 (estado repetido en un motor
  determinista, con acuerdo de motores en el tramo medido); no se ejecutan infinitos
  pasos.
- Usar los bloques dentro de un programa que calcule algo elegido por la petición.
- La memoria final del oráculo y del runner C: no la exponen.
