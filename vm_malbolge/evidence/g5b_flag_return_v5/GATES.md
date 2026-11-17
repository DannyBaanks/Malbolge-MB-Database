# G5b P5: cinco llamadores secuenciales

Fecha del protocolo: 2026-11-17. Continúa P2–P4. Este protocolo se fija antes de generar imágenes P5.

## Enmienda de ruteo — 2026-11-17

El primer prototipo se generó bajo el protocolo y terminó tras una sola llamada: el llamador inicial `lll` llegó a `15016` y emitió `62`. La causa fue la orientación de la hoja nueva: `f_extra` en estado inicial sigue la rama `MOVD`. Se conserva como resultado fallido en `prototype_v1/`. La ruta final asigna la rama `MOVD` a `lll` y la rama `NOP` a `llr`; las predicciones y controles siguientes aplican a esta asignación corregida.

Antes de capturar REA, el validador de la herramienta rechazó `event_capture_limit=10000` y declaró un máximo de 4096. Se corrige el límite de captura abajo; el motor conserva el presupuesto completo de 10 000 pasos y se informará cualquier truncamiento.

## Pregunta y alcance

¿Un mismo sitio de operación puede servir cinco llamadores distintos en una secuencia, con una variable y un retorno dedicado para cada llamador? P5 divide la hoja `ll` de P4 en `lll` y `llr` mediante una tercera bandera.

## Predicciones

- Orden medido: `lll → rr → lr → rl → llr`.
- Las cinco llamadas usan `pc=38058` y `d=40006`; cada valor pasa por `12345 → 12130 → 21990 → 7534 → 21990 → 7534`.
- Las cinco continuaciones visitadas son `15000 → 15004 → 15008 → 15012 → 15016`; la salida es `62e66ee66e`.
- Olmstead, `clasesbolge` y el trazador independiente coinciden en salida, orden y terminación.
- Una segunda generación independiente produce la misma imagen byte a byte.
- El control agrega una selección extra de `f_extra` al primer llamador `lll`; debe salir por el retorno `llr` terminal (`15016`) después de una sola llamada y emitir `62`.
- REA termina ambas imágenes, informa la salida completa y permite observar las llamadas al sitio dentro del prefijo retenido; se reporta el estado de truncamiento.

## Puertas

- **G0 — cargador:** las dos imágenes positivas independientes y la imagen de control pasan el cargador Classic.
- **G1 — nativo:** Olmstead devuelve 0; positivo `62e66ee66e`, control `62`.
- **G2 — paridad:** trazador local y `clasesbolge` coinciden en ambas ejecuciones; positivo con cinco llamadas y cinco retornos, control con una llamada al retorno terminal.
- **G3 — control:** la selección extra en `lll` desvía a `15016`, muestra una llamada y conserva solo el primer byte `62`.
- **G4 — reproducción:** las dos imágenes positivas son idénticas byte a byte.
- **REA — traza:** entrada vacía, `eof_mode=olmstead_1998`, máximo 10 000 pasos y captura máxima 4096 eventos (tope declarado por la herramienta); se registra si el límite de captura trunca el flujo.

## Límites previstos

Se mide un orden fijo de cinco hojas, una variable, un sitio compartido y una variante negativa. No se mide el barrido de permutaciones de cinco llamadores, más de cinco hojas, varias variables, entrada/EOF ni recursión.

## Reproducción

Desde la raíz del repositorio:

```sh
RUN_ROOT=$(mktemp -d)
mkdir -p "$RUN_ROOT/run01" "$RUN_ROOT/run02" "$RUN_ROOT/run01/control"
python3 vm_malbolge/evidence/g5b_flag_return_v5/probe.py "$RUN_ROOT/run01/positive.mb" > "$RUN_ROOT/run01/probe.stdout.raw.json" 2> "$RUN_ROOT/run01/probe.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v5/probe.py "$RUN_ROOT/run02/positive.mb" > "$RUN_ROOT/run02/probe.stdout.raw.json" 2> "$RUN_ROOT/run02/probe.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v5/control.py "$RUN_ROOT/run01/control/negative.mb" > "$RUN_ROOT/run01/control/control.stdout.raw.json" 2> "$RUN_ROOT/run01/control/control.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v5/verify.py "$RUN_ROOT/run01" "$RUN_ROOT/run02"
```
