# Incremento de bytes en Malbolge: dos lecturas, no streaming

2026-11-11. Base `eae037d`, puertas `bcc4081`, extensión de una lectura `e2e8961` y de dos lecturas `828d036`. Este es un experimento nuevo y no sobrescribe el UNIECO anterior.

## Resultado

Se construyeron dos imágenes aceptadas por el cargador de Olmstead que calculan `(byte+1)%256` **dentro de Malbolge**: una de una lectura y otra de dos lecturas en una ejecución. La segunda restaura la tabla de datos antes de volver a usarla y probó pares repetidos, incluidos `00 00→01 01` y `ff ff→00 00`. Son programas acotados: no reconocen EOF ni procesan streams arbitrariamente largos. El objetivo general sigue abierto.

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 Python/BF | PASS para casos medidos | `references.results.json`: 262 casos y control de eco detectado; BF16 con EOF=65535. |
| G1 Malbolge | PARTIAL | Una lectura: 256 bytes, Olmstead y cinco casos scratch. Dos lecturas: 512 pares, Olmstead, más traza scratch y controles de tabla. EOF limpio no demostrado. |
| G2 REA | PARTIAL | REA activo trazó las imágenes de una y dos lecturas y coincidió en cuatro casos; eventos limitados a 64. No se probó EOF bajo REA para esta construcción. |
| G3 bucle de 10 000 bytes | NOT_DEMONSTRATED | Imagen de dos lecturas emite sólo dos bytes; no existe aquí un bucle general. |
| G4 compilación BF → esta imagen | NOT_DEMONSTRATED | Las imágenes se sintetizaron a partir de un diseño específico; no hay compilador BF para esta operación. |

## Evidencia ejecutable

- `increment_oneshot.mb`: 33 822 bytes, SHA-256 `9119cf5901bd44e6906f2ca40a1273529375bb8927bf197e85cdd715f937a1bc`. El instalador prepara 294 celdas y la primera I/O es IN en PC 40000, D 50000; verificación de objetivos sin discrepancias. Olmstead ejecutó 256 casos, uno por valor. El control `increment_control_echo.mb` usa la misma forma pero tabla de eco; cinco casos coinciden con la entrada y son detectados como incorrectos para incremento.
- `increment_two.mb`: 56 382 bytes, SHA-256 `807c42ae8f5890e25df0500e3af0a29f9362ac9d7ee794fb2d7612b28de03a97`. El plan instala 879 celdas; el modelo mide primera lectura en paso 43920 y segunda en 43969. Para entrada `ff ff`, compara las 256 celdas de tabla antes de la segunda lectura y al HALT: sin discrepancias respecto del estado inicial. Esto es una medición para ese caso, no una prueba de todas las rutas.
- `two_verify.results.json`: 512 pares nativos exactos: para cada byte `b`, los pares `(b,b)` y `(b,(b+1)%256)`. Cuatro controles reales de tabla-eco son detectados. La traza scratch registra `HALTED` y bytes `00 00` para `ff ff` tras 44017 pasos.
- REA activo: `rea_oneshot_nul.redacted.json` y `rea_oneshot_ff.redacted.json` muestran `01` y `00`; `rea_two_zero_ff.redacted.json` y `rea_two_ff_ff.redacted.json` muestran `01 00` y `00 00`, todos `HALTED`. El replay observa esas ejecuciones acotadas; no es medición eléctrica. Las capturas de Python/BF son de procesos con wrapper hexadecimal y no constituyen trazas internas independientes de BF. Los originales completos están en estado local privado, con hashes en el manifiesto.
- El emisor de cada imagen, plan y celdas destino se repitió en un árbol aislado y produjo bytes idénticos: `reproduction.results.json` y `two_reproduction.results.json`. Los tiempos no son deterministas.

## Cómo funciona la tabla

El camino de una lectura guarda el byte mediante dos operaciones CRAZY con máscara 29524, rota nueve veces para formar `3*byte`, construye `base+3*byte` con dos CRAZY y usa MOVD para seleccionar la celda de tabla. ROT carga el resultado y OUT lo emite. El control positivo ejecuta las mismas operaciones para los distintos bytes; la salida no la calcula el host.

La variante de dos lecturas dispone una tabla con tres celdas por byte: valor, retorno a la celda y retorno al segundo scratch. Realiza diez ROT sobre el valor, lo que devuelve la palabra a su estado inicial y deja el resultado en el acumulador. Después de OUT salta al segundo bloque, que usa otro scratch y la misma tabla. Los dos bloques de código son distintos: no son un bucle reutilizable.

`table_model.results.json` es un diseño algebraico exploratorio anterior, no la traza del programa de dos lecturas. La orientación es `crazy(acumulador,celda)=tabla[celda][acumulador]`. La paridad completa de memoria se volvió a comprobar al finalizar (`parity.results.json`), con cero discrepancias en la orientación correcta y discrepancias en el control invertido; también existía el control completo del pack anterior antes de esta construcción.

## EOF y límites observados

La imagen de una lectura con entrada vacía emite `e6`; con `00 ff` emite sólo `01`. La imagen de dos lecturas con entrada vacía emite `0c 00`; con `41` emite `42 0c`; con `41 42 43` emite sólo `42 43`. Por tanto ninguna cumple la especificación completa de filtro con EOF. No se afirma funcionamiento para todos los pares posibles: las familias medidas cubren 512 de los 65 536 pares.

Faltan la detección y el salto en EOF dentro de esta construcción, el rearme de código y scratch para un bucle reutilizable, y la comparación de 10 000 bytes bajo Malbolge/REA. La integración con el núcleo UNIECO EOF-capable anterior sigue `NOT_DEMONSTRATED`.

## Reproducción

`GUIA.md` muestra una prueba nativa de la imagen de dos lecturas. Los scripts de síntesis y verificación escriben en su carpeta: ejecutar únicamente en un árbol aislado nuevo con las dependencias indicadas por el manifiesto. Los resultados fallidos y controles se conservan junto a los positivos.
