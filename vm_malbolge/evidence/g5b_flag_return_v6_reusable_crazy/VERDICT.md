# G5b P6 — crazy compartido con retornos repetidos

2026-11-24. PASS acotado: dos llamadores, una variable, un sitio crazy, tres vueltas completas y parada por reloj.

P1 ya demostró retornos repetidos con ROT. Este experimento compone ese protocolo con crazy y elimina la salida duplicada de A. No atribuye novedad al mecanismo de retorno de P1. Usa el ensamblado de P5, cargador Classic estricto y dependencias BolgeForge del mismo entorno.

## Puertas y resultados

Una sola imagen visita A → B → A → B → A → B; vuelve al mismo reloj K después de cada par. El reloj 66 en residuo 2 termina en su cuarta visita, después de tres vueltas. El único sitio que escribe V=41000 es crazy en 38246. En las cuatro visitas a K la bandera y crazy valen 74; las colas JMP se conservan durante toda la fase de trabajo.

| Caso | Retornos | Salida hexadecimal | Pasos locales/REA |
|---|---|---|---|
| Positivo | A B A B A B | fc58fc58fc58 | 3236 |
| Control A: omitir conmutación inicial | B B B | fc58fc | 3029 |
| Control B: omitir rearmado de bandera | A B B B | fc58fc58 | 3127 |

Olmstead nativo termina con rc=0, clasesbolge con end, trazador local con halt; salidas idénticas en los tres. REA confirma por eventos todos los accesos al sitio compartido y cada continuación de los tres casos. Dos ensamblados producen imágenes, planes y salidas crudas idénticos byte a byte.

El acumulador inicial en el sitio vale 55999, producido por el preámbulo. Se comprueba la recurrencia crazy desde V0=12345 para las seis llamadas; los valores escritos son 17916,29272,252,29272,252,29272. La salida repetitiva viene de esa órbita y no implica que la rutina deje de ejecutarse: las trazas registran seis accesos al mismo pc con d=41000.

## Reproducción

Desde este directorio, con las dependencias locales de P5 disponibles:

```sh
python3 -B probe.py /tmp/g5b-p6-new-run
node rea.mjs /home/danny/Development/rea/dist /tmp/g5b-p6-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

probe.py rechaza un directorio ya existente. MALBOLGE_MB_DATABASE_ROOT permite elegir otro checkout. verify.py compara las dos tandas conservadas y sus hashes; para una nueva generación comparar sus imágenes con run01. environment.json identifica las dependencias utilizadas y commands.json registra las invocaciones de cierre.

## NOT_DEMONSTRATED y próximo paso

No demuestra ejecución ilimitada, elección del orden por entrada, más de dos llamadores repetidos, dos variables, recursión ni pila de retornos. El orden A/B está fijado por el cableado de las continuaciones. El contador de tres vueltas es un reloj que consume fases, no un contador general.

Siguiente experimento: dos variables con trazas que demuestren aislamiento de las escrituras y que los retornos conservan la selección de variable. Después, llamadas anidadas. P5c y P6 son capacidades complementarias: cinco hojas una vez frente a dos llamadores repetidos.
