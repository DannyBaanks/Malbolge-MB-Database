# G5b P5: cinco llamadores secuenciales — resultado

Fecha: 2026-11-17. Resultado dentro del alcance: **PASS G0–G4; REA confirma terminación y salida, pero la cobertura de rutas por eventos queda NOT_DEMONSTRATED**.

La hoja `ll` del router P4 se dividió en `lll` y `llr` con la tercera bandera `f_extra`. En el orden `lll → rr → lr → rl → llr`, las cinco llamadas usan el mismo sitio (`pc=38058`) y la misma variable (`d=40006`). El trazador local observó los cinco retornos `15000 → 15004 → 15008 → 15012 → 15016`, la secuencia `12345 → 12130 → 21990 → 7534 → 21990 → 7534` y la salida `62e66ee66e`.

| Medición | Resultado |
|---|---|
| Cargador Classic | PASS en las dos imágenes positivas y el control |
| Olmstead | 2/2 positivos rc 0 con `62e66ee66e`; control rc 0 con `62` |
| Trazador local | 2/2 positivos `halt`, cinco llamadas/retornos; control `halt`, una llamada y retorno a `15016` |
| `clasesbolge` | `end` y salida coincidente para positivos y control |
| Reproducción | las dos imágenes positivas son idénticas: SHA-256 `c5b56940aa23efeb6f16f8876f818ca28d349bf3d6392add8126385c028c6bab` |
| Control | añadir `f_extra` al primer `lll` selecciona `llr`; la ejecución termina tras una llamada con `62` |
| REA | ambas imágenes `HALTED` con la salida prevista; 4096 eventos capturados de 4723/4806 y truncamiento en ambos casos; las direcciones del router no aparecen en el prefijo |

REA no demuestra las cinco llamadas por eventos porque su límite de captura retuvo solo los primeros 4096 pasos, antes del bloque compartido. La ejecución completa y la salida sí quedaron registradas; la cobertura de sitio/retornos permanece NOT_DEMONSTRATED en REA.

El primer prototipo, que tomó la rama nueva al revés y produjo una sola llamada con `62`, se conserva en [prototype_v1/](prototype_v1/). No cuenta como una corrida positiva.

## Límites

Se probó un orden fijo de cinco llamadores, una variable y un sitio compartido. No se midieron las 120 permutaciones de cinco llamadores, más de cinco hojas, múltiples variables, entrada/EOF ni recursión.

## Evidencia y reproducción

Consulta [GATES.md](GATES.md), [REA.md](REA.md), [manifest.json](manifest.json), [hashes.sha256](hashes.sha256) y [verification.json](verification.json). Las dos imágenes positivas, el control y sus flujos nativos están bajo `run01/` y `run02/`.
