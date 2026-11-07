# Despacho computado sobre flujo de bytes — frente 3, máquina de bytecode

## Resultado

`vm_malbolge/tools/dispatch2_gen.py` emite `mbir_dispatch2.mb` (29.562 bytes,
**sin LMAO**) que lee un flujo de instrucciones de longitud variable y **enruta
según el opcode**:

| instrucción | bytes | efecto |
|---|---|---|
| `PUSH` | `01 operando` | guarda el operando en la celda de pila |
| `POP` | `F2` | emite el valor guardado (lectura exacta) |

La máquina ejecuta dos instrucciones y para (HALT), o para antes si el flujo se
agota a mitad de instrucción (EOF, parada limpia en los dos motores).

| stdin | salida | qué demuestra |
|---|---|---|
| `01 41 F2` | `68` | el POP emite lo que el PUSH guardó |
| `01 42 F2` | `69` | otro operando, otro valor: el almacén es real |
| `F2 01 43` | `21` | enrutado correcto: POP primero (valor inicial), luego PUSH |
| `01 41 01 42` | (vacío) | dos PUSH, ninguna emisión |
| `F2` | `21` | un POP solo emite el valor inicial |
| `01 41 F2 F2` | `68` | la tercera instrucción se ignora (máquina de 2) |

**8/8 casos** y **111/111 combinaciones** de un barrido (operandos `00..1F`,
`7F`, `80`, `C3`, `FE`, `FF` × tres formas de secuencia) con acuerdo **byte a
byte** entre `oracle_classic.py` (`stop_on_eof=True`) y
`runners/malbolge-original/malbolge`. Evidencia máquina:
`vm_malbolge/evidence/dispatch2.json`.

## El mecanismo: salto computado por el dato

En un programa one-shot cada celda se escribe una sola vez, así que
`mem[P] = crazy(a, mem[P])` es una **función pura del byte leído** (`mem[P]`
vale `V`, fijo). Eligiendo `V` de forma que

```
crazy(0x01, V) = landing_push - 1
crazy(0xF2, V) = landing_pop  - 1
```

un `JMP` que lea `mem[P]` salta al manejador correcto. No hay cadena de
comparaciones ni contador: **el dato es la dirección**. Los cuatro destinos salen
de un `crazy` sobre el opcode, y por eso caen en una banda alta (~29.400-29.650):
los trits 5-9 del opcode son 0 y `crazy(x,0)` solo produce 1 o 2.

Cada despacho lleva su bootstrap cuando arranca en lockstep (k NOPs + un `MOVD`
que lee su propia celda, valor `V(k) = ((7-k) mod 94) + 33`); el segundo despacho
entra con un `d` externo y arranca directamente con el `IN`. La coreografía de
`(c, d)` la calcula un simulador dentro del emisor, y las celdas-puntero se
colocan donde el flujo de `d` las lee; los rellenos de cola se ajustan para que
los dos caminos de cada despacho dejen el **mismo** `d` (si no, la celda-puntero
del despacho siguiente necesitaría dos valores distintos).

## Estandar del loader (honesto)

Las 75 celdas de código decodifican a opcode válido en su propia dirección. De
las 14 celdas de dato, **11 no** decodifican a opcode válido: nunca se ejecutan
como instrucción (el flujo no las visita), solo las leen `MOVD`/`JMP` como dato.
Está listado en el JSON (`dato_no_valido`).

## Relación con el resto de la campaña

- `stack2_oneshot.md`: la pila de profundidad 2 con **horario fijo** (push,
  push, pop, pop) y loader estricto completo. Esta máquina añade el **enrutado**:
  el flujo decide el orden, y la codificación es de longitud variable.
- `native_fold_loop.md`: el bucle de fetch con estado entre bytes.
- El bucle de la máquina de bytecode sigue bloqueado, con causa probada en
  `stack2_oneshot.md` §"Lo que queda bloqueado": `CRAZY` (escritura) y `ROT`
  (lectura) de la misma celda dejan `d` en el mismo sitio y compartirían las
  celdas de puntero.

## Siguiente paso natural (sin bloqueante)

El emisor ya es una plantilla: **N instrucciones** en lugar de 2 (cada despacho
copia con su propio `P`/`V`, los manejadores se duplican por pareja). Eso da una
máquina de bytecode de longitud arbitraria, incluida una pila de profundidad N
con PUSH/POP enrutados, sin tocar el bucle.
