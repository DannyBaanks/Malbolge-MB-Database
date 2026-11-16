# G5b-2 P1: una variable, dos llamadores, retorno por bandera — preregistro

2026-11-15. Base `aed60b2`. Primera primitiva del "mini-LMAO nativo". Motivación:
`g5b_crazy_mix_loop_v1/ATTEMPT01_OBSTRUCTION.md` (una celda de datos = un sitio)
y `g5b_o3_sites_v1` (las órbitas largas no bastan). Construcción con islas de
tick (`clasesbolge_v3.md` §6.4: op de fase en `m`, JMP en `m+1` que aterriza en
`m`, E²=id) y flujos de `d` por encima de la imagen (threaded code).

## Diseño

- Islas de código en la imagen: reloj K (pc≡2, palabra 66, sin tick), bandera F
  (MOVD, pc≡60, palabra 74, **sin tick**: alterna MOVD/NOP en cada ejecución),
  MOVD_V, ROT_V, OUT, MOVD_loop (con tick).
- La fase NOP de 70↔74 no carga, así que F arranca **armada** (MOVD). A conmuta F
  (MOVD con puntero a sí mismo, sin efecto) antes de llamar; B no la toca.
- Retorno tras `ROT V`: F en NOP → se rearma y continúa por `V+4` (A). F armada
  → MOVD a `p1`, segunda ejecución de F (la rearma) y continúa por `p1+3` (B).
  F termina armada en los dos casos.
- Iteración: K, conmutar F, A llama, `OUT OUT`, B llama, `OUT`, MOVD_loop.

## Puertas

- G0 (estática): todas las celdas de la imagen cargan (`ji*p</vo`); planificador
  y ensamblador independientes coinciden en la disposición.
- G1 (nativo): Olmstead, entrada vacía → exactamente
  `r1 r1 r2 r3 r3 r4 r5 r5 r6` (`rᵏ = rot^k(V0) mod 256`), rc 0 por HALT del reloj.
- G2 (traza): trazador scratch del repo y `tools/malbolge.py` de clasesbolge
  (tercer intérprete) dan la misma salida; F vale 74 (armada) al inicio de cada
  iteración; ROT_V es el único sitio que escribe en V; los JMP de isla no cambian.
- G3 (controles), con predicción del modelo antes de ejecutar:
  (a) A no conmuta F → las dos llamadas vuelven por B: `r1 r2 r3`;
  (b) la ruta B no rearma F (`p1+1` salta la segunda ejecución de F) → la salida
  diverge del positivo a partir de la 2.ª iteración.
- G4: dos planificaciones+ensamblados en directorios aislados idénticos byte a byte.
- Fuera de alcance: más de dos llamadores, varias variables, EOF, mezcla crazy.

Planificador de disposición en Zig (`plan.zig`); el preámbulo lo sintetiza
BolgeForge (Python), que no se reescribe.
