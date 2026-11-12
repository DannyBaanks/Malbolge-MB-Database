# Movimiento de cinta Brainfuck (> y <) sobre memoria desacoplada en Malbolge Classic

2026-11-12. Hipótesis: El direccionamiento multi-celda en Malbolge permite implementar el movimiento de puntero de cinta de Brainfuck (`>` y `<`) preservando celdas de almacenamiento independientes (`cell0` y `cell1`) sin interferencia destructiva, ejecutando un bucle de intercambio continuo de pares y finalizando limpiamente ante EOF bajo la semántica canónica de Olmstead (59048).

G0 (Álgebra y control negativo anti-fake): Demostración analítica y oráculo de que 2 celdas independientes producen intercambio ordenado (`BA`), mientras que un modelo de celda única (sin movimiento de cinta real) colapsa y falla en el 100% de los 256 pares distintos emitiendo `BB`.

G1 (Imagen estricta autoinstalable): Síntesis de imagen ejecutable en el cargador estricto (`ji*p</vo`), donde la mutación deliberada de un opcode en el instalador provoca rechazo inmediato por el cargador.

G2 (EOF autónomo limpio): Finalización con rc=0 sin bytes espurios para entradas vacías, secuencias impares (descarte exacto del byte incompleto según semántica BF) y flujos masivos.

G3 (Tortura adversarial y verificación cruzada BF16/Olmstead): Flujo masivo de 10.000 bytes (5.000 pares aleatorios), tormenta NUL, tormenta 0xFF, secuencia completa 0..255 y 256 pares individuales, con coincidencia exacta bit a bit contra el intérprete BF16 canónico del repositorio (`vm_malbolge/evidence/unieco_rea_eof_v2/bf16.py`).

G4 (Compilador reproducible especializado): Herramienta `vm_malbolge/tools/tape_bf/compile.py` que toma el código Brainfuck `,>,+[-.<.,>,+]`, genera HeLL, extrae la disposición con LMAO y sintetiza la imagen sin copiar plantillas prefabricadas.
