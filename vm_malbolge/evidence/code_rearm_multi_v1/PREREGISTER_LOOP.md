# Preregistro: bucle auto-sostenido con dos restauradores

2026-11-12. Pack `code_rearm_multi_v1`. Este documento preregista el diseño y
sus puertas ANTES de sintetizar imagen; nada de lo aquí descrito está
demostrado todavía.

## Base ya demostrada

- Cadena de restauración uniforme (`algebraic_restart.results.json`): para las
  48 celdas del bloque, `e --crazy(a=ONE)--> x --crazy(a=x)--> 29524
  --crazy(a=ctrl)--> want` con `ctrl=crazy(want,ONE)`.
- `loop_feasibility.results.json`generaliza esa cadena a TODO el espacio:
  1. `crazy(crazy(v,ONE),ONE)==v` para los 59049 valores: cualquier celda, de
     código o de datos, admite restauración con la misma cadena de 5
     operaciones (ROT de la celda ONE, CRAZY, CRAZY, ROT de la celda de
     control, CRAZY).
  2. Para los 94 valores imprimibles `e` (una celda de código recién
     ejecutada), `e -> crazy(ONE,e) -> crazy(x,x) == 29524` siempre.
  3. xlat2 tiene 6 ciclos (longitudes 2, 4, 5, 6, 9 y 68). En 48 pares
     (pc, ciclo) los cars `o` y `v' comparten ciclo; en 23 de ellos `o`
     precede a `v`. Un reloj de orbita puro (solo NOP y HALT) sólo permite
     N<=2 iteraciones; N mayor exige coreografiar d/a en la celda reloj.

## Diseño del bucle

Dos rutinas R y R2, más el cuerpo B y una celda reloj H sin restaurar:

```
iteración:
  1. R ejecuta    -> restaura celdas de R2 y de B (excepto H). R se cifra.
  2. B ejecuta    -> trabajo útil; H avanza un paso en su orbita. B se cifra.
  3. R2 ejecuta   -> restaura celdas de R y de B (excepto H). R2 se cifra.
  4. salto a 1    -> R y B prístinas; R2 se restaurará en el paso 1.
```

La parada: cuando la orbita de H decodifica `v` (HALT). Sin entrada, sólo
N<=2 con NOP puro; con opcodes peligrosos controlados (d/a coreografiados) o
con EOF de UNIECO, N arbitrario.

## Puertas (preregistro)

- G5: imagen estricta con R, R2, B mínimo (2-4 celdas) y H; dos iteraciones
  completas observadas por REA (ventana tardía) y por un trazador scratch
  independiente; Olmstead rc=0.
- G6: control roto: suprimir una operación de restauración en R (o en R2) y
  comprobar que la segunda iteración difiere (opcode distinto o salto a celda
  no imprimible); registrar si la ejecución nativa sola lo distingue.
- G7: reproducir la síntesis en árbol aislado; hashes y capturas crudas.
- G8: N>=3 iteraciones, cuerpo de 48 celdas contiguas del bloque real,
  integración con el detector de EOF de UNIECO y parada limpia: siguen
  NOT_DEMONSTRATED hasta tener imagen y verificación.

## NOT_DEMONSTRATED (se mantiene)

- Bucle de longitud arbitraria con EOF limpio.
- Rutina restauradora genérica sobre tabla (pc, control) iterada.
- Selección automática de controles dentro de Malbolge.
- Bloque contiguo de 48 celdas restaurado y reejecutado.
