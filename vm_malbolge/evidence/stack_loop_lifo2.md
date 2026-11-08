# Pila LIFO de profundidad 2 dentro de un bucle real — fases por ciclo de cifrado

## Resultado

`vm_malbolge/tools/stack_loop_lifo2_gen.py` emite dos imágenes de **256 bytes,
sin LMAO**:

| artefacto | sha256 | papel |
|---|---|---|
| `vm_malbolge/src/mbir_stack_loop_lifo2.mb` | `1a911964fbc980fbc3b1b5386fedd37cc8e1e81dce12b820e5a83be141954a82` | positivo |
| `vm_malbolge/src/mbir_stack_loop_lifo2_ctrl.mb` | `8e99863331dafee000beeaa3f84c561accd8c5ff0315a08faf5c763bccb04a01` | control `W1`/`W2` inertes |

Un bucle real con **dos ranuras de pila** y orden **LIFO**: en cada ciclo de 9
iteraciones se apila en `S1`, luego en `S2`, y se desapila primero `S2`
(fase 4) y después `S1` (fase 5). El valor apilado más tarde sale primero.
**8/8 casos en oráculo y runner C, positivo y control**, con 2048 bytes
aleatorios incluidos. Evidencia máquina:
`vm_malbolge/evidence/stack_loop_lifo2.json`.

## El mecanismo: el ciclo de cifrado como calendario de fases

Continuidad directa de `stack_loop_phase.md`. Si una celda de trabajo **no se
restaura**, su valor avanza por su ciclo de `XLAT2` y el opcode que decodifica
cambia en cada iteración: el estado de cifrado de la celda es el selector de
fase.

Aquí hacen falta **dos** celdas de trabajo con fases distintas. La clase de
ciclo de longitud 9 es `C = [73, 50, 80, 66, 62, 76, 79, 67, 85]`, y dentro de
ella existen dos direcciones que dan exactamente el calendario LIFO:

| celda | dirección | valor inicial | opcode inicial | fases |
|---|---|---|---|---|
| `W1` | 71 | 85 | `CRAZY` (62) | `CRAZY`@0, `ROT`@5 |
| `W2` | 83 | 79 | `NOP` (68) | `CRAZY`@3, `ROT`@4 |

Las dos arrancan en un opcode **válido** (loader estricto completo: `W1` como
`CRAZY`, `W2` como `NOP`), y las dos están en la misma clase de ciclo, así que
sus fases no derivan: ambas avanzan un paso por iteración.

Calendario por ciclo de 9 iteraciones (= 9 bytes de entrada):

| fase | acción |
|---|---|
| 0 | `W1` `CRAZY` → **push** en `S1` |
| 1, 2 | inerte |
| 3 | `W2` `CRAZY` → **push** en `S2` |
| 4 | `W2` `ROT` → **pop** de `S2`, emite |
| 5 | `W1` `ROT` → **pop** de `S1`, emite |
| 6, 7, 8 | inerte |

El orden `push S1 (0) < push S2 (3) < pop S2 (4) < pop S1 (5)` es LIFO.

## Programa

Con `S1 = 47`, `S2 = 87`, `A_IN = 43`, `A_MOVD1 = 60`, `A_MOVD2 = 64`,
`A_OUT = 119`, `A_W1 = 71`, `A_W2 = 83`:

```
bootstrap:
  0  MOVD    d = mem[0] = 40
  1  MOVD    d = mem[41] = 90
  2  JMP     c = mem[91] = 42  (landing antes de IN)

vuelta (16 pasos):
  IN        a = byte
  J_IN      restaura IN; despacha a MOVD1
  M1 MOVD   d = mem[95] = S1-3      (post d = S1-2)
  J_M1      restaura M1; despacha a W1 con d = S1
  W1        CRAZY (fase 0) / NOP / ROT (fase 5) sobre mem[S1]
  J_W1      UN solo salto (no restaura W1): despacha a MOVD2
  M2 MOVD   d = mem[49] = S2-3      (post d = S2-2)
  J_M2      restaura M2; despacha a W2 con d = S2
  W2        CRAZY (fase 3) / NOP / ROT (fase 4) sobre mem[S2]
  J_W2      UN solo salto: despacha a OUT
  O  OUT    emite a & 255
  J_O       restaura OUT; despacha de vuelta a IN
```

Los punteros son 13 celdas: `41→90, 45→60, 46→70, 48→63, 49→84, 85→64,
86→82, 88→118, 90→119, 91→42, 93→43, 94→59, 95→44`. Los landings (celdas
sacrificiales que se cifran en cada salto) son `42, 59, 63, 70, 82, 118`.

`IN`, `M1`, `M2` y `OUT` se restauran con el par JMP de siempre y valores en
2-ciclo de `XLAT2`; `W1` y `W2` **no** se restauran, y por eso sus fases
avanzan.

## Trazado verificado

Trazando la imagen positiva en el oráculo (instrumentación del bucle de
`oracle_classic.run`, en `trazado` del JSON):

| celda | d en todas sus ejecuciones | secuencia de opcodes (6 primeras) |
|---|---|---|
| `W1` (71) | 47 = `S1` | `CRAZY`, inv, inv, inv, inv, `ROT` |
| `W2` (83) | 87 = `S2` | `NOP`, inv, inv, `CRAZY`, `ROT`, inv |

