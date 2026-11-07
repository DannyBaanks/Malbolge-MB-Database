# Bucle de pila por fases — CRAZY y ROT sobre la misma celda, en iteraciones distintas

## Resultado

`vm_malbolge/tools/stack_loop_phase_gen.py` emite dos imágenes de **256 bytes,
sin LMAO**:

| artefacto | sha256 | papel |
|---|---|---|
| `vm_malbolge/src/mbir_stack_loop_phase.mb` | `ad40caf8e62ab763d8194f7546ffa4974993d4224345910b992a46e0451e83d1` | positivo |
| `vm_malbolge/src/mbir_stack_loop_phase_ctrl.mb` | `5022713b1619b4a6ed40e411189dbe69c865f54130937fe0591ed547e7edc4fa` | control `W` inerte |

El positivo mantiene un bucle real en el que la **misma celda de pila `S`** se
escribe con `CRAZY` en la iteración 0 y se lee con `ROT` en la iteración 1; a
la novena iteración el ciclo se repite. El control cambia **una sola celda**
(la instrucción `W`) por un valor cuyo ciclo de cifrado nunca decodifica a
`CRAZY` ni a `ROT`, y la salida pasa a ser el flujo de entrada sin tocar.
**8/8 casos en oráculo y runner C, positivo y control**, incluidos 4096 bytes
aleatorios. Evidencia máquina: `vm_malbolge/evidence/stack_loop_phase.json`.

## El bloqueante que ataca

`stack2_oneshot.md` (líneas 68-78) demostró que, con la primitiva de
restauración por 2-ciclo, **una celda no puede escribirse y leerse en el mismo
ciclo**: `CRAZY` y `ROT` dejan ambos `d = S`, comparten las celdas-puntero
`(S+1, S+2)` y los valores que necesitan para restaurarse (sus propias
direcciones) no pueden coincidir. La salida documentada era una celda-puntero
escrita en runtime; esa primitiva se cerró one-shot en `pointer_cell_rt.md`.

## La salida: el ciclo de cifrado como selector de fase

En este dialecto cada celda ejecutada se cifra con `XLAT2`. Si una celda de
trabajo **no se restaura**, su valor avanza por su ciclo de `XLAT2` y el opcode
que decodifica cambia en cada iteración. Ese es el selector de fase, y es
estado runtime puro: no hace falta una celda-puntero de fase.

Medido en la dirección `A_W = 83` (mod 94), con la celda arrancando como
`CRAZY`:

| iteración | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| valor de celda | 73 | 50 | 80 | 66 | 62 | 76 | 79 | 67 | 85 |
| opcode | `CRAZY` | `ROT` | inv | inv | inv | inv | `NOP` | inv | inv |

- **Iteración 0:** `CRAZY` escribe `mem[S] = crazy(byte, mem[S])`.
- **Iteración 1:** `ROT` lee `mem[S]`, lo rota y lo deja en `a`.
- **Iteraciones 2..8:** la celda no toca `S` (opcodes inválidos = NOP).
- **Iteración 9:** el ciclo de `XLAT2` vuelve a 73 y se repite.

La clave: hay **una sola celda de instrucción** para escritura y lectura, así
que hay **una sola pareja de punteros** `(S+1, S+2)`. La colisión del bloqueante
desaparece porque no hay dos direcciones que la necesiten.

## Programa

Con `S = 50`, `A_IN = 43`, `A_MOVD = 60`, `A_NOP = 88`, `A_OUT = 119`,
`A_W = 83`:

```
bootstrap:
  0  MOVD    d = mem[0] = 40
  1  MOVD    d = mem[41] = 53
  2  JMP     c = mem[54] = 42  (landing antes de IN)

vuelta (14 pasos):
  IN        a = byte
  J_IN      primer salto restaura IN; segundo despacha a MOVD
  M  MOVD   d = mem[S+8] = S-6   (post d = S-5)
  J_M       restaura MOVD; despacha a NOP
  P  NOP    consume d            (post d = S-2)
  J_P       restaura NOP; despacha a W con d = S
  W         CRAZY / ROT / NOP según la fase
  J_W       UN solo salto: despacha a OUT; NO restaura W
  O  OUT    emite a & 255
  J_O       restaura OUT; despacha de vuelta a IN
```

Los punteros viven en `S-6..S+8` y **ninguno cae en `S`**: la celda de pila no
se usa como puntero. `IN`, `MOVD`, `NOP` y `OUT` usan valores en 2-ciclo de
`XLAT2` (74/70) y se restauran en cada vuelta con el par JMP de siempre. `W` es
la única celda que no se restaura, y por eso avanza por su ciclo.

## Trazado verificado

Trazando la imagen positiva en el oráculo (instrumentación del mismo bucle de
`oracle_classic.run`, registrada en `trazado_w` del JSON), las primeras diez
ejecuciones de la celda `W` (dirección 83) son:

