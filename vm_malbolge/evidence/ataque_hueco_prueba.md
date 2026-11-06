# Ataque al hueco de la prueba — comparador de dos operandos

Fecha: 2026-11-07.

## El hueco

La prueba de no-existencia (`cmp2_two_operand_blocker.json`) cubre cadenas de
`ROT` + `CRAZY`-con-constante sobre el segundo operando, y prueba que son
funciones **separables** de los trits de entrada, por lo que `a < b` no es
computable. La prueba deja explícitamente fuera el caso en que el operando del
`CRAZY` es una celda cuyo contenido **depende de la entrada**.

## El mecanismo que abre el hueco

`p` (op 62) hace `mem[d] = crazy(a, mem[d])`. Una receta puede:

```
IN A            a = A
p @celda(C)     a = crazy(A, C);  mem[celda] = crazy(A, C)   <- ALMACENA A
IN B            a = B                                          <- sobreescribe
p @celda        a = crazy(B, crazy(A, C))   <- combinación dependiente de AMBOS
```

## Medido

| Medida | Resultado |
|---|---|
| `crazy(A, C)` almacenado distingue los 10 dígitos | **Sí, 10/10** con C=49 y C=85 |
| `crazy(B, crazy(A, C))` pares distintos de 100 | **23 a 28** de 100 |
| Alguna constante C separa las clases de entrada | **Ninguna** (0 de 94) |

## Interpretación

El almacenamiento **preserva** la información del primer operando (10/10 dígitos
distinguibles), así que el mecanismo funciona. Pero la combinación directa de dos
etapas colapsa: como máximo 28 de 100 pares quedan distintos, muy por debajo de
los 100 que harían falta para que el byte bajo separe las dos clases.

## Estado de la búsqueda

Barrido sobre 94 constantes con cadena de `rot`/`crazy(constante)` de longitud
≤ 8 sobre el resultado de la combinación: **en curso**.

Modelo rico (múltiples `IN` intercalados con `p` sobre la celda almacenada,
longitud ≤ 4): excede el tiempo de cómputo con el barrido actual.

## Conclusión provisional

El hueco de la prueba es real y el mecanismo de almacenamiento funciona, pero la
combinación directa colapsa. La búsqueda en curso determina si una cadena
adicional recupera la separación. Si no la recupera, el resultado se registra
como una **extensión de la prueba**: no solo las funciones separables fallan,
tampoco las que pasan por un `crazy` con un operando almacenado de una etapa.
