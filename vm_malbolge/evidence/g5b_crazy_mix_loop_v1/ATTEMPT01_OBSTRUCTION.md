# G5b-1a, intento 1: el bloque lineal en la imagen no es construible

2026-11-15, preregistro `a4ad8d9`. Resultado: **NOT_DEMONSTRATED** (G1–G4 no
alcanzadas). El álgebra G0 sigue válida. Negativo preservado.

## Qué falló

`synthesize.py` colocó las 68 instrucciones activas y sus punteros, pero al
rellenar el bloque falló en la celda 15005 (`attempt01_synthesis.stderr.raw.txt`):
no hay palabra NOP persistente cargable en ese residuo.

## Por qué es estructural (`obstruction.py`, dos fuentes de tablas, coinciden)

- **O1.** Solo 14 de 94 residuos `pc mod 94` tienen una palabra que el cargador
  acepta (`o`) y cuya órbita `xlat2` entera decodifica NOP:
  `6 8 10 17 26 27 37 42 48 51 82 86 88 92`. En los otros 80, la única palabra
  `o` tiene órbita de 4–68 pasos con instrucciones reales. Una celda ejecutada
  en cada pasada recorre su órbita completa en un bucle no acotado, así que no
  sirve de relleno.
- **O2.** Para ROT (59/63), MOVD (60/64) y CRAZY (82/86) la celda anterior nunca
  es un NOP persistente. Un op que lee `d` sólo puede alcanzarse aterrizando en
  `X−1` tras un JMP. Ese JMP lee `d = T−1` (con `T` la celda que lee el op), y
  el JMP que sigue al op lee `T+1`.
- **Consecuencia.** Cada celda de datos `T` tiene **un único sitio de código**,
  con entrada (`T−1`) y salida (`T+1`) fijas. Una variable usada desde varios
  puntos del programa (aquí Z, C2, C3, C5, K y U) necesita un sitio por variable
  y un **retorno calculado**, es decir, un despacho por bandera. Es el modelo de
  HeLL/LMAO (rutinas `U_CRAZY` y banderas `F1..Fn` de `tape_circuit_loop_v1`).
  Aquí queda derivado desde el intérprete, no tomado de HeLL.

Alcance: O2 se aplica a las órbitas de periodo 2 (70↔74). Con órbitas largas
(un solo activo, más visitas por iteración) no se ha medido.

## Preservación

`attempt01_synthesis.stderr.raw.txt`: se relativizaron las rutas absolutas de la
estación (exigencia de repo-engine); el resto del texto está intacto.
`synthesize.py` queda tal cual se ejecutó en el intento 1.
