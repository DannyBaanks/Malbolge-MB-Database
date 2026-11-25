# P9 — preregistro: dos continuaciones interiores

2026-11-24. Base P8 1a21d6f. Contrato: cada llamada exterior O invoca dos veces al mismo I/crazy; el primer retorno interior es X y el segundo Y, antes de retornar a A/B. La misma imagen debe cubrir las combinaciones A/X, A/Y, B/X y B/Y durante tres vueltas A/B.

- G0: un O_ENTRY, un I_ENTRY/crazy, dos continuaciones físicas diferentes X/Y. Cargador Classic estricto.
- G1: seis grupos O → I → X → I → Y → A/B; 12 llamadas interiores, seis exteriores. Profundidad 0→1→2→1→2→1→0.
- G2: FO conserva la identidad A/B durante ambas llamadas interiores. FI selecciona X o Y y queda rearmada a 74 en ambos retornos. FO/FI/crazy recuperan 74 en cada vuelta; colas JMP intactas.
- G3: recurrencia crazy exacta en V persistente; solo el sitio interior modifica V.
- G4: control que omite preparar FI debe retornar a Y primero, omitiendo X, aunque A/B sigan correctos. Control que cifra FO durante el segundo retorno interior debe conservar X/Y y romper A/B. Ambos deben ser detectados por el contrato nominal.
- G5: cuatro motores coinciden en salida y parada; REA confirma recorridos y ausencia de escrituras interiores en FO en el positivo. Dos generaciones idénticas byte a byte.

Alcance: rutas X/Y y A/B cableadas, banderas por nivel, tres vueltas. No es pila general, recursión, profundidad arbitraria ni selección por stdin. Cierre al satisfacer o falsar estas puertas.