Cada celda de trabajo se ejecuta **siempre** sobre su propia ranura: `W1` con
`d = S1 = 47`, `W2` con `d = S2 = 87`. No hay colisión de punteros porque cada
ranura tiene su propio par `(S+1, S+2)`.

## Evidencia del orden LIFO

Bloque de 9 bytes con `A` en la posición 0 y `B` en la posición 3 (las dos
posiciones de push):

| bloque de entrada | salida |
|---|---|
| `A`@0, `B`@3 | `68 2e 2e 69 5b 78 2e 2e 2e` |
| `B`@0, `A`@3 | `69 2e 2e 68 78 5b 2e 2e 2e` |

Las posiciones 0 y 3 son los pushes (`crazy(byte, 33)`: `0x68` para `A`,
`0x69` para `B`). Las posiciones 4 y 5 son los pops: en el primer bloque sale
`0x5b` (el valor apilado en la posición 3, el más reciente) y después `0x78`
(el de la posición 0, el más antiguo); al intercambiar las entradas, los dos
pops intercambian posiciones. Es LIFO, medido byte a byte.

## Control negativo

El control usa la **misma imagen** con dos cambios: `W1` y `W2` pasan a valer
42, cuyo ciclo de `XLAT2` es `[42, 114, 125, 105]` y cuyos opcodes en las
direcciones 71 y 83 son `[19, 87, 8, 82]` y `[31, 9, 20, 0]` — todos
inválidos. Ninguna de las dos celdas escribe ni lee jamás, y la salida
esperada es exactamente la entrada. El control da **8/8** en ambos motores:
el comportamiento del positivo lo causan las celdas de trabajo, no la cadena
de punteros.

## Estándar de celdas

Las celdas de **código** decodifican a opcode válido en su propia dirección
(incluidas `W1` y `W2` en su valor inicial: `CRAZY` y `NOP`); las celdas de
**puntero** son imprimibles pero pueden decodificar a un opcode inválido
porque nunca se ejecutan (solo las leen `MOVD`/`JMP` como datos). Las dos
ranuras de pila arrancan en 33 y son datos.

## Alcance y NOT_DEMONSTRATED

- **Demostrado:** dos ranuras de pila en un bucle real con orden LIFO; las
  fases las elige el ciclo de `XLAT2` de cada celda de trabajo; doble motor,
  8/8 positivo y 8/8 control, 2048 bytes aleatorios incluidos.
- **NOT_DEMONSTRATED:** pop **exacto**. El pop es un `ROT`: lee la ranura, la
  rota y la deja rotada; no vacía la ranura. Un pop exacto (10 `ROT`, porque
  `rot^10` es la identidad) es **imposible en bucle**: varios `ROT` sobre la
  misma celda dejan todos `d` en la misma dirección y compartirían las
  celdas-puntero `(S+1, S+2)`. Es el mismo bloqueante del `one-shot`, y por
  eso el `one-shot` sí podía pagar los 10 `ROT`.
- **NOT_DEMONSTRATED:** supresión de las fases inertes 1, 2, 6, 7, 8. `IN` y
  `OUT` se ejecutan en todas las iteraciones y emiten el byte.
- **NOT_DEMONSTRATED:** profundidad 3 o mayor. Harían falta tres celdas de
  trabajo con calendario de fases LIFO coherente; en la clase de ciclo de 9
  solo hay dos direcciones que den el par `CRAZY`/`ROT` con fases distintas
  (71 y 83).
- **NOT_DEMONSTRATED:** que la clase de ciclo de 9 sea la única posible. Se
  eligió por medir que da el calendario LIFO buscado; la clase de 68 también
  contiene parejas `CRAZY`→`ROT` (por ejemplo `84→61`), pero con un ciclo de
  68 fases.

## Reproducir

```
python3 vm_malbolge/tools/stack_loop_lifo2_gen.py
```

El emisor busca el primer layout válido en orden determinista, escribe las dos
imágenes, ejecuta cada caso en `tools/oracle_classic.py` (`stop_on_eof=True`) y
en `runners/malbolge-original/malbolge`, traza las ejecuciones de `W1`/`W2` y
escribe `vm_malbolge/evidence/stack_loop_lifo2.json`. La comparación con el
runner usa el stdout **crudo** (`crudo == esperado` o `crudo == esperado +
b"\n"`), para no repetir la trampa CRLF documentada en `pointer_cell_rt.md`.

---

## Corrección medida (2026-11-07) — el "pop exacto" se acota, no se refuta entero

El texto anterior **se conserva** como registro histórico. La nota de
`NOT_DEMONSTRATED` sigue siendo correcta **para el pop por carga** (extraer una
ranura de dato arbitrario con `ROT` la rota y no la vacía; 10 `ROT` en bucle siguen
bloqueados por el choque de celdas-puntero). Lo que queda **refutado** es la
implicación general de que un valor exacto no puede emitirse: con la máscara
imprimible `121` el doble `crazy` escribe un valor exacto y arbitrario en la celda y
**esa celda lo ejecuta**, emitiendo el byte exacto sin rotación (768 escrituras
medidas, 0 discrepancias; [`epoch_algebra_v3/`](epoch_algebra_v3/)). El coste medido:
la máscara de la celda se consume y hay que rearmarla antes del siguiente uso.
