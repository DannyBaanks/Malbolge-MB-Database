# G5b P11 — primitiva de pila dinámica acotada de tokens

2026-11-24. Base P10 eedfafb. Resultado: PASS acotado para G0–G5 de GATES.md y sus enmiendas. Esto construye la primitiva push/pop; todavía no la conecta con la rutina reentrante R de P10.

## Qué cambia respecto de P10

La selección ya depende de ocupación y contenido modificados por el propio programa Malbolge. Dos flags D0/D1 representan profundidad 0,1,2 y dos flags S0/S1 guardan tokens de retorno A/B. Cada push consulta la ocupación, escribe el slot correspondiente y actualiza profundidad; cada pop consulta la ocupación y el contenido del slot superior, devuelve A/B y reduce profundidad. Las posiciones se reutilizan y los valores viejos se sobrescriben en runtime.

Los tokens están codificados como estados 74=A y 70=B en celdas de código auto-modificable. D0/D1 codifican vacío=(74,74), una posición=(70,74), lleno=(70,70). Las ramas de lectura restauran el flag tras consultarlo; las mutaciones lógicas se aplican por cifrado dirigido de la celda. Los estados intermedios de esa microsecuencia no constituyen operaciones atómicas; la validez de ocupación se exige en sus fronteras. No hay concurrencia.

El host ensambla el grafo y ejecuta un modelo de lista para verificarlo; no ejecuta los push/pop del programa objetivo ni imprime su resultado. A/B/U/O salen por ROT/OUT nativos: la rama elegida selecciona una constante diagnóstica local al punto de salida. El emisor está compartido; esas constantes de salida no son el almacenamiento del stack.

## Programas medidos

| Programa | Operaciones | Salida nativa | Resultado |
|---|---|---|---|
| LIFO | push A, push B, pop, pop | BA | PASS |
| Reutilizar slot inferior | push B, pop, push A, push B, pop, pop | BBA | PASS |
| Reutilizar slot superior | push A, push B, pop, push A, pop, pop | BAA | PASS |
| Desbordamiento | push A, push B, push A, pop, pop | OBA | PASS |
| Pila vacía | pop, push B, pop, pop | UBU | PASS |
| Control: omitir profundidad al push | mismo programa LIFO | UU | incumplimiento detectado |
| Control: leer slot inferior al pop de pila llena | mismo programa LIFO | AA | incumplimiento detectado |

Los guardas O y U dejan exactamente las cuatro flags de ocupación/contenido como estaban antes de la operación; no solo conservan profundidad. La salida BA posterior a O confirma que el push rechazado no reemplazó la cima B. Ambos slots se reutilizan en los programas correspondientes y se comparan contenidos y profundidad contra un modelo abstracto después de cada operación, no solo al final.

## Afirmaciones y evidencia

| Afirmación | Estado | Evidencia |
|---|---|---|
| Ocupación y tokens cambian en runtime | DEMONSTRATED | changes, flag_reads y fronteras de operaciones |
| LIFO para el catálogo A/B y capacidad 2 | DEMONSTRATED en los programas medidos | modelo de lista, emisiones y stdout nativo |
| Reutilización de ambas posiciones | DEMONSTRATED | programas reuse y reuse_top |
| Overflow y underflow conservan estado | DEMONSTRATED | snapshots completos antes/después de O/U |
| Controles rompen la especificación | DEMONSTRATED | specification.failures y salidas UU/AA |
| Pila dinámica de direcciones arbitrarias integrada con R | NOT_DEMONSTRATED | aún fuera de la primitiva |

Olmstead termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED para los programas positivos y los controles. Salidas coincidentes byte a byte. REA reconstruye todas las escrituras, lecturas de flags, profundidad y tokens desde eventos reales. Las capturas se dividen en ventanas de hasta 4096 eventos con un paso de solapamiento; status, pasos, salida, digests y eventos comunes deben coincidir entre ventanas y su unión debe contener exactamente todos los pasos 1..N. Se conservan rangos y conteos.

run04/run05 son las generaciones finales: imágenes, planes, trazas, salidas y capturas REA idénticos byte a byte. run02/run03 y probe_pre_top.py conservan las primeras pruebas reducidas, antes de añadir el caso de reutilización superior. Todas las imágenes cargan bajo las reglas Classic estrictas y las colas JMP permanecen intactas.

## Fallo de presupuesto preservado

Categoría GAP de construcción: la secuencia combinada inicial de 13 operaciones no llegó a ejecutar Malbolge. El preámbulo sintetizado termina en 70745 y solapa el código; tampoco cabe en las 59049 celdas Classic. oversized_probe.py y run01.stdout/stderr.raw.txt preservan el generador y el exit=1. El programa se dividió en casos menores, con un modelo abstracto común. No se atribuye la ejecución de toda la secuencia combinada a una única imagen, ni se resuelve con ello el presupuesto de un intérprete de operaciones general.

## Reproducción

Desde este directorio, con las dependencias de P5/P10:

```sh
python3 -B probe.py /tmp/g5b-p11-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p11-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

La salida debe ir a un directorio nuevo. REA_DIST apunta al dist compilado de REA; MALBOLGE_MB_DATABASE_ROOT permite otro checkout. verify.py audita run04/run05 contra una lista abstracta independiente; comparar nuevas generaciones con run04. environment.json identifica dependencias con SHA-256 y commands.json registra comandos y exit status. Se conservan los logs crudos de ensamblado, generación, captura y ejecución nativa.

## NOT_DEMONSTRATED y siguiente intervención

Capacidad 2 y catálogo binario A/B; no guarda todavía palabras arbitrarias ni direcciones numéricas de retorno. Cada programa tiene su secuencia de operaciones compilada en el grafo de datos; no hay intérprete de órdenes por stdin ni bucle general de comandos. La profundidad y el contenido son dinámicos; la capacidad, el catálogo, las celdas y la secuencia de operaciones están fijados al ensamblar. No hay asignación dinámica de memoria, recursión general, pila ilimitada ni prueba exhaustiva de todas las secuencias A/B.

Siguiente intervención: conectar el token que devuelve pop con el salto a su continuación A/B y sustituir por esa pila el contexto de retorno fijo de R. La integración debe conservar guardas y demostrar push de retorno, reentrada y pop en orden. En paralelo, el crecimiento del preámbulo queda como límite medido para un intérprete reutilizable de operaciones; no es una imposibilidad de Malbolge.
