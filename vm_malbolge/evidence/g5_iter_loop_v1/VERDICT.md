# Reloj de iteración pc≡2 con dos pases v4

2026-11-12. Base `c8ba028`.

## Resultado

| Puerta | Estado | Evidencia |
| --- | --- | --- |
| G0 | PASS | Olmstead rc=0; HALT en 58376; stdout vacío. |
| G1 | PASS | TA/TB visitadas ×2; HCLOCK ×4 (66→62→76→79); steps≈6009. |
| G2 | PASS | Control altera traza TA (`j*jooj` en H1). |
| G3 | PASS | `synthesize.py` aislado; `synthesis.results.json`. |
| G4 | NOT_DEMONSTRATED | Sin R/R2 mutuo; sin mismo T×3; sin EOF. |

## Hallazgo

El reloj `pc≡2`/66 funciona en imagen real si el JMP de reentrada tiene un
cinturón de `HCLOCK-1` bajo el paseo de `d`. Eso desbloquea la parada limpia
de G5_DESIGN tras N=2 pases de cuerpo.
