# Selector A → B → A: intentos de rearme

**H1:** una imagen selecciona la ruta correspondiente a cada byte de `01 02 01` y retorna al mismo punto de entrada, emitiendo `50 52 50` en una ejecución; H0: algún paso falla. Resultado **NOT_DEMONSTRATED**: se construyeron tres variantes sobre el clasificador existente. Ninguna cumple el contrato de tres bytes; esto no prueba imposibilidad general ni falsifica PureEpoch.

| Variante | 01 | 02 | 010201, oráculo / C | Resultado |
|---|---|---|---|---|
| `loop`: 18 colas OUT/HALT sustituidas por retorno | 50 | 52 | 50 / 50 | Se detiene tras procesar el segundo byte. |
| `rearmed`: reinicializa explícitamente cuatro datos mediante CRAZY | 50 | 52 | 5000 / 5000 | No entrega la secuencia; pasos Python/C difieren 38. |
| `rearmed2`: retorno mediante un trampoline `R_MOVED` | 5052 | 52 | 5052fe53 / 5052fe | Falla ya el control de un byte y diverge en salida y pasos entre motores. |

Las entradas y salidas de la tabla excluyen el LF extra del runner, registrado crudo en JSON. `probe.py` valida primero los controles de un byte y rechaza cada construcción multi-byte. El exit 0 del probe indica que la falsación y sus controles se ejecutaron como se esperaba, **no** que se construyó el selector.

## Estado observado, no causa universal

En `loop`, justo antes del primer IN, `value/value_C1/save_tmp/save_B` valen `29524/29524/29524/29524`; al volver al segundo IN valen `59048/29523/29523/1`. En `rearmed`, al segundo IN valen `0/0/0/0`, no C1: el rearme intentado no alcanza su invariante. En `rearmed2`, al segundo IN las cuatro celdas sí valen C1, pero eso **no basta** para establecer que las flags, instrucciones y cursores fueron restaurados: el control de un byte y la paridad ya fallan. Las causas exactas de estas últimas desviaciones no están demostradas. El trazador Python replica semántica del oráculo; el runner C aporta contraste externo de salida y pasos, no introspección de memoria.

## Reproducir y alcance

`python3 vm_malbolge/evidence/epoch_selector_rearm_v0/probe.py` reproduce los experimentos sobre las imágenes conservadas y reescribe `results.json`: copiar antes el pack para preservar el original. `build.py <directorio-nuevo>` reconstruye las variantes desde `vm_malbolge/src/byte_dispatch18.hell` con LMAO; sus bytes pueden diferir. No se ha integrado PureEpoch ni conectado el almacén exacto al selector. Probar la restauración del estado de control/flags y resolver la divergencia entre motores es el siguiente experimento, no una garantía de solución.
