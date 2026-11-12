# Eco binario con EOF: comparación y límites

Fecha 2026-11-11. Gates preregistradas en `370cb73`, base `84e83e0`.

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 BF con bucle y EOF binario explícito | PASS | `echo.bf`, `bf16.py`, `tests.stdout.raw.txt` |
| G1 salidas de Python/BF/Olmstead | PASS para los cinco casos | `results.json`, `probe.stdout.raw.txt` |
| G2 controles negativos | PASS en el alcance indicado | `results.json`, `tests.stdout.raw.txt` |
| G3 REA observa el comportamiento | PARTIAL | `rea_trace.redacted.json`, `rea_summary.json` |
| G4 EOF autónomo en la candidata relocalizada | NOT_DEMONSTRATED | La candidata de `unieco_strict_relocation_v1` no fue modificada. |

Python copia bloques hasta EOF. El programa BF `,+[-.,+]` usa celdas de 16 bits que desbordan modularmente; la entrada asigna 65535 al EOF y la salida emite el byte bajo. Una lectura válida más uno da 1..256; EOF más uno da cero. De ese modo NUL no se confunde con EOF. `bf16.py` implementa BF, no afirma que esa convención de EOF sea universal.

Con vacío, NUL, `00 0a 80 ff`, todos los bytes 0..255 y 10 000 bytes, Python, BF16 y Olmstead con `reference_cat_functional.mb` producen exactamente la entrada y terminan con código 0. Los datos y la salida están en hex en `results.json`. Se probaron además los 256 bytes individualmente y casos mal formados en `test_bf16.py`. El control de EOF equivocado BF=0 no termina dentro de 100 pasos y emite bytes; el control de pérdida de OUT y un byte de salida invertido son detectados.

Son tres construcciones distintas: **no existe aquí una traducción demostrada de ese BF a la imagen Malbolge**. La imagen deriva del pack anterior y conserva SHA-256 `0d298645bcabd8c832c6bbad0769124828a8805bb46cc4644e35added50334f1`. Las pruebas son finitas y el CLI BF carga toda la entrada antes de ejecutarse; no se afirma equivalencia temporal de streaming interactivo.

## Qué reveló REA

Para la misma imagen con entrada `A`, Olmstead da `41` y termina. `trace_malbolge` de REA 6.5.0 (evidence ID en `rea_summary.json`) agotó 30 000 pasos y produjo `41` seguido de bytes `54`. En el código fuente local de REA, `src/domain/malbolge/malbolgeClassic.ts`, el `IN` agotado asigna `-1`; Olmstead usa la palabra de diez trits 59048. Son semánticas distintas para este experimento. El replay REA no prueba halt bajo Olmstead y no es una medición de silicio. La evidencia completa se guarda localmente fuera del repo; su digest y copia saneada están en el pack. Los eventos están truncados a 128.

## Pista constructiva para el bucle

En `algebra.results.json` se verifica para los 256 bytes que `crazy(crazy(59048, value), 29524)` es cero en EOF y distinto de cero en todos los bytes, usando la orientación `crazy(acumulador, celda)` del motor scratch. Hay 256 resultados distintos entre los bytes. Esta fórmula está documentada por `Malbolge-PureEpoch/tools/cat_real.py`: es un discriminador existente, no una invención ni una prueba de que esté instalado en la candidata. Los trits que individualmente distinguen EOF de todos los bytes son **5, 6, 7, 8 y 9**; esto corrige la afirmación 6..9 del veredicto previo. El promedio de operaciones por celda del pack anterior es una estimación, no una cota superior demostrada de 1060 celdas.

`reference_footprint.py` traza la imagen de referencia desde la primera lectura para la entrada `00 ff` y EOF, con 36 posiciones de código ejecutadas y 107 posiciones de datos accedidas en esta corrida. Es una observación acotada de un modelo, no un conjunto exhaustivo para cualquier entrada ni un plan de relocalización. La primera lectura ocurre en PC 7657, con D=58975; las siguientes en los pasos 7938 y 8345, la última con EOF=59048. La ejecución del modelo finaliza en 8620 pasos y salida `00ff`.

## NOT_DEMONSTRATED

- Compilar este BF a Malbolge o reproducir su estado de cinta en Malbolge.
- Instalar el discriminador en la candidata relocalizada, preservar el byte y rearmar su estado entre vueltas.
- Halt limpio en EOF de la candidata `candidate.mb` previa. El control histórico mostró bytes extra.
- Equivalencia general para todos los streams o equivalencia de estado paso a paso entre Python, BF y Malbolge.
- Un límite máximo matemático de celdas para toda variante futura.

## Reproducción

Los scripts escriben resultados en su propia carpeta: copiarlos a una **ruta nueva y aislada**, conservando el árbol relativo que conecta `vm_malbolge/evidence/epoch_dload_compose_v1`, `unieco_strict_relocation_v1` y el repo hermano `Malbolge-PureEpoch`. No ejecutarlos sobre este pack sellado. En una copia aislada se repitieron `probe.py` y `algebra.py`: resultados JSON idénticos a los almacenados. El resultado de REA es una ejecución delimitada, no una prueba de repetibilidad temporal idéntica.
