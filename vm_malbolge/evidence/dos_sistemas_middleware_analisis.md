# Análisis: arquitectura de dos sistemas (extractor + PureEpoch como middleware)

## Propuesta

El usuario sugiere un sistema de dos componentes:

1. **Sistema A (extractor/cat)**: Extrae el valor necesario de una celda de datos de Malbolge
2. **Sistema B (PureEpoch como middleware)**: Recibe el valor, lo "busca" y lo devuelve
3. **Sistema A**: Vuelve a meter el valor conocido en una celda de Malbolge

## Veredicto

**NO RESUELVE el bloqueante.** El problema no está en encontrar el valor, está en **escribirlo** en una celda de datos de Malbolge Classic.

## Por qué falla en cada paso

### Paso 1: Sistema A extrae un valor

Esto es posible. `MOVD` lee `mem[d]` y lo deja en `d`; `JMP` lee `mem[d]` y lo deja en `c`. Puedes leer cualquier celda.

### Paso 2: Sistema B (PureEpoch) recibe y devuelve el valor

PureEpoch es un programa `.mal` que corre dentro de la misma VM Classic. Está sujeto a las mismas restricciones:

- No hay instrucción `mem[d] = valor_conocido`
- `ROT`: `mem[d] = rot(mem[d])` — transforma, no asigna
- `CRAZY`: `mem[d] = crazy(a, mem[d])` — depende de `a` y del valor previo

Incluso si PureEpoch "encuentra" el valor X, no hay instrucción Malbolge para escribir X en `mem[d]`.

### Paso 3: Sistema A vuelve a meter el valor conocido

Mismo problema. Para escribir un valor conocido V en una celda X necesitarías:

```
mem[X] = V   ← NO EXISTE esta instrucción en Malbolge
```

El rearme de PureEpoch (`write_high` en `tools/boss3_real_loop.py`) puede escribir valores en celdas específicas, pero solo porque **conoce tanto el valor actual como el objetivo en tiempo de compilación** y precompila una secuencia de `CRAZY`/`ROT` que transforma el valor actual en el objetivo. No es middleware que decide en runtime "escribir este valor que acabo de calcular".

## Causa raíz unificada

Todos los bloqueantes del roadmap comparten la misma causa raíz:

> **Malbolge Classic no tiene instrucción `mem[d] = valor_conocido` ni `c = valor_conocido`.**

Sin asignación directa a memoria ni lectura del PC, no se puede:

| Operación | ¿Posible en Malbolge? | ¿Por qué? |
|---|---|---|
| Leer una celda | Sí | `MOVD`, `JMP` leen `mem[d]` |
| Escribir un valor conocido en una celda | **No** | Solo `ROT`/`CRAZY` escriben, y transforman |
| Leer el PC (`c`) | **No** | No hay instrucción que copie `c` a `a` o a memoria |
| Saltar a una dirección conocida | **No** | `JMP` lee `mem[d]`, no acepta un valor inmediato |
| Direccionamiento indexado | **No** | No hay `mem[mem[d]]` |

## Conclusión

La arquitectura de dos sistemas no resuelve el bloqueante porque el cuello de botella no está en "encontrar el valor", sino en la **inexistencia de una instrucción de asignación directa a memoria** en Malbolge Classic. PureEpoch puede precomputar transiciones de estado para valores conocidos en tiempo de compilación, pero no puede actuar como middleware que escriba valores decididos en runtime.

## Lo que SÍ se ha demostrado (alternativa honesta)

- **Rearme de instrucciones automutadas**: PureEpoch puede restaurar una instrucción `<` en una celda específica entre iteraciones, porque conoce el valor actual y el objetivo en tiempo de compilación.
- **Precomputación offline de transiciones**: Secuencias de `CRAZY`/`ROT` que transforman un estado conocido en otro, compiladas en el builder Python.

Ambas requieren que todo sea conocido antes de la ejecución. Ninguna permite decidir en runtime "escribir este valor en esta celda".
