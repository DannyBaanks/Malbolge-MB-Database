# G5b P13 — dirección numérica completa, journal y retorno indirecto

2026-11-24 (America/Mexico_City; cierre 2026-11-25 UTC). Base P12 26fe9a2. PASS acotado para GATES.md.

## Resultado concreto

Una única imagen Classic de 39932 bytes guarda sucesivamente 19999,24999,29999 en el mismo slot=50000. Son palabras numéricas completas, no tokens A/B. Cada valor representa destino-1 por el incremento del PC tras JMP. El salto ejecuta JMP con d=50000, lee mem[50000] y llega respectivamente a 20000,25000,30000; esas continuaciones imprimen ABC.

Los llamadores proporcionan explícitamente sus direcciones en celdas fuente. La fase de trabajo las carga mediante diez ROT, conservándolas, y escribe el slot con instrucciones nativas. El host no parchea memoria durante la ejecución. Los valores de esas fuentes son conocidos al ensamblar esta prueba; la selección desde stdin queda pendiente.

## PureEpoch: protocolo adaptado

Se adapta la lógica de journal M1b documentada en epoch_journal_state_v2, no se enlaza un proceso externo PureEpoch ni se reubica su binario. La secuencia es:

1. Con journal y slot inicializados a C1=29524, cargar la dirección X y escribir journal=g(X)=crazy(X,C1).
2. Escribir slot=crazy(g(X),C1)=X.
3. Alterar el slot hasta C1; el journal sigue conteniendo g(X).
4. Diez ROT sobre el journal conservan su contenido y cargan g(X) en a.
5. Restaurar slot=crazy(g(X),C1)=X.
6. Diez ROT sobre el slot conservan X y lo recuperan exactamente en a.
7. Colocar d sobre el slot y ejecutar JMP mem[d].

Tras cada retorno, el slot y el journal se rearman a C1 antes de guardar la siguiente dirección. El rearme usa primero crazy(C1,celda)=E y después crazy(E,E)=C1; el orden de operandos difiere del usado en g(X). C1 se lee desde una fuente de diez trits 1, invariante bajo ROT. La prueba comprueba los estados intermedios; no deduce restauración solo a partir de stdout.

## Mediciones y controles

| Caso | Valor leído por JMP | Destinos físicos | Salida | Pasos locales/REA |
|---|---|---|---|---|
| Positivo | 19999,24999,29999 | 20000,25000,30000 | ABC | 11834 |
| Omitir RESTORE | 29524 | 29525 | E | 11349 |
| ROT adicional del slot restaurado | 26349 | 26350 | E | 11353 |

Los manejadores E son código real en esos destinos erróneos. En el segundo control la dirección sí se restauró correctamente a 19999 y luego se alteró durante ejecución; JMP usa el valor alterado. En el primero se conserva el journal pero no se restaura el slot, de modo que salta según C1. Ambos distinguen contenido del journal, recuperación exacta y destino efectivo.

Olmstead termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED; salidas byte a byte idénticas. REA reconstruye todas las escrituras y snapshots a partir de ventanas solapadas de eventos, verifica igualdad de eventos comunes y estado final entre ejecuciones, exige pasos contiguos 1..N, y comprueba que el evento inmediatamente posterior a cada JMP está en (valor_guardado+1)%59049.

Dos generaciones independientes tienen idénticas imágenes, planes, trazas, stdout/stderr y capturas REA. El slot y el journal son las mismas celdas en las tres transacciones y quedan ambos en C1 al finalizar el positivo.

## Afirmaciones

| Afirmación | Estado | Evidencia |
|---|---|---|
| Guardar y recuperar una dirección completa en una celda | DEMONSTRATED para las tres direcciones medidas | snapshots slot/journal/source_loaded/read_back |
| Restauración tras alterar el slot | DEMONSTRATED | clobbered→journal_loaded→restored y control skip_restore |
| Retorno numérico indirecto sin tabla de tokens | DEMONSTRATED | JMP con d=50000 y tres PC efectivos |
| Rearme y reutilización del mismo dato/journal | DEMONSTRATED en tres transacciones | begin/rearmed y estado final |
| crazy(crazy(X,C1),C1)=X para todas las palabras de diez trits | DEMONSTRATED algebraicamente por enumeración independiente Python y REA JS | algebra.json y algebra_rea.json, 59049 palabras |
| Ejecución integral para las 59049 direcciones | NOT_DEMONSTRATED | solo tres destinos legales ejecutados |

## Reproducción

Desde este directorio, con las dependencias de P5:

```sh
python3 -B probe.py /tmp/g5b-p13-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p13-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

Usar un directorio de salida nuevo. REA_DIST apunta al dist compilado de REA y MALBOLGE_MB_DATABASE_ROOT permite otro checkout. verify.py audita los runs conservados; comparar nuevas generaciones con run01. environment.json identifica motores/helpers por SHA-256 y commands.json registra invocaciones y exit status. Se conservan stdout/stderr de generación, captura y ejecución nativa.

## NOT_DEMONSTRATED y próximo paso

La prueba reutiliza el almacenamiento y rearma máscaras; el código de las tres transacciones está desplegado en segmentos distintos y se ejecuta una vez por segmento. No demuestra un servicio cíclico reutilizando las mismas instrucciones ni integra aún el slot numérico con los dos niveles de R. No hay entrada de dirección desconocida al ensamblar, pila numérica de varias posiciones, retorno a toda celda del espacio físico ni recursión general. Las celdas de aterrizaje anterior al destino son pads reservados cuyo cifrado no afecta al programa.

Siguiente intervención: suministrar una dirección completa por entrada runtime y comprobar guardado, recuperación y salto en la misma imagen para distintos valores legales. Después: componer esta representación numérica con los dos slots y el control de ocupación de P12, conservando el contrato LIFO.
