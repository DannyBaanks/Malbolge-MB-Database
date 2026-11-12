# Rearme de una celda con primitivas compartidas: preregistro

2026-11-12. Base `c364fa9`. Objetivo: en una sola ejecución Malbolge estricta, combinar celdas compartidas ROT/NOP, MOVD/NOP y CRAZY/NOP para transformar la celda de dato T desde 70 al valor objetivo 40, y detenerse. El valor 40 es elegido por la ruta de cuatro fases: `crazy(q,q)=40` con q de trits 0/1; no implica restauración de un valor arbitrario.

G0: imagen aceptada por Olmstead y ejecución autónoma sin I/O ni escrituras del host. G1: traza scratch y ventana REA observan el estado inicial T=70, el camino CRAZY a 29524, las primitivas compartidas y T=40 al HALT; las ventanas deben coincidir. G2: control de constante alterada o fase alterada rompe el valor objetivo; registrar si Olmstead sin instrumentar distingue el control. G3: reproducir síntesis aislada y comparar hashes. G4: generalización a celdas arbitrarias, múltiples destinos, autorrearme del despachador y EOF siguen NOT_DEMONSTRATED salvo evidencia nueva.
