# Prefijos estrictos que preparan fases: tres testigos individuales

Puertas previas en commit `9163d87`; base `2eadc75`. Se pidió construir un prefijo que pase el cargador de Olmstead y prepare una celda del eco compacto con `74`, sin IN ni OUT. **Se consiguió por separado para las tres celdas 47, 64 y 123.** Cada imagen termina tras preparar una sola celda; unirlas al eco compacto y detectar EOF siguen NOT_DEMONSTRATED.

| Celda | Imagen | Valor fuente → intermedio → final | Pasos hasta HALT | Control sin último CRAZY |
|---|---|---|---:|---:|
| 47 (fase IN) | `repair_47.mb` | 115 → ROT 19721 → CRAZY 74 | 16 | 19721 |
| 64 (fase DLOAD) | `repair_64.mb` | 111 → ROT 37 → CRAZY 74 | 29 | 37 |
| 123 (fase OUT) | `repair_123.mb` | 39 → CRAZY 29524 → CRAZY 74 | 36 | 29524 |

Entre la primera transformación y el CRAZY final cada prefijo usa instrucciones y celdas auxiliares para preparar el acumulador, y un DLOAD para volver a la celda objetivo. El CRAZY final usa acumuladores 29562, 29564 y 29561, respectivamente. `phase_repair.results.json` contiene valores, posiciones, trazas completas y controles. Los testigos se encontraron mediante una búsqueda acotada sobre valores de datos válidos al cargar, ayudantes NOP/ROT/CRAZY, un DLOAD de retorno y un CRAZY final; las semillas, valores y primera operación se fijaron exploratoriamente. No se afirma minimalidad ni se trata esa elección como predicción ciega.

Para cada imagen y su mutante sin el último CRAZY, **todas** las celdas de fuente son aceptables según la regla del cargador; el binario histórico de Olmstead las ejecutó y retornó 0 sin salida. Scratch y el intérprete independiente coinciden en la memoria completa y en `mem[objetivo]=74`; oráculo y runner C llegan a HALT en el mismo paso, aunque ni Olmstead ni esos dos exponen memoria final. Las trazas de scratch no contienen IN ni OUT. Los mutantes terminan también, pero dejan la celda en el valor intermedio indicado. No hay comparación de memoria con Olmstead.

La corrección de operandos de CRAZY se controló de nuevo antes de buscar: `crazy(acumulador,celda)` usa fila = trit de celda y columna = trit de acumulador. En la reconstrucción completa de 59 049 celdas de la imagen de referencia, common y scratch tuvieron cero diferencias frente al oráculo; el control con operandos invertidos tuvo 18 709. Ver `parity.json`.

## Resultados negativos y alcance

No existe un único CRAZY que convierta directamente un byte imprimible aceptado por el cargador en `74` en ninguna de esas tres posiciones, para **ningún** acumulador de 10 trits: `probe.py` comprueba por trit si la tabla permite el valor deseado. Para 47 y 64 sí encontró una solución algebraica ROT → CRAZY con un acumulador apropiado; para 123 no con una sola ROT inicial. Los programas posteriores muestran que introducir operaciones auxiliares hace posible la conversión también en 123. Las imágenes `prefix_47.mb` y `prefix_64.mb` verifican separadamente las primeras rotaciones y sus controles.

**Esto no termina todavía el eco compatible.** Los tres testigos tienen prefijos y condiciones iniciales distintos, y usan celdas auxiliares que coinciden con posiciones de código o datos del eco anterior; por ejemplo, el testigo de 123 usa la celda 124, que en el eco compacto contiene el JMP. No se pueden pegar sin analizar interferencias, preservar el estado y reinstalar los valores de código y tablas. Tampoco se ha incorporado detección de EOF. La observación de tres reparaciones individuales no demuestra que el programa combinado exista o funcione.

## Reproducción

`parity_fixed.py`, `probe.py` y `phase_repair.py` generaron los respectivos JSON y stdout crudos. Para evitar sobrescribir el pack, copiar `phase_repair.py` a una carpeta vacía y ejecutarlo con `MBDB_ROOT` apuntando a la raíz de MALBOLGE-MB-DATABASE y `PYTHONDONTWRITEBYTECODE=1 python3 -I phase_repair.py`. Una segunda ejecución aislada produjo resultados, stdout y las seis imágenes de reparación/control idénticos byte por byte. El script se adaptó después de la primera corrida para admitir `MBDB_ROOT`; se comprobó que la versión portable reproduce esos mismos resultados.

El primer intento de paridad falló por una ruta construida incorrectamente; se preservó `parity.py` y su stdout crudo local, sin trackear por contener la ruta privada. `parity_fixed.py` corrigió la ruta y produjo el resultado descrito. El manifiesto conserva el hash del stdout local y de los demás artefactos. El resultado de la búsqueda de fases es exploratorio y no prueba nada sobre terminación o EOF del eco completo.
