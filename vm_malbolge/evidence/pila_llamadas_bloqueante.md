# Bloqueante: pila de llamadas imposible en Malbolge Classic

## Veredicto

**IMPOSIBLE construir una pila de llamadas de más de una trama en Malbolge Classic.**
El bloqueante no es una limitación del generador; es una consecuencia directa de la
semántica del dialecto: no existe instrucción que permita leer el program counter
`c` ni escribirlo en una celda de datos.

## Causa raíz: no se puede leer ni guardar `c` ni `d`

| Instrucción | Lee `mem[d]` | Escribe `mem[d]` | Lee `c` | Escribe `c` |
|---|---|---|---|---|
| `JMP` (4) | Sí (`c = mem[d]`) | No | No | Sí (`c = mem[d]`) |
| `MOVD` (40) | Sí (`d = mem[d]`) | No | No | Sí (`d = mem[d]`) |
| `CRAZY` (62) | Sí | Sí (`mem[d] = crazy(a, mem[d])`) | No | No |
| `ROT` (39) | Sí | Sí (`mem[d] = rot(mem[d])`) | No | No |
| `IN` (23) | No | No | No | Sí (`a = stdin`) |
| `OUT` (5) | No | No | No | No |
| `NOP` (68) | No | No | No | No |

- No existe instrucción `mem[d] = c` ni `mem[d] = d`.
- No existe instrucción que copie `c` en `a` o en cualquier celda de datos.
- `c` solo se puede escribir con `JMP` (desde `mem[d]`) e incrementar automáticamente
  (`c = (c + 1) % MEM_SIZE` después de cada instrucción). Nunca se puede leer.

## Por qué esto bloquea la pila de llamadas

Una pila de llamadas requiere, como mínimo:

1. **Guardar el PC de retorno (`c`)** en una celda de datos antes de saltar a la subrutina.
2. **Avanzar un stack pointer** para la siguiente llamada.
3. **Restaurar `c`** desde la celda de datos al regresar (`JMP` lee `mem[d]` y lo pone en `c`).
4. **Restaurar el stack pointer** y los registros (`a`, `d`, estado del cifrado de celdas).

El paso 1 es imposible: no hay forma de obtener el valor de `c` para escribirlo en
una celda de datos. El paso 3 es posible (`JMP` lee `mem[d]` → `c`), pero sin el
paso 1 no hay nada que restaurar.

El paso 2 también está bloqueado: para avanzar un stack pointer necesito escribir
el nuevo valor en una celda de datos, y la única forma de escribir es `CRAZY` o
`ROT`, ambas transforman el valor existente en lugar de asignar uno conocido.

## ¿Se puede eludir con CRAZY como asignación?

Teóricamente, si se controlaran ambos operandos de `CRAZY` (`a` y `mem[d]` antes
de la operación), se podría predecir el resultado trit a trit y escribir un valor
deseado en `mem[d]`. Pero:

- No se puede leer `c` para saber qué valor guardar.
- No se puede establecer `mem[d]` a un valor conocido previamente (no hay asignación directa).
- Controlar 10 trits de `a` y 10 trits de `mem[d]` simultáneamente para obtener
  un resultado de 10 trits dado es inviable en la práctica para un runtime.

## Conclusión

Una pila de llamadas de más de una trama no es construible en Malbolge Classic
porque el program counter `c` es un registro de solo escritura: se puede saltar a
él (`JMP`), se auto-incrementa, pero nunca se puede leer ni guardar en memoria.
Sin guardar `c`, no hay retorno de subrutina; sin retorno, no hay pila de llamadas.

## Alternativa demostrada (no es pila de llamadas)

El LIFO de profundidad 2 en bucle (`stack_loop_lifo2.md`) demuestra dos ranuras
de datos con orden LIFO, pero no hay retorno de subrutina ni stack pointer
desplazable. Es una pila de datos estática, no una pila de llamadas.

## Próximo frente

Este bloqueante cierra el frente de "pila de llamadas" del roadmap. Los frentes
restantes son la integración del pipeline M2+ALU+CMP y el comparador de dos
operandos variables, que tienen obstáculos distintos (presupuesto de imagen y
separabilidad trit-a-trit de `CRAZY`/`ROT`).
