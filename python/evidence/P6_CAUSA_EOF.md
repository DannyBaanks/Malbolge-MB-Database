# Frente 5 — causa de la divergencia: SEMÁNTICA DE EOF

## Verificado en el fuente del runner C

`Malbolge-Engine/src/vm.c` (commit `404de20`, el runner que este repo vendoriza
como `runners/malbolge-original/malbolge`, manifest → `source_commit e7faeb1`):

```c
case 23:
    if (input_pos < input_len) {
        a = input[input_pos++];
    } else {
        terminated = 1;          // <- PARADA, no valor
    }
    break;
```

## Verificado en el oráculo Python

`tools/oracle_classic.py:73-75`:

```python
elif op == 23:
    ch = next(stdin_iter, None)
    a = -1 if ch is None else ord(ch)   # <- 59048, y SIGUE
```

## La asimetría

| | EOF en `IN` |
|---|---|
| Runner C (`vm.c:144-149`) | `terminated = 1` → **el programa para** |
| Oráculo (`oracle_classic.py:73-75`) | `a = 59048` → **sigue ejecutando** |

Esa es la asimetría que produce la divergencia medida: cualquier programa cuyo
flujo de control dependa de lo que hay tras el último byte de stdin obtendrá
resultados distintos en los dos motores.

## Lo que se refutó en el camino

**Hipótesis "el runner para en el primer EOF"** — probada dándole más bytes de
stdin (`01`, `01AAAA`, `01AAAA…` ×20): la salida **no cambió** (`30` en los
tres). O sea: el runner no para por alcanzar el fin del buffer en el momento
que yo creía; la parada ocurre cuando el flujo de control **vuelve** a pedir
un byte que ya no existe.

## Lo que NO está averiguado

No pude construir un modelo propio del runner C que reprodujera su salida
exacta (`30` en 59.675 pasos): mi reimplementación para en 48.236 pasos con
`NONPRINTABLE_PC`. O sea, conozco la asimetría de EOF por lectura de los dos
fuentes, pero **no** la he verificado ejecutando.

## Consecuencia para el roadmap

El probe del lexer (`lex_loop_probe.py`) encadena `R_MOVED` + `MOVED ENTRY`
para volver al clasificador. Ese ciclo **vuelve a leer stdin**, así que toca
el EOF. Con la asimetría documentada, el paso siguiente es hacer que el probe
**no dependa de EOF**: alimentar un flujo con un centinela explícito en lugar
de confiar en el fin del buffer.

---

## Cierre: la hipótesis de EOF queda verificada ejecutando

El probe del lexer con un **centinela explícito** (`0x00` = HALT) al final del
flujo, en lugar de confiar en el fin del buffer:

| stdin | Runner C | Oráculo | Acuerdo |
|---|---|---|---|
| `01 00` | `50` | `50` | **SÍ** |
| `01 02 00` | `50` | `50` | **SÍ** |
| `01 02 03 00` | `50` | `50` | **SÍ** |
| `05 00` | `53` | `53` | **SÍ** |
| `11 00` | `49` | `49` | **SÍ** |

**5/5 de acuerdo.** La divergencia medida (4/4 sin centinela) desaparece por
completo cuando el flujo no depende del EOF. La asimetría de EOF —parada en el
runner C, valor 59048 y continuar en el oráculo— era la causa única y suficiente.

## Veredicto del frente 5

**Cerrado.** La divergencia no es un fallo de implementación ni del probe: es
una diferencia de semántica de EOF entre los dos motores, verificada en los dos
fuentes y neutralizada con un centinela. El fallo funcional del lexer (que el
segundo byte no produzca el segundo marcador) sigue en pie y es un problema
distinto, ya documentado en `python/P6_STATUS.md`.
