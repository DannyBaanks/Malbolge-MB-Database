# epoch_dload_compose_in_v1 — plan previo a la medición

2026-11-11. Base: MALBOLGE-MB-DATABASE 55a574f; dialecto Classic permisivo.
Pregunta: ¿se compone DLOAD con IN en un cuerpo de tabla constante, leyendo datos reales?

Construcción: reutilizar la derivación y el constructor de epoch_dload_compose_v1 con opcode 23, sin copiar sus resultados como predicción. Derivación independiente de sus parámetros y comprobación estructural de bytes.

G0: imagen imprimible; comprobación estructural y derivación independiente coinciden.
G1: con 10 000 bytes deterministas, traza y motor scratch cierran 10 000 vueltas, exactamente un IN y un DLOAD por vuelta, con el salto siempre a T; la traza registra exactamente los bytes de entrada en orden. Los motores scratch e independiente coinciden en memoria final, pasos y salida; el oráculo alcanza el mismo tope. Evaluar también runner C con entrada si su interfaz lo admite.
G2: cuatro controles k_off, no_dload, op_phase y dload_phase rompen el criterio de G1; registrar las razones observadas sin predecir un patrón inverificado.
G3: con entrada constante suficientemente larga, repetir el estado completo de la máquina (memoria, a,c,d) en entradas de vuelta; medir periodo y contrastar con mcm de los ciclos cifrados y periodo de d=2. Esto demuestra periodicidad bajo suministro infinito constante, no para cualquier flujo. Para bytes variables no inferir repetición del estado total sin incluir estado de entrada.
G4: documentar EOF separadamente en cada motor, y aceptación por cargador Olmstead. Para las comparaciones de G1 no agotar el flujo.

Mantener salida cruda, hashes, controles, entorno, negativos y alcance. No modificar el pack anterior. Gates definidos antes de correr el probe; no rebajar ante resultados adversos. Experimento preliminar en /tmp por límites de escritura del entorno; promoción posterior al repositorio requiere acceso autorizado por sandbox.
