# E1 — instrumentación definitiva (2026-11-06, direcciones verificadas)

`.dbg` regenerado con `lmao -d` sobre el `.hell` actual. Direcciones confirmadas:
value=57729, value_C1=57737, value2_C1=57761, value2=57784.

Imagen: 33.822 chars. Entrada: "1 2".

```
contenidos iniciales:
  value      @57729 = 81
  value_C1   @57737 = 81
  value2_C1  @57761 = 81
  value2     @57784 = 29443

eventos durante 400.000 pasos:
  (33340, OUT, 255)
  (33341, HALT, None)
```

## Resultado concluyente

**CERO escrituras** en value, value_C1, value2_C1 o value2 durante toda la
ejecución. Las celdas conservan sus contenidos iniciales.

Las direcciones del `.dbg` anterior resultaron correctas (la regeneración da las
mismas), así que la instrumentation previa no leía celdas equivocadas: la
conclusión se mantiene y queda confirmada por segunda vía.

## Qué significa

El camino de lectura de este programa **nunca escribe** el byte leído en la
celda destino. Las pruebas de las celdas disparan (el flujo avanza) pero la
instrucción que debe escribir (CRAZY con d sobre la celda) no se ejecuta con el
puntero en la posición correcta.

## Estado

El diagnóstico está cerrado y verificado por dos métodos independientes:
instrumentación de celdas y comparación de contenidos iniciales. El arreglo
requiere recolocar el R_CRAZY de la cadena de lectura, que es un cambio de
posición dentro del camino, no de lógica.
