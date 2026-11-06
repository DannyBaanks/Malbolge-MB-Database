# Frente 1 — contador de programa genérico: ATAQUE

## Resultado: el bucle de despacho existe

Traza instrumentada de `mbir_native_cmp_decimal.mb` (imagen nativa del emisor,
motor: oráculo Python) con stdin `"35"`:

```
paso 1:   IN  '3'   (c=0)      <- primer opcode
paso 22:  JMP 77    (c=21)     <- salto a destino computado
paso 37:  OUT 51    (c=92)
paso 196: JMP 53    (c=251)
paso 238: IN  '5'   (c=95)     <- SEGUNDO opcode
paso 242: JMP 54    (c=99)
paso 250: IN  EOF   (c=62)     <- tercer fetch
paso 254: OUT 255   (c=66)
paso 334: HALT
```

**La imagen no es one-shot: vuelve al despacho y busca un segundo opcode.**

## Primitivas verificadas

| Primitiva | Estado | Evidencia |
|---|---|---|
| Escritura en celdas (`p`, op 62) | ✅ | 15 celdas distintas escritas durante la ejecución |
| Salto a destino computado (`i`, op 4) | ✅ | 6 saltos, cada uno a `mem[d]` |
| Retorno al despacho | ✅ | 3 fetch de opcode con `"35"` (uno real + EOF) |

## Capacidad del selector dinámico

Clave de despacho `Q = crz(rot^7(crz(48+d, 85)), 48)` sobre el rango completo
del byte de entrada (0..255):

| Medida | Valor |
|---|---|
| Destinos distintos | **72** |
| Rango | 18 .. 7686 |
| Gap mínimo | **27** (= arena por ruta) |
| Gaps ≥ 26 | **71/71** |

O sea: el destino del salto puede servir de selector dinámico general con 72
rutas, todas con espacio de arena suficiente.

## Conclusión del frente

El contador de programa genérico **no está bloqueado**. Las tres primitivas que
exige están demostradas en imágenes de este repo, y la capacidad de selección
está medida. Lo que falta es ensamblarlas en una sola imagen que ejecute una
cadena de opcodes completa.

## Siguiente

Frente 2: escribir el merge sobre el andamio del cargador (18.740 B de margen,
512 celdas y 8 flags admitidos) usando elmotor nativo, que no gasta flags de
código nuevos.
