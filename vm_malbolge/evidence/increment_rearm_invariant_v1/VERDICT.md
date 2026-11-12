# Invariante de rearme del bucle de incremento Malbolge

2026-11-12. Base `7d2e34c`. Se caracterizó exhaustivamente el estado de memoria y el mecanismo de rearme de la imagen de incremento `vm_malbolge/evidence/increment_circuit_loop_v1/run02/increment.mb` (SHA-256 `aec09e9fe64ae4b456818ce1960b7ecb92ccfae456592c2d5b8413b6190757f1`) durante las 257 visitas a `IN` (flujo `00..ff` seguido de EOF).

| Puerta de este experimento | Resultado y alcance |
|---|---|
| G0: Invariante de datos (scratch) | PASS algebraico y operativo. Las únicas celdas de datos con variación entre iteraciones son los temporales `t1` (58160) y `t2` (56938). En los 256 ciclos de iteración, los dos primeros accesos a cada temporal ejecutan `crazy` con constante que reinicia su valor a `29524`. Se demostró para todo el espacio ternario (59 049 palabras) que `crazy(crazy(29524, x), crazy(29524, x)) == 29524`. |
| G1: Invariante de código (NOP orbits) | PASS formal. 13 celdas de código mutan por cifrado XLAT2 durante el bucle (órbitas de longitud 2 a 9). Se evaluó la órbita completa de cada una: el 100% de las fases decodifica a NOP (`(word + addr) % 94 ∉ {4, 5, 23, 39, 40, 62, 81}`). Las variaciones de código son operacionalmente inertes en todas sus fases. |
| G2: Aislamiento de relleno (padding) | PASS. 43 celdas de relleno (tipo 4) cambian al ser atravesadas en saltos; se verificó que ninguna es leída jamás como operando de datos (`reserved_data_reads: []`). |
| G3: Paridad de ejecución y parada | PASS en el dominio 0..255 + EOF. 1 446 585 pasos en el modelo de referencia hasta `HALTED` con salida `01..00`. Ejecución nativa en Olmstead idéntica byte a byte (rc=0, SHA-256 `9bc038d0a0fb391f3b33618dcf08b6553560ef0ae0f7ad557871598f27b7194b`). |

## Por qué el estado bit a bit no es idéntico (y por qué no hace falta)

1. **Ausencia de puntos fijos en XLAT2**: La tabla de cifrado de instrucciones de Malbolge Classic `XLAT2` tiene exactamente cero (0) puntos fijos en los 94 caracteres imprimibles (`XLAT2[i] != chr(i+33)` para todo `i ∈ [0..93]`). Por definición, cualquier celda de código ejecutada un número de veces que no sea múltiplo exacto de su periodo de órbita (2, 4, 5, 6, 9 ó 68) alterará su valor binario en memoria.
2. **Disparidad de bifurcaciones ternarias**: La detección de EOF y el filtrado de trits derivan el flujo hacia ramas distintas (`NON_EOF_0..3`) según los trits de la entrada. Por lo tanto, los contadores de ejecución de cada rama avanzan a ritmos dispares dependiendo de los bytes procesados.
3. **Rearme semántico vs. identidad física**: El compilador garantiza la invariante del bucle mediante dos mecanismos complementarios:
   - *Reiniciador algebraico*: `t1` y `t2` se resetean antes de cualquier cómputo activo en cada ciclo.
   - *Órbitas cerradas estériles*: El código que cambia de fase no altera semántica alguna al pertenecer íntegramente a órbitas NOP.

## Evidencia preservada

- `observe.py`: script de medición paso a paso contra el modelo exacto y Olmstead nativo.
- `observe.stdout.raw.txt`: volcado JSON con la auditoría de las 257 visitas, registro de las 13 celdas de código y sus órbitas, y confirmación de los 256 ciclos de reinicio.
- `observe.stderr.raw.txt`: salida de error vacía (salida limpia).
- `observe_v1.stderr.raw.txt`: registro histórico del primer intento de aserción (preservado).
