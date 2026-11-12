# Dos invocaciones con rearme auxiliar

2026-11-12. Base `4172c2e` (`shared_restore_one_v1`). Preregistro en
`GATES.md` / `DESIGN.md`. Segunda invocación del restaurador compartido en la
misma imagen estricta, sin puente host.

## Resultado

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 loader | PASS | Imágenes estrictas; Olmstead rc=0, stdout vacío, HALT en CLOCK2. |
| G1 dos celdas | PASS | `verification.results.json`: T1 y T2 `70→…→40`; T3=REARM-1=57564; halt_pc=58397. |
| G2 control | PASS | Call1 ctrl 39 → T1=39; C2=117 → T2=39. Positivo T1=T2=40. |
| G3 síntesis | PASS | `synthesize.py` / `synthesis.results.json` en árbol aislado. |
| G4 general | NOT_DEMONSTRATED | Objetivo fijo 40; no N>2, no EOF, no REA window pack. |

## Diseño que desbloqueó el nativo

En lugar de rearmar el reloj y la constante de call1, call2 usa **CLOCK2**
(pc≡23, valor 117) y **C2** (120 / 117 en control). STORE solo hace JMP a S2.
Así no hace falta escribir clock/C en caliente entre invocaciones.

Camino call1 (nativo):

1. Phase1 divert `T+4=T+1`, `T+2=PCRAZY-1` → CRAZY privado escribe T+3←57564.
2. ROT@C + crazy3 (`→29484`) con primitivas compartidas.
3. REARM: crazy final `→40` sobre T1.
4. STORE → S2 → call2 sobre T2 con CLOCK2 hasta HALT (clock2=58).

## Límites

- Objetivo fijo 40 (ruta `crazy(q,q)`).
- REA vs scratch en la ventana call1→call2: no capturado en este pack.
- G5 R/R2 / bucle / EOF: siguen pendientes.
