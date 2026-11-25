# P11 — preregistro: pila dinámica acotada de tokens de retorno

2026-11-24. Base P10 eedfafb. Alcance: primitiva nativa push/pop de capacidad 2, catálogo A/B, ocupación y contenido modificados en runtime. Secuencia de operaciones compilada en una imagen; la profundidad y el token que sale dependen del estado mutable, no de un destino de marco fijado por nivel como P10.

- G0: imagen Classic estricta, código genérico compartido de entrada/selección y salida. Dos flags de ocupación y dos de contenido A/B.
- G1: llenar, vaciar, reutilizar ambas posiciones y sobrescribir tokens viejos; resultados pop concuerdan con una pila LIFO abstracta. Token devuelto como byte A/B.
- G2: push a profundidad 2 emite O y conserva estado; pop a profundidad 0 emite U y conserva estado. Cada operación termina con ocupación válida.
- G3: contenido y profundidad de la pila se escriben durante la fase de trabajo y se conservan entre operaciones. El pop no puede deducirse solo del índice de operación: lee el estado del slot seleccionado por ocupación.
- G4: omitir actualización de ocupación al push y leer el slot equivocado al pop deben romper la especificación abstracta. Conservar trazas y discrepancias.
- G5: Olmstead, clasesbolge, trazador local y REA concuerdan; dos generaciones byte a byte y hashes.

No demuestra aún pila de direcciones numéricas arbitrarias, asignación de memoria dinámica, capacidad mayor que dos, entrada stdin ni integración de esta primitiva con R. Es el siguiente componente necesario, no una afirmación de recursión general. Cierre al verificar o falsar este contrato.

## Enmienda tras el primer intento, antes de ejecutar la versión reducida

El script combinado de 13 operaciones no ensambla: preamble_end=70745, por encima del código y de la memoria Classic. Se conserva oversized_probe.py y run01.stderr.raw.txt (exit=1). Se divide en cuatro programas acotados: LIFO (4 operaciones), reutilización (6), overflow (5) y underflow (4). Los controles se aplican al programa LIFO. Las puertas semánticas no cambian; no se atribuye cobertura de toda la secuencia combinada a una única imagen.

Tras los primeros runs corregidos, se añade un segundo programa de reutilización (6 operaciones) para cubrir explícitamente la sobrescritura del slot superior; el primero cubre la del inferior. Se conservan los runs intermedios y probe_pre_top.py. Los runs finales verifican ambas posiciones.
