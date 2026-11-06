# ANDAMIO ITERANTE ENCONTRADO — y el oráculo del repo no lo ejecuta

## El hallazgo

`third_party/lmao/example_simple_cat.hell` (LMAO v0.6.0, GPL-3) es un **bucle
de fetch real**, commiteado en nuestro repo:

```
loop:                    // restore MOVD-command
ENTRY:                   // program starts here
    IN ?-                // read input character to A register
    R_IN
    OUT ?-               // write A register to stdout
    R_OUT
    MOVD loop            // infinite loop
```

Ensamblado: **2.051 bytes**, margen **56.998 B** bajo el límite.

## Verificado en el runner C (nativo)

| stdin | salida | len in | len out |
|---|---|---|---|
| `A` | `A` | 1 | 1 |
| `AB` | `AB` | 2 | 2 |
| `ABC` | `ABC` | 3 | 3 |
| `HELLO` | `HELLO` | 5 | 5 |
| `12345` | `12345` | 5 | 5 |

**Itera de verdad**: salida = entrada, byte a byte.

## El problema: nuestro oráculo diverge 8/8

Sobre el mismo binario:

```
stdin    oraculo Python                    runner C   acuerdo
'A'      (cadena basura larga)             'A'...     NO
'AB'     (cadena basura larga)             'AB'      NO
'ABC'    (cadena basura larga)             'ABC'     NO
0/8 acuerdo entre motores
```

**El runner C itera correctamente; el oráculo Python del repo
(`tools/oracle_classic.py`) no.**

## Por qué esto es el hallazgo de la sesión

1. **El andamio que los frentes 3 y 5 necesitaban existe**, es pequeño, y tiene
   margen de sobra (56.998 B). El bloqueante "no hay imagen que itere" queda
   refutado.
2. **El bloqueante real se traslada**: es el oráculo de referencia del repo, no
   la ausencia de primitivas. Un andamio que itera es inusable para verificación
   si el oráculo no lo ejecuta.
3. **Es la misma clase de falla que el frente 5** (divergencia oráculo-vs-runner),
   pero ahora sobre el andamio correcto y con margen de sobra. Eso sugiere una
   causa común: probablemente el tratamiento de EOF o del cifrado xlat2 en el
   bucle de retorno.

## Siguiente paso

Diagnosticar por qué `oracle_classic.py` no itera sobre `simple_cat.mb`.
Candidatos concretos, en orden de probabilidad:
1. Tratamiento de EOF: el runner C para en EOF (`terminated=1`, ya medido en
   `Malbolge-Engine/src/vm.c:144-149`); el oráculo pone `a=59048` y sigue. En un
   bucle infinito, el oráculo nunca sale y sigue leyendo EOF.
2. El `MOVD loop` del final: el oráculo puede no estar resolviendo el salto de
   retorno igual que el runner C.
3. Diferencio los dos con una traza paso a paso de ambos sobre el mismo binario.

