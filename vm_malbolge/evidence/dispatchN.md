# Máquina de bytecode de N instrucciones encadenadas — frente 3, siguiente paso

## Resultado

`vm_malbolge/tools/dispatchN_gen.py` emite `mbir_dispatchN.mb` (29.572 bytes,
**sin LMAO**) que ejecuta un programa de **N = 3 instrucciones leídas del flujo**,
enrutando cada una por su opcode con un salto computado. La diferencia con
`mbir_dispatch2.mb` (2 instrucciones) es que aquí el programa **vive en el flujo
de entrada**, no en la imagen: tres instrucciones encadenadas, con la celda de
pila sobreviviendo de una a otra.

Protocolo de longitud variable: `PUSH (0x35) operando` = 2 bytes,
`POP (0x41)` = 1 byte.

| stdin | instrucciones ejecutadas | salida |
|---|---|---|
| `35 41 41 35 42 41` | push 'A', pop, push 'B' | `78` |
| `35 41 35 42 41 41` | push 'A', push 'B', pop | `52` |
| `41 35 41 41 35 42` | pop, push 'A', pop | `0b 48` |
| `35 41 35 42 35 43 41` | push, push, push (el 4º opcode se ignora) | (vacía) |
| `35 41 41 35` | push 'A', pop, pop | `78 98` |
| `35 41` | push 'A' y EOF a mitad | (vacía) |
| `41` | pop con la pila a su valor inicial | `0b` |
| (vacío) | — | (vacía) |
| `35 00 41 35 ff 41` | push `0x00`, pop, push `0xff`, pop | `55` |

**9/9 acuerdo byte a byte** entre `oracle_classic.py` (`stop_on_eof=True`) y
`runners/malbolge-original/malbolge`, HALT tras la tercera instrucción (o EOF si
el flujo se agota a mitad de una). Evidencia máquina:
`vm_malbolge/evidence/dispatchN.json`.

## Lo que midió el diseño (no se eligió a ojo)

**El protocolo de opcodes es un resultado de medida.** La constante `V` de la
celda de despacho tiene que ser imprimible (es una celda del fichero), y
`V < 243` deja los trits 5-9 a cero, así que `crazy(opcode, V)` tiene los trits
altos fijados por el opcode: **todos los destinos caen en una ventana de ~284
celdas** (`[29280, 29564]`). Con manejadores que ocupan ~26 celdas (la lectura
exacta de 10 rotaciones) haría falta separarlos 32 celdas, y la búsqueda sobre
las 255×255 parejas de opcodes —con el constraint de emparejado, porque cada `V`
da un destino push y uno pop— dio un máximo de **N = 2**.

Para llegar a N = 3 hubo que **reducir el manejador del POP a una rotación**: el
POP emite `rot(slot) & 255` y rota la celda, en vez de leer el valor exacto con
`rot^10`. Con manejadores de ~10 celdas la separación baja a 14 y la búsqueda
encontró protocolos con N = 3; el mejor es `PUSH = 0x35 (53)`, `POP = 0x41 (65)`
con `V = [67, 72, 90]`. El modelo de referencia aplica el mismo `rot`, así que la
semántica es exacta aunque el valor emitido sea el rotado: `35 41 41 35` da
`78 98` = `rot(slot)` y `rot²(slot)`.

## Arquitectura

Tres despachos encadenados (`D_0` en la dirección 0 con su bootstrap de
lockstep, `D_1` en 45, `D_2` en 75). Cada uno lee el opcode, escribe
`mem[P_k] = crazy(opcode, V_k)` —función pura del byte, porque la celda se
escribe una sola vez— y el `JMP` que la lee salta al manejador. Los manejadores
de cada pareja salen al despacho siguiente; los de la última, al `HALT` (127).

Las direcciones de las celdas-puntero las calcula un simulador de `(c, d)` dentro
del emisor, y los rellenos de cola se ajustan para que los dos caminos de cada
despacho dejen el **mismo** `d`. Las regiones de memoria van disjuntas: código en
`[0,6] ∪ [45,49] ∪ [75,79] ∪ {127}` y los destinos (~29.500), celdas `P` en el
hueco `[50,74]`, y la pila con sus punteros en `[82,126]`.

## Estandar del loader (honesto)

Las 69 celdas de código decodifican a opcode válido en su propia dirección. De
las 19 celdas de dato, **16 no**: nunca se ejecutan como instrucción, solo las
leen `MOVD`/`JMP` como dato. Listado en `dispatchN.json` (`dato_no_valido`).

## Lo que queda medido y bloqueado

**N > 3 está bloqueado por la ventana de destinos**, no por la coreografía: con
`V` imprimible los destinos viven en ~284 celdas, y con manejadores de ~10 celdas
caben como máximo 6 destinos separados 14 (3 parejas). Para más instrucciones
haría falta una constante de despacho no imprimible (imposible en una celda de
fichero) o un mecanismo que disperse los destinos —por ejemplo una celda de
despacho escrita en tiempo de ejecución con una cadena de constantes, que es la
misma salida que documenta `stack2_oneshot.md` para la pila con bucle.

El bucle de la máquina sigue bloqueado por la causa probada en
`stack2_oneshot.md`: `CRAZY` (escritura) y `ROT` (lectura) de la misma celda
dejan `d` en el mismo sitio y compartirían las celdas de puntero.
