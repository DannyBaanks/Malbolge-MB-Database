# Mecanismo de retorno al despacho — AUTO-ENRUTADO POR EL DATO

## Traza del mecanismo exacto

`mbir_native_cmp_decimal.mb` con stdin `"35"`:

```
paso 238: IN  '5'   (c=95)   a=53
paso 241: c=98 d=240 a=53 op=42    <- crazy: a = crazy(53, mem[240])
paso 242: c=99 d=241 a=53 op=4     <- JMP: c = mem[241] = 54   ¡EL BYTE LEÍDO!
paso 243: c=55 ...                 <- ejecuta desde la direccion 54
```

**El salto de retorno no es un `JMP` a una dirección fija: el destino es el
propio byte de entrada recién leído (`53` + 1 → `54`).**

## Qué significa

El emisor nativo no tiene un "bucle de despacho" con una dirección de vuelta
constante. Tiene **auto-enrutado**: el byte leído se convierte en la dirección
de la siguiente instrucción vía una operación `crazy` y un `JMP` indirecto.

Eso es exactamente la primitiva que el frente 3 (pila) y el frente 5 (lexer)
necesitan, y es más potente que un simple loop-back: permite que el flujo de
control lo dirija el **dato**, no el programa.

## Por qué explica los tres frentes

| Frente | Cómo encaja |
|---|---|
| 3 (pila > 2) | El retorno al despacho tras un `OUT` puede ser auto-enrutado por el siguiente opcode del flujo, en vez de requerir un slot de pila por nivel |
| 5 (lexer) | El segundo token se clasifica volviendo al clasificador; el auto-enrutado elimina la necesidad del reset que faltaba |
| 2 (unificada) | Las rutas pueden operar sobre lo cargado porque el destino depende del operando |

## Verificado

Traza instrumentada del oráculo Python sobre la imagen comprometida. El valor
`54` en `mem[241]` coincide con el segundo byte leído (`53`) más el desplazamiento
de la operación `crazy` intermedia.

## Implicación para el siguiente experimento

No hay que "injertar un salto de retorno fijo" — hay que injertar la **cadena
crazy + JMP indirecto** que convierte el byte de entrada en dirección. Esa
cadena es de 2 instrucciones sobre 2 celdas de dato, y su coste ya está medido
en el rango del graft del frente 2 (~657 B para la primitiva completa).
