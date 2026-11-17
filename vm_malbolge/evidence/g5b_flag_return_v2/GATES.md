# G5b P2: una operación compartida con cuatro llamadores

Fecha del pack: 2026-11-16. Continúa la medición G5b P1 de `g5b_flag_return_v1`.

## Pregunta y alcance

¿Una imagen Classic puede recorrer cuatro llamadores secuenciales que comparten una única operación y una única variable, y volver a cuatro continuaciones distintas? Se fija el orden `ll → lr → rl → rr`; no se generaliza a una cantidad arbitraria de llamadores.

## Predicciones de la imagen positiva

- Sitio compartido: `pc=38058`; variable: `d=40006`.
- Continuaciones: `15000 → 15004 → 15008 → 15012`.
- Salida: `62e66ee6`; flags de ruta y sitio compartido en `74` al entrar en cada continuación.
- Los JMP de retorno permanecen sin cambios.

## Control negativo

Se omite deliberadamente el ajuste de bandera raíz en `lr`. Predicción: la ruta pasa de `ll` directamente a `rr`, visita `15000 → 15012`, produce `62e6` y se detiene antes de las otras dos llamadas.

## Puertas

- **G0 — imagen:** validar que la imagen completa satisface el cargador Classic.
- **G1 — ejecución nativa:** Olmstead termina con código 0 y produce las salidas previstas.
- **G2 — paridad:** trazador local y `clasesbolge` coinciden con la salida; verificar sitio, puntero, continuaciones, flags y JMP.
- **G3 — control:** la omisión de la bandera cambia la ruta y la salida según la predicción.
- **G4 — reproducción:** dos ejecuciones separadas del generador producen imágenes positivas idénticas byte a byte.
- **REA — traza:** guardar las referencias de evidencia para positivo y control, con salida y número de pasos.

La primera imagen positiva y el control se exploraron antes de formalizar este pack; por eso este documento describe el protocolo y alcance, no una preregistración previa a toda exploración.

## Dependencias y reproducción

Se esperan `BolgeForge` y `Malbolge-PureEpoch` junto a este repositorio; `clasesbolge` se espera en la ruta relativa `../../clasesbolge/tools/malbolge.py`. Desde otro entorno, configura `MALBOLGE_MB_DATABASE_ROOT`, `BOLGEFORGE_ROOT`, `OLMSTEAD_BIN` y `CLASESBOLGE_MALBOLGE`. Los scripts aceptan una ruta de imagen nueva y conservan stdout/stderr nativos como archivos `.native.*.raw` junto a ella.

```sh
RUN_ROOT=$(mktemp -d)
mkdir -p "$RUN_ROOT/run01" "$RUN_ROOT/run02"
python3 vm_malbolge/evidence/g5b_flag_return_v2/probe.py "$RUN_ROOT/run01/positive.mb" > "$RUN_ROOT/run01/probe.stdout.raw.json" 2> "$RUN_ROOT/run01/probe.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v2/control.py "$RUN_ROOT/run01/negative.mb" > "$RUN_ROOT/run01/control.stdout.raw.json" 2> "$RUN_ROOT/run01/control.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v2/probe.py "$RUN_ROOT/run02/positive.mb" > "$RUN_ROOT/run02/probe.stdout.raw.json" 2> "$RUN_ROOT/run02/probe.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v2/verify_repro.py "$RUN_ROOT/run01" "$RUN_ROOT/run02"
cmp "$RUN_ROOT/run01/positive.mb" "$RUN_ROOT/run02/positive.mb"
```