| paso | opcode | `d` con el que se ejecuta | valor de la celda `W` | `mem[S]` |
|---|---|---|---|---|
| 13 | `CRAZY` | 50 | 50 | 29544 |
| 27 | `ROT` | 50 | 80 | 9848 |
| 41 | inválido | 50 | 66 | 9848 |
| 55 | inválido | 50 | 62 | 9848 |
| 69 | inválido | 50 | 76 | 9848 |
| 83 | inválido | 50 | 79 | 9848 |
| 97 | `NOP` | 50 | 67 | 9848 |
| 111 | inválido | 50 | 85 | 9848 |
| 125 | inválido | 50 | 73 | 9848 |
| 139 | `CRAZY` | 50 | 50 | 29551 |

Las diez ejecuciones ocurren **con `d = 50 = S`**: la escritura y la lectura
caen sobre la misma celda, en iteraciones distintas (14 pasos de diferencia),
y la novena iteración vuelve a `CRAZY`. `mem[S]` cambia en la fase `CRAZY`, en
la fase `ROT`, y no se mueve en las siete de tránsito.

## Modelo de salida (verificado, no supuesto)

Para el byte `i`-ésimo de la entrada, con `fase = i mod 9`:

| fase | operación | salida |
|---|---|---|
| 0 | `S = crazy(byte, S)` | `S & 255` |
| 1 | `S = rot(S)` | `S & 255` |
| 2..8 | ninguna sobre `S` | el byte de entrada |

Las fases 2..8 son **tránsito**: `IN` y `OUT` siguen ejecutándose y emiten el
byte. Es una consecuencia del diseño de una sola celda de trabajo, no un
defecto oculto; el JSON lo registra en `alcance.no_demostrado`. Con entrada
`AB` los dos primeros bytes de salida son el push y la lectura rotada; los
siguientes son los bytes de relleno tal cual.

## Control negativo

El control usa la **misma imagen** con un solo cambio: `mem[A_W] = 42` en vez de
73. El ciclo de `XLAT2` de 42 en la dirección 83 es
`[42, 114, 125, 105]` y sus opcodes son `[31, 9, 20, 0]`: todos inválidos. La
celda nunca escribe ni lee `S`, y la salida esperada es exactamente la entrada.
El control da **8/8** en ambos motores. Esto atribuye el comportamiento del
positivo a la celda `W`, no a la cadena de punteros.

## Layout y estándar de celdas

| parámetro | valor |
|---|---|
| `S` celda de pila | 50 |
| `A_IN` / `A_MOVD` / `A_NOP` / `A_OUT` / `A_W` | 43 / 60 / 88 / 119 / 83 |
| `v_stack` inicial | 33 |
| punteros | `41→53, 45→60, 46→87, 48→88, 49→82, 51→118, 53→119, 54→42, 56→43, 57→59, 58→44` |
| landings | `42, 59, 82, 87, 118` |
| pasos por vuelta | 14 |

Igual que `native_fold_loop_gen.py`: las celdas de **código** decodifican a
opcode válido en su propia dirección; las celdas de **puntero** son imprimibles
pero pueden decodificar a un opcode inválido porque nunca se ejecutan (solo las
leen `MOVD`/`JMP` como datos). El control, a propósito, arranca `W` en un
opcode inválido: es una celda inerte y así se documenta.

## Alcance y NOT_DEMONSTRATED

- **Demostrado:** `CRAZY` y `ROT` sobre la misma celda `S` en iteraciones
  distintas dentro de un bucle real; la fase la selecciona el ciclo de cifrado
  de `W`; sin celda-puntero de fase y sin colisión de pares. Doble motor, 8/8
  positivo y 8/8 control, 4096 bytes aleatorios incluidos.
- **NOT_DEMONSTRATED:** pila LIFO de profundidad 2 o mayor en bucle. Este
  artefacto demuestra la primitiva de escritura/lectura alternada, no una pila
  completa.
- **NOT_DEMONSTRATED:** supresión de las fases de tránsito 2..8. `IN` y `OUT`
  se ejecutan en todas las iteraciones y emiten el byte.
- **NOT_DEMONSTRATED:** que el ciclo de 9 sea el único posible. Se eligió
  `A_W = 83` por `CRAZY@0` y `ROT@1` medidos; otras direcciones con `ROT`
  posterior (p. ej. 71, `ROT@5`) no se construyeron aquí.

## Reproducir

```
python3 vm_malbolge/tools/stack_loop_phase_gen.py
```

El emisor busca el primer layout válido en orden determinista, escribe las dos
imágenes, ejecuta cada caso en `tools/oracle_classic.py` (`stop_on_eof=True`) y
en `runners/malbolge-original/malbolge`, y escribe
`vm_malbolge/evidence/stack_loop_phase.json`. La comparación con el runner usa
el stdout **crudo**: `crudo == esperado` o `crudo == esperado + b"\n"`, para no
repetir la trampa CRLF documentada en `pointer_cell_rt.md`.
