# Una celda restaurada con primitivas compartidas

2026-11-12. Base `c364fa9`, puertas preregistradas en `9ce3a12`. Esta prueba responde al primer paso: conectar las primitivas compartidas para recuperar una celda. No construye el restaurador general ni el bucle de incremento.

## Resultado

La imagen `restore_positive.mb` prepara una celda T=57100 con valor 70, ejecuta su rutina dentro de Malbolge y termina con T=40. Utiliza una única celda de código para cada primitiva `ROT`, `MOVD` y `CRAZY`; cada una alterna operación/NOP por su órbita 74↔70. El control altera la constante y termina con T=39.

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 loader y ejecución | PASS en las imágenes medidas | Ambas imágenes son estrictas y Olmstead termina rc=0, sin I/O. |
| G1 una celda | PASS, objetivo fijo 40 | `verification_v2.results.json`: T `70→60→29524→29484→40`; las ventanas scratch y REA son idénticas. |
| G2 control | PASS en trazas | Constante cambiada: T `70→60→29524→29485→39`. Olmstead sin instrumentación no distingue positivo y control por stdout ni rc. |
| G3 reproducibilidad | PASS | Síntesis aislada: imágenes, objetivos y planes idénticos byte a byte (`reproduction.results.json`). |
| G4 valores y llamadas generales | NOT_DEMONSTRATED | La imagen usa un solo objetivo fijo, punteros preparados y un reloj de cuatro fases. |

## Trazas y estado

En el positivo, la rutina empieza en el paso 3302 y llega a HALT en el 3348. Las cuatro escrituras observadas sobre T ocurren en la misma posición de código CRAZY, PC 58268. Las posiciones compartidas ROT 58057, MOVD 58152 y CRAZY 58268 regresan al valor inicial 74 al acabar; no se restauran entre sí mediante otro bloque de código. La ventana REA desde el paso 3200 coincide paso por paso, registros y escrituras con el trazador scratch hasta HALT. `events_truncated=true` indica que se omitió el bootstrap previo a la ventana.

El reloj de despacho sigue `46 (NOP), 40 (MOVD), 49 (NOP), 81 (HALT)`. Su valor cambia de 117 a 58 y la constante de control cambia de 120 a 40. Por ello **la rutina no está lista para otra llamada** aunque las tres primitivas vuelvan a su fase inicial. La parada es por el reloj, no por detección EOF.

La primera versión `verify.py` comparó erróneamente el valor anterior al salto de handoff para la celda 58056. Olmstead cifra esa celda durante el salto; `verify_v2.py` compara el valor ya cifrado y mantiene las demás comprobaciones. Se conserva el fallo original en estado local privado con su hash y una copia saneada en el pack; no se reescribe el resultado de la primera corrida.

## Alcance algebraico

La ruta elegida tiene un cuarto CRAZY necesario por las fases del reloj. Su última operación es `crazy(q,q)`, cuya salida por trit sólo puede ser 0 o 1. `algebra_scope.results.json` comprueba la ruta para las 59049 palabras de entrada con objetivo fijo 40, y cuenta 1024 palabras ternarias sin trit 2; para esas palabras realiza 5120 comprobaciones de ejemplo. Es álgebra ejecutada en el host: **no** demuestra que la imagen nativa acepte 1024 objetivos ni que pueda escogerlos dinámicamente.

La paridad completa de orientación se repitió antes de este análisis (`parity.results.json`). La convención es `crazy(acumulador,celda)=tabla[celda][acumulador]`.

## Pendiente

- Restaurar valores con trit 2 mediante una ruta distinta o modificar el despacho para evitar el cuarto CRAZY.
- Rearmar la constante y el reloj, y demostrar una segunda invocación real sobre otra celda.
- Integrar un cuerpo de incremento, detector EOF y un bucle de longitud arbitraria.
- Observar el estado interno de Olmstead mediante instrumentación independiente; su ejecución actual sólo comprueba carga y terminación sin salida.

El manifiesto incluye hashes de imágenes, scripts, trazas saneadas y evidencia cruda privada. Reproducir scripts de escritura en un árbol aislado nuevo.
