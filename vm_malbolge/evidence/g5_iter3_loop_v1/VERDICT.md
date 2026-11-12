# Tres pases de cuerpo + reloj de iteración

2026-11-12. Extiende `g5_iter_loop_v1` @ `3ee057f` a N=3 cuerpos.

## Resultado

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 | PASS | Olmstead rc=0; HALT 58376. |
| G1 | PASS | TA/TB/TC ×2 visitas; HCLOCK ×4 `[66,62,76,79]`; ~7682 pasos. |
| G2 | PASS | Control cambia imagen/H1. |
| G3 | PASS | `synthesize.py` / `synthesis.results.json`. |
| G4 | NOT_DEMONSTRATED | Sin R/R2 mutuo ni mismo T reentrado. |
