# UNIECO — objetivo y puertas anteriores a la exploración

2026-11-11. Base `f6adbc3`: tres reparaciones individuales de fase con cargador estricto; eco compacto en `e42938d`; referencia `cat_real` es un programa distinto y no prueba la combinación.

Objetivo: una única imagen aceptada por el cargador Olmstead, que integre preparación de fases sin alterar entrada/salida y ejecute un eco binario; investigar terminación EOF dentro de esa imagen. Registrar límites con precisión.

G0: imagen fuente entera válida para el cargador; control con una celda inválida rechazado; Olmstead ejecuta el programa, no sólo carga.
G1: antes de la primera vuelta, un único prefijo sin IN/OUT prepara las fases, código y datos necesarios sin interferencias no restauradas; registrar estado completo, orden y hashes. Testigos individuales anteriores no satisfacen G1.
G2: una única imagen emite exactamente 10 000 bytes variables consumidos (incluyendo 00 y ff), sin pérdida ni salida de preparación, y los motores contrastados coinciden en salida y estado donde lo expongan. DLOAD y el bucle se miden, no se infieren.
G3: al agotar la entrada el intérprete Olmstead termina por ejecución del programa y no emite bytes adicionales; contrastar host con parada automática y modelos que entregan EOF como valor. Las diferencias de mecanismo quedan explícitas.
G4: controles negativos detectan las fases y/o preparación y la lectura/escritura; no atribuir causas no observadas.

Subobjetivo medible: ¿puede una misma imagen estricta preparar las celdas 47, 64 y 123 a 74 sin IN/OUT, aunque termine en HALT? Si se obtiene sólo eso, G0–G4 no pasan y se conserva como avance parcial. Si no se encuentra imagen, registrar búsquedas, límites y resultados negativos; no inferir imposibilidad general. No modificar o destruir evidencia anterior. `crazy` exige control de paridad de memoria/orientación antes de sus afirmaciones. Guardar comandos, salida cruda, hashes y controles.
