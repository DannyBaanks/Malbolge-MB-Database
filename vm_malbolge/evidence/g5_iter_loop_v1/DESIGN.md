# Diseño: reloj de iteración pc≡2 tras dos pases v4

2026-11-12. Pack `g5_iter_loop_v1`.

## Qué demuestra

Tras el bloqueo de rearme in-place del despachador compartido (`g5_loop_v1`),
este pack conecta el reloj de iteración de `G5_DESIGN.md` a islas v4 reales:

1. Isla H1 restaura y reejecuta TA=58550 (want 74).
2. Isla H2 restaura y reejecuta TB=58573 (want 51).
3. Salto a HCLOCK=58376 (`pc≡2`, valor 66).
4. JMP en HCLOCK+1 con cinturón de punteros `HCLOCK-1` en TB+8… drena la
   órbita `66→62→76→79` hasta HALT.

## Cinturón de punteros

Tras ejecutar HCLOCK, `d` avanza y HCLOCK+1 hace JMP con `c=mem[d]`. Para
reentrar hace falta `mem[d]==HCLOCK-1` en las posiciones impares del paseo
(probe: primer `d=TB+8`). Cuatro visitas: tres reentradas y HALT en la cuarta.

## Fuera de alcance

R restaura R2 y R2 restaura R (explosión de tamaño con islas de 19 si cada
celda de ayudante exige su propia isla). Siguiente: islas mínimas o primitivas
compartidas con órbita 2 como cuerpo de R/R2.
