# E1 — instrumentación de las celdas value/value2 (2026-11-06)

Imagen: mbir_cmp_lt_dec.mb (33.823 B). Entrada: "1 2".
Direcciones (del .dbg): value=57729, value2=57784.

```
paso    evento  dato   value   value2    a
33314   IN      1          81    29443    49     <- lee '1'
33324   IN      ' '        81    29443    32     <- lee el espacio
33332   IN      2          81    29443    50     <- lee '2'
33333   IN      EOF        81    29443    -1
33340   OUT              81    29443    -1     <- emite 255
33341   HALT             81    29443    -1
```

## Hallazgo concluyente

**Las tres instrucciones IN se ejecutan, pero los bytes NUNCA se escriben en
`value` ni en `value2`.** Las dos celdas conservan sus contenidos iniciales
(81 y 29443, que ni siquiera son C1) durante toda la ejecución.

## Qué significa

El camino de lectura arma las banderas y las pruebas de las celdas disparan
(el flujo avanza de read_digit_A a read_digit_B y de ahí a compare), pero la
**escritura del acumulador en la celda** —que la hace la instrucción CRAZY
cuando d apunta a la celda destino— no ocurre.

## Consecuencia

La alternancia de compare decrementa dos celdas que nunca recibieron los
operandos, así que el primer carry llega siempre por el lado de `value` y
`result_false` se selecciona siempre. El 0x00 constante es la consecuencia
directa de esto, no de la lógica de comparación.

## Arreglo concreto

La cadena de lectura necesita que el CRAZY se ejecute con d sobre la celda
destino. En las imágenes que funcionan, la secuencia es:

    R_FLAG2 ; MOVED crazy_value_C1     -> d apunta a la celda crazy
    (la prueba de value_C1 dispara)
    R_CRAZY R_MOVED                    -> ejecuta CRAZY: a = crazy(a, mem[d]) y mem[d] = a
    R_FLAG2 ; MOVED crazy_value        -> d apunta a la celda crazy de value
    ...

El punto crítico es el `R_CRAZY` **inmediatamente después** de que la prueba
dispara: es esa instrucción la que escribe. Si la cadena de retorno no la
incluye en la posición correcta, el byte se pierde.
