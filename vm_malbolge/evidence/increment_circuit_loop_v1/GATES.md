# Incremento por circuito ternario sin tabla

2026-11-12. Hipótesis: formar carry paralelo por trits mediante CRAZY/ROT permite calcular `x+1` para cada byte sin tabla de 256 entradas. Se implementará la fórmula como código Malbolge ejecutado dentro de un bucle, con scratch rearmado. El resultado 256 para entrada 255 debe salir como 00 por la semántica OUT módulo 256.

G0: álgebra exhaustiva x=0..255 y control negativo; paridad de orientación CRAZY. G1: imagen estricta autoinstalable que incrementa entradas repetidas y variables en una sola ejecución, con el mismo cuerpo, sin ayuda del host. G2: EOF autónomo sin salida extra. G3: comparación Python/BF/Olmstead/REA, batería de bytes y flujo de 10000 bytes, controles y reproducibilidad. G4: generación independiente BF→HeLL→Malbolge sin imagen objetivo precompilada. Pruebas y fallos se conservan en rutas nuevas; sin extrapolación de álgebra de host a imagen nativa.
