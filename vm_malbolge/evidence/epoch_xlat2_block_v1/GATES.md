# epoch_xlat2_block_v1 — puertas pre-registradas

Se commitea **antes** de `probe.py` y de medir nada. Correcciones posteriores: sólo
como adición fechada al final, con el motivo.

Autor: opencode_engine_1794376200_block (handoff de claude_code_a029a379be0f4681,
bridge seq 11995/11996, pedido de Danny), 2026-11-11. Base: MALBOLGE-MB-DATABASE
`bb4e204`, local sin push. GATES.md del censo sigue en `cb6bfd1` (intacto).

## Contexto

`epoch_xlat2_phase_census_v1` (dc7ae64) midió el censo con la definición de ventana
de sus puertas: `L` celdas **consecutivas**. La corrección posterior de su VERDICT
(commit `bb4e204`) y `epoch_audit_v1/relaxed_window_check.py` mostraron que la
contigüidad era de las puertas, no de Classic: quitándola, y con una celda de
relleno inocua (existe en las 94 posiciones), hay un bloque fijo de 5 celdas por
operación sobre el ciclo de longitud 2 (dos celdas del ciclo desfasadas + 3 de
relleno) que, según el cálculo, ejecuta la operación exactamente una vez por vuelta.
Ese cálculo **no ejecutó ninguna imagen**. Este pack la construye y la ejecuta.

## Idea a medir: el bloque de 5 celdas

Para una operación `X` y el ciclo de XLAT2 de longitud 2, un **bloque** son 5 celdas:

- dos celdas `X1`, `X2` con valores del ciclo de longitud 2, en posiciones separadas,
  de modo que **exactamente una** decodifique `X` en cada vuelta;
- tres celdas de relleno entre ellas, cada una con un valor cuyo ciclo XLAT2 decodifica
  sólo opcodes inocuos (NOP 68 u opcode no válido) en **todas** sus vueltas.

El bloque va dentro de un bucle cerrado por `JMP`: la celda `JMP` no se cifra al
ejecutarse, así que el bucle no degrada su propia instrucción. El `JMP` salta a un
trampolín justo antes del bloque; el destino lo da una tabla de celdas que apuntan al
trampolín, porque `d` avanza una celda por instrucción ejecutada.

- **Inocuo** = decodifica `NOP` (68) o un opcode no válido. `HARMLESS` = los 86
  opcodes que no son ninguno de `{JMP 4, OUT 5, IN 23, ROT 39, DLOAD 40, CRAZY 62,
  NOP 68, END 81}`.
- **Vuelta** = una pasada por las 5 celdas del bloque más el `JMP`.
- **Perjudicial** (en el cuerpo del bucle) = cualquier opcode válido distinto del
  opcode objetivo y del `JMP`. `IN` y `END` son perjudiciales: consumen stdin o paran.

## Dialecto y motores

Dialecto: Classic 3^10. Motores: oráculo del repo (`tools/oracle_classic.py`),
intérprete independiente (`vm_malbolge/evidence/epoch_audit_v1/indep_interpreter.py`),
un trazador local con la misma semántica, el runner C
(`runners/malbolge-original/malbolge`, stdin cerrado) y Olmstead 1998
(`Malbolge-PureEpoch/build/olmstead`) como cargador/tercer motor. El runner C
caracterizado en `c_printable_guard_v1`: variante RESTRINGIDA que para cuando la
celda a decodificar no es imprimible.

## Preguntas

**Q1 — construcción del bloque.** Para cada objetivo de {OUT, IN, ROT, DLOAD, CRAZY}:
posiciones de las dos celdas `X` (módulo 94), valores iniciales, ciclo de relleno y
valores de las tres celdas de relleno, posición del trampolín, del `JMP` y rango de
la tabla de destinos. Q1 no verifica ejecución: sólo fija los datos que el probe
calcula.

**Q2 — OUT construido y ejecutado.** El bloque de OUT corre dentro del bucle cerrado
por `JMP` durante `R = 60` vueltas. Se mide, por vuelta, el número de ejecuciones del
opcode `5` (`OUT`) y el conjunto de opcodes válidos decodificados en las posiciones
del cuerpo del bucle.

**Q3 — controles negativos.**

- control `desfase`: la segunda celda `X` se siembra en la otra fase del ciclo de
  longitud 2. El criterio de Q2 debe romper (una vuelta con 2 o con 0 ejecuciones);
- control `relleno_no_inocuo`: una celda de relleno se siembra con un valor que
  decodifica un opcode válido no inocuo (`39`, `ROT`) en su posición. El criterio de
  Q2 debe romper por el opcode perjudicial, aunque el recuento de `OUT` por vuelta
  parezca correcto.

**Q4 — ROT, CRAZY y DLOAD.** Para cada uno: se construye el bloque análogo y se mide
(1) el número de ejecuciones del opcode objetivo por vuelta, (2) los opcodes válidos
del cuerpo del bucle, y (3) el valor del puntero `d` al ejecutarse la celda objetivo,
separado por vueltas pares e impares. El resultado (construido o NO construido) es lo
que mida la medición, no está prefijado aquí.

**Q5 — cargador de Olmstead 1998.** Se prueba la imagen del bloque en el cargador
(`olmstead`, stdin cerrado) y se declara el dialecto de la imagen: si pasa, Classic
permisivo compatible con el cargador de 1998; si no pasa, Classic permisivo que usa
opcodes no válidos como relleno inocuo (el cargador de 1998 exige un opcode válido en
todas las celdas cargadas).

## Puertas

- **G0 — reproducibilidad de Q1.** Las posiciones, valores, ciclos de relleno y rangos
  de Q1 salen de calcularlos en el probe; la construcción no lee tablas escritas a
  mano. `G0` es verdadero si el probe reconstruye el bloque desde el cálculo.
- **G1 — acuerdo de motores (Q2).** El oráculo, el intérprete independiente y el
  trazador local coinciden byte a byte en la salida y los pasos ala ejecución
  acotada (parando en la vuelta `R`-ésima), y el runner C coincide en los bytes de
  `OUT` (él añade un `\n` final). `G1` es verdadero si no hay discrepancia.
- **G2 — criterio de Q2.** `G2` es verdadero **si y sólo si**: exactamente una
  ejecución del opcode objetivo en cada una de las `R` vueltas, y ningún opcode
  perjudicial en el cuerpo del bucle. Los dos controles de Q3 deben romper ese
  criterio; el desglose por tolerancia no es una salida.
- **G3 — controles (Q3).** `G3` es verdadero si los dos controles fallan el criterio
  de Q2 por el motivo declarado (recuento 2/0 para el control de desfase; opcode
  `39` en el cuerpo para el de relleno no inocuo).
- **G4 — Q4 y Q5.** `G4` es verdadero si, para cada uno de ROT, CRAZY y DLOAD, el
  probe publica la medición pedida (recuento por vuelta, opcodes del cuerpo, `d` en
  vueltas pares/impares) y el resultado declarado es el medido; y si Q5 publica el
  resultado del cargador de Olmstead 1998 y la declaración de dialecto.

## Fuera de alcance

- Elzor de armar estos bloques en un programa que haga otra cosa (los bloques emiten
  la operación, no calculan un payload elegido por petición).
- Cualquier ventana/cuerpo más grande que el tramo medido `R = 60`: la tabla de
  destinos es finita y el probe lo declara.
