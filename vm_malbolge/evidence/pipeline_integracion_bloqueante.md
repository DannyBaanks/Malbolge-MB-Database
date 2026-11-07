# Bloqueante: integración M2 + ALU + CMP_EQ en una sola imagen

## Veredicto

**NOT_DEMONSTRADO.** No existe una sola imagen de Malbolge Classic que cargue un
programa en RAM y además ejecute la ALU de 14 vectores (`ADD`, `SUB`) y el
`CMP_EQ`.

## Obstáculo medido: espacio insuficiente en el inicializador de LMAO

La imagen base `vm_malbolge/src/mbir_m2_alu.hell` ya carga un programa de 7
bytes en RAM y ejecuta `ADD`/`SUB` (8/8 PASS en oráculo y runner C). Ensambla
a **56,361 bytes**, dejando solo **2,688 bytes de margen** sobre los 59,049
del espacio de direcciones de Malbolge.

El generador `vm_malbolge/tools/unified_gen.py` intenta añadir `CMP_EQ`
(opcode 0x04) sobre `mbir_m2_alu.hell` mediante:
1. Dos flags nuevas (`OPCODE_PHASE`, `CMP_MODE`)
2. Extensión de la clasificación de opcode de 3 a 5 decrementos
3. Bifurcación de los bloques de salida por `OPCODE_PHASE`
4. Bloques `cmp_equal` / `cmp_not_equal` para el resultado

**LMAO v0.6.0 rechaza la imagen:**

```
Error: Free space exceeded (Add Malbolge command).
Internal error: Cannot generate initialization code for cell 58969.
Error: Memory usage conflict while generating initialization code.
```

El fallo ocurre en la celda 58,969, a solo **80 celdas del límite** (59,049).
Los flags caben; lo que no cabe es el **código de despacho** adicional en el
margen restante.

## Ruta constructiva documentada (no ejecutada)

El README sugiere construir sobre el andamio del **cargador**
(`vm_malbolge/src/mbir_m2_loader.hell`), que ensambla a 40,309 bytes y deja
**18,740 bytes de margen**. Sin embargo:

- El cargador es un andamio con **vectores de ejecución específicos** (v1, v2,
  v4), no un bucle fetch-decode-execute general.
- No tiene un PC general ni un despacho de opcodes arbitrario.
- Agregar `ADD`/`SUB`/`CMP_EQ` al cargador requeriría construir un bucle de
  ejecución y un despacho de opcode desde cero sobre las flags existentes,
  lo cual es una reescritura significativa.

## Causa raíz

El inicializador de LMAO genera código de inicialización para cada celda de
datos y cada flag. Cuando el programa está cerca del límite del espacio de
direcciones (59,049 celdas), el inicializador no puede encontrar ubicaciones
válidas para todas las celdas requeridas sin conflictos. Esto no es una
limitación del generador HeLL, sino del ensamblador LMAO v0.6.0.

## Próximo frente

Este bloqueante cierra el frente de "integración completa del pipeline" del
roadmap. Los únicos frentes restantes son los ya documentados:
- Pila de llamadas: imposible (`c` es solo escritura)
- Pop exacto: imposible en bucle (`rot^10` requiere 10 ROTs, sin contador estable)
- Comparador de dos operandos variables: bloqueado por separabilidad trit-a-trit
