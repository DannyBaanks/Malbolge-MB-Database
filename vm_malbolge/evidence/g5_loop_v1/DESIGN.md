# Diseño: rearme in-place del CLOCK compartido

2026-11-12. Pack `g5_loop_v1`. Base `d56a602`.

## Meta

Tras call1, devolver `CLOCK=58303` de 58→117 dentro de Malbolge y reusar el
mismo despachador para call2 (sin CLOCK2).

## Álgebra (PASS en host)

`crazy` uniforme restaura 58→117 con `ctrl=29407` y C 40→120 con `ctrl=29404`
(`scratch_clock_rearm.py`). Call2 sobre el mismo CLOCK, con rearme hecho en
host, termina T2=40 y HALT en CLOCK.

## Bloqueo nativo (medido)

1. Tras CRAZY sobre la celda T, `d` pasa a `T+1`.
2. El despachador ejecuta CLOCK y cae en CLOCK+1 (JMP, valor inicial 74).
3. Para un segundo CRAZY sobre CLOCK hace falta un MOVD que recargue
   `CLOCK-1` cuando `d` apunta a una celda que contiene ese puntero. El
   candidato natural es CLOCK+1, pero esa celda es código del despachador,
   no un banco de punteros.
4. Tras 3 visitas, CLOCK+1 vale 70. No existe `a` con
   `crazy(a,70)==58302` (CLOCK-1): no se puede parchear CLOCK+1 a ese puntero
   con un solo CRAZY.

Conclusión: el CLOCK de fase compartido no es un buen T de su propio rearme
mientras siga siendo código con fallthrough. Por eso two_v1/three_v1 usan
CLOCK2/CLOCK3.

## Camino que sigue abierto (G5_DESIGN)

- Reloj de **iteración** en `pc≡2`, valor 66: tres NOP y HALT (no es el
  despachador de fase).
- Islas v4 (`j*jpojpooj*ojpooooi`) para R/R2, donde el objetivo T no es el
  propio despachador.
- O un pool finito de relojes de fase (ya demostrado N=3).
