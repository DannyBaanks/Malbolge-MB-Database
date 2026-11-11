# IN → DLOAD → OUT: eco en bucle de tabla constante

Puertas pre-registradas en commit `96d14c0`, antes de la implementación y las mediciones. Base `4a5cd45`. Modelo **Classic permisivo 3^10**; pasos acotados salvo la inferencia determinista expresamente descrita abajo.

## Resultado

**G0–G4 verdaderas**. La imagen de 150 bytes ejecuta el patrón `[IN, DLOAD, OUT, JMP]` una vez por vuelta durante 10 000 vueltas y 820 043 pasos. La tabla de salto ocupa dos celdas y cada salto vuelve al trampolín 42. `d` al inicio alterna 126 y 127. Se alimenta la secuencia `(73*i+195)%256`: incluye cero, los 256 valores de byte y un último byte leído igual a `0x0a`. La salida coincide byte a byte con los primeros 10 000 bytes de entrada; queda un byte adicional disponible.

La imagen, cinco mutantes y el programa se construyen mediante el cálculo de parámetros y ciclos XLAT2. Parámetros: cuerpo 43..124, DLOAD en 60/64, OUT en 119/123, JMP en 124, tabla `(126,125)`, datos DLOAD `(143,148)`; imagen SHA-256 `bdc1e06a3bdc54df07893baae52e89b066657ae9b609fb397ddc073d70d76e39`. `results.json` conserva todos los campos y comprobaciones.

La traza, scratch, intérprete independiente, oráculo y runner C alcanzan el mismo tope y producen el eco completo. La traza, scratch e independiente coinciden en el SHA-256 de memoria `eec018171b753823cbfe694bc6b0db3ae1ae404ff5b6676cc9b85073dce58891`; el oráculo y el runner C no exponen memoria ni acumulador. `input.raw`, `scratch.raw`, `independent.raw`, `oracle.raw` y `runner_c.raw` conservan los bytes. El runner C agrega exactamente un `0x0a` propio al final: como el último byte del programa también es `0x0a`, `runner_c.raw` termina en **dos** saltos de línea. El cotejo comprueba la secuencia completa más ese byte adicional; no elimina un byte de datos por heurística.

## Periodo y corrección de la exploración

Con una fuente que suministra `0x41` constantemente, el primer estado `(memoria,a,c,d)` repetido aparece en las vueltas 1 y 181: **periodo 180**, con `d` de periodo 2. Los ciclos de las celdas efectivamente cifradas son 2, 4, 5, 6 y 9, cuyo mcm es 180. La repetición permite inferir continuación periódica en el modelo determinista si la fuente sigue suministrando el mismo byte. No se afirma periodo de todo el sistema para entradas arbitrarias ni se ejecutaron infinitos pasos.

La primera medición exploratoria calculó incorrectamente mcm=3060, porque incluyó la celda del JMP (valor 68, ciclo 68). El JMP cambia `c` al trampolín **antes** del cifrado: se cifra la celda del trampolín, no la celda del JMP. La corrección excluye esa celda y conserva el trampolín, sin alterar la puerta G3. Se preservan `exploratory_probe.py`, `exploratory_results.json` y `exploratory_stdout.raw.txt`, donde G3 figura falsa. La corrección se hizo después de ver esa discrepancia y antes de la corrida aquí presentada; por ello el acuerdo de G3 con el mcm corregido debe interpretarse con esa salvedad, no como predicción independiente ciega.

Antes de esa exploración, el primer intento de construir el control de orden inverso dio `ValueError: no construction found` bajo una búsqueda restringida que exigía DLOAD después de la primera operación. Se amplió el control para colocar DLOAD antes de OUT y construir el orden contrario. Su salida cruda quedó en `/tmp/isyco-inout-explore/stdout.raw.txt`, SHA-256 `c9652bff8d46c6fe2be4a27350eb2ef901dda22fe8f301a6986e50f64258762a`; esa ruta es temporal y no es un artefacto durable del pack.

## Controles y EOF

Los cinco controles fallan el criterio: invertir la fase de IN provoca dos lecturas y luego cero; invertir la de OUT produce dos escrituras y luego cero; quitar DLOAD y alterar la tabla llevan a saltos incorrectos; el control inverso ejecuta `[DLOAD, OUT, IN, JMP]` y emite el acumulador anterior. El detalle de cada vuelta inicial, destinos y estado está en `results.json`.

Para entradas de 0, 1, 2 y 257 bytes, la traza, el oráculo con `stop_on_eof=True`, el intérprete independiente y el runner C producen exactamente los bytes disponibles y llegan al intento de lectura siguiente en el mismo paso. Los tres primeros lo llaman `EOF` y el runner C `HALTED`. Scratch no se detiene en EOF: sustituye 59048 y sigue; sólo se le comparó hasta el paso de EOF en esta prueba. El comportamiento por defecto del oráculo también difiere al no activar `stop_on_eof`.

El cargador de Olmstead 1998 rechaza la imagen (`rc=1`, `invalid character in source file`; 9 de las 150 posiciones son válidas según su prueba de carga). Compatibilidad con ese cargador y terminación uniforme en EOF siguen **NOT_DEMONSTRATED**. La construcción no constituye todavía un cálculo elegido más allá del eco.

## Reproducción y alcance

`probe.py` escribe archivos en su propio directorio. Para no alterar evidencia, copiarlo a una carpeta nueva y ejecutar esa copia con `MBDB_ROOT` apuntando al repositorio y `PYTHONDONTWRITEBYTECODE=1 python3 -I probe.py`; capturar stdout y stderr. La corrida comprometida y una copia aislada produjeron `results.json`, stdout y las seis imágenes idénticos byte por byte. `capture_io.py` se ejecutó adicionalmente para preservar los flujos crudos; usa creación exclusiva para impedir sobreescrituras. El código del probe informa las puertas en JSON pero no produce exit code de fallo por una puerta falsa: inspeccionar sus valores.

Los metadatos, comandos, hashes de artefactos y dependencias están en `manifest.json`. Este experimento no prueba que otros programas de Malbolge funcionen, ni que el cargador histórico acepte estas imágenes, ni que la máquina continúe bajo todas las interpretaciones de EOF.
