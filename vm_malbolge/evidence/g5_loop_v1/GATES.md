# G5 loop brick: in-place CLOCK/C rearm + same-clock call2

2026-11-12. Base `d56a602` (`shared_restore_three_v1`). Objetivo: tras call1
(T1 70→40), restaurar **el mismo** reloj de despacho `58303` (58→117) y la
constante C (40→120) dentro de Malbolge, luego call2 sobre T2 con ese mismo
reloj hasta HALT. Sin CLOCK2/CLOCK3. El reloj de iteración pc≡2 (valor 66) se
reserva para el bucle R/R2; este pack demuestra el ladrillo de rearme auxiliar.

G0: Olmstead rc=0, sin I/O host. G1: T1=40, CLOCK y C rearman, T2=40, HALT en
CLOCK. G2: control rompe call2 → T2≠40. G3: síntesis aislada. G4: R/R2 mutuo,
N>2 sobre el mismo reloj, EOF = NOT_DEMONSTRATED.
