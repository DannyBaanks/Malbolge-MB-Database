# Tres invocaciones del restaurador compartido: preregistro

2026-11-12. Base `3947d79` (`shared_restore_two_v1`). Objetivo: en una sola
ejecución Malbolge estricta, restaurar T1, T2 y T3 (cada una 70→40) con las
primitivas compartidas ROT/MOVD/CRAZY, usando relojes auxiliares distintos y
desvíos nativos call1→call2→call3, sin puente host. No construye el bucle G5
R/R2, EOF ni restauración a un valor arbitrario.

G0: imagen aceptada por Olmstead; ejecución autónoma sin I/O ni escrituras del
host. G1: scratch observa T1, T2 y T3 `70→…→40` y HALT en CLOCK3; ventanas
alineadas. G2: control con constantes alteradas → T1=T2=T3=39. G3: síntesis
aislada + hashes. G4: bucle R/R2 autorrearmable, rearme in-place del mismo
reloj, valores ≠40 y EOF siguen NOT_DEMONSTRATED.
