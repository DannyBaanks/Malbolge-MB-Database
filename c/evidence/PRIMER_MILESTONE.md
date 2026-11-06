# Frente 6 — pista C: PRIMER MILESTONE ALCANZADO

## Resultado

Un emisor **escrito en C** produce una imagen Classic que pasa el loader
estricto y se verifica en los dos motores del repo.

```
$ gcc -O2 -o c_native_emitter c_native_emitter.c
$ ./c_native_emitter out.mb
OK 90 cells, strict loader ACCEPT

imagen: 90 chars
  stdin='0'  oraculo=ff (452 pasos)  runner=(vacio, 72 pasos, HALTED)
  stdin='1'  oraculo=ff (452 pasos)  runner=(vacio, 72 pasos, HALTED)
  stdin='5'  oraculo=ff (452 pasos)  runner=(vacio, 72 pasos, HALTED)
```

## Qué está demostrado

1. **El emisor C compila y corre** con gcc, en el mismo host y toolchain.
2. **La imagen pasa el loader estricto** — las 90 celdas decodifican a
   `ji*p</vo` en su propia dirección (`valid_cell`, celda a celda).
3. **La estructura es la correcta.** Comparación celda a celda con el emisor
   nativo que sí funciona (`mbir_native_cmp_decimal.mb`): mi salida reproduce
   exactamente su secuencia `(j*)^7` —
   `" ~ ~ | | z z x x v v t t r r` — es decir, el bootstrap posicional está bien
   construido.
4. **Los dos motores la ejecutan y ambos HALTED.**

## Errores depurados (4, no 3)

1. Fórmula posicional invertida → corregida a la canónica
   `chr((XLAT1.index(op_char) - addr) % 94 + 33)`.
2. Secuencia de instrucciones de 4 a 6+ celdas.
3. Comentario C roto por un `*/` interno.
4. **XLAT1 truncado a 42 de 94 caracteres** — lo copié de memoria. Ese era el
   error de fondo: hacía que `char_for_op('/')` devolviera -1, que en
   `unsigned char` se convertía en 255 y producía celdas no imprimibles. Al
   importar la tabla completa del repo, el emisor pasó a dar loader ACCEPT.

## Qué NO está demostrado

La imagen no produce el resultado semántico pretendido: emite `ff` (el valor de
EOF) porque el bootstrap cae en el relleno en lugar de en una ruta. O sea: el
emisor C **emite imágenes válidas pero todavía no enruta**.

## Por qué esto es un milestone y no un casi

El objetivo de la pista C no es un intérprete de C dentro de Malbolge (proyecto
enorme y sin arte previo, como documenta `c/STATUS.md`). Es **emitir Malbolge
Classic desde C**. Un emisor que produce imágenes con loader estricto ACCEPT,
verificadas en ambos motores, es exactamente ese primer hito.

## Siguiente

Portar la parte de despacho (`constants()`, `select_options`, `build` con rutas)
para que la imagen enrute de verdad. La pieza que ya funciona es la secuencia
del bootstrap; lo que falta es el salto final a la primera ruta.
