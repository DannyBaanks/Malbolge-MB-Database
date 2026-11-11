# epoch_rearm_budget_v1 — puertas pre-registradas

Este archivo se commitea **antes** de escribir `probe.py` y de medir nada. Las
puertas no se ajustan después de ver los resultados; cualquier corrección va como
adición fechada al final, con el motivo, sin borrar esta versión.

Autor: claude_code_a029a379be0f4681, 2026-11-11.

## Pregunta

¿Puede `epoch_resolver_epoch_select_v1/resolver_epoch.mb` (340 B) volver a quedar
listo para una **segunda petición** dentro de la misma ejecución? Este pack **no
construye** el bucle: mide el presupuesto de la restauración con los mecanismos ya
demostrados (`epoch_rearm_cost_v1`: carga de palabra con `ROT` + un `CRAZY`;
restore exacto con un `CRAZY`; rearm de dato a 29524) y nombra la restricción que
manda.

## Dialecto declarado

Classic permisivo (3^10), igual que los packs que mide. El resolvedor no carga en
el intérprete de Olmstead de 1998 (`epoch_audit_v1`, H3); el pack no lo cambia.

## Definiciones

- **Cuerpo** = el conjunto de celdas de código que ejecuta el resolvedor en una
  petición, sacado de la traza (se espera ~218, `epoch_audit_v1` H8; el número se
  vuelve a medir aquí, no se copia).
- **Estado sucio** = toda celda cuyo valor al terminar la petición difiere del de la
  imagen (código cifrado + datos escritos), comparando la memoria inicial con la
  final en la traza.
- **Vía A (un CRAZY)**: existe `ctrl` con `crazy(ctrl, sucio) = original`.
- **Vía B (dos pasos)**: rearm a 29524 y escritura exacta con
  `crazy(swap01(original), 29524)`.
- **Alcanzable**: una palabra que se puede dejar en `a` con `ROT`^i de una celda
  sembrada (i = 1..10), o con eso seguido de un `CRAZY` contra otra celda sembrada
  rotada `j` veces (j = 0..9).
- **Direccionable**: una celda a la que `d` puede llegar. Un `DLOAD` deja `d` en
  `mem[d] + 1`; con un valor sembrado (imprimible) eso da como máximo 127. Por
  encima, `d` sólo llega avanzando +1 por instrucción o leyendo una palabra escrita
  en runtime.

## Mediciones

- **Q1** tamaño del cuerpo y del estado sucio (desde la traza, varias peticiones).
- **Q2** por cada celda sucia: si se restaura por la vía A, por la vía B o por
  ninguna, con la palabra de control alcanzable de menor coste en `ROT`s.
- **Q3** coste agregado mínimo (instrucciones de carga + `CRAZY`s de restore), sin
  contar rutado de `d`, y el número de celdas auxiliares consumidas.
- **Q4** direccionamiento: cuántas celdas sucias quedan por encima de 127 y el coste
  mínimo de llevar `d` hasta ellas.
- **Q5** regresión: el código restaurador también se cifra al ejecutarse. Se mide si
  su tamaño (cota inferior por Q3) es menor que el cuerpo que restaura.
- **Q6** alternativa sin restore: la estructura de ciclos de la permutación XLAT2 y,
  para cada celda del cuerpo, cuántas ejecuciones tarda en volver a su valor
  original (la vía de ciclos que usa PureEpoch). Se reporta el mcm de esas
  longitudes.

## Puertas

**G0 REPRODUCCIÓN.** El resolvedor se ejecuta con el trazador del pack y con el
intérprete independiente de `epoch_audit_v1` y ambos dan la misma salida, pasos y
estado en las 7 instancias del pack original. FALLA si difieren.

**G1 SIN LITERALES.** `probe.py` no contiene tamaños de cuerpo, conteos ni
resultados escritos a mano; todo número del VERDICT sale de `results.json`.

**G2 VEREDICTO DE FACTIBILIDAD.** El probe emite exactamente uno de estos:

- `FEASIBLE_BUDGET` si toda celda sucia se restaura por A o B, el coste de Q3 más el
  de Q4 cabe en 59049 celdas, y el restaurador de Q5 es más chico que el cuerpo;
- `BLOCKED(<restricción>)` nombrando la primera que falle en ese orden
  (`RESTORE`, `MEMORY`, `ADDRESSING`, `REGRESS`).

Cualquiera de los dos es un resultado válido; el pack PASA si el veredicto está
justificado con los números de Q1–Q5.

**G3 CONTROL.** Se cuenta también un control trivial: el estado sucio de una
petición con byte de época fuera de catálogo (b = 50); su presupuesto se reporta
aparte y no entra en el veredicto.

## NOT_DEMONSTRATED por diseño

- El bucle construido (este pack no ejecuta una segunda petición).
- El rutado completo de `d`: Q4 es una cota inferior.
