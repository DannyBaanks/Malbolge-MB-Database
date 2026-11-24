# G5b P9 — dos continuaciones interiores, retorno exterior preservado

2026-11-24. Base: P8, commit 1a21d6f. PASS para las puertas G0–G5 de GATES.md.

## Capacidad medida

Una sola imagen Classic de 39932 bytes ejecuta seis llamadas exteriores alternando A/B. Dentro de cada llamada exterior, O llama dos veces al mismo sitio interior crazy: primero vuelve a X y después a Y, antes del retorno a A/B. Son doce llamadas interiores y seis recorridos de profundidad 0→1→2→1→2→1→0.

X e Y son continuaciones físicas diferentes, seleccionadas por FI; no son dos copias de crazy. La misma imagen cubre A/X, A/Y, B/X y B/Y. La bandera exterior FO conserva la identidad A/B durante ambas llamadas interiores: las trazas REA no contienen escrituras en FO en esos intervalos del positivo. FI vale 70 en la primera entrada interior (retorno X) y 74 en la segunda (retorno Y); en ambos retornos se recupera a 74. FO, FI y crazy vuelven a 74 en las cuatro visitas al reloj; las colas JMP se conservan.

El único sitio interior modifica V=41000 con la recurrencia crazy, conservando el valor entre invocaciones. El preámbulo deja a=55999, V0=12345. La salida se emite una vez por retorno exterior, después de la segunda llamada interior: las doce llamadas interiores se verifican por trazas y recurrencia, no por contar bytes de salida.

| Caso | Recorrido interior por O | Retornos exteriores | Salida hex | Pasos locales/REA |
|---|---|---|---|---|
| Positivo | I X I Y | A B A B A B | 585858585858 | 4474 |
| FI sin preparar | I Y | A B A B A B | fc58fc58fc58 | 4318 |
| Cifrar FO durante el segundo retorno interior | I X I Y | B B B | 585858 | 4413 |

El primer control mantiene A/B pero omite X y la segunda llamada interior: tener retornos exteriores correctos no demuestra continuación interior correcta. El segundo mantiene X/Y y cifra FO dentro del retorno interior, desviando los retornos exteriores. Los dos controles incumplen el contrato nominal por causas distintas y medibles.

Olmstead nativo termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED; salidas coincidentes byte a byte. Dos generaciones independientes tienen idénticas imágenes, planes, trazas, salidas crudas y capturas REA. verify.py comprueba explícitamente las cuatro combinaciones exterior/interior, los controles y todos los hashes.

## Captura REA: límite encontrado y resuelto

Categoría GAP de observabilidad: las ejecuciones superan el límite de 4096 eventos retenidos por captura. rea_prefix_only.mjs conserva el intento inicial, que falla su aserción de no truncamiento; stdout/stderr y exit=1 están preservados. Esa falla no es un fallo del programa Malbolge.

rea.mjs ejecuta dos capturas: prefijo 1..4096 y sufijo max(1,pasos-4095)..pasos. Compara status, pasos, salida y digests inicial/final entre ejecuciones; exige igualdad de cada evento del solapamiento. Su unión debe contener exactamente cada paso 1..N, sin huecos ni duplicados. Después reconstruye las banderas y V usando todos los eventos de escritura y verifica llamadas y retornos contra el trazador local. rea.json conserva rangos, tamaño del solapamiento, cobertura completa, eventos del sitio interior y las mediciones verificadas.

## Reproducción

Desde este directorio, con las dependencias de P5/P8:

```sh
python3 -B probe.py /tmp/g5b-p9-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p9-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

Los directorios de salida deben ser nuevos. REA_DIST apunta al dist compilado de REA y MALBOLGE_MB_DATABASE_ROOT permite otro checkout. verify.py audita los runs conservados; comparar una nueva generación con run01. environment.json identifica las dependencias con SHA-256; commands.json registra los comandos y exit status. Los logs crudos de generación y captura se conservan.

## NOT_DEMONSTRATED

X/Y están fijadas en el layout y se recorren siempre en ese orden dentro de cada O. La selección no proviene de stdin. Cada nivel conserva su propia bandera asignada estáticamente. No se demuestra pila de direcciones, recursión, reentrada de la misma rutina en ambos niveles, profundidad mayor que dos, ejecución ilimitada ni llamadas arbitrarias. El reloj termina tras tres vueltas.

Siguiente intervención propuesta: probar reentrada de una misma rutina en dos niveles, con contexto de retorno seleccionado por profundidad; la asignación estática de banderas por nivel sigue siendo el límite frente a una pila general.
