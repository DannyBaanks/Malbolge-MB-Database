# Búsqueda del comparador con CRAZY dependiente de entrada

## Resultado del primer barrido (BFS + beam naive)

94 constantes × cadenas de longitud ≤ 8. **Ninguna solución.**

Pero el barrido dejó un hallazgo que explica por qué, y que no es un fallo
sino una propiedad del sistema:

**El beam alcanzó "spread 2" (un valor por clase) en 658 ocasiones, y en
ninguna separó.** En todas, las dos clases colapsaban al **mismo** valor.

## Qué significa

Una fila que colapsa a un solo valor es un **callejón sin salida**: cualquier
operación punto a punto aplicada a un valor único produce otro valor único,
así que la separación es inalcanzable desde ahí. La heurística original
(contar valores distintos por clase) no distinguía "1+1 con el mismo valor"
de "1+1 con valores distintos", así que el beam se llenaba de callejones sin
salida y ahogaba la exploración útil.

Corregido: los callejones sin salida se excluyen del beam.

## Medidas acumuladas del ataque

| Medida | Resultado |
|---|---|
| `crazy(A, C)` almacenado distingue los 10 dígitos | **10/10** con C=49 y C=85 |
| `crazy(B, crazy(A, C))` pares distintos de 100 | **23 a 28** |
| Constantes que separan las clases de entrada | **0 de 94** |
| Soluciones con cadena ≤ 8 (beam naive) | **0 de 94** |
| Callejones sin salida encontrados | **658** |

## Interpretación

El mecanismo de almacenamiento funciona (preserva A: 10/10 dígitos
distinguibles), así que el hueco de la prueba es real. Pero la combinación
directa colapsa muy por debajo de los 100 pares necesarios, y la dinámica de
las cadenas empuja hacia el colapso total, no hacia la separación.

## Estado

Barrido corregido (sin callejones sin salida) en curso.
