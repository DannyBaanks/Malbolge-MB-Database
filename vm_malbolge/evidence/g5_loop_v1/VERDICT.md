# Rearme in-place del CLOCK: bloqueo estructural

2026-11-12. Base `d56a602`.

## Resultado

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 | NOT_DEMONSTRATED | No hay imagen nativa de rearme in-place. |
| G1 álgebra + same-CLOCK tras host rearm | PASS | `scratch_clock_rearm.results.json`: T2=40, halt=CLOCK. |
| G2 | NOT_DEMONSTRATED | Sin imagen de control nativa. |
| G3 | NOT_DEMONSTRATED | Sin síntesis de imagen completa. |
| G4 bloqueo | PASS (negativo) | `scratch_aux_probe1.json` + búsqueda: `crazy(*,70)` no alcanza CLOCK-1; d++ acopla CLOCK con CLOCK+1. |

## Implicación

N>2 con el patrón shared-restore sigue siendo pool de relojes (three_v1) o
islas v4 + reloj de iteración pc≡2 (`code_rearm_multi_v1/G5_DESIGN.md`), no
rearme in-place del despachador compartido.
