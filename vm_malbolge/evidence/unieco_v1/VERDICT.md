# UNIECO — preparación conjunta y observación nativa

Puertas `6209ea1`; base `f6adbc3`. **UNIECO completo sigue NOT_DEMONSTRATED.** Sí se alcanzó el subobjetivo: una sola imagen aceptada por Olmstead prepara simultáneamente las tres celdas de fase, sin entrada ni salida, y termina. Todavía no transfiere el control al eco, restaura su cuerpo ni resuelve EOF.

## Prefijo conjunto

`prepare_v2_main.mb` contiene 19 830 bytes, todos válidos para el cargador histórico. Su comienzo utiliza MOVD, ROT, MOVD, NOP y JMP para saltar a código auxiliar alto sin ejecutar las celdas de fase. El código alto prepara las celdas 47, 64 y 123 en 74 y llega a HALT tras **137 pasos**. Olmstead devuelve 0 sin salida; scratch, independiente, oráculo y runner C llegan a HALT al mismo paso; scratch e independiente coinciden en la memoria completa. Las trazas no contienen IN ni OUT. Se comprobo un mutante por cada escritura final: al quitarla, la celda correspondiente queda distinta de 74. Un cuarto mutante tiene un byte inicial inválido y Olmstead lo rechaza.

La primera versión `prepare_main.mb` no funcionó: por un error en el incremento posterior de `d`, el salto leyó otra celda, entró en el cuerpo prematuramente y alcanzó IN. `multi_prepare.results.json` conserva la traza y las comprobaciones falsas. La segunda versión agrega el NOP necesario; las puertas originales no cambiaron. Los tres objetivos se alcanzan en una sola ejecución, pero el código y datos auxiliares no se restauran para ejecutar el eco.

## REA: traza de la VM y proceso x86 real

REA `trace_malbolge` produjo una ejecución completa de 137 eventos; `(paso, posición, opcode, d)` coincide con scratch en todos ellos (`rea_compare.results.json`). Es una ejecución de la semántica Classic dentro del proceso de REA, no una medición eléctrica del silicio.

A solicitud de Danny, se examinó además el ELF x86-64 de Olmstead (SHA-256 `dfee14b7b7914facf36094e1b6c2b509b4f49277e093d9440f41c6f091c132f6`). REA/Rizin identificó en este binario la llamada `sym.op` y la escritura `mov word [rdx], ax` en el desplazamiento `0x1486` del ELF. Mediante REA `capture_process_scenario`, GDB ejecutó ese binario con la imagen y colocó breakpoints inmediatamente antes y después de esa instrucción. Observó estas escrituras nativas:

| Celda | Antes | Valor a escribir | Después |
|---|---:|---:|---:|
| 47 | 19721 | 74 | 74 |
| 64 | 37 | 74 | 74 |
| 123 | 104 | 9850 | 9850 |
| 123 | 9850 | 74 | 74 |

Coinciden con las cuatro escrituras CRAZY seleccionadas de la traza de REA. El proceso observado terminó normalmente. Esto es observación de instrucciones y memoria de un proceso nativo bajo depurador, **no** observación de transistores ni de señales físicas; cubre esas escrituras, no cada instrucción del programa. El vínculo entre `rdx`, `rbp` y el índice de celda se obtiene del ensamblado del binario y del estado observado, no de un símbolo independiente por celda. El binario fue hasheado y analizado por REA, pero la captura declara que su identidad de ejecutable es una muestra previa y no una vinculación atómica del inferior; se conserva esa limitación. Los offsets son específicos de ese binario y se deben revalidar al recompilar.

Las respuestas completas de REA se guardaron como evidencia local privada en `~/.local/state/isyco/research/unieco-rea-20261111/`, con SHA-256 en `rea_evidence_manifest.json`. Las copias `unieco_rea_*.redacted.json` sustituyen prefijos privados de rutas; no son los originales crudos. El primer intento GDB quedó esperando entrada de comandos y agotó el tiempo; el segundo terminó con error de tipos al calcular una expresión. Se conservan ambos, además de las capturas posteriores, sin presentarlos como exitosos. La opción de análisis profundo automático de REA no estaba configurada en esta máquina; se usaron Rizin y la ejecución GDB capturada por REA.

## El puente que falta

Al detener el prefijo, la máquina está en `a=74`, `c=19828`, `d=124`; el eco original, justo antes de entrar al cuerpo, está en `a=0`, `c=43`, `d=126`. Al comparar el trampolín, el cuerpo y las cuatro celdas de tabla/datos relevantes (`42..126`, `143`, `148`), **84 celdas** difieren. También 63 posiciones de relleno elegidas como NOP válido inicial adquieren algún opcode válido distinto de NOP durante su ciclo XLAT2; no basta dejarlas como NOP de carga.

`state_bridge_v2.py` realizó una intervención **del host**, copiando esas celdas y registros directamente en la memoria del modelo: la continuación hizo eco de 10 000 bytes, igual que el eco original. Esto valida el estado objetivo para esa corrida, pero **no es un programa Malbolge**, no usa el cargador para realizar las restauraciones y no satisface G1/G2. `write_plan.py` da un dato algebraico útil: de las 84 celdas distintas, 51 admiten la escritura deseada con un CRAZY y las 84 con hasta dos, **si** se puede fijar arbitrariamente el acumulador antes de cada operación y apuntar `d` a la celda. No construye esas operaciones ni prueba que exista un plan ejecutable. El control de orientación CRAZY de memoria completa se conservó en `parity.json`.

## Estado de las puertas

- G0: la preparación aislada sí carga y el control de carga se rechaza; **la imagen de eco integrada todavía no existe**.
- G1: se prepararon las tres fases, pero no el código, tablas y registros del eco: **NOT_DEMONSTRATED**.
- G2: eco real en una imagen estricta integrada: **NOT_DEMONSTRATED**. La intervención del host no lo demuestra.
- G3: detección interna de EOF en esa imagen: **NOT_DEMONSTRATED**.
- G4: pasan controles de las tres escrituras y del cargador para el prefijo; controles del eco integrado y EOF siguen **NOT_DEMONSTRATED**.

La segunda corrida aislada de `multi_prepare_v2.py` reprodujo los resultados, stdout e imágenes byte por byte. Para repetir sin sobrescribir evidencia, copiar el script a una carpeta nueva y proporcionar `MBDB_ROOT`; la versión portable se comprobó con esa reproducción. El manifiesto identifica artefactos, dependencias y comandos. No se han modificado las imágenes anteriores.
