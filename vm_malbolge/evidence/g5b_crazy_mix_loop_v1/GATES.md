# G5b-1a: bucle nativo de mezcla crazy con parada EOF — preregistro

2026-11-15. Base `cb3410e` (lemas L1/L2 de `g5b_orbit_lemmas_v1`). Imagen
Malbolge Classic **híbrida nativa**: preámbulo BolgeForge solo para celdas de
datos/punteros por encima de la imagen; el bloque de código vive dentro de la
imagen (relleno tras el preámbulo) con instrucciones activas en órbita 70↔74,
recorrido dos veces por iteración (fase activa + fase NOP). Sin HeLL/LMAO en
la construcción. Función: por cada byte `x`, emitir
`crazy(crazy(57590, crazy(x,29524)), KEY) mod 256`; HALT autónomo en EOF.
Álgebra: `algebra.py` (rama AAADA, reinicios exhaustivos).

- G0 (álgebra, host): todos los bytes → 57590, EOF → 58319; reinicios de
  Z/C2/C3/C5/K correctos para las 59 049 palabras. *Ya medido antes de la
  imagen; se registra aquí.*
- G1 (nativo): cargador estricto (todas las celdas ∈ `ji*p</vo`). Olmstead:
  entrada vacía → 0 bytes, rc 0; `00..ff` → 256 bytes = modelo de `algebra.py`,
  rc 0; 10 000 bytes pseudoaleatorios, 1 000×`00`, 1 000×`ff` → salida exacta y
  rc 0 (HALT por la propia imagen, no por el host).
- G2 (traza): trazador scratch y vendor instrumentado: cada celda activa
  ejecuta su opcode en la pasada 1 y NOP en la pasada 2 de cada iteración, en
  la misma dirección; ninguna celda JMP cambia; en cada visita a IN las celdas
  de datos valen su valor inicial.
- G3 (controles): (a) IN en fase invertida; (b) omitir el CRAZY final del
  reinicio de K; (c) C5 alterada (rama EOF rota). Cada uno debe divergir del
  positivo en Olmstead; registrar cómo.
- G4: síntesis repetida en directorio aislado idéntica byte a byte.
- G5 (testigo externo, posterior): misma función compilada por HeLL/LMAO con
  salida idéntica. NOT_DEMONSTRATED hasta hacerlo.
- Fuera de alcance: XOR real (G5b-1b), compilador BF, claves arbitrarias en
  tiempo de ejecución.
