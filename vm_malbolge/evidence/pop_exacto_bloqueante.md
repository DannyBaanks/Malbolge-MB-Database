# Bloqueante: pop exacto imposible en bucle (Malbolge Classic)

## Veredicto

**IMPOSIBLE en un bucle real de Malbolge Classic.** Un "pop exacto" —emitir el valor
almacenado en una celda de pila sin rotarlo ni modificarlo— no es construible
dentro de un bucle de fases. El bloqueante no es una limitación del generador;
es una consecuencia de la semántica del dialecto.

## Causa 1: no existe instrucción de lectura pura

| Instrucción | Lee `mem[d]` | Afecta `a` | Modifica `mem[d]` |
|---|---|---|---|
| `ROT` (39) | Sí | `a = mem[d]` | **Sí** (`mem[d] = rot(mem[d])`) |
| `CRAZY` (62) | Sí | `a = mem[d]` | **Sí** (`mem[d] = crazy(a, mem[d])`) |
| `MOVD` (40) | Sí | No | No (solo cambia `d`) |
| `JMP` (4) | Sí | No | No (solo cambia `c`) |
| `IN` (23) | No | `a = stdin` | No |
| `OUT` (5) | No | emite `a` | No |

`MOVD` y `JMP` leen `mem[d]` pero no lo ponen en `a`. `IN` pone algo en `a`
pero lee de stdin, no de `mem[d]`. **`ROT` es la única instrucción que puede
poner el contenido de una celda en `a`, y siempre la rota.** Por tanto, cualquier
pop que emita el valor de una celda la altera.

## Causa 2: `rot^10 = identidad`, pero ningún `rot^k` para `k < 10`

Verificado empíricamente para todo `[33, 126]`:

| `k` | ¿`rot^k = identidad`? | ¿punto fijo de `rot^k`? |
|---|---|---|
| 1 | No | Ninguno |
| 2 | No | Ninguno |
| 3 | No | Ninguno |
| 4 | No | Ninguno |
| 5 | No | Ninguno |
| 6 | No | Ninguno |
| 7 | No | Ninguno |
| 8 | No | Ninguno |
| 9 | No | Ninguno |
| 10 | **Sí** | — |

Para emitir exactamente `S` (sin rotar) se necesitan **10 `ROT` consecutivos**
sobre la misma celda: `rot^10(S) = S`, y tras el décimo `ROT`, `a = S`.

## Causa 3: una celda de trabajo no puede hacer `ROT` en 2+ fases de su ciclo

El ciclo de `XLAT2` de una celda que no se restaura avanza una fase por iteración.
Medido empíricamente: **ninguna dirección imprimible tiene `ROT` en 2 o más
posiciones de su ciclo de `XLAT2` sin incluir `HALT`/`JMP` que romperían el
bucle.** Una celda ejecuta `ROT` como máximo una vez por ciclo completo.

## Causa 4: distribuir 10 `ROT` en múltiples vueltas requiere un contador

Dado que una celda solo puede hacer un `ROT` por ciclo, aplicar 10 `ROT` sobre
la misma celda `S` requiere distribuirlos en al menos 10 vueltas del bucle (o
más, si el ciclo es largo). Entre cada par de `ROT` hay que:

1. Restaurar `d = S` (cada `ROT` incrementa `d` automáticamente).
2. Saber cuándo se han completado exactamente 10 `ROT` para parar y emitir.

El punto 2 requiere un **contador de rotaciones**. Pero cualquier celda usada
como contador se cifra con `XLAT2` al ejecutarse, y no hay forma de mantener un
valor estable a través del cifrado. Un contador que cambia de valor no puede
señalar "ya van 10".

## Conclusión

El pop exacto es imposible en un bucle de Malbolge Classic porque:

- No hay instrucción de lectura pura (`mem[d]` → `a` sin modificar `mem[d]`).
- Un pop exacto requiere exactamente 10 `ROT` sobre la misma celda.
- Una celda no puede hacer `ROT` en 2+ fases de su ciclo.
- Distribuir 10 `ROT` en el tiempo requiere un contador estable, y los
  contadores se cifran.

## Alternativa demostrada (no es pop exacto)

El LIFO de profundidad 2 en bucle (`stack_loop_lifo2.md`) usa `ROT` como pop:
lee la celda, la rota y emite el valor rotado. El valor almacenado queda
rotado en la ranura, no se vacía. Esto es un **pop con rotación**, no un pop
exacto, y es lo máximo expresible en un bucle real.

## Próximo frente

La pila de llamadas (contador de programa general, múltiples marcos) sigue
abierta y no está bloqueada por este problema.
