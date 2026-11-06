# Frente 3 — veredicto final: el andamio iterante no tiene ciclos de 5

## Lo que se intentó

Construir la pila de profundidad 2 sobre el andamio iterante verificado
(`example_simple_cat.hell`, 2.051 B, bucle de fetch real, oráculo ya arreglado
para parar en EOF).

## El obstáculo, localizado exactamente

`simple_cat` solo contiene tres comandos loop-resistant: `MOVD`, `IN` y `OUT`,
todos ellos ciclos de **2**. No tiene **ningún ciclo de 5**.

Clasificar tres opcodes (PUSH / POP / HALT) exige al menos un ciclo de 5
(es la técnica que usa todo el repo: `LOOP5: Nop/Nop/Nop/Nop/MovD`). Al
añadírselo, LMAO responde:

```
Error: Forced xlat cycle doesn't exist at line 62 column 2.
```

Ese es el mismo muro que E3 midió cuantitativamente: **los flags y ciclos de
código nuevos son lo que revienta el inicializador**, no las celdas de datos.

## Por qué no se resuelve copiando el andamio A04

`cell_stack_loop_echo.hell` (A04) tiene los ciclos, pero **no tiene
`decrement_value`** (grep = 0), que es la subrutina que el decremento de
clasificación necesita. El único `.hell` del repo que la tiene es
`mbir_cmp_lt.hell`, que ya pesa 57.511 B y no admite ni un flag nuevo (medido
en `cmp_lt_extensibility_probe.json`).

## Síntesis

| Pieza necesaria | Dónde existe | Coste de añadirla |
|---|---|---|
| Bucle de fetch iterante | `simple_cat` (2.051 B) ✅ | ya existe |
| `decrement_value` | `mbir_cmp_lt.hell` (57.511 B) ✅ | no cabe sobre `simple_cat` |
| Ciclos de 5 | en casi todos los andamios ✅ | el initializer los rechaza sobre `simple_cat` |

Las tres piezas existen por separado. **No coexisten en una imagen**: el
andamio que itera no tiene ciclos, y el andamio con ciclos no itera.

## Veredicto

Frente 3: **NOT_DEMONSTRATED**, con el obstáculo ahora localizado al nivel de
"ciclos de 5 sobre un andamio de 2.051 B". No es un fallo de diseño del probe:
es el muro del initializer de LMAO aplicado al andamio equivocado.

## Camino que sigue abierto

La ruta nativa (frentes 1 y 6, ya medidos): el emisor nativo no paga ciclos de
código porque emite recetas rectilíneas sobre celdas de datos, que E3 midió como
baratas. La pila profunda habría que emitirla por esa vía, no en HeLL.
