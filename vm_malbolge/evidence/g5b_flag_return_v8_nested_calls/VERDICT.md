# G5b P8 — llamadas anidadas de profundidad fija 2

2026-11-24. Base: P7, 0fb866c. PASS acotado para G0–G5 de GATES.md. Las generaciones finales son run04 y run05; se conservan también el primer fallo y los runs intermedios.

## Contrato demostrado

Dos llamadores A/B entran en la misma rutina exterior O (pc=38318). O llama a I (crazy, pc=38340) sobre V=41000 y recibe el retorno en O_AFTER (pc=38346). Después O usa la bandera exterior FO=38130 para seleccionar el retorno a A o B. I usa una bandera distinta FI=38224 y la rearma antes de O_AFTER. V mantiene su estado entre llamadas.

Una sola imagen de 39932 bytes hace tres vueltas A B, seis llamadas exteriores y seis interiores. La traza contiene seis secuencias de profundidad lógica 0→1→2→1→0, delimitadas por los puntos de entrada y retorno. No vuelve al llamador exterior antes de ejecutar la llamada interior y su continuación.

FO vale 70 al entrar desde A y 74 al entrar desde B. En el positivo conserva ese valor durante I y hasta O_AFTER. REA confirma que no hay ninguna escritura en FO durante los intervalos interiores, no solo igualdad entre snapshots. FI vale 74 antes y después de I. En las cuatro visitas al reloj, FO, FI y crazy recuperan 74; ninguna cola JMP cambia. Solo pc=38340 modifica V en la fase de trabajo.

| Caso | Retornos exteriores | Salida hexadecimal | Pasos locales/REA |
|---|---|---|---|
| Positivo | A B A B A B | fc58fc58fc58 | 3838 |
| Cifrar FO dentro del retorno interior | B B B | fc58fc | 3790 |
| Omitir armado de A en el llamador | B B B | fc58fc | 3599 |

En el control interior se cambia el destino de un enlace: aterriza sobre FO y la cifra, en lugar de pasar por el puente neutro. REA registra una escritura interior en FO por llamada. El retorno interior sigue llegando a O_AFTER, pero la continuación exterior cambia a B. Es un control causal de la conservación del retorno exterior.

Olmstead termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED; las salidas coinciden byte a byte. Los eventos REA completos confirman todas las entradas, retornos, snapshots de banderas y escrituras. run04/run05 son idénticos en imágenes, planes, trazas, salida cruda y capturas REA.

## Fallo de construcción preservado y corregido

Categoría BUG: el primer layout se congela en el paso 3709 antes de retornar al llamador. Tenía un desfase de una celda en la continuación A y un puente contiguo a una cola JMP; entrar al puente cifraba esa cola vecina. No es evidencia de imposibilidad de llamadas anidadas. La corrección desplaza el puente dejando separación y alinea la continuación con el avance real de d.

run01 conserva imagen, plan y failed.trace.json. reproduce_failure.py reconstruye ese layout desde el generador final y produce exactamente la misma imagen (failure_replay); reproduce la congelación y el cambio de cola. run02/run03 conservan los primeros resultados corregidos; run04/run05 añaden las mediciones explícitas de clasesbolge al reporte y el conteo de escrituras interiores en FO. No se reescribió evidencia histórica.

## Reproducción

Desde este directorio, con las dependencias locales de P5/P7:

```sh
python3 -B probe.py /tmp/g5b-p8-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p8-new-run
python3 -B reproduce_failure.py /tmp/g5b-p8-failed-layout
python3 verify.py .
sha256sum -c hashes.sha256
```

Los directorios de salida deben ser nuevos. REA_DIST apunta al dist compilado de REA; MALBOLGE_MB_DATABASE_ROOT permite otro checkout. verify.py audita los runs finales conservados; comparar cualquier nueva generación con run04. environment.json identifica dependencias mediante SHA-256 y commands.json conserva invocaciones con rutas relativas al entorno de desarrollo. Los stdout/stderr crudos de las generaciones finales acompañan a la evidencia de ejecución nativa.

## NOT_DEMONSTRATED

Dos niveles con banderas diferentes asignadas estáticamente; I tiene un único llamador y una continuación fija. Esto no demuestra una pila de direcciones de retorno, profundidad arbitraria, llamadas recursivas o reentrada de la misma rutina en ambos niveles, elección por stdin ni selección dinámica de continuaciones interiores. Las tres vueltas terminan mediante un reloj de fases, no un contador general.

Siguiente intervención propuesta: hacer que la rutina interior atienda dos continuaciones distintas manteniendo el retorno exterior. Separar ese experimento de una pila general; la continuación interior fija es el límite inmediato de P8.
