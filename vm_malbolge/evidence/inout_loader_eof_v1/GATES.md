# Límites de cargador y EOF — puertas previas

Base `e42938d`, 2026-11-11. El objetivo es investigar el eco IN/DLOAD/OUT del pack anterior y sus límites; una referencia funcional distinta no demuestra adaptación de ese mismo bucle.

A. Inspeccionar la regla del cargador histórico y el código y la imagen del pack. Medir cuántos bytes fuente pasan su regla; explicar cualquier incompatibilidad específica del patrón de pares y del relleno. Buscar una variante que cargue si es factible; no afirmar imposibilidad global a partir de una familia de construcciones.

B. Evaluar un cat de referencia existente que detecta EOF. Con el Olmstead 1998 original y stdin binario: 0, 1 y 2 bytes, secuencia con 00/0a/80/ff, y los 256 valores. Medir retorno, timeout, salida cruda y paridad exacta. Cotejar, donde sea practicable, runner C, scratch e intérprete independiente y oráculo, sin ocultar el byte de framing del runner. En el oráculo distinguir `stop_on_eof` de comportamiento por defecto. Cada ejecución tendrá timeout o tope de pasos explícito y se preservan fallos.

C. Controles: versión de referencia con EOF alterado si existe y mutación local que viola el cargador. Exigir que el cargador rechace el mutante, y que el control de EOF se diferencie en al menos un caso; si no, publicar el control como no demostrado.

D. Reanalizar la salida de los motores para el eco del pack anterior con datos cortos y EOF: ¿la salida observable coincide, aun si se detienen por motivos diferentes? Distinguir coincidencia de salida, terminación y semántica de EOF. No cambiar los motores ni atribuir terminación al programa cuando el host la impone.

Registrar stdout y stderr crudos, hashes, comandos, entorno y ejecución/reproducción. Todos los resultados del cat de referencia se etiquetan como referencia independiente hasta demostrar una conexión real con el bucle del pack anterior. El cálculo de los 256 bytes es acotado; no es prueba de equivalencia para toda entrada. No se alteran imágenes ni evidencia anteriores.
