# Incremento streaming: scratch rearmado y una celda de código reutilizada

Fecha de ejecución: 2026-11-11/12. Base `3d26a95`; puertas `da0101e`, enmienda `dab065c`. Los packs anteriores se conservan.

## Resultado

Se logró rearmar el scratch de cálculo dentro de Malbolge dos veces consecutivas, usando una tabla que también vuelve a su estado previo. Una imagen estricta de cuatro lecturas incrementó correctamente 512 vectores nativos. En un experimento independiente se ejecutó una **misma celda de código**, se restauró dentro de Malbolge tras el cifrado y se ejecutó de nuevo como `CRAZY` en la misma dirección.

**La longitud arbitraria y EOF limpio siguen `NOT_DEMONSTRATED`.** El programa de incremento tiene cuatro bloques desenrollados, no un bucle. El experimento de rearme de código sólo cubre una celda y no está integrado con el incremento.

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 referencias Python/BF | Conservadas del pack anterior | `byte_increment_v1/references.results.json`; no se cambió la especificación. |
| G1 bucle con tabla, scratch y código rearmados | PARTIAL | Cuatro lecturas con dos rearms de scratch y tabla; una celda de código separada rearmada y reejecutada. No hay bucle integrado. |
| G2 EOF autónomo | NOT_DEMONSTRATED | Entrada corta produce bytes extra o timeout. |
| G3 10 000 bytes | NOT_DEMONSTRATED | Las imágenes de incremento procesan exactamente 3 o 4 lecturas. |
| G4 loader e instalación | PASS para imágenes parciales | Celdas estrictas verificadas, arranque dentro de Malbolge, Olmstead rc=0 para entradas de la longitud admitida. |

## Scratch y tabla

`increment_three.mb` instala 1024 celdas y ejecuta tres lecturas. `verification_v2.results.json`: 512 tríos (256 repetidos y 256 variables) son exactos bajo Olmstead. En trazas de `00 00 00`, `ff ff ff` y `ABC`, el scratch y la tabla coinciden con su estado inicial antes de la tercera lectura. La primera versión `verify.py` midió por error una ventana de código desplazada una celda; se preserva y `verify_v2.py` corrige el rango a las 48 celdas exactas del segundo bloque.

`increment_four.mb` instala 1159 celdas y repite el rearme de scratch dos veces. `four_verification_v2.results.json`: 512 vectores de cuatro bytes exactos bajo Olmstead; trazas de `00000000`, `ffffffff` y `ABCD` comparan seis celdas de scratch y las 256 de tabla en cada lectura, sin diferencias. Se reutilizan los datos y scratch, mientras el código de cada bloque es distinto. Los controles eliminan una operación CRAZY del primer rearme: `ABCD` produce `42 43 0e 45`, pero los controles `00 00 00 00` y `ff ff ff ff` no detectan la alteración; se registran ambos hechos.

REA activo observó las imágenes con entradas completas: tres bytes `ABC→BCD` y `00 ff 80→01 00 81`; cuatro bytes `ABCD→BCDE` y `00 ff 80 fe→01 00 81 ff`. Estos replays paran antes de EOF y capturan sólo 64 eventos iniciales; no prueban EOF ni contienen los eventos finales de cálculo. Las evidencias completas originales se guardan en estado local privado, con hashes en el manifiesto.

La primera ejecución de `verify_four.py` terminó con timeout al probar EOF y dejó un traceback con rutas privadas. El original se conserva localmente con su hash; el pack incluye copia saneada. `verify_four_v2.py` captura ese caso explícitamente sin descartar los demás resultados. Con entrada vacía o `41` se agota el límite de 1 s; con `ABC` emite `42 43 44 1f`; con `ABCDE` sólo emite `42 43 44 45`.

## Una celda de código: ejecutar, rearmar, volver a ejecutar

El modelo `code_rearm_v2.results.json` observa el bloque de 48 instrucciones después de una ejecución: 29 celdas admiten restauración directa con CRAZY, 38 tras como máximo nueve ROT, y las 48 mediante un reinicio algebraico a 29524 seguido de CRAZY con un control calculado offline. Ese cálculo no es un plan ejecutable para las 48 celdas.

Se seleccionó la celda **PC 58550**, inicialmente `74` (opcode CRAZY), cuyo valor cifrado tras ejecución es `70`. `revisit_positive.mb` instala estado, ejecuta esa celda, recupera su valor en ejecución y vuelve a ella:

| Paso | Evento observado por REA y scratch |
| --- | --- |
| 3817 | Ejecuta CRAZY en PC 58550; cifrado `74→70`. |
| 3822 y 3825 | CRAZY rearmador `70→60→29524`. |
| 3850 | CRAZY con control preparado `29524→74`. |
| 3856 | Vuelve a ejecutar CRAZY en PC 58550; cifrado `74→70`. |
| 3858 | HALT. |

`revisit_control.mb` elimina un CRAZY del rearme: el valor pasa `70→60→33` y la segunda visita decodifica opcode 21, no CRAZY. REA y scratch coinciden en pasos, visitas y escrituras para positivo y control; REA capturó la ejecución completa sin truncamiento. Olmstead ejecutó ambas imágenes y retornó rc=0, sin salida; esa ejecución nativa sin instrumentación no distingue por sí sola las visitas internas. `revisit_verification.results.json` conserva las diferencias y controles.

El control y su valor 29561 se instalaron previamente desde el plan Malbolge; no se ha demostrado generar o seleccionar automáticamente los controles para 48 celdas, mantener el planificador de rearme, ni restaurar la rutina de rearme a sí misma. La ejecución de una celda dos veces **no** establece que el bloque completo pueda repetirse indefinidamente.

## Integridad y reproducción

Se repitieron en un árbol aislado la síntesis de cuatro lecturas y la prueba de reejecución: imagen y plan son byte a byte iguales (`reproduction.results.json`). Se verificó nuevamente la paridad de memoria de CRAZY (`parity.results.json`); la orientación es `crazy(acumulador,celda)=tabla[celda][acumulador]`. La guía usa la imagen de cuatro lecturas. Los scripts que escriben resultados deben ejecutarse en una copia aislada nueva.

## NOT_DEMONSTRATED

- Restaurar y volver a ejecutar las 48 instrucciones del bloque completo, incluyendo la propia rutina de rearme.
- Integrar ese rearme con detección EOF y la tabla en un único bucle de incremento.
- Eco transformado para cualquier longitud, incluidos 10 000 bytes, y parada limpia en EOF.
- Compilación general desde BF o equivalencia de estado entre lenguajes.
