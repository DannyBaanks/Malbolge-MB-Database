# Cargador de 1998 y EOF: eco de referencia y límites de la composición

Puertas registradas en `8f36a7f` antes de medir; base del bucle compuesto `e42938d`. Hay una solución funcional de referencia que cubre ambos requisitos de forma observable, pero **aún no se ha adaptado el bucle compacto IN/DLOAD/OUT** para obtener esas propiedades. No son la misma imagen ni hay una composición de código demostrada entre ellas.

## Una referencia que sí carga y termina

Se copió, para poder reproducir la prueba, `Malbolge-PureEpoch/candidates/cat_real.mal` como `reference_cat.mb` (7 972 bytes, SHA-256 `0d298645bcabd8c832c6bbad0769124828a8805bb46cc4644e35added50334f1`). No fue construida en este experimento. El cargador del intérprete original de Ben Olmstead acepta sus 7 972 celdas; para las entradas vacía, `00`, `80 ff`, `00 0a 80 ff`, y `00..ff`, emite exactamente la entrada y sale con código 0. Además, con 10 000 bytes `(73*i+195)%256`, emite esos 10 000 bytes y termina con código 0. Las salidas binarias y errores crudos están en `attempt_02/raw/` y `long_raw/`.

Para los mismos 10 000 bytes scratch y el oráculo por defecto emiten el eco exacto y alcanzan `HALTED` al paso 4 077 806. El intérprete independiente y el oráculo con `stop_on_eof=True` emiten el mismo eco pero su host detiene la lectura en EOF al paso 4 077 531. El runner C también se detiene en ese paso (`HALTED`) y añade su salto de línea de framing a la salida cruda. Olmstead no expone contador de pasos. Por tanto coinciden los bytes visibles tras considerar el framing, pero **no** el mecanismo ni el paso de terminación: Olmstead, scratch y el oráculo por defecto dejan que la imagen procese EOF; los otros hosts terminan al leerlo.

Los casos vacía, un byte, mezcla y los 256 valores se contrastaron con los seis modos; el caso de dos bytes se contrastó con Olmstead y runner C. No se prueba para todas las entradas posibles. La imagen que se llama `reference_cat_bad_eof.mb` en el proyecto hermano salió con señal 11 (`rc=-11`) en la prueba de cuatro bytes, mientras la referencia normal terminó y emitió los cuatro. Es una diferencia de control, **no** evidencia suficiente para atribuir la señal específicamente a la lógica de EOF. El mutante `reference_cat_bad_loader.mb` altera la primera celda y el cargador lo rechaza con rc 1.

## Lo que falta en el bucle compacto

La imagen anterior `compose_inout.mb` tiene sólo 9/150 celdas aceptadas inicialmente por el cargador estricto. Sus pares usan 74 en ambas posiciones: en la primera vuelta IN decodifica `[23,27]`, DLOAD `[40,44]` y OUT `[5,9]`. El segundo valor de cada par no es una instrucción válida de carga. Además, el relleno de ese cuerpo se eligió para ejecutar opcodes inválidos, que el cargador también rechaza.

`pair_obstruction.py` enumera los 94² pares imprimibles de cada una de esas tres posiciones fijas. Tras exigir que ambos bytes sean válidos al cargar y que las dos celdas se visiten y cifren exactamente una vez por vuelta, no hay par que ejecute exactamente una operación objetivo en cada una de las primeras dos vueltas. Esto descarta el reemplazo directo de esos pares bajo esas hipótesis; **no demuestra imposibilidad de otra disposición, un prefijo que modifique el código, una tabla distinta ni otro mecanismo**. Adaptar el bucle puede requerir cambiar la construcción, no sólo sus bytes de fase.

En el bucle compacto, el runner C, el independiente y el oráculo con parada en EOF producen exactamente la entrada en los casos cortos y el host detiene la ejecución. Scratch y el oráculo por defecto continúan hasta el tope de 30 000 000 pasos. Por ejemplo, con `00 0a 80 ff`, ambos emiten el prefijo correcto y luego siguen: scratch emite `a8` por cada EOF (59048 mod 256), mientras el oráculo por defecto emite `ff` (-1 mod 256). El programa compacto no detecta EOF ni termina por sí mismo; las salidas largas crudas se conservan. Integrar una detección de EOF con la construcción compacta sigue **NOT_DEMONSTRATED**.

## Trazabilidad y límites

`attempt_02/results.json` y `long_results.json` describen los resultados, pasos, timeouts y hashes. El probe principal usa 30 000 000 pasos y 15 segundos por ejecución; la prueba larga usa 30 segundos por ejecución. `pair_obstruction.json` contiene la enumeración posterior, con las hipótesis indicadas arriba. No se modificaron los packs anteriores.

El primer intento del probe abortó por un `KeyError` en el resumen de impresión, después de generar algunos crudos; se conservan su programa y salidas parciales. Su `stdout.raw.txt` original contiene una ruta privada de la máquina y queda sólo como archivo local no comprometido, sin alterar; su SHA-256 se registra en el manifiesto. La segunda ejecución corrigió esa impresión y dejó todos sus resultados. El byte de framing del runner se comprueba exactamente; no se elimina a ciegas.

El manifiesto registra hashes de artefactos, dependencias, comandos, controles y alcance. La referencia demuestra una ruta disponible para eco binario con cargador histórico y EOF; conectar esas propiedades con la composición periódica compacta requiere investigación adicional.
