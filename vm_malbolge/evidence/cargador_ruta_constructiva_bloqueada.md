# Intento de ruta constructiva: integración vía cargador M2

## Veredicto

**BLOQUEADO** por la misma causa raíz que los otros frentes: no existe instrucción
`mem[d] = valor_conocido` ni `c = valor_conocido` en Malbolge Classic.

## Lo que se intentó

Se partió de `vm_malbolge/src/mbir_m2_loader.hell` (40,309 B, 18,740 de margen),
que ya carga 4 bytes de stdin en `prog_0..prog_3` y ejecuta vectores específicos
(v1, v2, v4). El objetivo era convertir ese andamio en un bucle
fetch-decode-execute general que ejecute `ADD`/`SUB`/`CMP_EQ` desde RAM.

Se verificó empíricamente que:
- Se pueden agregar celdas de RAM (`prog_4`) y flags al loader (ensambla a 43,223 B).
- Se pueden agregar bloques de ejecución al final del bloque `{...}` del loader.

## Bloqueante: imposibilidad de ejecutar el contenido de RAM como código

Para que `prog_0..prog_3` se ejecuten como instrucciones, el program counter `c`
debe apuntar a esas direcciones. Pero:

1. `JMP` hace `c = mem[d]`: lee el **valor** de la celda, no su dirección.
   Si `d = dir(prog_0)`, entonces `c = valor(prog_0)` (ej. 1), no `dir(prog_0)`.
2. No existe instrucción `mem[d] = c` ni `c = valor_conocido`.
3. `c` solo se puede establecer con `JMP` (desde `mem[d]`) o auto-incrementar
   (`c = (c + 1) % MEM_SIZE`).
4. Las celdas de datos no están en 2-ciclo de `XLAT2`, así que una vez ejecutadas
   (o leídas), se cifran y no pueden repetirse con el mismo valor.

Por tanto, no hay forma de hacer que el contenido de `prog_0..prog_N` se ejecute
como instrucciones de bytecode. El loader puede almacenar datos en RAM, pero no
puede ejecutarlos como programa.

## Conclusión

La ruta constructiva del cargador está bloqueada por la misma causa raíz que
todos los demás frentes: **no hay asignación directa a memoria ni lectura del
PC**. Sin `mem[d] = valor_conocido`, no se puede:
- Guardar el PC para retorno de subrutina (pila de llamadas)
- Hacer direccionamiento indexado (array lookup)
- Ejecutar el contenido de RAM como instrucciones (bucle fetch-decode-execute)

Este bloqueante cierra el frente 1 (integración M2+ALU+CMP_EQ vía cargador).

## Frentes restantes del roadmap

Todos los frentes `NOT_DEMONSTRATED` tienen ahora un bloqueante medido:
- Pop exacto en bucle: imposible (`rot^10` requiere 10 ROTs, sin contador estable)
- Pila de llamadas: imposible (`c` es solo escritura)
- Integración M2+ALU+CMP_EQ: imposible (sin ejecución de RAM como código)
- Comparador de dos operandos variables: bloqueado por separabilidad trit-a-trit
