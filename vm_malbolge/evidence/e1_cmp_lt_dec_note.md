E1 2026-11-06: segunda subrutina de decremento implementada (bloque autonomo,
equilibrado) + compare con alternancia B/A. ENSAMBLA a 33.453 B (margen 25.596).
Rejilla 100 vectores: 0/100 PASS, 0/100 acuerdo entre motores.
Causa restante: la transferencia A -> value2 no ocurre. `R_FLAG_D2_VAL8;
MOVED crazy_value2` arma una bandera y mueve el puntero de datos, pero NO
copia el contenido de value a value2: la maquinaria U_CRAZY calcula el
contenido de value2 desde su propia celda crazy, no desde value.
