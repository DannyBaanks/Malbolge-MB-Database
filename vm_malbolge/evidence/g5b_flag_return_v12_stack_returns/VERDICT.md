# G5b P12 — pila de tokens conectada a los retornos de R

2026-11-24. Base P11 a8cd9be. PASS acotado para G0–G5 de GATES.md.

## Resultado

La pila de P11 gobierna ahora saltos reales de retorno de R. Un cliente guarda A, entra en R a profundidad 1; R guarda A para su continuación interior, reentra por la misma R_ENTRY a profundidad 2 y ejecuta el mismo MIX. El primer pop recupera la continuación RESUME; el segundo pop recupera el retorno exterior A. Esa continuación imprime A e inicia el cliente B, que repite el recorrido y retorna a B. Una misma imagen emite AB y termina con pila vacía.

Se elimina la bandera exterior FO separada de P10. La identidad del retorno exterior reside en S0; la del interior en S1. La profundidad D0/D1 selecciona el contexto V/W de R en runtime después del push; el llamador ya no pasa directamente el puntero V/W como en P10. R_ENTRY y MIX son únicos y se ejecutan en ambos niveles.

El catálogo es explícitamente contextual: (profundidad antes de pop,token) resuelve (1,A)→RETURN_A, (1,B)→RETURN_B, (2,A)→RESUME, (2,B)→error E. Esos destinos son nodos físicos diferentes del programa; pop reduce la ocupación y entra en el nodo seleccionado. A profundidad 2, A es un identificador local de RESUME; no es una dirección numérica global.

## Medición y controles

| Caso | Salida nativa | Profundidad final | Pasos locales/REA |
|---|---|---|---|
| Positivo | AB | 0 | 21310 |
| Cifrar S0 después del primer push A | B | 0 | 21509 |
| Leer slot inferior al pop de profundidad 2 | AE | 1 | 21393 |
| Intentar otro push desde R a profundidad 2 | O | 2 | 21071 |
| Retornar con pila vacía | U | 0 | 21009 |

En el positivo, los contenidos vivos tras push son [A], [A,A], [B], [B,A]. Los pop recuperan en orden (2,A,RESUME), (1,A,RETURN_A), (2,A,RESUME), (1,B,RETURN_B). El verificador reconstruye esa secuencia con una lista LIFO independiente y comprueba que las activaciones de R vuelven en orden.

El control de cifrado conserva en la traza que se guardó A; después modifica S0 durante ejecución, antes de entrar en R. El pop recupera B y salta a RETURN_B, omitiendo RETURN_A. Por tanto, el destino no depende solo de qué cliente fue compilado o de imprimir una etiqueta prevista.

El control de slot erróneo funciona accidentalmente para el primer cliente, porque ambos slots contienen A. Para B, el exterior contiene B y la cima A: leer S0 selecciona el destino inválido de profundidad 2 y emite E. REA detecta exactamente esa discrepancia entre la cima real y el destino físico visitado. Es una razón para probar contenidos distintos a ambos niveles.

Los guardas O/U conservan las cuatro flags de ocupación y tokens y ambas variables de R desde el intento rechazado hasta HALT. En O quedan dos retornos pendientes; se detiene por error conservando el estado, no se simula un vaciado exitoso. En U no se ejecuta R.

## Afirmaciones y evidencia

| Afirmación | Estado | Evidencia |
|---|---|---|
| Push/pop de P11 determina el retorno físico de R | DEMONSTRATED para el catálogo medido | eventos pop/resume/return y pops REA |
| Misma R reentra, contexto seleccionado por ocupación | DEMONSTRATED a profundidad 2 | r_entry, body, D0/D1 y d de MIX |
| Contexto exterior conservado mientras se escribe el interior | DEMONSTRATED | snapshots V/W y escrituras de MIX |
| Cambio runtime del token cambia el retorno | DEMONSTRATED | control tamper_outer, changes y retorno B |
| Guardas conservan estado | DEMONSTRATED | overflow_call y underflow_return |
| Direcciones arbitrarias o recursión general | NOT_DEMONSTRATED | fuera del catálogo/capacidad |

V=50000 y W=51000 conservan su estado entre invocaciones. Solo MIX las modifica en la fase de trabajo, y cada escritura afecta a la variable elegida por la profundidad. El acumulador transporta resultados entre llamadas; no se afirma independencia algebraica de las variables.

Olmstead termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED. Salidas byte a byte coincidentes en los cinco casos. Dos generaciones independientes producen imágenes, planes, trazas, stdout/stderr y capturas REA idénticos. REA conserva cobertura de todos los pasos mediante ventanas de 4096 eventos con solapamiento: exige igualdad de eventos comunes, status, pasos, salida y digests. Reconstruye memoria y las lecturas de slots, y asocia cada pop con la continuación física efectivamente ejecutada. Colas JMP intactas; no se alteró evidencia de P10/P11.

## Reproducción

Desde este directorio, con las dependencias P5/P11:

```sh
python3 -B probe.py /tmp/g5b-p12-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p12-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

La salida debe ir a un directorio nuevo. REA_DIST apunta al dist compilado de REA; MALBOLGE_MB_DATABASE_ROOT permite otro checkout. verify.py audita los runs conservados; comparar nuevas generaciones con run01. environment.json identifica por hash los helpers y motores, incluido P11. commands.json registra comandos y exit status; se conservan logs crudos de generación, ejecución y captura.

## NOT_DEMONSTRATED y siguiente intervención

Pila integrada de capacidad 2, catálogo binario dependiente del nivel y orden exterior A→B fijado en el programa. No almacena direcciones arbitrarias de retorno, no lee órdenes por stdin, no asigna marcos de memoria dinámicamente, no implementa recursión general ni profundidad arbitraria. Los slots y rutas de catálogo son estáticos; ocupación, contenido y selección del retorno cambian durante la ejecución.

Siguiente intervención propuesta: hacer que una entrada runtime elija la continuación exterior y la decisión de reentrada en una sola imagen, conservando el contrato LIFO y las guardas. Ampliar el catálogo o guardar direcciones numéricas debe medirse por separado.
