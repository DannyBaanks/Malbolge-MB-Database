# epoch_xlat2_phase_census_v1 — puertas pre-registradas

Se commitea **antes** de `probe.py` y de medir nada. Correcciones posteriores: sólo
como adición fechada al final, con el motivo.

Autor: claude_code_a029a379be0f4681, 2026-11-11.

## Contexto

`epoch_rearm_budget_v1` dejó `BLOCKED(REGRESS)`: restaurar el código del
resolvedor no cierra, porque el restaurador también se cifra. Quedan dos salidas
estructurales: celdas que no se cifran al ejecutarse (`JMP`, `END`) y celdas que
vuelven solas a su valor (ciclos de XLAT2). Este pack mide si la segunda salida
basta para construir un cuerpo de bucle de tamaño constante.

## Idea a medir: ventanas desfasadas

Un cuerpo que se ejecuta una vez por vuelta hace avanzar cada celda (salvo `JMP` y
`END`) un paso en su ciclo de XLAT2. Para una operación útil `X` y un ciclo de
longitud `L`, una **ventana desfasada** son `L` celdas consecutivas `c..c+L-1`,
cada una con un valor del mismo ciclo, elegidos de modo que **en cada vuelta
exactamente una** de ellas decodifique `X` y las otras `L-1` sean **inocuas**.
Entonces la ventana hace `X` una vez por vuelta, para siempre, con `L` celdas fijas.

- **Inocua** = decodifica `NOP` (68) o un opcode no válido (que el intérprete de
  Olmstead de 1998 y el oráculo del repo ejecutan como no-op).
- **Perjudicial** = cualquier opcode válido distinto de `NOP` cuando no es el turno
  de `X` (incluye `JMP`, `IN`, `END`, `OUT`, `ROT`, `CRAZY`, `DLOAD`).
- **Válida al cargar** = el valor inicial de cada celda decodifica un opcode válido
  en su posición (regla del cargador de 1998). La fase inicial de la ventana es la
  de la vuelta 0.

## Mediciones

- **Q1** estructura de XLAT2: miembros de cada ciclo; se espera un ciclo de cada
  longitud 2, 4, 5, 6, 9, 68 (`epoch_rearm_budget_v1` Q6), y se vuelve a medir.
- **Q2** para cada `X` en {`OUT`, `IN`, `ROT`, `DLOAD`, `CRAZY`}, cada ciclo y cada
  posición inicial `c` (mod 94): si existe una ventana desfasada. Se cuentan las
  posiciones factibles, también restringidas a ventanas válidas al cargar.
- **Q3** lo mismo para `JMP`, sólo como control: el `JMP` no se cifra al ejecutarse,
  así que no necesita ventana (se verifica en el intérprete que una celda `JMP`
  ejecutada conserva su valor).
- **Q4** comprobación ejecutada: para cada `(X, L)` con al menos una ventana,
  la ventana más chica se ejecuta en un intérprete (cuerpo = ventana + `JMP` de
  vuelta) durante `2·L` vueltas y se verifica que `X` ocurre exactamente una vez por
  vuelta, y que el programa no hace nada perjudicial.

## Puertas

**G0 REPRODUCCIÓN.** Q1 coincide con la Q6 de `epoch_rearm_budget_v1`. FALLA si
no.

**G1 SIN LITERALES.** Ningún conteo del VERDICT está escrito a mano en `probe.py`.

**G2 VEREDICTO.** Para cada `X` se reporta `WINDOW_EXISTS(L mínimo,
#posiciones)` o `NO_WINDOW`, y por separado la versión válida al cargar. Cualquier
resultado es válido; el pack PASA si cada veredicto sale de la enumeración
exhaustiva de Q2.

**G3 EJECUCIÓN.** Toda ventana reportada en Q2 que se ejecute en Q4 se comporta como
se predijo. FALLA si alguna predicción no coincide con la ejecución.

## NOT_DEMONSTRATED por diseño

- El resolvedor rediseñado: este pack sólo mide los bloques.
- El estado de `d` dentro del bucle (las ventanas `DLOAD` dicen dónde es posible
  cambiar `d`, no construyen el rutado).
