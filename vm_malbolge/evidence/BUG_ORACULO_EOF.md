# Bug del oráculo del repo: no para en EOF (bucle infinito)

## Causa raíz, confirmada

`tools/oracle_classic.py` sobre `simple_cat.mb` con stdin `"AB"`:

| max_steps | pasos | status | salida (hex) |
|---|---|---|---|
| 200 | 200 | MAX_STEPS | (vacía) |
| 1.000 | 1.000 | MAX_STEPS | (vacía) |
| 5.000 | 5.000 | MAX_STEPS | `4142ffffffffffffffffffff` |
| 50.000 | 50.000 | MAX_STEPS | `4142ffffffffffffffffffff` |
| 200.000 | 200.000 | MAX_STEPS | `4142ffffffffffffffffffff` |

## Diagnóstico

`41 42` = `A` `B` → **el oráculo procesa los dos bytes correctamente**. Luego
emite `ff` = 255 indefinidamente hasta agotar `max_steps`.

`ff` = `59048 & 255` = el valor que el oráculo asigna en EOF
(`oracle_classic.py:75`: `a = -1 if ch is None else ord(ch)`; con `a` como
`unsigned short`, -1 → 65535, y `a % 256` = 255… el valor observado es
consistente con el EOF).

## El mecanismo

El runner C **para** cuando el stdin se agota:
`Malbolge-Engine/src/vm.c:144-149`:
```c
case 23:
    if (input_pos < input_len) { a = input[input_pos++]; }
    else { terminated = 1; }        // <- PARADA
    break;
```

El oráculo Python **no para**: asigna el valor de EOF y sigue ejecutando. En un
programa con bucle de fetch (`MOVD loop`), eso es un bucle infinito que emite
basura hasta el tope de pasos.

## Veredicto

**Es un bug de `tools/oracle_classic.py`, no del andamio.** El andamio
(`example_simple_cat.hell`) itera correctamente: el runner C lo demuestra con
salida = entrada byte a byte.

## Impacto en la campaña

1. **El bloqueante de los frentes 3 y 5 no era la ausencia de un bucle**: el
   bucle existe (2.051 B, 56.998 B de margen).
2. **El bloqueante es el oráculo de referencia**, que no puede verificar ningún
   programa iterante. Todo lo medido hasta ahora contra el oráculo en programas
   con bucle de lectura es inválido o necesita el runner C como motor primario.
3. **Arreglo concreto**: hacer que el oráculo termine en EOF igual que el runner C
   (`terminated`), o documentar que el runner C es el motor canónico para
   programas con bucle de entrada.

## Nota importante

Esto **reabre** la medición del frente 5: la divergencia medida allí (`runner C
'50' vs oráculo basura) tiene la misma causa. El centinela funcionaba no porque
resolviera el EOF, sino porque evitaba que el oráculo entrara en el bucle
infinito. La conclusión del frente 5 era correcta en la práctica pero su
mecanismo estaba mal entendido.
