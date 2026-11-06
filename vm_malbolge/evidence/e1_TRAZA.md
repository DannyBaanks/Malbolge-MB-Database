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
