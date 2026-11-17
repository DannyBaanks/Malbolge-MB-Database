# G5b P4: permutaciones de cuatro llamadores — resultado

Fecha: 2026-11-17. Resultado dentro del alcance: **PASS G0–G4 y REA, 24/24 órdenes**.

Las 24 permutaciones de `ll`, `lr`, `rl` y `rr` ejecutaron cuatro veces la misma operación (`pc=38058`) sobre la misma variable (`d=40006`). Cada imagen visitó `15000 → 15004 → 15008 → 15012`, transformó `12345 → 12130 → 21990 → 7534 → 21990` y produjo `62e66ee6`.

| Medición | Resultado |
|---|---|
| Cobertura de órdenes | 24/24 permutaciones, cada una con imagen distinta |
| Imágenes positivas | 39 932 bytes por imagen; 48/48 aceptadas por el cargador Classic |
| Olmstead nativo | 48/48 rc 0; salida `62e66ee6` |
| Trazador local | 48/48 `halt`; cuatro llamadas, un sitio y una variable |
| `clasesbolge` | 48/48 `end`; salida `62e66ee6` |
| REA | 24/24 HALTED; 24 trazas completas, 0 truncadas; 4 llamadas a `pc=38058` por orden |
| Pasos | 3748–4014 en ambas generaciones y en REA |
| Flags y operación | `[74,74,74]` en cada continuación; la operación vuelve a 74 |
| G4 | 24/24 parejas idénticas byte a byte; los 24 hashes positivos son distintos |
| Control de fallo conocido | La mutación de P3 produce una llamada, retorno a `15012` y salida `62` |

Los IDs REA, hashes de cada imagen y conteos de eventos están en [REA.md](REA.md) y [rea_summary.json](rea_summary.json). El control reutiliza la imagen P3 con el mismo hash, registrada en [la traza P3](../g5b_flag_return_v3/REA.md).

## Límites

Se cubren exhaustivamente las 24 permutaciones de estos cuatro llamadores fijos. No se demuestra un número distinto de cuatro, llamadores nuevos, varias variables compartidas, entrada/EOF ni recursión.

## Evidencia y reproducción

Consulta [GATES.md](GATES.md), [manifest.json](manifest.json) y [hashes.sha256](hashes.sha256). Las dos generaciones completas, los JSON por orden y las salidas nativas están en `run01/` y `run02/`.
