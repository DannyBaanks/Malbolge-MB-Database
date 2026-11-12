# Eco BF compilado a un núcleo Malbolge relocalizado

2026-11-11. Gates `8d675bc`; enmienda del backend relocalizado `5e02233`. REA código fuente local: commit `2cd5ccc7e` (repo separado). Evidencias previas conservadas.

## Resultado y alcance

Se generó una imagen Malbolge estricta nueva que instala su propio núcleo relocalizado, reproduce los bytes y se detiene ante EOF bajo Olmstead. El compilador `compile_bf.py` acepta el patrón BF `,+[-.,+]` con celdas de 16 bits, wrap y EOF=65535, y emite esta imagen como **plantilla autenticada**. BF y la imagen se compararon funcionalmente. Esto es compilación por especialización para un solo patrón; no es un compilador general ni una VM BF ni una traducción instrucción por instrucción.

La imagen usa el núcleo EOF-capable de la referencia PureEpoch/BolgeForge, relocalizado por 28 200 posiciones. **No es el núcleo compacto IN/DLOAD/OUT de `unieco_strict_relocation_v1`**: no se modificó la candidata anterior ni se demuestra que ella tenga EOF. Tampoco se afirma composición de código con ella. El perfil de direcciones y la síntesis se hicieron offline; durante el arranque la imagen ejecuta el plan dentro de Malbolge y no recibe escrituras del host.

| Afirmación | Estado | Evidencia y límite |
| --- | --- | --- |
| BF admitido → plantilla Malbolge autenticada | PASS, patrón único | `compile_bf.py`, `compile_relocated.stdout.raw.txt`; se niegan patrones o convenciones distintos. |
| Cargador histórico y salida compilada | PASS para casos medidos | `compiled_relocated.results.json`; vacío, NUL, mixto, 0..255 y 10 000 bytes. |
| Instalación y handoff | PASS en modelo instrumentado | `relocated_verify.results.json`: primera operación I/O es IN en PC 35857, D=58975; 281 celdas del estado objetivo coinciden, cero discrepancias. |
| Eco y EOF de la imagen nueva | PASS para casos medidos | Olmstead: 261 entradas, 256 valores de un byte y cinco vectores, incluyendo 10 000; rc=0 y salida exacta. Scratch: cinco vectores, `HALTED`, incluido 10 000. |
| Controles | PASS en alcance medido | Loader corrupto rc=1; último CRAZY del instalador alterado no produce el eco y es terminado por el arnés tras timeout. El compilador rechaza cuatro configuraciones erróneas. |
| REA con EOF Olmstead | PASS en código fuente, alcance acotado | `rea_capture.redacted.json` y pruebas MCP fuente: `olmstead_1998`; vector `00 0a 80 ff`, `HALTED`, 11556 pasos, salida exacta. Los eventos se limitaron a 64. |
| Núcleo compacto anterior con EOF | NOT_DEMONSTRATED | La solución nueva relocaliza otro núcleo; la imagen previa no fue alterada. |
| Runner C con 10000 bytes | NOT_DEMONSTRATED | Primera corrida terminó por timeout de 90 s; se conserva el fallo. El código del runner usa búsqueda lineal del overlay y esta imagen es larga; posible explicación, no causa demostrada. |

## Síntesis y validación

- `relocation_model.py` probó primero una hipótesis de relocalización sobre un snapshot sembrado por el host; eso no es evidencia de instalación autónoma.
- `synthesize_relocated.py` extrae el estado de referencia y un perfil que cubre los 256 valores más `00 ff`, instala 281 celdas y produce 9651 instrucciones de plan. La imagen ocupa 33822 bytes y tiene SHA-256 `c7b0aef98363242607c1fb13aa964fd412da057bcea04105f7e9b8559e986d13`.
- La primera lectura es el paso 9653. La verificación del estado compara los 281 objetivos después de la encriptación del salto de handoff. El control negativo altera un escritor y no alcanza la salida esperada.
- El backend se selecciona por hash completo; `compiled_relocated.mb` es byte a byte la imagen generada. `compiled_relocated.results.json` compara directamente esa salida del compilador con BF16 y Olmstead. `relocated_verify.results.json` conserva además 261 corridas nativas y los controles.
- REA reproduce la imagen compilada en su servicio de código fuente; el test atraviesa además el servidor MCP en memoria. El proceso MCP preexistente sigue con el binario anterior y **no fue reiniciado ni desplegado**. El modo legado sigue siendo el valor por defecto; `olmstead_1998` es explícito y queda en Evidence.
- `parity.results.json`: el control completo de memoria se repitió después de la síntesis para auditar orientación (59049 celdas, scratch y common sin diferencias, operandos invertidos difieren). Una comprobación equivalente anterior al experimento vive en `unieco_strict_relocation_v1/parity.json`.
- `reproduction.results.json`: una síntesis separada en árbol nuevo produjo imagen, plan y objetivos byte a byte iguales. `bf_reproduction.results.json` repite los controles del compilador en un árbol aislado.

## Semántica EOF del runner C

`eof_semantics.mb` hace IN; OUT; HALT con entrada vacía. Olmstead emite `a8`; el runner C emite sólo el salto de línea de su wrapper y registra `HALTED` en el paso 1. Por tanto su etiqueta no demuestra que la imagen ejecutó HALT. El código fuente declarado por su manifiesto, `Malbolge-Engine` commit `e7faeb1`, termina el host cuando se agota la entrada. Esto corrige la lectura anterior que trataba su `HALTED` como prueba de halt autónomo. Sus salidas cortas pueden compararse, pero la prueba decisiva de EOF aquí es Olmstead y el modelo scratch.

## Límites pendientes

- No se demuestra BF completo, traducción arbitraria ni correspondencia de cinta/estados internos entre lenguajes.
- No se prueba una entrada infinita, todos los streams posibles, ni independencia de cada ruta para cualquier estado de máquina.
- No se integró EOF en el núcleo compacto de la candidata previa ni se probó que esta nueva imagen sea una modificación de esa candidata.
- No se midió la ejecución del runner C sobre los 10 000 bytes hasta su fin; se conserva el timeout.
- REA fuente se probó con cinco vectores en el motor y uno en MCP, no con 10 000 bytes; el proceso MCP conectado anteriormente necesita una actualización separada.

## Reproducción

El compilador se ejecuta como en `GUIA.md`. Los scripts de evidencia escriben resultados en su carpeta; repetirlos **sólo en una copia aislada nueva**, con las dependencias hermanas indicadas en los scripts. El manifiesto identifica hashes, artefactos y comandos. No sobrescribir este pack ni los packs anteriores.
