# Tres invocaciones con relojes auxiliares

2026-11-12. Base `3947d79` (`shared_restore_two_v1`). Tercera invocación del
restaurador compartido en la misma imagen estricta, sin puente host.

## Resultado

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 loader | PASS | Olmstead rc=0, stdout vacío, HALT en CLOCK3=58679. |
| G1 tres celdas | PASS | T1=T2=T3 `70→60→29524→29484→40`; halt_pc=58679. |
| G2 control | PASS | T1=T2=T3=39 con C/C2/C3=117. |
| G3 síntesis | PASS | `synthesize.py` / `synthesis.results.json` aislado. |
| G4 general | NOT_DEMONSTRATED | Objetivo fijo 40; no R/R2; no rearme in-place; no EOF. |

## Hallazgo de layout

`CLOCK2=58397` (two_v1) no admite REARM2: `crazy(ONE,58396)=58392` colisiona.
CLOCK2 relocado a 58585 desbloquea el desvío nativo call2→call3.

## Límites

- Tres relojes distintos, no un solo despachador rearmado.
- G5 R/R2 / bucle / EOF siguen pendientes (`code_rearm_multi_v1/G5_DESIGN.md`).
