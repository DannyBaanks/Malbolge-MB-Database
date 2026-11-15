# R/R2 mínimo (1 celda cada uno): preregistro

2026-11-12. Base `4865408`. Objetivo: dos celdas de código R y R2; R restaura
R2; R2 restaura R; dos visitas a R con el opcode original; HCLOCK pc≡2 para
parada; sin islas v4 de 19 celdas (evita explosión N×19). Olmstead rc=0.

G0: HALT limpio. G1: R visitada ×2 con mismo opcode inicial; escrituras de
rearme en R y R2 observadas. G2: control omite un CRAZY de rearme → 2ª visita
a R distinta. G3: síntesis aislada. G4: cuerpo B de trabajo, N≥3, EOF =
NOT_DEMONSTRATED.
