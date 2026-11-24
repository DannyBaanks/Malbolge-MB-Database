# G5b P10 — reentrada de la misma rutina en dos niveles

2026-11-24. Base: P9 c08fd4d. PASS acotado para G0–G5 de GATES.md.

## Qué se ejecutó

A/B llaman a R por ENTRY=38224. R ejecuta MIX=38246 sobre su contexto V=41000 y DISPATCH=38318 decide, mediante el marco de datos exterior, volver a llamar a ENTRY con el contexto W=43000. Esa segunda entrada ocurre antes del retorno de la primera activación. El segundo MIX usa la misma celda de código; el segundo DISPATCH devuelve a RESUME=38346. RESUME recupera la activación exterior y vuelve a usar DISPATCH para seleccionar el retorno A/B guardado en FO=38130.

No hay una copia de ENTRY, MIX o DISPATCH por nivel. Las instrucciones se rearman a 74 en cada visita. Los dos contextos son datos y marcos distintos; el código de entrada, operación y despacho es común.

Una imagen de 39932 bytes hace seis secuencias:

`ENTRY(V) → MIX(V) → ENTRY(W) → MIX(W) → RESUME → RETURN_A/B`

La profundidad lógica observada es 0→1→2→1→0, con ambos cuerpos ejecutados al mismo pc. La primera activación sigue pendiente cuando se entra a la segunda; RESUME ocurre después de ésta y antes de volver a A/B. Las seis continuaciones exteriores alternan A B A B A B durante tres vueltas.

## Puertas

| Afirmación | Estado | Evidencia |
|---|---|---|
| Mismo ENTRY y MIX en los dos niveles | DEMONSTRATED | plan, eventos de entrada/cuerpo y body_events REA |
| Dos activaciones vivas antes del primer retorno | DEMONSTRATED, profundidad fija 2 | secuencia de eventos y depths REA |
| DISPATCH común antes de reentrar, al retornar del segundo nivel y al finalizar el primero | DEMONSTRATED | tres visitas al mismo pc por activación exterior |
| V exterior preservada durante la escritura interior W | DEMONSTRATED | snapshots, eventos de escritura y mutations |
| FO preservada durante el segundo nivel | DEMONSTRATED en positivo | ausencia de escrituras interiores en FO; control causal |
| Dos generaciones byte a byte y cuatro motores coincidentes | DEMONSTRATED | run01/run02, stdout crudo, results.json, rea.json y hashes |
| Pila dinámica, profundidad arbitraria o recursión general | NOT_DEMONSTRATED | fuera del contrato |

## Resultados y controles

| Caso | Entradas por activación exterior | Retornos A/B | Salida hex | Pasos locales/REA |
|---|---|---|---|---|
| Positivo | R(V), R(W) | A B A B A B | 7c73a07c73a0 | 4659 |
| Cifrar FO durante el retorno interior | R(V), R(W) | B B B | 7c73a0 | 4603 |
| Omitir segunda entrada | R(V) | A B A B A B | fc58fc58fc58 | 4617 |

El control de omisión conserva A/B, pero nunca alcanza profundidad 2 y deja W=23456 intacta. Esto descarta usar solo la salida exterior como prueba de reentrada. El control de FO mantiene ambas entradas pero pierde el retorno A. REA cuenta una escritura interior en FO por llamada exterior de ese control y ninguna en el positivo.

Solo MIX modifica V/W durante la fase de trabajo. Empiezan en 12345 y 23456 y conservan sus valores entre vueltas; el acumulador a transporta el resultado de una activación a la siguiente. El aislamiento es de las escrituras, no independencia algebraica. W regresa a su valor inicial al final del positivo; los estados intermedios prueban sus escrituras.

Olmstead termina con rc=0, clasesbolge con end, trazador local con halt y REA con HALTED. Salidas byte a byte coincidentes. ENTRY/MIX/DISPATCH/FO están restaurados en las cuatro visitas al reloj; ninguna cola JMP cambia. REA combina prefijo/sufijo de hasta 4096 eventos, exige igualdad de status, pasos, salida, digests y eventos solapados, y reconstruye todos los pasos contiguos. A partir de las escrituras reconstruye memoria, argumentos de contexto, banderas y variables; verifica que V siga intacta mientras W está activa y que los retornos retiren los contextos en orden.

## Reproducción

Desde este directorio, con las dependencias de P5/P9:

```sh
python3 -B probe.py /tmp/g5b-p10-new-run
node rea.mjs "$REA_DIST" /tmp/g5b-p10-new-run
python3 verify.py .
sha256sum -c hashes.sha256
```

El directorio debe ser nuevo. REA_DIST apunta al dist compilado de REA; MALBOLGE_MB_DATABASE_ROOT permite otro checkout. verify.py audita los runs conservados; comparar nuevas imágenes con run01. environment.json contiene hashes de dependencias; commands.json registra invocaciones y exit status. Se conservan stdout/stderr de generación, captura y ejecución nativa.

## NOT_DEMONSTRATED y límite inmediato

La reentrada está acotada a dos contextos asignados estáticamente. El marco de V fija una entrada a W; el marco de W fija el retorno a RESUME. No se decide por una entrada externa si debe seguir llamándose, ni se asignan marcos durante la ejecución. Es autollamada acotada del mismo código; no demuestra recursión general ni una pila dinámica de direcciones. Tampoco cubre profundidad mayor que dos, ejecución ilimitada o estado local arbitrario.

Siguiente intervención propuesta: pasar de marcos fijos a selección de contexto/continuación por un estado de profundidad en runtime, con controles de desbordamiento y recuperación del contexto anterior. Ese avance debe medirse por separado.
