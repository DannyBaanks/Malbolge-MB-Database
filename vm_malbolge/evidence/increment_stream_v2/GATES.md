# Incremento de longitud arbitraria: puertas preregistradas

2026-11-11. Base `3d26a95`. Meta: una imagen Classic que, en ejecución única y sin intervención del host, lea un stream arbitrario, emita cada byte incrementado módulo 256 y termine en EOF bajo Olmstead.

G0 Python/BF y oráculos ya medidos, revalidar si cambian. G1: bucle reutilizable con rearme exacto de tabla, scratch y código, varios bytes incluso repetidos y control negativo. G2: detección autónoma de EOF, sin bytes extra, incluyendo entrada vacía. G3: 10 000 bytes variables, `00..ff`, casos de longitud variable, Olmstead y modelo independiente; REA según semántica y cobertura disponible. G4: loader estricto, instalación ejecutada dentro de Malbolge y controles. No llamar bucle a una secuencia finita desenrollada. Si sólo se demuestra una pieza, conservarla como parcial, sin elevar las puertas generales.

Hipótesis auxiliar: el reset `crazy(crazy(29524,x), crazy(29524,x))=29524` y reconstrucción de máscaras desde C1 pueden restaurar scratch después de procesar un byte. Verificar orientación de operandos y ejecuciones reales; el rearme de scratch por sí solo no restaura el código ni demuestra EOF.
