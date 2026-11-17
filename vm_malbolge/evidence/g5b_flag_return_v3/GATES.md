# G5b P3: secuencia cruzada con cuatro llamadores

Fecha de protocolo: 2026-11-16. Continúa G5b P2; no se ejecutó una imagen P3 antes de fijar estas predicciones.

## Pregunta y alcance

¿El sitio compartido funciona cuando los cuatro llamadores se enlazan en el orden cruzado `rr → ll → rl → lr`, distinto del recorrido por hojas contiguas de P2? Se mantienen una variable, un sitio de operación y una ejecución por imagen. Este P3 mide un orden alternativo; no equivale a probar las otras 23 permutaciones.

## Predicciones positivas

- El orden de llamadas y retornos será `rr → ll → rl → lr`.
- El sitio común seguirá en `pc=38058`, con `d=40006`.
- Las continuaciones por orden serán `15000 → 15004 → 15008 → 15012`; cada una deja flags y sitio compartido en `74`.
- La cadena del valor seguirá `12345 → 12130 → 21990 → 7534 → 21990`; la salida prevista es `62e66ee6`.
- Los JMP de retorno no cambian; Olmstead, el trazador local y `clasesbolge` terminan con sus estados normales y coinciden en bytes.

## Control negativo

El primer llamador `rr` debe dejar la bandera raíz en su fase inicial. El control añade un toggle de `f_root`; eso cambia la selección de `rr` a la hoja `lr`, que es la continuación terminal de este orden. Predicción: una sola llamada, visita a `15012`, salida `62` y HALT.

## Puertas

- **G0 — imagen:** el ensamblador acepta todas las celdas por el cargador Classic.
- **G1 — nativo:** Olmstead devuelve 0 y las salidas positivas/control son las previstas.
- **G2 — paridad:** trazador local y `clasesbolge` coinciden; verificar orden, cuatro llamadas positivas, un sitio, una variable, flags y JMP.
- **G3 — control:** el toggle extra del primer `rr` selecciona `lr` y corta el recorrido tras una llamada.
- **G4 — reproducción:** dos generaciones positivas son idénticas byte a byte.
- **REA — traza:** entrada vacía, `eof_mode=olmstead_1998`, máximo de 10 000 pasos y captura de hasta 4096 eventos. Ambas corridas deben quedar completas, sin truncamiento, y registrar visitas al sitio y continuaciones esperadas.

## Dependencias y reproducción

Se esperan `BolgeForge` y `Malbolge-PureEpoch` junto a este repositorio; `clasesbolge` se espera en la ruta relativa `../../clasesbolge/tools/malbolge.py`. Si cambian de ubicación, configura `MALBOLGE_MB_DATABASE_ROOT`, `BOLGEFORGE_ROOT`, `OLMSTEAD_BIN` y `CLASESBOLGE_MALBOLGE`.

```sh
RUN_ROOT=$(mktemp -d)
mkdir -p "$RUN_ROOT/run01" "$RUN_ROOT/run02"
python3 vm_malbolge/evidence/g5b_flag_return_v3/probe.py "$RUN_ROOT/run01/positive.mb" > "$RUN_ROOT/run01/probe.stdout.raw.json" 2> "$RUN_ROOT/run01/probe.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v3/control.py "$RUN_ROOT/run01/negative.mb" > "$RUN_ROOT/run01/control.stdout.raw.json" 2> "$RUN_ROOT/run01/control.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v3/probe.py "$RUN_ROOT/run02/positive.mb" > "$RUN_ROOT/run02/probe.stdout.raw.json" 2> "$RUN_ROOT/run02/probe.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v3/verify_repro.py "$RUN_ROOT/run01" "$RUN_ROOT/run02"
cmp "$RUN_ROOT/run01/positive.mb" "$RUN_ROOT/run02/positive.mb"
```
