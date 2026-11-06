# E1 — traza decisiva (2026-11-06)

Imagen: mbir_cmp_lt_dec.mb (32.695 B). Entrada: "1 2".

```
paso 9706:  OUT  emite 0x31 ('1')   <- el PRIMER byte de stdin, crudo
paso 13150: IN   a <- 49 ('1')      <- se lee OTRO byte
paso 13159: HALT
```

## Lo que demuestra

El programa **emite el byte leído tal cual** y luego lee otro y para. No compara.

## Consecuencia para el diagnóstico

Los caminos de lectura están aterrizando en `print` (que hace `OUT`+`HALT`) en
lugar de en sus continuaciones. El flujo real es:

  read A -> ... -> print(OUT) -> read B -> HALT

## Dónde está el cruce

`value` prueba FLAG1 y salta a `return_from_value_3`, que pertenece al bucle de
rotación de `decrement_value`. `value2` prueba FLAG_D2_READ y salta a `compare`.
Ambas pruebas se disparan durante la lectura porque la lectura arma esas mismas
banderas, así que el flujo se desvía al primer bloque cuya prueba coincida.

## Arreglo concreto

Cada etapa de la lectura debe armar una bandera que **solo** pruebe la celda
destino de esa etapa, y ninguna otra. Es decir: separar completamente las
banderas de lectura de las banderas de las subrutinas de decremento.

---

# Segunda traza (2026-11-06, commit 7d65748)

Imagen 33.823 B. Salida: UN solo byte 0x00 para todos los pares.

## Flujo verificado

  read_digit_A -> value (vía FLAG_READ_A_C1/FLAG_READ_A)
  read_digit_B -> value2 (vía FLAG_READ_B_C1/FLAG_READ_B)
  compare      -> alterna decrement_value (value) y decrement_value2 (value2)

El formato de salida es correcto: un byte booleano.

## Defecto restante

La comparación decide siempre "falso". El primer decremento de `value` produce
carry de inmediato, así que `value` NO contiene a A en el momento de compare,
aunque la cadena de lectura de A se complete (su prueba dispara y el flujo
avanza a read_digit_B).

## Hipótesis para el siguiente paso

La escritura del byte leído en `value` la hace la maquinaria crazy de LMAO
(`U_CRAZY`/`U_ROT`), que deriva el contenido de la celda en tiempo de
ensamblaje y lo reescribe en tiempo de ejecución. Si la celda `crazy_value` no
está encadenada a `value_C1` —como sí lo está en las imágenes que funcionan—
el byte queda en el acumulador pero no en la celda.

