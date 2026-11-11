# epoch_dload_reset_v1 — puertas pre-registradas

Se commitea **antes** de `probe.py` y de medir nada. Correcciones posteriores: sólo
como adición fechada al final, con el motivo.

Autor: claude_code_87747efe962f42f4 (pedido de Danny, 2026-11-11). Base:
MALBOLGE-MB-DATABASE `61a0278`, local sin push.

## Contexto

`epoch_xlat2_block_v1` construyó un bloque de 5 celdas sobre el ciclo de longitud 2 de
XLAT2 que ejecuta OUT, ROT o CRAZY una vez por vuelta dentro de un bucle cerrado por
`JMP`. Ese bucle es **finito**: `d` avanza una celda por instrucción, así que cada `JMP`
lee una celda nueva de una tabla que crece con R (y el bucle se rompe unas vueltas
después de que la tabla se acaba). El bloque de `DLOAD` quedó `NOT_DEMONSTRATED` (C8):
su `JMP` cayó en 70 (la segunda celda X), no en el trampolín 59, porque la colocación no
tuvo en cuenta que `DLOAD` cambia `d`.

## Idea a medir

`DLOAD` (`d = mem[d]`) y `JMP` (`c = mem[d]`) sólo **leen** `mem[d]`, y el cifrado
posterior sólo toca `mem[c]`. Celdas que sólo se leen como dato no cambian nunca. Si el
`DLOAD` de cada vuelta lleva `d` a una zona fija de celdas de dato, el `JMP` lee siempre
las mismas celdas y la tabla de destinos tiene **tamaño constante**, independiente de R.

## Modelo (cálculo en papel, NO medido)

Bucle del bloque de `DLOAD` de `epoch_xlat2_block_v1` (mismas posiciones): cuerpo de
`n` celdas `[shift, jmp]`, celdas X en los offsets `0` y `g` del cuerpo, trampolín
`T = shift - 1`. En la vuelta `r`, con `d = D_r` al ejecutar la celda `shift`, el `DLOAD`
está en el offset `o_r ∈ {0, g}` (alterna por el ciclo de longitud 2). Entonces:

- el `DLOAD` lee `V_r = mem[D_r + o_r]`;
- el `JMP` lee `mem[V_r + n - 1 - o_r]`, que debe valer `T`;
- la vuelta siguiente empieza con `D_{r+1} = V_r + n - o_r`.

Punto fijo de periodo 2 (`D_2 = D_0`), eligiendo `V_0 = D_0 + o_0`:

| celda | valor |
|---|---|
| `D_0 + o_0` | `D_0 + o_0` |
| `D_0 + o_0 + n - 1 - o_0` | `T` |
| `D_1 + o_1` con `D_1 = D_0 + o_0 + n - o_0` | `D_0 - n + o_1` |
| `D_0 - 1` | `T` |

**Predicción** con los parámetros medidos en `epoch_xlat2_block_v1` (`shift = 60`,
`jmp = 65` → `n = 6`, `g = 4`, `T = 59`, `D_0 = 100`, `o_0 = 0`, `o_1 = 4`): celdas
`99 ← 59`, `100 ← 100`, `105 ← 59`, `110 ← 98`. El probe las **calcula** desde los
parámetros que mide; no las copia de esta tabla. Si lo calculado difiere de la
predicción, se publica la diferencia.

## Dialecto y motores

Classic permisivo 3^10. Motores: oráculo (`tools/oracle_classic.py`), intérprete
independiente (`epoch_audit_v1/indep_interpreter.py`), motor scratch
(`epoch_xlat2_block_v1/scratch_engine.py`), runner C
(`runners/malbolge-original/malbolge`, stdin cerrado), un trazador local y el cargador
de Olmstead 1998 (`Malbolge-PureEpoch/build/olmstead`).

## Preguntas

**Q1 — construcción.** Parámetros medidos (`n`, `g`, `T`, `D_0`, `o_0`, `o_1`), celdas
de dato calculadas, longitud de la imagen. La imagen se construye **igual para todo R**.

**Q2 — bucle largo.** `R = 10 000` vueltas. Por vuelta: ejecuciones de `DLOAD` (opcode
40) en el cuerpo, opcodes válidos del cuerpo, destino de cada `JMP`, `d` al empezar la
vuelta.

**Q3 — periodicidad del estado completo.** Hash del estado `(mem[0..59048], a, c, d)` al
empezar cada vuelta. Se busca el primer par de vueltas con el mismo estado. Como la
máquina es determinista, un estado repetido implica que el bucle se repite **para
siempre** (en este dialecto y con esta semántica). **Predicción:** `d` toma 2 valores
(periodo 2) y el periodo del estado es `P = mcm` de las longitudes de ciclo XLAT2 de las
celdas que se cifran cada vuelta (el cuerpo salvo el `JMP`, más el trampolín).

**Q4 — controles negativos.**

- `ctrl_k_off`: la celda `D_1 + o_1` lleva `D_0 - n + o_1 + 1`. Debe romper el criterio
  (algún `JMP` que no cae en `T`) en las primeras 2 vueltas.
- `ctrl_no_dload`: las dos celdas X se sustituyen por un relleno inocuo (sin `DLOAD`).
  Debe romper el criterio: `d` deja de reiniciarse y la tabla constante no alcanza.
- `ctrl_block_v1`: la imagen `dload_block.mb` de `epoch_xlat2_block_v1` (histórica). Debe
  cerrar menos de 2 vueltas.

**Q5 — cargador de 1998.** Se prueba la imagen en `olmstead` y se declara el dialecto.

## Puertas

- **G0 — construcción.** Las celdas de dato salen de calcularlas en el probe desde los
  parámetros medidos; se comprueban leyendo los bytes de la imagen (las cuatro
  ecuaciones del punto fijo) y la imagen construida para `R = 60` y `R = 10 000` es
  **byte a byte la misma**. Los dos controles construidos fallan esa comprobación o el
  criterio de G2.
- **G1 — acuerdo de motores.** En la ejecución acotada de Q2: oráculo, intérprete
  independiente, scratch y runner C no paran antes del tope; el sha256 de la memoria
  final coincide en trazador, scratch e intérprete independiente; los destinos de JMP y
  `d` al empezar cada vuelta coinciden en trazador y scratch.
- **G2 — criterio de Q2.** **Si y sólo si**, en las `R = 10 000` vueltas: exactamente un
  `DLOAD` por vuelta, ningún opcode válido en el cuerpo salvo 40 y 4, todos los `JMP` en
  `T`, y `d` al empezar la vuelta toma exactamente 2 valores.
- **G3 — periodicidad.** Se encuentra un estado repetido dentro de las `R` vueltas, `d`
  tiene periodo 2 y el periodo del estado es el `P` predicho.
- **G4 — controles y cargador.** Los tres controles de Q4 rompen el criterio por el
  motivo declarado, y Q5 publica el resultado del cargador y la declaración de dialecto.

## Fuera de alcance

- Componer `DLOAD` con OUT/ROT/CRAZY en el mismo bucle (siguiente experimento).
- IN y una variante que pase el cargador de 1998.
- "Ilimitado" se demuestra sólo en el sentido de Q3 (estado repetido en un motor
  determinista, con acuerdo de motores en el tramo medido); no se ejecutan infinitos
  pasos.
- La memoria final del oráculo y del runner C no se compara: no la exponen.
