# Rediseño de disposición R/R2: resultado y límite

2026-11-12, base MALBOLGE-MB-DATABASE `4865408`. Se separaron las secuencias de instrucciones de sus bancos de datos y se corrigió la celda de parada: en PC 58376 el valor 79 decodifica HALT; 66 decodificaba NOP. Cada salida de síntesis exige ahora un directorio vacío para preservar evidencia.

| Puerta | Resultado observado |
| --- | --- |
| G0 | La imagen positiva termina sin salida ni error en Olmstead (rc 0); traza independiente: HALT en paso 4669. |
| G1 | R se visita dos veces con opcode JMP; hay escrituras hacia R y R2. **Rearme mutuo después de ejecución: NOT_DEMONSTRATED.** |
| G2 | Se sustituye el último CRAZY de rearme de R por NOP. La traza llega a R con valor 29524, no ejecutable; Olmstead queda ejecutándose hasta el timeout de 10 s. |
| G3 | Dos síntesis aisladas producen imágenes, objetivos y planes idénticos byte a byte; ver `reproduction.json`. |
| G4 | Cuerpo de trabajo B, N≥3 y EOF: NOT_DEMONSTRATED. |

## Por qué G1 no demuestra rearme mutuo

En el intérprete original, JMP asigna `c = mem[d]` antes de cifrar `mem[c]`, y luego incrementa `c`. Así se cifra la celda anterior al destino efectivo, no el JMP recién ejecutado. En la traza positiva, R vale 38 antes y después de su primera visita; el sled la cambia expresamente `38 → 2 → 29524 → 38`. R2 se procesa `82 → 0 → 29524 → 82` antes de su primera visita. Por tanto se demuestra una restauración inducida y una segunda visita, no la necesidad de restaurar dos instrucciones que se autocifraron. Tampoco se demuestra un bucle reutilizable: los sleds son privados y de una sola pasada, y el HALT está prefijado, no es un reloj iterativo.

La traza scratch y Olmstead son comprobaciones diferentes: Olmstead no expone los registros; su rc 0 corrobora la terminación del positivo. El control entra en un PC no imprimible en la traza, mientras el Olmstead original hace `continue` en esa condición; por eso se registra timeout, no HALT ni rechazo. No hay traza REA independiente en este intento.

## Reproducción

Desde la raíz del repositorio, elija una ruta que no exista y capture la salida fuera de ella:

```sh
RR_OUTPUT_DIR=/tmp/rr-repro-NUEVO python3 vm_malbolge/evidence/g5_rr_min_v1/synthesize.py
python3 vm_malbolge/evidence/g5_rr_min_v1/verify_redesign.py /tmp/rr-repro-NUEVO
```

La síntesis usa `../BolgeForge` y la verificación usa `../Malbolge-PureEpoch/build/olmstead`; sus versiones y hashes relevantes están en `manifest.json`. El trazador compara estrictamente la carga y exige las visitas, el HALT y el control. El siguiente diseño debe usar celdas que efectivamente se modifiquen al ejecutarse o demostrar que el rearme de JMP es innecesario y rediseñar el despacho; no debe presentar esta imagen como bucle general.
