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

---

## Corrección medida (2026-11-07) — el cuello de botella medido era la máscara, no la escritura

El texto anterior **se conserva** como registro histórico. Esta sección corrige el
análisis con la medición de v3.

**Medición:** `vm_malbolge/evidence/epoch_algebra_v3/` (imagen `resolver.mb`,
SHA-256 `ffb2453a7c9301c16ed14801d7ca91c496ed0db1f2c1b00d689c90bef818a32b`).
Comando: `python3 vm_malbolge/evidence/epoch_algebra_v3/probe.py` → salida 0,
`[verdict] all_checks_pass = True`.

**Refutado:** la línea "no hay instrucción `mem[d] = valor_conocido`" y la causa raíz
unificada "Malbolge Classic no tiene instrucción `mem[d] = valor_conocido`". La
escritura exacta en runtime existe y está medida:

| lo que el documento declaraba imposible | medición v3 |
|---|---|
| escribir un valor conocido en una celda | `mem[T] = V` exacto, con `V` leído de `stdin` en runtime; 256 payloads × 3 épocas, 0 discrepancias |
| saltar a una dirección conocida en runtime | el `JMP` lee `mem[45] = b` y salta a `b+1` = 36 / 130 / 224 según la petición |
| direccionamiento indexado (`mem[mem[d]]`) | `d = mem[mem[45]]` (+1 del autoincremento) y escritura en `mem[T]` |

El mecanismo es la **involución de `crazy` con máscara imprimible `121 = 11111_3`**
(`crazy(crazy(V,121),121) = V` para todo `V` de byte), en dos celdas distintas: la
primera aplicación deja el intermedio en un scratch y la segunda lee la máscara que
sigue intacta en el destino. El intento anterior fallaba (`gen_resolver.py`, `MASK=121`
sobre la misma celda) porque la celda destino quedaba ocupada por el intermedio:
`crazy(V',V')` no es la involución de la máscara y el puntero salía corrupto.

**Por qué esto resuelve el paso 3 del diseño de dos sistemas:** el "Sistema A" ya no
necesita un middleware externo para escribir: la propia VM, en runtime y sin
precompilar la transición, escribe el valor exacto y salta a la celda elegida. El
middleware de búsqueda (PureEpoch) sigue sin generalizar —no hay búsqueda ni síntesis
general de transiciones—, pero el **cuello de botella de escritura que motivaba la
arquitectura de dos sistemas ya no está donde estaba**.

**Lo que sigue vigente:** `c` sigue sin poder leerse (nada copia el PC a memoria), y
la máscara consumida obliga a rearmar la celda antes del siguiente uso; el rearm con
journal está demostrado en `epoch_journal_state_v2` para celda fija, y componerlo con
la selección dinámica de época es `NOT_DEMONSTRATED`.

**Conclusión revisada:** el análisis de los tres pasos queda refutado en el paso 3
(escritura) y en el paso 1 (el valor puede ser escrito y ejecutado dentro de la misma
VM); permanece abierto el punto de "búsqueda" del paso 2, que no es un bloqueo de
escritura sino de búsqueda general.
