# Dos invocaciones del restaurador compartido: preregistro

2026-11-12. Base `4172c2e` (`shared_restore_one_v1`). Objetivo: en una sola
ejecución Malbolge estricta, (1) restaurar la celda T1 de 70 a 40 con las
primitivas compartidas ROT/MOVD/CRAZY, (2) rearmar dentro de Malbolge el reloj
de despacho y la constante de control, (3) invocar la misma composición sobre
una segunda celda T2 (también 70→40), y (4) detenerse. No construye el bucle
G5 completo, EOF ni restauración nativa a un valor arbitrario.

G0: imagen aceptada por Olmstead; ejecución autónoma sin I/O ni escrituras del
host. G1: traza scratch y ventana REA observan T1 `70→…→40`, luego rearme de
reloj `58→117` y constante `40→120`, luego T2 `70→…→40` y HALT; las ventanas
deben coincidir. G2: control que altere la constante o el rearme del reloj y
rompa el segundo objetivo; registrar si Olmstead sin instrumentar distingue el
control. G3: reproducir síntesis aislada y comparar hashes. G4: N>2
invocaciones, valores distintos de 40, autorrearme del despachador genérico y
EOF siguen NOT_DEMONSTRATED salvo evidencia nueva.
