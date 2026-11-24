# G5b P7 — dos variables, un sitio crazy y retornos repetidos

Fecha: 2026-11-24. Base: P6, commit 26a9030. Resultado: PASS para las puertas G0–G5 de GATES.md.

## Qué demuestra

Una imagen Classic imprimible de 39932 bytes ejecuta A(V) → B(W) tres veces. V=41000 empieza en 12345, W=43000 en 23456. El único sitio crazy de trabajo es pc=38246, compartido por las seis llamadas. Las continuaciones fijan la siguiente selección y las dos variables conservan su estado entre vueltas; el preámbulo no se vuelve a ejecutar.

Cada llamada escribe crazy(a, valor anterior) en la variable seleccionada. La celda no seleccionada conserva su valor. El trazador vigila ambas celdas durante toda la fase de trabajo: todas sus modificaciones proceden de ese único pc. REA reconstruye los valores a partir de todos los eventos de escritura (sin truncamiento) y confirma snapshots, llamadas, retornos y estado final independientemente del trazador local.

El aislamiento es de escrituras: el acumulador a lleva el resultado de una llamada a la siguiente, por lo que los cálculos de V y W sí están acoplados por a.

## Resultados

| Caso | Selección por vuelta | Salida hex | Pasos | Estado final V,W |
|---|---|---|---|---|
| Positivo | V,W | fc7c297305a0 | 3868 | 17925,23456 |
| Control: primero a W | W,W | 8f5103510351 | 3899 | 12345,29521 |
| Control: segundo a V | V,V | fc58fc58fc58 | 3901 | 29272,23456 |
| Selección invertida | W,V | 8f12b90f9239 | 3898 | 12345,40850 |

Todos los casos hacen seis llamadas y retornan A B A B A B. En cada uno, las cuatro visitas al reloj encuentran la bandera y crazy en 74; las colas JMP permanecen intactas. Por tanto, tener retornos correctos por sí solo no demuestra selección correcta: los dos controles conservan los retornos pero incumplen el contrato V,W alternado y dejan una variable sin escribir.

En el positivo, los estados después de cada llamada son:

1. V=17916, W=23456
2. V=17916, W=25724
3. V=15657, W=25724
4. V=15657, W=25715
5. V=17925, W=25715
6. V=17925, W=23456

W vuelve a su valor inicial en la última llamada; las trazas intermedias demuestran que sí se modificó. Comparar solo el estado final habría ocultado esas escrituras.

Olmstead nativo termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED. Las salidas son idénticas en los cuatro motores. Dos generaciones independientes producen las mismas cuatro imágenes y planes, y las mismas salidas, trazas y capturas REA byte a byte.

## Reproducción

Desde este directorio, con BolgeForge, clasesbolge y Olmstead disponibles como en P5/P6:

```sh
python3 -B probe.py /tmp/g5b-p7-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p7-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

REA_DIST apunta al dist compilado de REA. MALBOLGE_MB_DATABASE_ROOT permite seleccionar otro checkout. probe.py rechaza directorios existentes. verify.py audita los runs conservados y sus hashes; comparar una nueva generación con run01. environment.json identifica los componentes mediante SHA-256 y rutas relativas al directorio de desarrollo. commands.json conserva los comandos de generación y sus códigos de salida.

## NOT_DEMONSTRATED

La selección de variable está fijada en el layout de cada imagen, no proviene de stdin. No se demuestra que cada llamador pueda seleccionar indistintamente ambas variables durante una misma ejecución. No cubre más de dos variables, más de dos llamadores repetidos, más de tres vueltas, independencia de los cálculos respecto del acumulador, llamadas anidadas, recursión ni pila general de retornos.

## Siguiente paso

Llamadas anidadas de profundidad fija 2: una rutina exterior llama a una interior y después conserva suficiente estado para volver a su propio llamador. Prerregistrar las continuaciones interior/exterior y un control que corrompa el retorno exterior. Los retornos de P7 son secuenciales: no prueban esa composición.
