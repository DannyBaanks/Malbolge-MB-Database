# Bloqueante: pop exacto imposible en bucle (Malbolge Classic)

## Veredicto

**IMPOSIBLE en un bucle real de Malbolge Classic.** Un "pop exacto" —emitir el valor
almacenado en una celda de pila sin rotarlo ni modificarlo— no es construible
dentro de un bucle de fases. El bloqueante no es una limitación del generador;
es una consecuencia de la semántica del dialecto.

## Causa 1: no existe instrucción de lectura pura

| Instrucción | Lee `mem[d]` | Afecta `a` | Modifica `mem[d]` |
|---|---|---|---|
| `ROT` (39) | Sí | `a = mem[d]` | **Sí** (`mem[d] = rot(mem[d])`) |
| `CRAZY` (62) | Sí | `a = mem[d]` | **Sí** (`mem[d] = crazy(a, mem[d])`) |
| `MOVD` (40) | Sí | No | No (solo cambia `d`) |
| `JMP` (4) | Sí | No | No (solo cambia `c`) |
| `IN` (23) | No | `a = stdin` | No |
| `OUT` (5) | No | emite `a` | No |

`MOVD` y `JMP` leen `mem[d]` pero no lo ponen en `a`. `IN` pone algo en `a`
pero lee de stdin, no de `mem[d]`. **`ROT` es la única instrucción que puede
poner el contenido de una celda en `a`, y siempre la rota.** Por tanto, cualquier
pop que emita el valor de una celda la altera.

## Causa 2: `rot^10 = identidad`, pero ningún `rot^k` para `k < 10`

Verificado empíricamente para todo `[33, 126]`:

| `k` | ¿`rot^k = identidad`? | ¿punto fijo de `rot^k`? |
|---|---|---|
| 1 | No | Ninguno |
| 2 | No | Ninguno |
| 3 | No | Ninguno |
| 4 | No | Ninguno |
| 5 | No | Ninguno |
| 6 | No | Ninguno |
| 7 | No | Ninguno |
| 8 | No | Ninguno |
| 9 | No | Ninguno |
| 10 | **Sí** | — |

Para emitir exactamente `S` (sin rotar) se necesitan **10 `ROT` consecutivos**
sobre la misma celda: `rot^10(S) = S`, y tras el décimo `ROT`, `a = S`.

## Causa 3: una celda de trabajo no puede hacer `ROT` en 2+ fases de su ciclo

El ciclo de `XLAT2` de una celda que no se restaura avanza una fase por iteración.
Medido empíricamente: **ninguna dirección imprimible tiene `ROT` en 2 o más
posiciones de su ciclo de `XLAT2` sin incluir `HALT`/`JMP` que romperían el
bucle.** Una celda ejecuta `ROT` como máximo una vez por ciclo completo.

## Causa 4: distribuir 10 `ROT` en múltiples vueltas requiere un contador

Dado que una celda solo puede hacer un `ROT` por ciclo, aplicar 10 `ROT` sobre
la misma celda `S` requiere distribuirlos en al menos 10 vueltas del bucle (o
más, si el ciclo es largo). Entre cada par de `ROT` hay que:

1. Restaurar `d = S` (cada `ROT` incrementa `d` automáticamente).
2. Saber cuándo se han completado exactamente 10 `ROT` para parar y emitir.

El punto 2 requiere un **contador de rotaciones**. Pero cualquier celda usada
como contador se cifra con `XLAT2` al ejecutarse, y no hay forma de mantener un
valor estable a través del cifrado. Un contador que cambia de valor no puede
señalar "ya van 10".

## Conclusión

El pop exacto es imposible en un bucle de Malbolge Classic porque:

- No hay instrucción de lectura pura (`mem[d]` → `a` sin modificar `mem[d]`).
- Un pop exacto requiere exactamente 10 `ROT` sobre la misma celda.
- Una celda no puede hacer `ROT` en 2+ fases de su ciclo.
- Distribuir 10 `ROT` en el tiempo requiere un contador estable, y los
  contadores se cifran.

## Alternativa demostrada (no es pop exacto)

El LIFO de profundidad 2 en bucle (`stack_loop_lifo2.md`) usa `ROT` como pop:
lee la celda, la rota y emite el valor rotado. El valor almacenado queda
rotado en la ranura, no se vacía. Esto es un **pop con rotación**, no un pop
exacto, y es lo máximo expresible en un bucle real.

## Próximo frente

La pila de llamadas (contador de programa general, múltiples marcos) sigue
abierta y no está bloqueada por este problema.

---

## Corrección medida (2026-11-07) — el bloqueante no es absoluto

El texto anterior **se conserva** como registro histórico. Esta sección lo corrige con
medidas nuevas y no lo reescribe.

**Medición:** `vm_malbolge/evidence/epoch_algebra_v3/` (imagen `resolver.mb`,
SHA-256 `ffb2453a7c9301c16ed14801d7ca91c496ed0db1f2c1b00d689c90bef818a32b`;
pack `manifest.json` con los hashes de todas las piezas).
Comando: `python3 vm_malbolge/evidence/epoch_algebra_v3/probe.py` → salida 0,
`[verdict] all_checks_pass = True`.

