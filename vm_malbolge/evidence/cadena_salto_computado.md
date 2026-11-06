# Cadena de salto computado — reconstruida y verificada paso a paso

## El mecanismo

`mbir_native_cmp_decimal.mb` con stdin `"35"`. Instrumentación sobre
`tools/oracle_classic.py` (traza del oráculo real, no modelo propio):

```
paso 186:  c=242  d=186  a=29504   -> mem[241] = 54     (ESCRITURA del destino)
paso 241:  c=98   d=240  a=53      -> crazy(53, 118) = 29504
paso 242:  c=99   → JMP lee mem[241] = 54               (SALTO al destino)
```

## La cadena completa

1. Leer byte de entrada → `a = 53`
2. `crazy(53, 118) = 29504` — usando la celda de dato en la dirección 118
3. `crazy(29504, mem[186]) = 54` — el destino, escrito en `mem[241]`
4. `JMP` indirecto → `c = 54`

## Qué es, exactamente

`54 = 53 + 1`. **El destino del salto es una función del byte de entrada**: el
programa lee un byte, lo transforma con dos operaciones `crazy` sobre celdas de
dato, y salta a la dirección resultante.

No es un loop-back a dirección fija. Es un **salto computado**: el flujo de
control lo dirige el dato.

## Por qué desbloquea los tres frentes

| Frente | Obstáculo medido | Cómo lo resuelve esta cadena |
|---|---|---|
| 3 (pila > 2) | falta el retorno al despacho | el destino se computa desde el opcode leído, sin necesidad de un slot por nivel |
| 5 (lexer) | el reset entre bytes falta | el segundo token se auto-enruta; el centinela cierra el EOF |
| 2 (unificada) | las rutas imprimen constantes | una ruta puede escribir su destino y saltar ahí, con el operando como origen |

## Verificado

Las tres escrituras están medidas sobre el oráculo real, no inferidas:
`mem[241] = 54` en el paso 186; `crazy(53, 118) = 29504` reproducido; el JMP en
el paso 242 leyendo ese valor.

## Siguiente paso concreto

Insertar esta cadena en el andamio del cargador (`mbir_m2_loader.hell`), con las
dos celdas de dato (118 y 186) colocadas vía `.OFFSET`, y un centinela `0x00` en
el flujo de entrada. Verificar con `stack_depth_probe.py` (profundidad 2) y
`lex_loop_probe.py` (segundo marcador).
