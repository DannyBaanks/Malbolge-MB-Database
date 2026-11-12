# Iter-clock + two v4 body passes: preregistro

2026-11-12. Base `c8ba028`. Objetivo: dos iteraciones de restauración+ejecución
sobre celdas de cuerpo (patrón v4), luego un reloj de iteración en `pc≡2`
(valor 66) que hace NOP×3 y HALT; Olmstead rc=0. No construye R/R2 mutuo ni
EOF.

G0: loader estricto, HALT en HCLOCK, sin I/O. G1: TA y TB visitadas; HCLOCK
visitado 4 veces (66→62→76→79/HALT). G2: control (CRAZY omitido en H1) difiere
en la traza de TA. G3: síntesis aislada. G4: R/R2 mutuo, misma dirección tres
veces, bloque 48, EOF = NOT_DEMONSTRATED.
