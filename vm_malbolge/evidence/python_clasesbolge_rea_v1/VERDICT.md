# Python → Brainfuck → Malbolge → REA: comparación acotada

Base `2f0d829`. Puertas originales en `c6b6dc8`; ampliación BF en `2a3d983`, registrada después de crear la referencia, la imagen Malbolge y las primeras capturas REA. Por ello **las comparaciones BF son exploratorias respecto de esa construcción previa**, no una validación ciega pre-registrada de ella.

## La prueba que sí funciona

`reference.py` copia hasta cuatro bytes y termina antes si encuentra EOF. El programa BF `,.,.,.,.` realiza cuatro pares lectura/escritura. `bf_fragment.py` implementa sólo repeticiones completas de `,.` sobre bytes, con EOF=0, y traduce ese patrón especializado a pares Malbolge IN/OUT más HALT. Rechaza otros patrones: no es un intérprete ni compilador general de BF.

La codificación usa la ecuación de Clasesbolge `33+((op-c-33)%94)`. La imagen resultante `echo4.mb` contiene nueve bytes (`ubs` seguido de acento grave y `q^o\\I`; ver `encoding.json` para bytes exactos), todos imprimibles y válidos para el cargador estricto. Ejecuta IN/OUT cuatro veces y HALT. El Olmstead de 1998 la aceptó y ejecutó.

Se probaron 256 vectores de cuatro bytes, construidos como `[i,(i+1)%256,(i*73)%256,255-i]`. Python en proceso separado, el ejecutor BF binario acotado y Olmstead produjeron exactamente cada vector, con retorno 0 en los procesos. Esto cubre cada valor de byte en esa batería, no todas las secuencias posibles de cuatro bytes. `full_inputs.raw`, `full_python.raw`, `full_bf.raw` y `full_olmstead.raw` son idénticos byte por byte; `results.json` registra cada caso. Con cinco bytes los tres emiten sólo los primeros cuatro. El control que cambia el primer OUT por NOP es aceptado por Olmstead y, con `Ab9!`, devuelve `b9!`; no satisface el contrato.

El intérprete BF existente de `workspace/assembly/brainfuck/brainfuck_interpreter.py` coincidió con el fragmento para vacío, ASCII, NUL y entrada corta. Su API recibe texto y lo codifica en UTF-8; por eso la batería binaria completa usa el ejecutor acotado y no se atribuye a ese intérprete una prueba binaria de 256 valores. El CLI de `bf_fragment.py` lee todo stdin antes de ejecutar, mientras que el Python de referencia lee hasta cuatro bytes: la comparación demuestra la salida acotada, no equivalencia de consumo o temporización de streams interactivos.

## REA, paso por paso

Para `Ab9!`, REA capturó como procesos el Python de referencia y el ejecutor BF, que imprimieron el mismo resultado en hex `41623921`; el replay de Malbolge de REA emitió los mismos cuatro bytes y terminó en 9 pasos. `bf_trace.py` emite su propia traza de ocho comandos BF; REA captura ese proceso, no instrumenta de forma independiente el intérprete BF. La traza Malbolge de REA muestra las cuatro parejas IN/OUT y que el acumulador antes de cada OUT coincide con la celda BF tras su lectura; `rea_step_compare.results.json` registra el cotejo. REA también reprodujo el vector binario `00 41 ff 0a` y devolvió esos cuatro bytes.

El control OUT→NOP devuelve `b9!` también en REA. Para una entrada de tres bytes, la llamada `trace_malbolge` devolvió un **error de validación de la herramienta**: un elemento negativo no cumplía el esquema de `output_bytes`. No se interpreta ese error como una salida válida ni como prueba del comportamiento nativo; se preserva la respuesta. REA Python/BF son capturas de procesos con wrappers que imprimen hex; el Malbolge es replay acotado en proceso. Ninguna de estas capturas es medición eléctrica ni demuestra instrucciones nativas idénticas.

## EOF: diferencia real, no equivalencia

Con entrada `Ab9`, las salidas medidas son:

