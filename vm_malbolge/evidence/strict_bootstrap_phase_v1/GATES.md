# Exploración: preparar fase tras pasar el cargador estricto

Base `2eadc75`, 2026-11-11. Objetivo de investigación: averiguar si un prefijo sin IN ni OUT puede transformar una celda de fase del eco compacto a 74 partiendo de una imagen aceptada por el cargador de Olmstead. Una reparación de UNA celda no demuestra el programa completo ni detección de EOF.

Antes de cualquier afirmación que use crazy, correr el control completo de orientación de operandos contra la memoria del oráculo y un control con operandos invertidos; `crazy(a, cell)` usa la fila de la celda y la columna del acumulador. Conservar salida cruda.

Búsqueda acotada: celdas objetivo 47, 64 y 123 del pack anterior. Se acepta como evidencia positiva sólo una imagen íntegramente válida al cargar, que llegue al estado deseado sin ejecutar IN ni OUT en el prefijo, con `mem[target]=74`, y una traza de pasos y controles que otro motor reproduzca. Un STOP acotado del trazador no prueba que Olmstead acepte y ejecute: comprobar el cargador real con límite de tiempo y, cuando sea posible, insertar HALT tras el prefijo. Conservar también cualquier fallo de búsqueda; no interpretar un espacio acotado como imposibilidad universal.

Si no se encuentra el prefijo, publicar el alcance exacto de la búsqueda, exploraciones descartadas y resultado negativo. No alterar packs anteriores ni modificar las puertas a posteriori. La integración de las tres fases, el bucle, eco binario y EOF son tareas posteriores hasta ser demostradas de forma separada.
