# P13 — preregistro: dirección numérica, journal y retorno indirecto

2026-11-24. Base P12 26fe9a2. Adaptar PureEpoch M1b: fuente X del llamador → journal g(X) → slot X → alterar slot → 10 ROT de journal → restaurar X → 10 ROT del slot → JMP mem[slot]. C1=29524.

- Classic estricto, sin escrituras de memoria del host.
- Una imagen usa el mismo slot para T-1 de destinos 20000,25000,30000; salida ABC. Sin tabla de tokens.
- Journal sobrevive a la alteración y restaura el valor exacto; slot/journal vuelven a C1 tras cada retorno.
- Omitir restore deja C1 y salta a 29525; rotar el slot después de restaurarlo cambia el destino. Ambos deben emitir E en manejadores reales de error.
- Cuatro motores, dos generaciones idénticas y hashes. Enumerar aparte la identidad algebraica sobre las 59049 palabras; no confundirla con ejecución integral en todo el espacio.

Secuencia acotada con código desplegado: reusar el dato no prueba un servicio de código cíclico. No stdin, profundidad >1, direcciones ilegales ni recursión general. Cierre al demostrar o falsar este contrato.
