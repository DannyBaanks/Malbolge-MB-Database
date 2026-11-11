# DLOAD + IN + OUT: puertas anteriores a la medición

2026-11-11. Base `4a5cd45`, Classic permisivo 3^10. Objetivo: un cuerpo que en cada vuelta ejecute IN seguido de OUT con el mismo acumulador, y DLOAD que mantenga una tabla de saltos de tamaño constante.

El cuerpo podrá colocar DLOAD antes, entre o después de IN y OUT, siempre que no modifique el valor leído y que IN preceda a OUT en cada vuelta. Se deriva la imagen a partir de ciclos XLAT2 y ecuaciones de las dos fases de DLOAD; se comprueba sobre bytes. No se asume que la construcción exista ni el periodo de estado.

- G0: imagen imprimible; pares de instrucciones y tablas verificadas; la construcción deriva automáticamente posiciones y valores, y es determinista.
- G1: flujo reproducible de al menos 10 000 bytes variados, que incluye 0 y valores altos. Se cierran 10 000 vueltas con exactamente un IN, un OUT posterior y un DLOAD, y un salto de vuelta a la misma celda. La salida coincide exactamente con los bytes de entrada, sin truncar silenciosamente. Traza, scratch, intérprete independiente, oráculo y runner C llegan al mismo paso; sus salidas coinciden byte por byte. Los tres motores que exponen memoria coinciden en su hash. Registrar tratamiento de la salida del runner, sin eliminar un posible byte de datos.
- G2: controles separados: mutar fase de IN, fase de OUT, retirar DLOAD, alterar tabla de salto, e invertir el orden IN/OUT si es constructible. Cada uno rompe el criterio; registrar por qué. Si no es constructible, el quinto control se declara no demostrado y G2 falla, sin modificar esta puerta.
- G3: con entrada constante, registrar primer estado repetido completo de máquina y comparar el periodo con mcm de los ciclos cifrados; `d` tiene periodo dos. La extensión indefinida presupone entrada constante infinita; no se extrapola a entradas arbitrarias.
- G4: sondear EOF para 0, 1, 2 y 257 bytes en los motores, registrando pasos, salida exacta y diferencias de semántica. Probar el cargador Olmstead y declarar resultado.

El pack deberá registrar comando, salida cruda, hashes de artefactos y dependencias, entorno, controles, límites y resultados negativos. Puertas falsas se publican como tales; cualquier enmienda se fecha, conserva la versión original y distingue exploración de medición canónica. La ejecución es acotada; repetir estados es un argumento para el modelo determinista con entrada futura especificada, no una corrida infinita.