| Implementación | Salida hex | Motivo |
|---|---|---|
| Python | `41 62 39` | detiene el bucle al leer EOF |
| BF de ensamblaje y fragmento BF | `41 62 39 00` | su contrato de EOF escribe cero |
| Olmstead 1998 | `41 62 39 a8` | EOF asigna 59048; OUT emite su byte bajo |
| AutoBolge dense Classic | `41 62 39` | el host detiene la ejecución por input underflow |

Así que la traducción **no preserva la semántica BF en EOF**, ni resuelve el eco de longitud arbitraria. En entrada vacía se observan respectivamente vacío, cuatro ceros y cuatro `a8` para Python, BF y Olmstead. Las políticas EOF dependen del ejecutor; no se supone una regla universal de Brainfuck.

## Qué aportan PureEpoch, BolgeForge y AutoBolge

- **PureEpoch:** `tools/boss2_brainfuck.py` compila un subconjunto lineal `><+-.` con puntero/cinta calculados en Python al compilar. En la prueba actual rechaza `,.`, `[.,]` y `+[-].` con `NotImplementedError`; no compiló nuestra imagen y no demuestra BF completo. Sus mecanismos de almacenamiento y el cat estricto previo son referencias separadas.
- **BolgeForge:** `tools/resynthesize.py` contiene `find_a_for_crazy` y `solve_sp`, usados por su planificador de preámbulos. Se extrajo mediante AST sólo la función pura y su tabla, sin importar el módulo que compila/escribe su solver C. Sobre las 84 diferencias de estado de UNIECO coincidió con nuestro cálculo para las 84, incluidas 51 con control directo de una operación. `forge_crosscheck_v2` se ejecutó después del control completo de orientación CRAZY. **No** hemos adaptado ni ejecutado `solve_sp` para el estado de UNIECO: requiere scratchpad, estado y rutas propios; no es todavía un plan ejecutable para nuestras 84 celdas. `forge_overlap.py` muestra que 55 de las 84 direcciones objetivo caen en su zona baja `[30,99)`, incluyendo sus celdas de control 82 y 94; hay que reconciliar el orden de uso y restauración. La superposición no demuestra que sea imposible.
- **AutoBolge:** su `relational.classic` ejecutó la imagen de cuatro bytes: eco exacto y HALT en 9 pasos; con `Ab9` detuvo el host en `INPUT_UNDERFLOW` tras 7 pasos y emitió sólo tres bytes. Su API de entrada es texto UTF-8 y su EOF difiere de Olmstead. El sintetizador de texto fijo y su frontera relacional son herramientas potenciales, no evidencia de que hayan sintetizado UNIECO.

El primer crosscheck de BolgeForge se hizo antes de repetir el control de orientación en esta sesión; se conserva. Después se repitió la paridad completa de memoria (`orientation_check.py`: common y scratch coinciden con oráculo; operandos invertidos difieren) y se repitió el crosscheck sin diferencias como `forge_crosscheck_v2`. `autobolge_check.py` se ejecutó una vez directamente y otra mediante REA, reutilizando inadvertidamente su ruta de salida JSON; la segunda ejecución sobrescribió ese único archivo con los mismos bytes conservados en el stdout de la primera. No se presenta como evidencia independiente de dos archivos distintos.

## Límites y reproducción

El objetivo UNIECO de bucle compacto con cargador estricto y detección interna de EOF sigue **NOT_DEMONSTRATED**. La prueba nueva es una línea recta de cuatro parejas, no el bucle ni una VM BF. Tampoco prueba correspondencia 1:1 entre las ocho instrucciones de cada lenguaje.

`probe.py` ejecuta las comparaciones y escribe artefactos en su propio directorio: repetir en una copia aislada, conservando las dependencias identificadas por hashes. `rea_compare.py` y `rea_step_compare.py` cotejan las respuestas de REA saneadas. Las respuestas completas de REA se guardaron en estado local privado; el manifiesto registra hashes y las copias del repositorio sustituyen prefijos de rutas. `manifest.json` identifica comandos, dependencias, evidencia, controles y limitaciones.
