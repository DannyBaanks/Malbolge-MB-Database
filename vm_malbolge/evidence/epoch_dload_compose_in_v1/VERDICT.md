# Composición de DLOAD con IN — prueba exploratoria

2026-11-11. Base local MALBOLGE-MB-DATABASE `55a574f`, dialecto Classic permisivo 3^10. `GATES.md` se escribió antes de ejecutar la primera prueba en esta sesión, pero no fue comprometido ni sellado externamente antes de medir: el orden es un registro de trabajo, no un pre-registro verificable independientemente. El probe se ajustó después de la primera ejecución para añadir controles de fin de entrada; no se cambiaron las puertas. Los resultados son exploratorios.

## Resultado

La imagen `compose_in.mb` ejecutó una lectura IN y un DLOAD por vuelta durante 10 000 vueltas, en 830 060 pasos. En cada vuelta el salto volvió a 59; `d` al inicio alternó 145 y 149, y en IN fue 143. Los únicos opcodes válidos del cuerpo observados fueron 4, 23 y 40. La traza registró exactamente los primeros 10 000 bytes de la secuencia `(73*i+19) % 256`, incluidos bytes cero y mayores de 127; el acumulador final fue 90, el último byte consumido. El byte de más impide agotar el flujo durante esta prueba.

Los parámetros calculados son `s=60`, `delta=77`, `J=142`, `n=83`, `D0=145`, `V0=V1=66`, datos `(145,148,153,144)`, `W=86`; la imagen tiene 155 bytes. La derivación independiente de la construcción y las comprobaciones de sus bytes coinciden.

Traza, scratch e intérprete independiente terminaron con memoria SHA-256 `30c6b26d791c8421aaa39e075b3ce132e6c4126974295f97304ab6cdfb6b53fb`. Oráculo, scratch, independiente y runner C alcanzaron el tope. El oráculo y el runner C no exponen memoria o acumulador: su acuerdo se limita al recorrido hasta el tope y la ausencia de salida. La traza registra los valores que suministra, no una observación externa de cada acumulador de los otros motores.

Con entrada constante 0x41, la primera repetición del estado completo observado `(memoria,a,c,d)` aparece entre vueltas 1 y 3061: periodo 3060, igual al mcm de los ciclos XLAT2 2, 4, 5, 6, 9 y 68; `d` tiene periodo 2. La extensión indefinida requiere una fuente que siga suministrando ese mismo byte. Con una entrada arbitraria no se afirma periodicidad del sistema que incluye el estado del flujo.

Los cuatro controles rompen el criterio: `k_off` produce salto incorrecto; `no_dload` ejecuta cero DLOAD en su primera vuelta; `op_phase` alterna 2 y 0 lecturas; `dload_phase` ejecuta dos DLOAD y posteriormente sale del bucle. Los detalles se conservan en `results.json`.

## EOF y cargador

Para longitudes de entrada 0, 1, 2 y 257, traza, oráculo (con `stop_on_eof=True`), intérprete independiente y runner C se detienen en el mismo paso al intentar leer después del último byte. El runner C llama `HALTED` a ese resultado y los otros tres `EOF`. El scratch, por diseño, continúa asignando 59048 en EOF; el oráculo por defecto continúa con -1. No se equiparan estas semánticas. `olmstead` rechaza la imagen con `invalid character in source file` (rc 1); sólo 7 de las 155 posiciones decodifican opcode válido al cargar.

Las cinco puertas del archivo de trabajo resultaron verdaderas. Esto no convierte la prueba en un experimento pre-registrado verificable ni demuestra compatibilidad con el cargador de 1998, una salida que refleje los bytes, un cálculo elegido, o comportamiento periódico bajo entradas arbitrarias. El estado repetido es evidencia finita más el argumento determinista, no una ejecución infinita.

## Reproducción y evidencia

Desde una copia aislada del probe, indicando el repositorio con `MBDB_ROOT` (si se ejecuta en el pack instalado, este se detecta automáticamente):

```
MBDB_ROOT="/ruta/al/repositorio/MALBOLGE-MB-DATABASE" PYTHONDONTWRITEBYTECODE=1 python3 -I probe.py > stdout.raw.txt 2>&1
```

El probe escribe imágenes y `results.json` en el directorio donde reside: para preservar los artefactos, ejecutar una copia aislada y cotejar hashes. `manifest.json` registra hashes SHA-256 de los artefactos y dependencias. El resultado de puertas se registra en JSON y stdout, y se debe inspeccionar: el probe no convierte una puerta falsa en un exit code no cero.

El probe se ajustó después de medir para eliminar una ruta local absoluta; una nueva ejecución de esa versión se comparó con los resultados de la corrida anterior.
El primer intento de ejecutar la variante portable en `/tmp` terminó con `IndexError` al evaluar la ruta alternativa; se corrigió antes de la reproducción exitosa. La salida del intento fallido permanece en la carpeta temporal de esa prueba.
