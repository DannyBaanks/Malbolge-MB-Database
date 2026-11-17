# G5b P4: barrido de las 24 permutaciones

Fecha del protocolo: 2026-11-17. Continúa P2/P3. Este protocolo queda fijado antes de generar imágenes P4.

## Pregunta y alcance

¿El mismo sitio de operación, compartido por los cuatro llamadores `ll`, `lr`, `rl` y `rr`, funciona en cada uno de sus 24 órdenes posibles con una sola variable?

## Predicciones

- Las 24 permutaciones terminan con cuatro llamadas en el orden solicitado.
- En cada imagen, las llamadas usan `pc=38058` y `d=40006`; los retornos visitan `15000 → 15004 → 15008 → 15012`.
- Cada permutación transforma `12345 → 12130 → 21990 → 7534 → 21990` y emite `62e66ee6`.
- Para cada permutación, dos procesos de generación independientes producen imágenes idénticas byte a byte.
- Olmstead, `clasesbolge`, el trazador local y REA coinciden en salida y terminación.
- El control de P3 (`rr → ll → rl → lr`, toggle extra de `f_root` en `rr`) conserva la salida de control `62` en la continuación terminal `15012`.

## Puertas

- **G0 — cargador:** las 48 imágenes (dos generaciones de 24 órdenes) pasan la validación Classic del ensamblador.
- **G1 — nativo:** Olmstead devuelve 0 y cada salida es `62e66ee6`.
- **G2 — paridad:** trazador local y `clasesbolge` terminan con sus estados previstos, salida exacta, cuatro llamadas al sitio y valores esperados.
- **G3 — control:** el control heredado de P3 conserva su salida `62`, una llamada y retorno terminal.
- **G4 — reproducción:** cada una de las 24 imágenes de `run01` es idéntica a su pareja de `run02`.
- **REA — traza:** entrada vacía, `eof_mode=olmstead_1998`, máximo 10 000 pasos, captura máxima 4096 eventos; las 24 trazas deben terminar sin truncamiento y mostrar cuatro visitas a `pc=38058`, con `d=40006`.

El control P3 se incluye de nuevo como control de fallo conocido; P4 no afirma que ese control mutado corresponda a cada orden.

## Límites previstos

El barrido cubre las 24 permutaciones de estos cuatro llamadores fijos. No cubre cantidades distintas de cuatro, llamadores nuevos, variables múltiples, entrada/EOF ni recursión.

## Reproducción

Desde la raíz del repositorio; el script elige y registra las permutaciones en orden lexicográfico.

```sh
RUN_ROOT=$(mktemp -d)
mkdir -p "$RUN_ROOT/run01" "$RUN_ROOT/run02" "$RUN_ROOT/run01/control"
python3 vm_malbolge/evidence/g5b_flag_return_v4/sweep.py "$RUN_ROOT/run01" > "$RUN_ROOT/run01/sweep.stdout.raw.json" 2> "$RUN_ROOT/run01/sweep.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v4/sweep.py "$RUN_ROOT/run02" > "$RUN_ROOT/run02/sweep.stdout.raw.json" 2> "$RUN_ROOT/run02/sweep.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v4/control.py "$RUN_ROOT/run01/control/negative.mb" > "$RUN_ROOT/run01/control/control.stdout.raw.json" 2> "$RUN_ROOT/run01/control/control.stderr.raw.txt"
python3 vm_malbolge/evidence/g5b_flag_return_v4/verify_repro.py "$RUN_ROOT/run01" "$RUN_ROOT/run02"
```