**Lo que sigue vigente (medido):** una celda que contiene un dato arbitrario `S` no
puede copiarse a `a` sin escribir en ella. Las únicas instrucciones que mueven
`mem[d]` a `a` son `ROT` (39) y `CRAZY` (62), y **ambas escriben `mem[d]`**. La tabla
de "Causa 1" es correcta tal cual.

**Lo que queda refutado:** la conclusión "el pop exacto es imposible". Con una
disciplina de máscara (`121 = 11111_3`, imprimible, involución válida para todo valor
de byte: `crazy(crazy(V,121),121) = V`) se puede:

1. escribir un valor **exacto** recibido en runtime (`stdin`) dentro de una celda
   cualquiera, y
2. emitir ese mismo valor exacto **ejecutando esa celda**: en la imagen v3 el `OUT`
   emite el byte exacto (63 → `3f`) en el PC de la celda escrita (36, 130, 224).

Barrido exhaustivo: 256 payloads × 3 épocas = 768 escrituras, **0 discrepancias**
(`results.json` → `exactness_sweep_0_255`). El valor exacto se emite **sin rotación**;
lo que se consume es la **máscara** de la celda, no el valor. Por tanto, la emisión
exacta de un valor almacenado sí es construible; lo que no es construible es copiar
una celda de dato arbitrario a `a` sin tocarla.

**Coste medido y límite:** la máscara de la celda consumida (`121 → V`) obliga a
rearmar la celda antes del siguiente uso. El rearm con journal y diez `ROT` está
demostrado en `epoch_journal_state_v2` para una celda fija; **componer** ese rearm
con la selección de época por puntero sigue siendo `NOT_DEMONSTRATED`. La emisión
exacta queda, por tanto, acotada al caso "el valor se escribe antes de emitirse" o
"la celda es una máscara cuyo valor se reproduce".

**Conclusión revisada:** el bloqueo real es más estrecho —no hay lectura pura de una
celda de dato arbitrario y hay que pagar una máscara por celda—, no "imposible" en
general.

---

## Corrección medida (2026-11-09) — la máscara imprimible deja de ser el límite: `29524` se construye en runtime

El texto anterior y la corrección de 2026-11-07 **se conservan** como registro
histórico. Esta sección los matiza con una medida nueva y no los reescribe.

**Medición:** `vm_malbolge/evidence/torus_reach_v1/`
(comando: `python3 vm_malbolge/evidence/torus_reach_v1/probe.py` → exit 0,
`[verdict] all_checks_pass = True`; pack con `manifest.json` de hashes).

**Lo que queda refutado aquí:** la idea de que hace falta una máscara imprimible
involutiva y que, al no existir una para palabras de 10 trits, la síntesis de
constantes grandes está bloqueada. Medido:

1. **`29524` (diez trits iguales a 1, la única máscara involutiva para toda
   palabra) se construye con UNA `CRAZY`: `crazy(54, 54) = 29524`**, donde `54`
   es un byte imprimible (`2000_3`, sin ningún trit 1). Ocho imprimibles sirven:
   `54, 56, 60, 62, 72, 74, 78, 80`. No hace falta imprimibilidad de la máscara
   porque la máscara se fabrica en memoria.
2. `0 = crazy(29524, 29524)` → la pareja se auto-reproduce.
3. La dependencia circular real, ahora exacta y probada enumerando los 9 pares de
   trits: `D(crazy(a,v)) ⊆ D(a) U D(v)` — un trit 2 no aparece donde ningún
   operando lo tenía. La salida es que **el acumulador es una fuente independiente
   de trits 2** y `ROT` los recoloca: un solo trit 2 (el de `54`) cubre las 10
   posiciones por rotación.
4. **`59048` (diez trits iguales a 2) es alcanzable**, con tres testigos
   verificados por replay contra el oráculo del repo: constructivo (1038 ops),
   compacto (`crazy(58806, crazy(242, crazy(54,54)))`, 7 ops) y fiel a la VM
   (11 ops, presuponiendo sólo la escritura exacta de bytes ya demostrada en
   `epoch_algebra_v3`).
5. Toda palabra de 10 trits tiene testigo constructivo (inducciones `Q`/`U`/`F`
   sobre los 1023 subconjuntos, fórmula general verificada en 209 palabras) y el
   cierre hacia atrás de `29524` cubre las 59049 palabras.
6. Medido además: `121` es involutivo sólo en 7776/59049 palabras
   (`= 3^5 · 2^5`), `29524` en todas → el upgrade del resolvedor de v3 a payload
   de palabra completa tiene ruta constructiva.
7. Medido: el relleno de memoria más allá del programa es **crazy-fill** en el
   runner C original (5 direcciones, 3 motores), no relleno con cero: **no hay
   celdas cero gratuitas**, el 0 se construye.

**Lo que sigue vigente (sin cambio):** no hay lectura pura de una celda de dato
arbitrario; el rearm en la misma ejecución con journal + selección dinámica; y la
ejecución nativa autónoma de estos testigos (`NOT_DEMONSTRATED` en el pack nuevo,
con las precondiciones identificadas).
