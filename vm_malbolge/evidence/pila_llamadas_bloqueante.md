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

---

## Corrección medida (2026-11-07) — la causa raíz es más estrecha

El texto anterior **se conserva** como registro histórico. Esta sección corrige la
causa raíz con una medición nueva.

**Medición:** `vm_malbolge/evidence/epoch_algebra_v3/` (imagen `resolver.mb`,
SHA-256 `ffb2453a7c9301c16ed14801d7ca91c496ed0db1f2c1b00d689c90bef818a32b`).
Comando: `python3 vm_malbolge/evidence/epoch_algebra_v3/probe.py` → salida 0.

**Lo que sigue vigente (medido):** `c` es un registro de solo escritura. Ninguna
instrucción copia el PC a `a` ni a una celda de datos, así que **guardar una
dirección de retorno generada en runtime sigue sin ser posible**. La tabla de la
sección "Causa raíz" es correcta para `c` y para `d`.

**Lo que queda refutado:** la afirmación "no hay forma de establecer `mem[d]` a un
valor conocido" y la línea "no existe asignación directa a memoria". Con la máscara
`121` (imprimible, involución de `crazy` para todo valor de byte) la secuencia

```
mem[scratch] = crazy(V, 121)
mem[destino]  = crazy(mem[scratch], 121) = V      # V exacto, decidido en runtime
```

**escribe un valor arbitrario conocido en una celda arbitraria**, con el valor
`V` llegando por `stdin` durante la ejecución. Medido: 256 payloads × 3 épocas,
0 discrepancias (`exactness_sweep_0_255` en `results.json`).

**Consecuencia colateral medida:** con esa escritura exacta se puede construir un
**puntero calculado en runtime** y, con él, un **salto dirigido por datos**. En la
imagen v3 el `JMP` lee `mem[45] = b` (el byte de petición) y salta a `b+1`, es decir
a 36, 130 o 224 según lo que se haya pedido: el destino del salto lo decide la
petición en runtime, no el ensamblador. La cadena `d = mem[mem[45]]` (con el `+1`
del autoincremento) da además **direccionamiento indexado** (`mem[mem[d]]`), que el
documento declaraba imposible.

**Lo que sigue bloqueado:** una pila de llamadas clásica necesita **direcciones de
retorno**, es decir valores de `c` en el momento de la llamada. Como `c` no se puede
leer, eso no se ha desbloqueado. Lo desbloqueado es el otro eje: una pila de
**direcciones de destino** elegidas en runtime (no de retorno). La composición de
ambos (llamada con retorno + destino dinámico) y el rearm del valor en la celda
siguen `NOT_DEMONSTRATED`.

**Conclusión revisada:** "imposible construir una pila de llamadas" se mantiene solo
en su forma clásica (con direcciones de retorno); la formulación por causa raíz —"no
existe asignación directa a memoria, luego no se puede actuar en runtime"— queda
refutada por la medición de v3.
