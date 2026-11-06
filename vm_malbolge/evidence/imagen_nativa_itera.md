# Frente 1/5 — la imagen nativa itera de forma estable; el centinela era el problema

## Medida

`mbir_native_cmp_decimal.mb` (imagen nativa del emisor), **sin centinela**,
dual-engine:

| stdin | Oráculo | Runner C | Acuerdo |
|---|---|---|---|
| `3` | `310a` | `310a` | **SÍ** |
| `3 4` | `310a` | `310a` | **SÍ** |
| `3 4 5` | `310a` | `310a` | **SÍ** |
| `1 2` | `310a` | `310a` | **SÍ** |
| `9 9` | `300a` | `300a` | **SÍ** |

**5/5 de acuerdo entre motores.** Cero divergencias.

## El segundo byte cambia el resultado

`9 9` → `30` (`0`), mientras que `3` → `31` (`1`). O sea: el segundo byte de
entrada **sí** altera la salida. El clasificador itera sobre el flujo.

## Lo que refuta el diagnóstico anterior

El frente 5 se cerró con "la divergencia era de EOF, neutralizada con
centinela". Eso era **correcto pero incompleto**: con centinela (`0x00`), el
flujo `"3\x00"` itera pero `"5\x00"` HALTea en el paso 23. Es decir, el
centinela no es neutral: ciertos bytes de control lo tratan como parada.

**Sin centinela, la imagen es estable en los dos motores.** La regla correcta
no es "usar centinela" sino "el flujo debe tener un número conocido de bytes,
o un byte de parada que el clasificador distinga de los operandos".

## Implicación para los frentes 3 y 5

El bloqueante reportado en `frentes3y5_bloqueante.md` sigue en pie para el
cargador de LMAO (flujo fijo, 2 IN, 40.034 pasos). Pero **la imagen nativa sí
itera y es estable**, así que la ruta de construir sobre ella está abierta y
mejor de lo que se dijo: no hace falta resolver el centinela, hace falta
respetar el contrato de flujo.

## Sigu experimento concreto

Tomar `mbir_native_cmp_decimal.mb` como andamio y medir si su cadena de
retorno puede encadenar un push/pop: con `"1 2"` ya se observa que el segundo
byte altera la salida, así que el mecanismo de "estado que sobrevive entre
bytes" existe. Medir **qué** estado sobrevive (¿una celda? ¿el acumulador?) es
el paso que decide si la pila de profundidad 2 es construible sobre esta
imagen.
